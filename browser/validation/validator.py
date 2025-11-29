"""
Validace názvů tabulek a bezpečnostní kontroly
"""
import re
from typing import Tuple, List
from config.constants import FORBIDDEN_SQL_KEYWORDS, SQL_COMMENT_PATTERNS
from core.exceptions import SQLInjectionAttempt, ValidationError
from core.logger import logger

class TableValidator:
    """Validátor pro názvy tabulek"""
    
    @staticmethod
    def validate_table_id(table_id: str) -> Tuple[str, str]:
        """
        Validuje a parsuje table_id ve formátu 'schema.table'.
        
        Args:
            table_id: ID tabulky ve formátu 'schema.table'
            
        Returns:
            Tuple[str, str]: (schema_name, table_name)
            
        Raises:
            ValidationError: Pokud je formát neplatný
        """
        try:
            schema_name, table_name = table_id.split('.', 1)
        except ValueError:
            raise ValidationError(
                f"Neplatný formát table_id: {table_id}. Očekáván 'schema.table'."
            )
        
        # Kontrola prázdných hodnot
        if not schema_name or not table_name:
            raise ValidationError("Schema ani název tabulky nesmí být prázdný")
        
        return schema_name, table_name
    
    @staticmethod
    def get_safe_table_sql(schema_name: str, table_name: str) -> str:
        """
        Vrátí bezpečný SQL identifikátor pro tabulku.
        
        Args:
            schema_name: Jméno schématu
            table_name: Jméno tabulky
            
        Returns:
            Bezpečný SQL string s quoted identifikátory
        """
        return f'"{schema_name}"."{table_name}"'

def validate_where_clause(where_clause: str, columns: List[str] = None) -> Tuple[bool, str]:
    """
    Validuje WHERE klauzuli pro bezpečnost.
    
    Args:
        where_clause: WHERE podmínka k validaci
        columns: Seznam povolených sloupců (optional)
        
    Returns:
        Tuple[bool, str]: (je_validní, clean_clause nebo error_message)
    """
    if not where_clause:
        return True, None
    
    where_clause = where_clause.strip()
    
    # Kontrola SQL komentářů a separátorů
    for pattern in SQL_COMMENT_PATTERNS:
        if pattern in where_clause:
            logger.warning(f"SQL injection attempt detected: comment pattern '{pattern}'")
            return False, f"Nepovolený znak: {pattern}"
    
    # Kontrola zakázaných SQL příkazů
    forbidden_pattern = re.compile(
        r"\b(" + "|".join(FORBIDDEN_SQL_KEYWORDS) + r")\b",
        re.IGNORECASE
    )
    
    if forbidden_pattern.search(where_clause):
        logger.warning(f"SQL injection attempt detected: forbidden keyword in '{where_clause}'")
        return False, "Nepovolené SQL klíčové slovo"
    
    # Pokud jsou zadané sloupce, zkontrolujeme, že se alespoň jeden vyskytuje
    if columns and len(columns) > 0:
        column_pattern = r"\b(" + "|".join(re.escape(str(col)) for col in columns) + r")\b"
        if not re.search(column_pattern, where_clause, re.IGNORECASE):
            return False, "WHERE klauzule neobsahuje žádný platný sloupec"
    
    return True, where_clause