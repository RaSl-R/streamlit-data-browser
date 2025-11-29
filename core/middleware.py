"""
Middleware - Auth guards a permission decorators
"""
import streamlit as st
from functools import wraps
from typing import Callable
from core.session import SessionManager
from core.exceptions import AuthenticationError, PermissionDeniedError
from core.logger import logger


def require_auth(func: Callable) -> Callable:
    """
    Dekorátor vyžadující přihlášení.
    
    Usage:
        @require_auth
        def protected_view():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not SessionManager.is_logged_in():
            st.error("🔒 Pro přístup k této stránce se musíte přihlásit.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def require_permission(schema_name: str, level: str = "read"):
    """
    Dekorátor vyžadující specifické oprávnění.
    
    Args:
        schema_name: Jméno schématu
        level: Úroveň oprávnění ('read' nebo 'write')
    
    Usage:
        @require_permission("public", "write")
        def edit_table():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not SessionManager.is_logged_in():
                raise AuthenticationError("Není přihlášen žádný uživatel")
            
            if not SessionManager.has_permission(schema_name, level):
                user_email = SessionManager.get_user_email()
                logger.warning(
                    f"Permission denied: {user_email} tried to access "
                    f"{schema_name} with {level} permission"
                )
                raise PermissionDeniedError(
                    f"Nemáte oprávnění '{level}' pro schéma '{schema_name}'"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class AuthGuard:
    """Helper třída pro kontrolu autorizace"""
    
    @staticmethod
    def check_schema_access(schema_name: str, level: str = "read") -> bool:
        """
        Zkontroluje přístup ke schématu.
        
        Args:
            schema_name: Jméno schématu
            level: Požadovaná úroveň
            
        Returns:
            True pokud má přístup
            
        Raises:
            PermissionDeniedError: Pokud nemá přístup
        """
        if not SessionManager.has_permission(schema_name, level):
            raise PermissionDeniedError(
                f"Nemáte oprávnění '{level}' k schématu '{schema_name}'"
            )
        return True
    
    @staticmethod
    def filter_accessible_schemas(schemas: list, level: str = "read") -> list:
        """
        Vyfiltruje pouze schémata, ke kterým má uživatel přístup.
        
        Args:
            schemas: Seznam všech schémat
            level: Požadovaná úroveň
            
        Returns:
            Seznam přístupných schémat
        """
        permissions = SessionManager.get_permissions()
        
        accessible = []
        for schema in schemas:
            user_level = permissions.get(schema)
            
            if level == "read":
                if user_level in ["read", "write"]:
                    accessible.append(schema)
            elif level == "write":
                if user_level == "write":
                    accessible.append(schema)
        
        return accessible