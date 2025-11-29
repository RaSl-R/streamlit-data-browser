"""
Validace e-mailových adres
"""
import re
from typing import Tuple
from config.constants import EMAIL_MAX_LENGTH
from core.exceptions import ValidationError


class EmailValidator:
    """Validátor pro e-mailové adresy"""
    
    EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    @classmethod
    def validate(cls, email: str) -> Tuple[bool, str]:
        """
        Validuje formát e-mailové adresy.
        
        Args:
            email: E-mailová adresa k validaci
            
        Returns:
            Tuple[bool, str]: (je_validní, chybová_zpráva)
        """
        if not email:
            return False, "E-mail nesmí být prázdný."
        
        email = email.strip()
        
        if not re.match(cls.EMAIL_REGEX, email):
            return False, "Neplatný formát e-mailu."
        
        if len(email) > EMAIL_MAX_LENGTH:
            return False, f"E-mail je příliš dlouhý (max {EMAIL_MAX_LENGTH} znaků)."
        
        return True, ""
    
    @classmethod
    def validate_or_raise(cls, email: str) -> str:
        """
        Validuje email a vyhodí výjimku při chybě.
        
        Args:
            email: E-mailová adresa
            
        Returns:
            Normalizovaný email
            
        Raises:
            ValidationError: Pokud je email neplatný
        """
        is_valid, error_msg = cls.validate(email)
        if not is_valid:
            raise ValidationError(error_msg)
        return email.strip()
    
    @staticmethod
    def normalize(email: str) -> str:
        """Normalizuje email (lowercase, strip)"""
        return email.strip().lower()