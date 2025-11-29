"""
Service layer pro autentizaci
"""
from typing import Tuple
from passlib.context import CryptContext

from auth.models import LoginResult, RegistrationResult, TokenResult
from auth.repositories import UserRepository, GroupRepository, TokenRepository
from auth.validation.email_validator import EmailValidator
from auth.validation.password_validator import PasswordValidator
from core.database import get_db_transaction
from core.exceptions import AuthenticationError, ValidationError
from core.logger import get_auth_logger

logger = get_auth_logger()

# Password context
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt_sha256", "bcrypt"],
    deprecated="auto"
)


class AuthService:
    """Service pro autentizační operace"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hashuje heslo"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Ověří heslo"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False
    
    @classmethod
    def login(cls, email: str, password: str) -> LoginResult:
        """
        Přihlásí uživatele.
        
        Args:
            email: E-mailová adresa
            password: Heslo
            
        Returns:
            LoginResult s výsledkem přihlášení
        """
        try:
            # Validace
            email = EmailValidator.normalize(email)
            
            with get_db_transaction() as conn:
                # Najdeme uživatele
                user = UserRepository.find_by_email(conn, email)
                
                if not user:
                    logger.warning(f"Login attempt for non-existent user: {email}")
                    return LoginResult(
                        success=False,
                        error_message="Neplatné přihlašovací údaje"
                    )
                
                # Kontrola aktivního účtu
                if not user.is_active:
                    logger.warning(f"Login attempt for inactive user: {email}")
                    return LoginResult(
                        success=False,
                        error_message="Váš účet byl deaktivován. Kontaktujte administrátora."
                    )
                
                # Ověření hesla
                if not cls.verify_password(password, user.password_hash):
                    logger.warning(f"Failed login attempt for: {email}")
                    return LoginResult(
                        success=False,
                        error_message="Neplatné přihlašovací údaje"
                    )
                
                # Načteme oprávnění
                permissions = UserRepository.get_permissions(conn, email)
                
                logger.info(f"Successful login: {email}")
                return LoginResult(
                    success=True,
                    user=user,
                    permissions=permissions
                )
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return LoginResult(
                success=False,
                error_message="Došlo k chybě při přihlašování"
            )
    
    @classmethod
    def register(
        cls,
        email: str,
        password: str,
        requested_group_id: int
    ) -> RegistrationResult:
        """
        Registruje nového uživatele.
        
        Args:
            email: E-mailová adresa
            password: Heslo
            requested_group_id: ID požadované skupiny
            
        Returns:
            RegistrationResult
        """
        try:
            # Validace
            EmailValidator.validate_or_raise(email)
            PasswordValidator.validate_or_raise(password)
            
            email = EmailValidator.normalize(email)
            password_hash = cls.hash_password(password)
            
            with get_db_transaction() as conn:
                # Kontrola, zda email již neexistuje
                existing = UserRepository.find_by_email(conn, email)
                if existing:
                    return RegistrationResult(
                        success=False,
                        error_message="Tento e-mail je již registrován."
                    )
                
                # Vytvoření uživatele
                user_id = UserRepository.create(
                    conn, email, password_hash, requested_group_id
                )
                
                logger.info(f"New user registered: {email}")
                return RegistrationResult(
                    success=True,
                    user_id=user_id
                )
                
        except ValidationError as e:
            return RegistrationResult(
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return RegistrationResult(
                success=False,
                error_message="Došlo k chybě při registraci"
            )
    
    @classmethod
    def request_password_reset(cls, email: str) -> TokenResult:
        """
        Vytvoří token pro reset hesla.
        
        Args:
            email: E-mail uživatele
            
        Returns:
            TokenResult
        """
        try:
            email = EmailValidator.normalize(email)
            
            with get_db_transaction() as conn:
                user = UserRepository.find_by_email(conn, email)
                
                # Z bezpečnostních důvodů vždy vracíme success
                if not user:
                    return TokenResult(
                        success=True,
                        message="Pokud účet s tímto e-mailem existuje, byl odeslán reset link."
                    )
                
                if not user.is_active:
                    return TokenResult(
                        success=False,
                        message="Tento účet je deaktivován."
                    )
                
                # Vytvoření tokenu
                token = TokenRepository.create_reset_token(conn, user.id)
                
                logger.info(f"Password reset requested for: {email}")
                return TokenResult(
                    success=True,
                    token=token,
                    email=email
                )
                
        except Exception as e:
            logger.error(f"Password reset request error: {e}")
            return TokenResult(
                success=False,
                message="Došlo k chybě při vytváření reset tokenu."
            )
    
    @classmethod
    def reset_password(cls, token: str, new_password: str) -> TokenResult:
        """
        Dokončí reset hesla.
        
        Args:
            token: Reset token
            new_password: Nové heslo
            
        Returns:
            TokenResult
        """
        try:
            # Validace hesla
            PasswordValidator.validate_or_raise(new_password)
            
            with get_db_transaction() as conn:
                # Ověření tokenu
                token_obj = TokenRepository.verify_token(conn, token)
                
                if not token_obj:
                    return TokenResult(
                        success=False,
                        message="Reset token je neplatný nebo vypršel."
                    )
                
                # Najdeme uživatele
                user = UserRepository.find_by_email(conn, 
                    conn.execute(
                        text("SELECT email FROM auth.users WHERE id = :id"),
                        {"id": token_obj.user_id}
                    ).scalar()
                )
                
                # Update hesla
                password_hash = cls.hash_password(new_password)
                UserRepository.update_password(conn, token_obj.user_id, password_hash)
                
                # Označíme token jako použitý
                TokenRepository.mark_token_used(conn, token)
                
                logger.info(f"Password reset completed for user ID: {token_obj.user_id}")
                return TokenResult(
                    success=True,
                    email=user.email,
                    message=f"Heslo bylo úspěšně změněno pro {user.email}"
                )
                
        except ValidationError as e:
            return TokenResult(
                success=False,
                message=str(e)
            )
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            return TokenResult(
                success=False,
                message="Došlo k chybě při změně hesla."
            )