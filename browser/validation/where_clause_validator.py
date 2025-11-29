"""
Pokročilá validace WHERE klauzulí
"""
import re
from typing import Tuple, Optional
from core.logger import logger

class WhereClauseValidator:
    """Validátor pro WHERE klauzule s pokročilými kontrolami"""
    
    # Povolené operátory
    ALLOWED_OPERATORS = [
        '=', '!=', '<>', '<', '>', '<=', '>=',
        'LIKE', 'ILIKE', 'IN', 'NOT IN',
        'IS NULL', 'IS NOT NULL',
        'BETWEEN', 'AND', 'OR'
    ]
    
    # Nebezpečné vzory
    DANGEROUS_PATTERNS = [
        r';\s*\w+',  # Více příkazů
        r'--',        # SQL komentáře
        r'/\*.*?\*/', # Blokové komentáře
        r'xp_\w+',    # Extended stored procedures (MSSQL)
        r'sp_\w+',    # Stored procedures
        r'\bexec\b',
        r'\bexecute\b',
        r'\beval\b',
    ]
    
    @classmethod
    def validate(cls, where_clause: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Komplexní validace WHERE klauzule.
        
        Args:
            where_clause: Klauzule k validaci
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: 
                (je_validní, očištěná_klauzule, chybová_zpráva)
        """
        if not where_clause:
            return True, None, None
        
        where_clause = where_clause.strip()
        
        # Kontrola nebezpečných vzorů
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, where_clause, re.IGNORECASE):
                logger.warning(f"Dangerous pattern detected: {pattern}")
                return False, None, "Nepovolený vzor v WHERE klauzuli"
        
        # Kontrola rovnováhy závorek
        if where_clause.count('(') != where_clause.count(')'):
            return False, None, "Neuzavřené závorky"
        
        # Kontrola rovnováhy uvozovek
        single_quotes = where_clause.count("'")
        if single_quotes % 2 != 0:
            return False, None, "Neuzavřené uvozovky"
        
        return True, where_clause, None
    
    @classmethod
    def sanitize(cls, where_clause: str) -> str:
        """
        Vyčistí WHERE klauzuli od nadbytečných bílých znaků.
        
        Args:
            where_clause: Klauzule k vyčištění
            
        Returns:
            Vyčištěná klauzule
        """
        if not where_clause:
            return ""
        
        # Nahradíme víceřádkové mezery za jednu mezeru
        cleaned = re.sub(r'\s+', ' ', where_clause.strip())
        return cleaned