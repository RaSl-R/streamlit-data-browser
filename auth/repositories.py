"""
Repository layer - SQL dotazy pro auth tabulky
"""
from typing import Optional, List, Dict
from sqlalchemy import text
from sqlalchemy.engine import Connection
from datetime import datetime, timedelta
import secrets

from auth.models import (
    User, Group, PasswordResetToken, SchemaPermission
)
from config.constants import TOKEN_EXPIRY_HOURS, TOKEN_LENGTH
from core.exceptions import DatabaseError
from core.logger import logger


class UserRepository:
    """Repository pro práci s uživateli"""
    
    @staticmethod
    def find_by_email(conn: Connection, email: str) -> Optional[User]:
        """Najde uživatele podle emailu"""
        try:
            row = conn.execute(
                text("""
                    SELECT id, email, password_hash, created_at, 
                           requested_group_id, is_active
                    FROM auth.users 
                    WHERE email = :email
                """),
                {"email": email}
            ).fetchone()
            
            if not row:
                return None
            
            return User(
                id=row[0],
                email=row[1],
                password_hash=row[2],
                created_at=row[3],
                requested_group_id=row[4],
                is_active=row[5]
            )
        except Exception as e:
            logger.error(f"Error finding user by email: {e}")
            raise DatabaseError(f"Chyba při hledání uživatele: {e}")
    
    @staticmethod
    def create(
        conn: Connection, 
        email: str, 
        password_hash: str, 
        requested_group_id: Optional[int] = None
    ) -> int:
        """Vytvoří nového uživatele"""
        try:
            result = conn.execute(
                text("""
                    INSERT INTO auth.users 
                    (email, password_hash, requested_group_id)
                    VALUES (:email, :hash, :requested_group_id)
                    RETURNING id
                """),
                {
                    "email": email,
                    "hash": password_hash,
                    "requested_group_id": requested_group_id
                }
            )
            return result.scalar()
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise DatabaseError(f"Chyba při vytváření uživatele: {e}")
    
    @staticmethod
    def update_password(conn: Connection, user_id: int, password_hash: str) -> None:
        """Aktualizuje heslo uživatele"""
        try:
            conn.execute(
                text("""
                    UPDATE auth.users 
                    SET password_hash = :hash 
                    WHERE id = :user_id
                """),
                {"hash": password_hash, "user_id": user_id}
            )
        except Exception as e:
            logger.error(f"Error updating password: {e}")
            raise DatabaseError(f"Chyba při aktualizaci hesla: {e}")
    
    @staticmethod
    def update_requested_group(
        conn: Connection, 
        email: str, 
        group_id: int
    ) -> None:
        """Aktualizuje požadovanou skupinu"""
        try:
            conn.execute(
                text("""
                    UPDATE auth.users
                    SET requested_group_id = :group_id
                    WHERE email = :email
                """),
                {"group_id": group_id, "email": email}
            )
        except Exception as e:
            logger.error(f"Error updating requested group: {e}")
            raise DatabaseError(f"Chyba při aktualizaci skupiny: {e}")
    
    @staticmethod
    def get_permissions(conn: Connection, email: str) -> Dict[str, str]:
        """Získá oprávnění uživatele"""
        try:
            query = text("""
                SELECT p.schema_name, MAX(p.permission) as max_permission
                FROM auth.users u
                JOIN auth.user_groups ug ON u.id = ug.user_id
                JOIN auth.group_schema_permissions p ON ug.group_id = p.group_id
                WHERE u.email = :email
                GROUP BY p.schema_name
            """)
            result = conn.execute(query, {"email": email})
            return {row[0]: row[1] for row in result}
        except Exception as e:
            logger.error(f"Error getting permissions: {e}")
            return {}


class GroupRepository:
    """Repository pro skupiny"""
    
    @staticmethod
    def get_all(conn: Connection) -> Dict[str, int]:
        """Vrátí všechny skupiny"""
        try:
            result = conn.execute(
                text("SELECT id, name FROM auth.groups ORDER BY name")
            )
            return {row[1]: row[0] for row in result}
        except Exception as e:
            logger.error(f"Error getting groups: {e}")
            return {}
    
    @staticmethod
    def get_requested_group_name(
        conn: Connection, 
        email: str
    ) -> Optional[str]:
        """Vrátí jméno požadované skupiny"""
        try:
            row = conn.execute(
                text("""
                    SELECT g.name
                    FROM auth.users u
                    LEFT JOIN auth.groups g ON u.requested_group_id = g.id
                    WHERE u.email = :email
                """),
                {"email": email}
            ).fetchone()
            
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Error getting requested group: {e}")
            return None


class TokenRepository:
    """Repository pro tokeny"""
    
    @staticmethod
    def create_reset_token(conn: Connection, user_id: int) -> str:
        """Vytvoří reset token"""
        try:
            # Invalidujeme staré tokeny
            conn.execute(
                text("""
                    UPDATE auth.password_resets 
                    SET used = TRUE 
                    WHERE user_id = :user_id AND used = FALSE
                """),
                {"user_id": user_id}
            )
            
            # Vytvoříme nový token
            token = secrets.token_urlsafe(TOKEN_LENGTH)
            expires_at = datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
            
            conn.execute(
                text("""
                    INSERT INTO auth.password_resets 
                    (user_id, token, expires_at)
                    VALUES (:user_id, :token, :expires_at)
                """),
                {
                    "user_id": user_id,
                    "token": token,
                    "expires_at": expires_at
                }
            )
            
            return token
        except Exception as e:
            logger.error(f"Error creating reset token: {e}")
            raise DatabaseError(f"Chyba při vytváření tokenu: {e}")
    
    @staticmethod
    def verify_token(
        conn: Connection, 
        token: str
    ) -> Optional[PasswordResetToken]:
        """Ověří reset token"""
        try:
            row = conn.execute(
                text("""
                    SELECT pr.id, pr.user_id, pr.token, pr.expires_at, 
                           pr.used, pr.created_at, u.email, u.is_active
                    FROM auth.password_resets pr
                    JOIN auth.users u ON pr.user_id = u.id
                    WHERE pr.token = :token
                """),
                {"token": token}
            ).fetchone()
            
            if not row:
                return None
            
            # Kontroly platnosti
            if row[4]:  # used
                return None
            if datetime.now() > row[3]:  # expires_at
                return None
            if not row[7]:  # is_active
                return None
            
            return PasswordResetToken(
                id=row[0],
                user_id=row[1],
                token=row[2],
                expires_at=row[3],
                used=row[4],
                created_at=row[5]
            )
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    @staticmethod
    def mark_token_used(conn: Connection, token: str) -> None:
        """Označí token jako použitý"""
        try:
            conn.execute(
                text("""
                    UPDATE auth.password_resets 
                    SET used = TRUE 
                    WHERE token = :token
                """),
                {"token": token}
            )
        except Exception as e:
            logger.error(f"Error marking token as used: {e}")
            raise DatabaseError(f"Chyba při označování tokenu: {e}")