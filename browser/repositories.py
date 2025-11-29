"""
Repository layer pro Data Browser - SQL operace
"""
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection
from typing import List, Dict, Optional
from browser.models import TableInfo, QueryResult
from browser.validation.validator import TableValidator
from core.database import get_db_connection
from core.exceptions import DatabaseError
from core.logger import logger
from config.constants import PAGE_SIZE

class BrowserRepository:
    """Repository pro Data Browser operace"""
    
    @staticmethod
    def get_schemas() -> List[str]:
        """
        Vrátí seznam všech schémat v databázi.
        
        Returns:
            Seznam názvů schémat
        """
        try:
            with get_db_connection() as conn:
                result = conn.execute(
                    text("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name")
                )
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error fetching schemas: {e}")
            raise DatabaseError(f"Chyba při načítání schémat: {e}")
    
    @staticmethod
    def get_user_schemas(permissions: Dict[str, str]) -> List[str]:
        """
        Vrátí seznam schémat přístupných pro uživatele.
        
        Args:
            permissions: Slovník oprávnění uživatele
            
        Returns:
            Seznam názvů schémat
        """
        return sorted(permissions.keys())
    
    @staticmethod
    def get_tables(schema_name: str) -> Dict[str, str]:
        """
        Vrátí slovník tabulek v daném schématu.
        
        Args:
            schema_name: Jméno schématu
            
        Returns:
            Dict[table_name, full_table_id]
        """
        try:
            with get_db_connection() as conn:
                result = conn.execute(
                    text("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = :schema
                        ORDER BY table_name
                    """),
                    {"schema": schema_name}
                )
                return {row[0]: f"{schema_name}.{row[0]}" for row in result}
        except Exception as e:
            logger.error(f"Error fetching tables for schema {schema_name}: {e}")
            return {}
    
    @staticmethod
    def get_row_count(schema_name: str, table_name: str, where_clause: str = None) -> int:
        """
        Spočítá počet řádků v tabulce.
        
        Args:
            schema_name: Jméno schématu
            table_name: Jméno tabulky
            where_clause: Volitelná WHERE podmínka
            
        Returns:
            Počet řádků
        """
        try:
            safe_table = TableValidator.get_safe_table_sql(schema_name, table_name)
            query = f"SELECT COUNT(*) FROM {safe_table}"
            
            if where_clause:
                query += f" WHERE {where_clause}"
            
            with get_db_connection() as conn:
                result = conn.execute(text(query)).scalar()
                return int(result)
        except Exception as e:
            logger.error(f"Error counting rows: {e}")
            return 0
    
    @staticmethod
    def fetch_data(
        schema_name: str,
        table_name: str,
        limit: int = PAGE_SIZE,
        offset: int = 0,
        where_clause: str = None
    ) -> pd.DataFrame:
        """
        Načte data z tabulky s podporou stránkování a filtrování.
        
        Args:
            schema_name: Jméno schématu
            table_name: Jméno tabulky
            limit: Max počet řádků
            offset: Offset pro stránkování
            where_clause: Volitelná WHERE podmínka
            
        Returns:
            DataFrame s daty
        """
        try:
            safe_table = TableValidator.get_safe_table_sql(schema_name, table_name)
            query = f"SELECT * FROM {safe_table}"
            
            if where_clause:
                query += f" WHERE {where_clause}"
            
            query += " ORDER BY 1 LIMIT :limit OFFSET :offset"
            
            with get_db_connection() as conn:
                result = conn.execute(
                    text(query),
                    {"limit": limit, "offset": offset}
                )
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                return df
        except Exception as e:
            logger.error(f"Error fetching data from {schema_name}.{table_name}: {e}")
            raise DatabaseError(f"Chyba při načítání dat: {e}")
    
    @staticmethod
    def replace_table(schema_name: str, table_name: str, df: pd.DataFrame) -> None:
        """
        Nahradí celou tabulku novými daty.
        
        Args:
            schema_name: Jméno schématu
            table_name: Jméno tabulky
            df: DataFrame s novými daty
        """
        try:
            from core.database import get_db_transaction
            
            safe_table = TableValidator.get_safe_table_sql(schema_name, table_name)
            
            with get_db_transaction() as conn:
                # Drop stávající tabulky
                conn.execute(text(f'DROP TABLE IF EXISTS {safe_table} CASCADE'))
                
                # Vytvoření nové tabulky z DataFrame
                create_sql = pd.io.sql.get_schema(
                    df, table_name, con=conn, schema=schema_name
                )
                conn.execute(text(create_sql))
                
                # Insert dat
                df.to_sql(
                    table_name,
                    conn,
                    schema=schema_name,
                    if_exists='append',
                    index=False,
                    method='multi'
                )
                
                logger.info(f"Table {schema_name}.{table_name} replaced successfully")
        except Exception as e:
            logger.error(f"Error replacing table: {e}")
            raise DatabaseError(f"Chyba při nahrazování tabulky: {e}")
    
    @staticmethod
    def get_table_info(schema_name: str, table_name: str) -> TableInfo:
        """
        Vrátí informace o tabulce.
        
        Args:
            schema_name: Jméno schématu
            table_name: Jméno tabulky
            
        Returns:
            TableInfo objekt
        """
        try:
            with get_db_connection() as conn:
                # Počet řádků
                safe_table = TableValidator.get_safe_table_sql(schema_name, table_name)
                row_count = conn.execute(
                    text(f"SELECT COUNT(*) FROM {safe_table}")
                ).scalar()
                
                # Počet sloupců
                column_count = conn.execute(
                    text("""
                        SELECT COUNT(*)
                        FROM information_schema.columns
                        WHERE table_schema = :schema AND table_name = :table
                    """),
                    {"schema": schema_name, "table": table_name}
                ).scalar()
                
                return TableInfo(
                    schema_name=schema_name,
                    table_name=table_name,
                    full_name=f"{schema_name}.{table_name}",
                    row_count=row_count,
                    column_count=column_count
                )
        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            raise DatabaseError(f"Chyba při získávání info o tabulce: {e}")