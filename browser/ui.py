import streamlit as st
from .service import BrowserService
import logging

logger = logging.getLogger(__name__)

def render_data_browser(service: BrowserService):
    """
    Hlavní UI komponenta pro prohlížeč dat.
    """
    st.header("🗃️ Data Browser")

    # 1. Výběr Schématu
    schemas = service.get_available_schemas()
    selected_schema = st.sidebar.selectbox("Schéma", schemas)

    if not selected_schema:
        st.info("Vyberte schéma pro zobrazení.")
        return

    # 2. Výběr Tabulky
    # (Zde by volání service.get_tables mělo být ideálně také cachované)
    tables = service.repo.get_tables(selected_schema) 
    selected_table = st.sidebar.selectbox("Tabulka", tables)

    # 3. Nastavení zobrazení (Session State)
    if "page" not in st.session_state:
        st.session_state.page = 1
    
    page_size = st.sidebar.slider("Řádků na stránku", 50, 500, 100)
    
    # 4. Filtry
    filters = st.sidebar.text_input("SQL Where (např. id > 5)")

    # 5. Načtení a zobrazení dat
    if selected_table:
        try:
            df = service.load_table_grid(
                selected_schema, 
                selected_table, 
                st.session_state.page, 
                page_size, 
                filters
            )
            
            st.subheader(f"Tabulka: {selected_table}")
            
            # Editace dat
            edited_df = st.data_editor(df, num_rows="dynamic", key="main_editor")

            # Akce
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Uložit změny"):
                    success = service.save_changes(selected_schema, selected_table, edited_df)
                    if success:
                        st.success("Data uložena!")
                    else:
                        st.error("Chyba při ukládání.")
            
            with col2:
                # Jednoduchá paginace
                if st.button("Další strana ▶️"):
                    st.session_state.page += 1
                    st.rerun()

        except ValueError as ve:
            st.error(f"Chyba validace: {ve}")
        except Exception as e:
            st.error("Nastala neočekávaná chyba při načítání dat.")
            logger.error(f"UI Error: {e}")