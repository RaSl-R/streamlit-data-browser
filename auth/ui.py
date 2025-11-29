"""
UI komponenty pro autentizaci
"""
import streamlit as st
import time

from auth.service import AuthService
from auth.repositories import GroupRepository
from auth.validation.email_validator import EmailValidator
from auth.validation.password_validator import PasswordValidator
from core.session import SessionManager
from core.database import get_db_transaction
from notifications.email_service import EmailService


class AuthUI:
    """UI komponenty pro autentizaci"""
    
    @staticmethod
    def login_form():
        """Přihlašovací formulář"""
        st.subheader("🔐 Přihlášení")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="vas.email@example.com")
            password = st.text_input("Heslo", type="password")
            submitted = st.form_submit_button("🔓 Přihlásit", use_container_width=True)
            
            if submitted:
                if not email or not password:
                    st.error("Vyplňte všechna pole.")
                    return
                
                # Přihlášení
                result = AuthService.login(email, password)
                
                if result.success:
                    SessionManager.login(result.user.email, result.permissions)
                    st.success(f"✅ Přihlášen jako {result.user.email}")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"❌ {result.error_message}")
        
        # Odkaz na reset hesla
        st.markdown("---")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔑 Zapomněl jsem heslo", use_container_width=True):
                st.session_state.show_password_reset = True
                st.rerun()
    
    @staticmethod
    def register_form():
        """Registrační formulář"""
        st.subheader("📝 Registrace nového účtu")
        
        with st.form("register_form"):
            email = st.text_input("Email", placeholder="vas.email@example.com")
            password = st.text_input("Heslo", type="password", key="reg_password")
            
            # Ukazatel síly hesla
            if password:
                strength = PasswordValidator.get_strength(password)
                st.caption(f"Síla hesla: {strength.value}")
            
            confirm = st.text_input("Potvrzení hesla", type="password")
            
            # Načtení skupin
            with get_db_transaction() as conn:
                groups_dict = GroupRepository.get_all(conn)
            
            if groups_dict:
                requested_group_name = st.selectbox(
                    "Požadovaná skupina",
                    options=list(groups_dict.keys())
                )
            else:
                st.warning("Nejsou dostupné žádné skupiny.")
                requested_group_name = None
            
            submitted = st.form_submit_button("✅ Registrovat", use_container_width=True)
            
            if submitted:
                # Validace
                is_valid_email, email_error = EmailValidator.validate(email)
                if not is_valid_email:
                    st.error(f"❌ {email_error}")
                    return
                
                if password != confirm:
                    st.error("❌ Hesla se neshodují")
                    return
                
                is_valid_password, password_error = PasswordValidator.validate(password)
                if not is_valid_password:
                    st.error(f"❌ {password_error}")
                    return
                
                if not requested_group_name:
                    st.error("❌ Vyberte skupinu")
                    return
                
                # Registrace
                requested_group_id = groups_dict.get(requested_group_name)
                result = AuthService.register(email, password, requested_group_id)
                
                if result.success:
                    st.success("✅ Registrace proběhla úspěšně!")
                    st.info("ℹ️ Nyní se můžete přihlásit. Přesměrovávám...")
                    
                    # Odeslání uvítacího emailu
                    EmailService.send_welcome_email(email)
                    
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ {result.error_message}")
    
    @staticmethod
    def password_reset_request_form():
        """Formulář pro žádost o reset hesla"""
        st.subheader("🔑 Reset hesla")
        st.info("Zadejte váš e-mail a pošleme vám odkaz pro reset hesla.")
        
        with st.form("password_reset_request_form"):
            email = st.text_input("Email", placeholder="vas.email@example.com")
            submitted = st.form_submit_button("📧 Odeslat reset link", use_container_width=True)
            
            if submitted:
                if not email:
                    st.error("Zadejte e-mailovou adresu.")
                    return
                
                # Validace emailu
                is_valid, error_msg = EmailValidator.validate(email)
                if not is_valid:
                    st.error(error_msg)
                    return
                
                # Vytvoření tokenu
                result = AuthService.request_password_reset(email)
                
                if result.success and result.token:
                    # Odeslání emailu
                    if EmailService.send_password_reset_email(result.email, result.token):
                        st.success("✅ E-mail s instrukcemi byl odeslán.")
                        st.info("⏱️ Odkaz je platný 1 hodinu.")
                    else:
                        st.error("❌ Chyba při odesílání e-mailu.")
                else:
                    st.success("✅ " + result.message)
        
        st.markdown("---")
        if st.button("← Zpět na přihlášení", use_container_width=True):
            st.session_state.show_password_reset = False
            st.rerun()
    
    @staticmethod
    def password_reset_form(token: str):
        """Formulář pro nastavení nového hesla"""
        st.subheader("🔐 Nastavení nového hesla")
        
        # Ověření tokenu
        from auth.repositories import TokenRepository
        with get_db_transaction() as conn:
            token_obj = TokenRepository.verify_token(conn, token)
        
        if not token_obj:
            st.error("❌ Tento reset link je neplatný nebo vypršel.")
            st.info("⏱️ Platnost linku je 1 hodina.")
            
            if st.button("🔄 Požádat o nový link", use_container_width=True):
                st.session_state.show_password_reset = True
                st.query_params.clear()
                st.rerun()
            return
        
        st.success("✅ Reset link je platný")
        
        with st.form("password_reset_form"):
            new_password = st.text_input("Nové heslo", type="password", key="reset_new_pass")
            
            if new_password:
                strength = PasswordValidator.get_strength(new_password)
                st.caption(f"Síla hesla: {strength.value}")
            
            confirm = st.text_input("Potvrzení", type="password", key="reset_confirm_pass")
            submitted = st.form_submit_button("✅ Nastavit nové heslo", use_container_width=True)
        
        if submitted:
            if new_password != confirm:
                st.error("❌ Hesla se neshodují")
                return
            
            is_valid, error_msg = PasswordValidator.validate(new_password)
            if not is_valid:
                st.error(f"❌ {error_msg}")
                return
            
            result = AuthService.reset_password(token, new_password)
            
            if result.success:
                st.success(f"✅ {result.message}")
                st.balloons()
                st.query_params.clear()
                st.session_state.show_password_reset = False
                st.info("ℹ️ Přesměrovávám na přihlášení...")
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(f"❌ {result.message}")