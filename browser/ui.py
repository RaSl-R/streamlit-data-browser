"""
UI komponenty pro Data Browser
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from browser.service import BrowserService
from core.session import SessionManager
from core.exceptions import PermissionDeniedError, ValidationError
from core.middleware import require_auth
from core.logger import logger
from config.constants import PAGE_SIZE

class BrowserUI:
    """UI komponenty pro Data Browser"""
    
    def __init__(self):
        self.service = BrowserService()
        self._init_session_state()
    
    def _init_session_state(self):
        """Inicializuje session state pro browser"""
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
        if "current_table_id" not in st.session_state:
            st.session_state.current_table_id = None
    
    def _load_css(self):
        with open("static/css/browser.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    def _clear_filter(self):
        """Vyčistí filtr a resetuje stránkování"""
        st.session_state.where_clause = ""
        st.session_state.filter_applied = False
        st.session_state.current_page = 1
        st.session_state.reload_data = True
    
    def _handle_table_change(self, new_table_id: str):
        """Zpracuje změnu tabulky"""
        if st.session_state.current_table_id != new_table_id:
            st.session_state.current_page = 1
            st.session_state.reload_data = True
            st.session_state.current_table_id = new_table_id
            self._clear_filter()
    
    @require_auth
    def render(self):
        """Hlavní render metoda pro Data Browser"""
        st.title("🗂️️️ Data Browser")
        
        # self._load_css()

        # Zobrazení zpráv
        message = SessionManager.get_and_clear_message()
        if message:
            st.success(message)
        
        # Získání přístupných schémat
        permissions = SessionManager.get_permissions()
        schemas = self.service.get_accessible_schemas(permissions)
        
        if not schemas:
            st.warning("⚠ Nemáte přiřazeno oprávnění k žádnému schématu. Obraťte se na administrátora.")
            st.stop()
        
        # Výběr schématu
        selected_schema = st.selectbox(
            "📂 Vyber schéma",
            schemas,
            index=0,
            key="selected_schema"
        )
        
        # Získání tabulek
        try:
            tables_dict = self.service.get_tables_for_schema(selected_schema)
        except PermissionDeniedError as e:
            st.error(f"❌ {str(e)}")
            st.stop()
        
        if not tables_dict:
            st.info("ℹ Zvolené schéma neobsahuje žádnou tabulku.")
            st.stop()
        
        # Výběr tabulky
        selected_table_name = st.selectbox(
            "📋 Vyber tabulku",
            options=list(tables_dict.keys()),
            key="selected_table"
        )
        
        selected_table_id = tables_dict[selected_table_name]
        
        # Zpracování změny tabulky
        self._handle_table_change(selected_table_id)
        
        # Render hlavního obsahu
        self._render_table_view(selected_table_id, selected_table_name)
    
    def _render_filter_panel(self, columns: list) -> str:
        """
        Renderuje panel s filtrem.
        
        Returns:
            WHERE klauzule nebo None
        """
        expander_label = "🔍 Filtrováno" if st.session_state.filter_applied else "🔍 Filtr"
        custom_expander_id = "filter-expander"

        if st.session_state.filter_applied:
            self._load_css()

        with st.expander(expander_label, expanded=st.session_state.filter_applied):
            where_clause = st.text_input(
                "Zadej WHERE podmínku (bez klíčového slova 'WHERE')",
                placeholder="např.: amount > 100 AND status = 'active'",
                value=st.session_state.where_clause if st.session_state.filter_applied else "",
                key="where_input"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑 Zrušit filtr", use_container_width=True):
                    self._clear_filter()
                    st.rerun()
            
            with col2:
                apply_filter = st.button("🔍 Filtrovat", use_container_width=True)
            
            if apply_filter and where_clause:
                # Validace filtru
                filter_state = self.service.validate_filter(where_clause, columns)
                
                if filter_state.is_valid:
                    st.session_state.where_clause = filter_state.where_clause
                    st.session_state.filter_applied = True
                    st.session_state.current_page = 1
                    st.session_state.reload_data = True
                    st.session_state.editor_key_counter += 1
                    st.rerun()
                else:
                    st.error(f"❌ {filter_state.error_message}")
                    return None

        return st.session_state.where_clause if st.session_state.filter_applied else None
    
    def _render_pagination(self, query_result):
        """Renderuje ovládací prvky pro stránkování"""
        if query_result.total_rows <= PAGE_SIZE:
            return
        
        col1, col2, col3, col4, _ = st.columns([1.6, 2.4, 2.4, 1.6, 4], gap="small")
        
        if col1.button(
            "<< První",
            use_container_width=True,
            disabled=not query_result.has_previous
        ):
            st.session_state.current_page = 1
            st.session_state.reload_data = True
            st.session_state.editor_key_counter += 1
            st.rerun()
        
        if col2.button(
            "< Předchozí",
            use_container_width=True,
            disabled=not query_result.has_previous
        ):
            st.session_state.current_page -= 1
            st.session_state.reload_data = True
            st.session_state.editor_key_counter += 1
            st.rerun()
        
        if col3.button(
            "Další >",
            use_container_width=True,
            disabled=not query_result.has_next
        ):
            st.session_state.current_page += 1
            st.session_state.reload_data = True
            st.session_state.editor_key_counter += 1
            st.rerun()
        
        if col4.button(
            "Poslední >>",
            use_container_width=True,
            disabled=not query_result.has_next
        ):
            st.session_state.current_page = query_result.total_pages
            st.session_state.reload_data = True
            st.session_state.editor_key_counter += 1
            st.rerun()
    
    def _render_action_buttons(self, selected_table_id: str, edited_df: pd.DataFrame):
        """Renderuje akční tlačítka (ROLLBACK, COMMIT)"""
        col1, col2, _ = st.columns([1, 1, 6])
        
        with col1:
            if st.button("↩ ROLLBACK", use_container_width=True):
                st.session_state.reload_data = True
                st.session_state.editor_key_counter += 1
                SessionManager.set_message(
                    "Změny byly zahozeny (ROLLBACK) – data byla znovu načtena z databáze."
                )
                st.rerun()
        
        with col2:
            if st.button("💾 COMMIT", use_container_width=True):
                # Kontrola oprávnění
                if not self.service.has_write_permission(selected_table_id):
                    schema_name = selected_table_id.split('.')[0]
                    st.error(f"❌ Nemáte oprávnění 'write' k zápisu do schématu '{schema_name}'.")
                else:
                    try:
                        success = self.service.save_table_changes(selected_table_id, edited_df)
                        if success:
                            st.session_state.reload_data = True
                            st.session_state.editor_key_counter += 1
                            SessionManager.set_message("✅ Změny byly uloženy (COMMIT).")
                            st.rerun()
                        else:
                            st.error("❌ Chyba při ukládání změn.")
                    except PermissionDeniedError as e:
                        st.error(f"❌ {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Chyba při COMMITu: {e}")
                        logger.error(f"Commit error: {e}")
    
    def _render_export_section(self, df: pd.DataFrame, table_name: str):
        """Renderuje sekci pro export"""
        with st.expander("📥 Export do CSV"):
            csv = df.to_csv(index=False).encode('utf-8')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{table_name}_{timestamp}.csv"
            
            st.download_button(
                "⬇ Stáhnout aktuální pohled jako CSV",
                csv,
                file_name=file_name,
                mime='text/csv'
            )
    
    def _render_import_section(self, selected_table_id: str):
        """Renderuje sekci pro import"""
        # Kontrola oprávnění
        if not self.service.has_write_permission(selected_table_id):
            st.info("ℹ Pro import CSV potřebujete 'write' oprávnění.")
            return
        
        with st.expander("📤 Import CSV – přepsání tabulky"):
            st.warning("⚠ Import přepíše celou tabulku novými daty!")
            
            uploaded_file = st.file_uploader("Vyber CSV soubor", type="csv")
            
            if uploaded_file:
                try:
                    imported_df = pd.read_csv(uploaded_file)
                    st.dataframe(imported_df, use_container_width=True)
                    
                    if st.button("🔄 Nahradit celou tabulku importovanými daty"):
                        success = self.service.save_table_changes(
                            selected_table_id,
                            imported_df
                        )
                        
                        if success:
                            st.session_state.reload_data = True
                            st.session_state.editor_key_counter += 1
                            SessionManager.set_message("✅ Tabulka byla nahrazena.")
                            st.rerun()
                        else:
                            st.error("❌ Chyba při importu dat.")
                except Exception as e:
                    st.error(f"❌ Chyba při čtení CSV: {e}")
    
    def _render_table_view(self, selected_table_id: str, table_name: str):
        """Renderuje hlavní pohled na tabulku"""
        try:
            # Načtení dat s ukládáním do cache
            if st.session_state.reload_data:
                where_clause = st.session_state.where_clause if st.session_state.filter_applied else None
                
                query_result = self.service.load_table_data(
                    selected_table_id,
                    page=st.session_state.current_page,
                    page_size=PAGE_SIZE,
                    where_clause=where_clause
                )
                
                st.session_state.reload_data = False
                st.session_state.cached_query_result = query_result
            else:
                query_result = st.session_state.get('cached_query_result')
                if not query_result:
                    st.session_state.reload_data = True
                    st.rerun()
            
            df = query_result.data
            
            # Panel s filtrem
            self._render_filter_panel(df.columns.tolist() if not df.empty else [])

            # Data editor
            editor_key = f"editor_{st.session_state.editor_key_counter}"
            edited_df = st.data_editor(
                df,
                num_rows="dynamic",
                use_container_width=True,
                key=editor_key
            )
            
            # Info o datech
            st.caption(
                f"Zobrazeno {query_result.row_count} z {query_result.total_rows} záznamů | "
                f"Stránka {query_result.page}/{query_result.total_pages}"
            ) 

            # Stránkování
            self._render_pagination(query_result)
            
            # Akční tlačítka
            self._render_action_buttons(selected_table_id, edited_df)

            # Export/Import
            self._render_export_section(edited_df, table_name)
            self._render_import_section(selected_table_id)
            
        except PermissionDeniedError as e:
            st.error(f"❌ {str(e)}")
        except ValidationError as e:
            st.error(f"❌ {str(e)}")
        except Exception as e:
            st.error(f"❌ Nastala neočekávaná chyba při načítání dat.")
            logger.error(f"Table view error: {e}", exc_info=True)


def render_data_browser():
    """Hlavní funkce pro render Data Browser"""
    browser = BrowserUI()
    browser.render()