"""
Data modely pro Browser modul
"""
from dataclasses import dataclass
from typing import Optional, List, Any
import pandas as pd

@dataclass
class TableInfo:
    """Informace o tabulce"""
    schema_name: str
    table_name: str
    full_name: str
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    
    @property
    def id(self) -> str:
        """Vrátí plně kvalifikované jméno tabulky"""
        return f"{self.schema_name}.{self.table_name}"

@dataclass
class SchemaInfo:
    """Informace o schématu"""
    name: str
    table_count: int
    description: Optional[str] = None

@dataclass
class QueryResult:
    """Výsledek dotazu"""
    data: pd.DataFrame
    row_count: int
    page: int
    page_size: int
    total_rows: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    @property
    def is_empty(self) -> bool:
        return self.data.empty
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

@dataclass
class FilterState:
    """Stav filtrování"""
    where_clause: str
    is_active: bool
    is_valid: bool
    error_message: Optional[str] = None