import streamlit as st
from config.settings import APP_NAME
from core.logger import setup_logging
from core.database import get_db_engine
from browser.repositories import BrowserRepository
from browser.service import BrowserService
from browser.ui import render_data_browser

# 1. Inicializace Loggingu (provede se jen jednou)
logger = setup_logging()

st.set_page_config(page_title=APP_NAME, layout="wide")

def main():
    logger.info("Spouštím aplikaci...")

    # 2. Dependency Injection (Inicializace služeb)
    try:
        engine = get_db_engine()
        browser_repo = BrowserRepository(engine)
        browser_service = BrowserService(browser_repo)
    except Exception as e:
        st.error("Kritická chyba: Nelze inicializovat databázi.")
        logger.critical(f"Init failed: {e}")
        st.stop()

    # 3. Routing (Jednoduchý sidebar routing)
    st.sidebar.title("Navigace")
    app_mode = st.sidebar.radio("Přejít na", ["Data Browser", "Statistiky", "Nastavení"])

    if app_mode == "Data Browser":
        # Předáváme pouze service vrstvu, UI neví o DB
        render_data_browser(browser_service)
    
    elif app_mode == "Statistiky":
        st.title("Statistiky")
        st.write("Zde by byly grafy...")
        
    elif app_mode == "Nastavení":
        st.title("Nastavení")
        if st.button("Resetovat Cache"):
            st.cache_data.clear()
            logger.info("Uživatel vymazal cache.")
            st.success("Cache vymazána.")

if __name__ == "__main__":
    main()