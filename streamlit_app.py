"""
Hlavní soubor Streamlit aplikace Data Browser
"""
import streamlit as st
from auth.ui import AuthUI
from browser.ui import render_data_browser
from core.session import SessionManager
from config.settings import settings

# Konfigurace stránky
st.set_page_config(
    layout="wide",
    page_title=settings.app.app_name,
    page_icon="🗂"
)

def main():
    """Hlavní funkce aplikace"""
    
    # Inicializace session state
    SessionManager.init_session()
    
    # Kontrola reset tokenu v URL parametrech
    query_params = st.query_params
    reset_token = query_params.get("reset_token")
    
    # SCÉNÁŘ 1: Uživatel je přihlášen → zobraz hlavní aplikaci
    if SessionManager.is_logged_in():
        render_logged_in_view()
    
    # SCÉNÁŘ 2: Uživatel přišel z e-mailu s reset tokenem
    elif reset_token:
        render_password_reset_view(reset_token)
    
    # SCÉNÁŘ 3: Uživatel klikl na "Zapomněl jsem heslo"
    elif st.session_state.show_password_reset:
        render_password_reset_request_view()
    
    # SCÉNÁŘ 4: Standardní přihlášení nebo registrace
    else:
        render_login_view()

def render_logged_in_view():
    """Renderuje pohled pro přihlášeného uživatele"""
    user_email = SessionManager.get_user_email()
    
    # Sidebar s uživatelským menu
    st.sidebar.success(f"👤 Přihlášen: **{user_email}**")
    
    if st.sidebar.button("🚪 Odhlásit", use_container_width=True):
        SessionManager.logout()
    
    st.sidebar.markdown("---")
    
    # Změna hesla
    with st.sidebar.expander("🔑 Změnit heslo"):
        AuthUI.change_password_form()
    
    # Žádost o skupinu
    with st.sidebar.expander("👥 Žádost o skupinu"):
        AuthUI.request_group_form()
    
    st.sidebar.markdown("---")
    st.sidebar.caption(f"📍 {settings.app.app_name}")
    st.sidebar.caption(f"🌐 Verze: 2.0")
    
    # Hlavní aplikace - Data Browser
    render_data_browser()

def render_password_reset_view(reset_token: str):
    """Renderuje pohled pro reset hesla"""
    st.title("🔑 Reset hesla")
    st.markdown("---")
    
    AuthUI.password_reset_form(reset_token)
    
    st.markdown("---")
    st.caption("🔒 Data Browser - Bezpečné přihlášení")

def render_password_reset_request_view():
    """Renderuje pohled pro žádost o reset hesla"""
    st.title("🔑 Reset hesla")
    st.markdown("---")
    
    AuthUI.password_reset_request_form()
    
    st.markdown("---")
    st.caption("🔒 Data Browser - Bezpečné přihlášení")

def render_login_view():
    """Renderuje hlavní přihlašovací pohled"""
    # Hlavička
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🗂 Data Browser")
        st.markdown("### Bezpečný přístup k datům")
    
    st.markdown("---")
    
    # Přepínač mezi přihlášením a registrací
    tab1, tab2 = st.tabs(["🔑 Přihlášení", "📝 Registrace"])
    
    with tab1:
        AuthUI.login_form()
    
    with tab2:
        AuthUI.register_form()
    
    # Patička
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.caption("🔒 Vaše data jsou v bezpečí • Všechna komunikace je šifrovaná")
        if settings.app.debug:
            st.caption("⚠ DEBUG MODE")

if __name__ == "__main__":
    main()