"""
Globální custom výjimky
"""


class DataBrowserException(Exception):
    """Základní výjimka aplikace"""
    pass


class AuthenticationError(DataBrowserException):
    """Chyby při autentizaci"""
    pass


class PermissionDeniedError(DataBrowserException):
    """Nedostatečná oprávnění"""
    pass


class ValidationError(DataBrowserException):
    """Chyby při validaci vstupu"""
    pass


class DatabaseError(DataBrowserException):
    """Chyby databáze"""
    pass


class TokenError(DataBrowserException):
    """Chyby při práci s tokeny"""
    pass


class EmailError(DataBrowserException):
    """Chyby při odesílání emailů"""
    pass


class SQLInjectionAttempt(ValidationError):
    """Pokus o SQL injection"""
    pass