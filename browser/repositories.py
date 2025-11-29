import pandas as pd
from sqlalchemy import text
import logging
from .models import TableInfo # Předpoklad dataclassy

logger = logging.getLogger(__name__)

class BrowserRepository:
    """
    Třída zodpovědná za přímou komunikaci s databází pro Data Browser.
    Žádná Streamlit logika zde nesmí být.
    """

    def __init__(self, engine):
        self.engine = engine

    def get_schemas(self):
        try:
            # SQL dotaz pro získání schémat
            query = text("SELECT schema_name FROM information_schema.schemata")
            # Pro SQLite fallback (protože nemá standardní schemas jako PG/MySQL)
            if 'sqlite' in self.engine.dialect.name:
                return ['main']
            
            with self.engine.connect() as conn:
                result = conn.execute(query)
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"DB Error - get_schemas: {e}")
            raise e

    def get_tables(self, schema_name):
        try:
            if 'sqlite' in self.engine.dialect.name:
                query = text("SELECT name FROM sqlite_master WHERE type='table'")
            else:
                query = text(f"SELECT table_name FROM information_schema.tables WHERE table_schema = :schema")
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"schema": schema_name})
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"DB Error - get_tables pro schéma {schema_name}: {e}")
            return []

    def fetch_data(self, schema, table, limit, offset, where_clause=None):
        try:
            table_path = f"{schema}.{table}" if schema != 'main' else table
            query_str = f"SELECT * FROM {table_path}"
            
            if where_clause:
                query_str += f" WHERE {where_clause}"
            
            query_str += f" LIMIT {limit} OFFSET {offset}"
            
            logger.debug(f"Executing query: {query_str}")
            return pd.read_sql(query_str, self.engine)
        except Exception as e:
            logger.error(f"DB Error - fetch_data ({table}): {e}", exc_info=True)
            raise e

    def update_table(self, schema, table, df):
        try:
            # Příklad jednoduchého replace - v produkci opatrně!
            with self.engine.begin() as conn:
                df.to_sql(table, conn, schema=schema if schema != 'main' else None, 
                          if_exists='replace', index=False)
            logger.info(f"Tabulka {table} byla aktualizována uživatelem.")
        except Exception as e:
            logger.error(f"DB Error - update_table: {e}")
            raise e