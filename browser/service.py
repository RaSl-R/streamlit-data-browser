"""
Business logika pro Data Browser
"""
import math
import pandas as pd
from typing import List, Dict, Optional
from browser.models import QueryResult, FilterState, TableInfo
from browser.repositories import BrowserRepository
from browser.validation.validator import validate_where_clause, TableValidator
from browser.validation.where_clause_validator import WhereClauseValidator
from browser.permission_service import BrowserPermissionService
from config.constants import PAGE_SIZE
from core.exceptions import ValidationError, PermissionDeniedError
from core.logger import logger

class BrowserService:
    """Service layer pro Data Browser"""
    
    def __init__(self):
        self.repo = BrowserRepository()
        self.permission_service = BrowserPermissionService()
    
    def get_accessible_schemas(self, permissions: Dict[str, str]) -> List[str]:
        """
        Vrátí seznam schémat přístupných uživateli.
        
        Args:
            permissions: Slovník oprávnění uživatele
            
        Returns:
            Seznam názvů schémat
        """
        return self.repo.get_user_schemas(permissions)
    
    def get_tables_for_schema(self, schema_name: str) -> Dict[str, str]:
        """
        Vrátí tabulky v daném schématu.
        
        Args:
            schema_name: Jméno schématu
            
        Returns:
            Dict[table_name, full_table_id]
        """
        # Zkontrolujeme oprávnění
        self.permission_service.check_schema_read_access(schema_name)
        
        return self.repo.get_tables(schema_name)
    
    def validate_filter(
        self,
        where_clause: str,
        columns: List[str] = None
    ) -> FilterState:
        """
        Validuje filtr.
        
        Args:
            where_clause: WHERE podmínka
            columns: Seznam sloupců tabulky
            
        Returns:
            FilterState objekt
        """
        if not where_clause:
            return FilterState(
                where_clause="",
                is_active=False,
                is_valid=True
            )
        
        # Základní validace
        is_valid, result = validate_where_clause(where_clause, columns)
        
        if not is_valid:
            return FilterState(
                where_clause=where_clause,
                is_active=False,
                is_valid=False,
                error_message=result
            )
        
        # Pokročilá validace
        advanced_valid, clean_clause, error = WhereClauseValidator.validate(result)
        
        if not advanced_valid:
            return FilterState(
                where_clause=where_clause,
                is_active=False,
                is_valid=False,
                error_message=error
            )
        
        return FilterState(
            where_clause=clean_clause,
            is_active=True,
            is_valid=True
        )
    
    def load_table_data(
        self,
        table_id: str,
        page: int = 1,
        page_size: int = PAGE_SIZE,
        where_clause: str = None
    ) -> QueryResult:
        """
        Načte data z tabulky s podporou stránkování.
        
        Args:
            table_id: ID tabulky (schema.table)
            page: Číslo stránky (od 1)
            page_size: Velikost stránky
            where_clause: Volitelná WHERE podmínka
            
        Returns:
            QueryResult s daty
        """
        # Validace table_id
        schema_name, table_name = TableValidator.validate_table_id(table_id)
        
        # Kontrola oprávnění
        self.permission_service.check_schema_read_access(schema_name)
        
        # Výpočet offsetu
        offset = (page - 1) * page_size
        
        # Získání celkového počtu řádků
        total_rows = self.repo.get_row_count(schema_name, table_name, where_clause)
        total_pages = math.ceil(total_rows / page_size) if total_rows > 0 else 1
        
        # Načtení dat
        df = self.repo.fetch_data(
            schema_name,
            table_name,
            limit=page_size,
            offset=offset,
            where_clause=where_clause
        )
        
        return QueryResult(
            data=df,
            row_count=len(df),
            page=page,
            page_size=page_size,
            total_rows=total_rows,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
    
    def save_table_changes(self, table_id: str, df: pd.DataFrame) -> bool:
        """
        Uloží změny v tabulce.
        
        Args:
            table_id: ID tabulky (schema.table)
            df: DataFrame s novými daty
            
        Returns:
            True pokud se uložilo úspěšně
        """
        if df is None or df.empty:
            logger.warning("Attempt to save empty dataframe")
            return False
        
        # Validace table_id
        schema_name, table_name = TableValidator.validate_table_id(table_id)
        
        # Kontrola oprávnění
        self.permission_service.check_schema_write_access(schema_name)
        
        try:
            self.repo.replace_table(schema_name, table_name, df)
            logger.info(f"Table {table_id} saved successfully by user")
            return True
        except Exception as e:
            logger.error(f"Error saving table {table_id}: {e}")
            return False
    
    def get_table_info(self, table_id: str) -> TableInfo:
        """
        Vrátí informace o tabulce.
        
        Args:
            table_id: ID tabulky (schema.table)
            
        Returns:
            TableInfo objekt
        """
        schema_name, table_name = TableValidator.validate_table_id(table_id)
        self.permission_service.check_schema_read_access(schema_name)
        
        return self.repo.get_table_info(schema_name, table_name)
    
    def has_write_permission(self, table_id: str) -> bool:
        """
        Zkontroluje, zda má uživatel write oprávnění k tabulce.
        
        Args:
            table_id: ID tabulky (schema.table)
            
        Returns:
            True pokud má write přístup
        """
        try:
            schema_name, _ = TableValidator.validate_table_id(table_id)
            return self.permission_service.has_write_access(schema_name)
        except Exception:
            return False