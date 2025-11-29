"""
Validace hesel a kontrola síly hesla
"""
import re
from typing import Tuple
from config.constants import PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH
from core.enums import PasswordStrength
from core.exceptions import ValidationError


class PasswordValidator:
    """Validátor pro hesla"""
    
    # Požadavky na heslo
    REQUIRES_UPPERCASE = True
    REQUIRES_LOWERCASE = True
    REQUIRES_DIGIT = True
    REQUIRES_SPECIAL = True
    
    SPECIAL_CHARS = r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/~`]"
    
    @classmethod
    def validate(cls, password: str) -> Tuple[bool, str]:
        """
        Kontroluje sílu hesla podle bezpečnostních pravidel.
        
        Požadavky:
        - Minimálně 8 znaků
        - Alespoň jedno velké písmeno
        - Alespoň jedno malé písmeno
        - Alespoň jedna číslice
        - Alespoň jeden speciální znak
        
        Args:
            password: Heslo k validaci
            
        Returns:
            Tuple[bool, str]: (je_validní, chybová_zpráva)
        """
        if not password:
            return False, "Heslo nesmí být prázdné."
        
        if len(password) < PASSWORD_MIN_LENGTH:
            return False, f"Heslo musí mít alespoň {PASSWORD_MIN_LENGTH} znaků."
        
        if len(password) > PASSWORD_MAX_LENGTH:
            return False, f"Heslo je příliš dlouhé (max {PASSWORD_MAX_LENGTH} znaků)."
        
        if cls.REQUIRES_UPPERCASE and not re.search(r"[A-Z]", password):
            return False, "Heslo musí obsahovat alespoň jedno velké písmeno."
        
        if cls.REQUIRES_LOWERCASE and not re.search(r"[a-z]", password):
            return False, "Heslo musí obsahovat alespoň jedno malé písmeno."
        
        if cls.REQUIRES_DIGIT and not re.search(r"[0-9]", password):
            return False, "Heslo musí obsahovat alespoň jednu číslici."
        
        if cls.REQUIRES_SPECIAL and not re.search(cls.SPECIAL_CHARS, password):
            return False, "Heslo musí obsahovat alespoň jeden speciální znak (!@#$%^&* atd.)."
        
        return True, ""
    
    @classmethod
    def validate_or_raise(cls, password: str) -> None:
        """
        Validuje heslo a vyhodí výjimku při chybě.
        
        Raises:
            ValidationError: Pokud je heslo neplatné
        """
        is_valid, error_msg = cls.validate(password)
        if not is_valid:
            raise ValidationError(error_msg)
    
    @classmethod
    def get_strength(cls, password: str) -> PasswordStrength:
        """
        Vrací indikátor síly hesla pro UI.
        
        Args:
            password: Heslo k vyhodnocení
            
        Returns:
            PasswordStrength enum
        """
        if not password:
            return PasswordStrength.WEAK
        
        score = 0
        
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if re.search(r"[A-Z]", password):
            score += 1
        if re.search(r"[a-z]", password):
            score += 1
        if re.search(r"[0-9]", password):
            score += 1
        if re.search(cls.SPECIAL_CHARS, password):
            score += 1
        
        if score < 4:
            return PasswordStrength.WEAK
        elif score < 6:
            return PasswordStrength.MEDIUM
        else:
            return PasswordStrength.STRONG
    
    @staticmethod
    def passwords_match(password: str, confirm: str) -> bool:
        """Zkontroluje, zda se hesla shodují"""
        return password == confirm