import streamlit as st
from streamlit_login import (
    login_form, 
    register_form, 
    change_password_form, 
    request_group_form, 
    password_reset_request_form,
    password_reset_form,
    logout
)
from streamlit_data_browser import main_data_browser

st.set_page_config(layout="wide", page_title="RaSl Data browser", page_icon="🔐")

def main():
    # Inicializace session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if "show_password_reset" not in st.session_state:
        st.session_state.show_password_reset = False
    
    # Kontrola reset tokenu v URL parametrech
    query_params = st.query_params
    reset_token = query_params.get("reset_token")
    
    # SCÉNÁŘ 1: Uživatel je přihlášen → zobraz hlavní aplikaci
    if st.session_state.logged_in:
        st.sidebar.success(f"✅ Přihlášen: **{st.session_state.user_email}**")
        
        if st.sidebar.button("🚪 Odhlásit", use_container_width=True):
            logout()
        
        st.sidebar.markdown("---")
        
        with st.sidebar.expander("🔒 Změnit heslo"):
            change_password_form()
        
        with st.sidebar.expander("👥 Žádost o skupinu"):
            request_group_form()
        
        # Hlavní aplikace - Data Browser
        main_data_browser()
    
    # SCÉNÁŘ 2: Uživatel přišel z e-mailu s reset tokenem
    elif reset_token:
        st.title("🔑 Reset hesla")
        st.markdown("---")
        password_reset_form(reset_token)
        
        st.markdown("---")
        st.caption("Data Browser - Bezpečné přihlášení")
    
    # SCÉNÁŘ 3: Uživatel klikl na "Zapomněl jsem heslo"
    elif st.session_state.show_password_reset:
        st.title("🔑 Reset hesla")
        st.markdown("---")
        password_reset_request_form()
        
        st.markdown("---")
        st.caption("Data Browser - Bezpečné přihlášení")
    
    # SCÉNÁŘ 4: Standardní přihlášení nebo registrace
    else:
        # Hlavička
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔐 Data Browser")
            st.markdown("### Bezpečný přístup k datům")
        
        st.markdown("---")
        
        # Přepínač mezi přihlášením a registrací
        tab1, tab2 = st.tabs(["🔓 Přihlášení", "📝 Registrace"])
        
        with tab1:
            login_form()
        
        with tab2:
            register_form()
        
        # Patička
        st.markdown("---")
        st.caption("🔒 Vaše data jsou v bezpečí • Všechna komunikace je šifrovaná")

if __name__ == "__main__":
    main()