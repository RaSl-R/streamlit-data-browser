import logging
from .repositories import BrowserRepository
from .validation.validator import validate_where_clause

logger = logging.getLogger(__name__)

class BrowserService:
    """
    Business logika pro Data Browser.
    Spojuje repository, validace a zpracování chyb.
    """

    def __init__(self, repository: BrowserRepository):
        self.repo = repository

    def get_available_schemas(self):
        """Vrátí seznam schémat nebo prázdný list při chybě."""
        try:
            return self.repo.get_schemas()
        except Exception as e:
            # Chyba je zalogována v repository, zde řešíme dopad na aplikaci
            logger.warning("Nepodařilo se načíst schémata, vracím default.")
            return []

    def load_table_grid(self, schema, table, page, page_size, filters=None):
        """Načte data pro mřížku (grid) s ošetřením vstupů."""
        if not schema or not table:
            return None

        # Validace filtrů (bezpečnostní logika z PDF)
        valid_where = None
        if filters:
            is_valid, clean_clause = validate_where_clause(filters)
            if is_valid:
                valid_where = clean_clause
            else:
                logger.warning(f"Neplatný SQL filtr od uživatele: {filters}")
                raise ValueError("Neplatný filtr")

        offset = (page - 1) * page_size
        
        logger.info(f"Načítání dat: {schema}.{table} (Page: {page})")
        return self.repo.fetch_data(schema, table, page_size, offset, valid_where)

    def save_changes(self, schema, table, edited_df):
        """Uloží změny a zaloguje akci."""
        if edited_df is None or edited_df.empty:
            return False
            
        try:
            self.repo.update_table(schema, table, edited_df)
            return True
        except Exception:
            return False