"""
Data modely pro autentizaci
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict
from core.enums import UserStatus, TokenType


@dataclass
class User:
    """Model uživatele"""
    id: int
    email: str
    password_hash: str
    created_at: datetime
    requested_group_id: Optional[int] = None
    is_active: bool = True
    
    @property
    def status(self) -> UserStatus:
        return UserStatus.ACTIVE if self.is_active else UserStatus.INACTIVE


@dataclass
class Group:
    """Model skupiny"""
    id: int
    name: str
    description: Optional[str] = None


@dataclass
class SchemaPermission:
    """Model oprávnění ke schématu"""
    group_id: int
    schema_name: str
    permission: str  # 'read' nebo 'write'


@dataclass
class UserGroup:
    """Vazba uživatel-skupina"""
    user_id: int
    group_id: int


@dataclass
class PasswordResetToken:
    """Token pro reset hesla"""
    id: int
    user_id: int
    token: str
    expires_at: datetime
    used: bool = False
    created_at: Optional[datetime] = None
    
    @property
    def is_valid(self) -> bool:
        """Zkontroluje, zda je token platný"""
        if self.used:
            return False
        if datetime.now() > self.expires_at:
            return False
        return True
    
    @property
    def token_type(self) -> TokenType:
        return TokenType.PASSWORD_RESET


@dataclass
class LoginResult:
    """Výsledek přihlášení"""
    success: bool
    user: Optional[User] = None
    permissions: Optional[Dict[str, str]] = None
    error_message: Optional[str] = None


@dataclass
class RegistrationResult:
    """Výsledek registrace"""
    success: bool
    user_id: Optional[int] = None
    error_message: Optional[str] = None


@dataclass
class TokenResult:
    """Výsledek operace s tokenem"""
    success: bool
    token: Optional[str] = None
    user_id: Optional[int] = None
    email: Optional[str] = None
    message: Optional[str] = None