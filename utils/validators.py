import re
from typing import Tuple

def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validuje formát e-mailové adresy.
    
    Returns:
        Tuple[bool, str]: (je_validní, chybová_zpráva)
    """
    if not email:
        return False, "E-mail nesmí být prázdný."
    
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email.strip()):
        return False, "Neplatný formát e-mailu."
    
    if len(email) > 120:
        return False, "E-mail je příliš dlouhý (max 120 znaků)."
    
    return True, ""


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Kontroluje sílu hesla podle bezpečnostních pravidel.
    
    Požadavky:
    - Minimálně 8 znaků
    - Alespoň jedno velké písmeno
    - Alespoň jedno malé písmeno
    - Alespoň jedna číslice
    - Alespoň jeden speciální znak
    
    Returns:
        Tuple[bool, str]: (je_validní, chybová_zpráva)
    """
    if not password:
        return False, "Heslo nesmí být prázdné."
    
    if len(password) < 8:
        return False, "Heslo musí mít alespoň 8 znaků."
    
    if len(password) > 128:
        return False, "Heslo je příliš dlouhé (max 128 znaků)."
    
    if not re.search(r"[A-Z]", password):
        return False, "Heslo musí obsahovat alespoň jedno velké písmeno."
    
    if not re.search(r"[a-z]", password):
        return False, "Heslo musí obsahovat alespoň jedno malé písmeno."
    
    if not re.search(r"[0-9]", password):
        return False, "Heslo musí obsahovat alespoň jednu číslici."
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/~`]", password):
        return False, "Heslo musí obsahovat alespoň jeden speciální znak (!@#$%^&* atd.)."
    
    return True, ""


def get_password_strength_indicator(password: str) -> str:
    """
    Vrací textový indikátor síly hesla pro UI.
    
    Returns:
        str: "Slabé", "Střední", "Silné"
    """
    if not password:
        return ""
    
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
    if re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/~`]", password):
        score += 1
    
    if score < 4:
        return "🔴 Slabé"
    elif score < 6:
        return "🟡 Střední"
    else:
        return "🟢 Silné"