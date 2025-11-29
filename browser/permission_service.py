"""
Služba pro kontrolu oprávnění v Browser modulu
"""
from typing import Dict, List
from core.session import SessionManager
from core.exceptions import PermissionDeniedError
from core.enums import PermissionLevel
from core.logger import logger

class BrowserPermissionService:
    """Service pro kontrolu oprávnění v Data Browser"""
    
    @staticmethod
    def check_schema_read_access(schema_name: str) -> bool:
        """
        Zkontroluje, zda má uživatel read přístup ke schématu.
        
        Args:
            schema_name: Jméno schématu
            
        Returns:
            True pokud má přístup
            
        Raises:
            PermissionDeniedError: Pokud nemá přístup
        """
        if not SessionManager.has_permission(schema_name, PermissionLevel.READ):
            user_email = SessionManager.get_user_email()
            logger.warning(
                f"Read access denied for {user_email} to schema {schema_name}"
            )
            raise PermissionDeniedError(
                f"Nemáte oprávnění číst data ze schématu '{schema_name}'"
            )
        return True
    
    @staticmethod
    def check_schema_write_access(schema_name: str) -> bool:
        """
        Zkontroluje, zda má uživatel write přístup ke schématu.
        
        Args:
            schema_name: Jméno schématu
            
        Returns:
            True pokud má přístup
            
        Raises:
            PermissionDeniedError: Pokud nemá přístup
        """
        if not SessionManager.has_permission(schema_name, PermissionLevel.WRITE):
            user_email = SessionManager.get_user_email()
            logger.warning(
                f"Write access denied for {user_email} to schema {schema_name}"
            )
            raise PermissionDeniedError(
                f"Nemáte oprávnění 'write' k zápisu do schématu '{schema_name}'"
            )
        return True
    
    @staticmethod
    def get_accessible_schemas(level: str = "read") -> List[str]:
        """
        Vrátí seznam schémat, ke kterým má uživatel přístup.
        
        Args:
            level: Požadovaná úroveň oprávnění ('read' nebo 'write')
            
        Returns:
            Seznam názvů schémat
        """
        permissions = SessionManager.get_permissions()
        accessible = []
        
        for schema_name, user_level in permissions.items():
            if level == "read":
                if user_level in [PermissionLevel.READ, PermissionLevel.WRITE]:
                    accessible.append(schema_name)
            elif level == "write":
                if user_level == PermissionLevel.WRITE:
                    accessible.append(schema_name)
        
        return sorted(accessible)
    
    @staticmethod
    def has_write_access(schema_name: str) -> bool:
        """
        Bezpečná kontrola write přístupu bez vyvolání výjimky.
        
        Args:
            schema_name: Jméno schématu
            
        Returns:
            True pokud má write přístup
        """
        return SessionManager.has_permission(schema_name, PermissionLevel.WRITE)