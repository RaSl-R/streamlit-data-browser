"""
Session management pro Streamlit
"""
import streamlit as st
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class UserSession:
    """Uživatelská session data"""
    email: str
    permissions: Dict[str, str]
    is_active: bool = True


class SessionManager:
    """Manager pro práci se Streamlit session state"""
    
    @staticmethod
    def init_session() -> None:
        """Inicializuje základní session state"""
        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False
        
        if "show_password_reset" not in st.session_state:
            st.session_state.show_password_reset = False
        
        if "editor_key_counter" not in st.session_state:
            st.session_state.editor_key_counter = 0
        
        if "filter_applied" not in st.session_state:
            st.session_state.filter_applied = False
        
        if "where_clause" not in st.session_state:
            st.session_state.where_clause = ""
        
        if "current_page" not in st.session_state:
            st.session_state.current_page = 1
        
        if "reload_data" not in st.session_state:
            st.session_state.reload_data = True
    
    @staticmethod
    def login(email: str, permissions: Dict[str, str]) -> None:
        """
        Přihlásí uživatele.
        
        Args:
            email: Email uživatele
            permissions: Slovník schéma -> oprávnění
        """
        st.session_state.logged_in = True
        st.session_state.user_email = email
        st.session_state.permissions = permissions
    
    @staticmethod
    def logout() -> None:
        """Odhlásí uživatele a vyčistí session"""
        st.session_state.clear()
        st.rerun()
    
    @staticmethod
    def is_logged_in() -> bool:
        """Zkontroluje, zda je uživatel přihlášen"""
        return st.session_state.get("logged_in", False)
    
    @staticmethod
    def get_current_user() -> Optional[UserSession]:
        """
        Vrátí aktuálního přihlášeného uživatele.
        
        Returns:
            UserSession nebo None
        """
        if not SessionManager.is_logged_in():
            return None
        
        return UserSession(
            email=st.session_state.get("user_email"),
            permissions=st.session_state.get("permissions", {})
        )
    
    @staticmethod
    def get_user_email() -> Optional[str]:
        """Vrátí email přihlášeného uživatele"""
        return st.session_state.get("user_email")
    
    @staticmethod
    def get_permissions() -> Dict[str, str]:
        """Vrátí oprávnění přihlášeného uživatele"""
        return st.session_state.get("permissions", {})
    
    @staticmethod
    def has_permission(schema_name: str, required_level: str) -> bool:
        """
        Zkontroluje, zda má uživatel požadované oprávnění.
        
        Args:
            schema_name: Jméno schématu
            required_level: Požadovaná úroveň ('read' nebo 'write')
            
        Returns:
            True pokud má oprávnění
        """
        permissions = SessionManager.get_permissions()
        user_level = permissions.get(schema_name)
        
        if required_level == "read":
            return user_level in ["read", "write"]
        elif required_level == "write":
            return user_level == "write"
        
        return False
    
    @staticmethod
    def set_message(message: str) -> None:
        """Nastaví dočasnou zprávu pro zobrazení"""
        st.session_state.message = message
    
    @staticmethod
    def get_and_clear_message() -> Optional[str]:
        """Vrátí a smaže zprávu"""
        message = st.session_state.get("message")
        if message:
            del st.session_state.message
        return message