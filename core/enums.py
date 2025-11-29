"""
Enumerace pro typovou bezpečnost
"""
from enum import Enum


class PermissionLevel(str, Enum):
    """Úrovně oprávnění"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class TokenType(str, Enum):
    """Typy tokenů"""
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"


class UserStatus(str, Enum):
    """Stavy uživatelského účtu"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class PasswordStrength(str, Enum):
    """Síla hesla"""
    WEAK = "Slabé"
    MEDIUM = "Střední"
    STRONG = "Silné"