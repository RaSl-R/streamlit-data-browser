"""
Formátovací utility
"""
from datetime import datetime, date
from typing import Any
import pandas as pd

class DateFormatter:
    """Formátování datumů a časů"""
    
    DEFAULT_DATE_FORMAT = "%Y-%m-%d"
    DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    CZECH_DATE_FORMAT = "%d.%m.%Y"
    CZECH_DATETIME_FORMAT = "%d.%m.%Y %H:%M:%S"
    
    @classmethod
    def format_date(cls, dt: date, format: str = None) -> str:
        """Formátuje datum"""
        if not dt:
            return ""
        format = format or cls.DEFAULT_DATE_FORMAT
        return dt.strftime(format)
    
    @classmethod
    def format_datetime(cls, dt: datetime, format: str = None) -> str:
        """Formátuje datetime"""
        if not dt:
            return ""
        format = format or cls.DEFAULT_DATETIME_FORMAT
        return dt.strftime(format)
    
    @classmethod
    def format_czech_date(cls, dt: date) -> str:
        """Formátuje datum v českém formátu"""
        return cls.format_date(dt, cls.CZECH_DATE_FORMAT)
    
    @classmethod
    def format_czech_datetime(cls, dt: datetime) -> str:
        """Formátuje datetime v českém formátu"""
        return cls.format_datetime(dt, cls.CZECH_DATETIME_FORMAT)

class CSVFormatter:
    """Formátování pro CSV export"""
    
    @staticmethod
    def dataframe_to_csv(df: pd.DataFrame, index: bool = False) -> bytes:
        """
        Konvertuje DataFrame na CSV bytes.
        
        Args:
            df: DataFrame k exportu
            index: Zda zahrnout index
            
        Returns:
            CSV jako bytes
        """
        return df.to_csv(index=index).encode('utf-8')
    
    @staticmethod
    def format_value(value: Any) -> str:
        """Formátuje hodnotu pro CSV"""
        if pd.isna(value):
            return ""
        if isinstance(value, (datetime, date)):
            return DateFormatter.format_datetime(value)
        return str(value)

class NumberFormatter:
    """Formátování čísel"""
    
    @staticmethod
    def format_integer(value: int) -> str:
        """Formátuje celé číslo s oddělovači tisíců"""
        if value is None:
            return ""
        return f"{value:,}".replace(",", " ")
    
    @staticmethod
    def format_decimal(value: float, decimals: int = 2) -> str:
        """Formátuje desetinné číslo"""
        if value is None:
            return ""
        return f"{value:.{decimals}f}"
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 1) -> str:
        """Formátuje procenta"""
        if value is None:
            return ""
        return f"{value:.{decimals}f}%"

class SizeFormatter:
    """Formátování velikostí (bytes, etc.)"""
    
    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """Formátuje velikost v bytech na lidsky čitelný formát"""
        if bytes_value is None:
            return ""
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        
        return f"{bytes_value:.1f} PB"