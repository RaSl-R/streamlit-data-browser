"""
Centralizovaná konfigurace aplikace.
Načítá nastavení z Streamlit secrets nebo proměnných prostředí.
"""
import streamlit as st
from typing import Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Konfigurace databáze"""
    user: str
    password: str
    host: str
    name: str
    sslmode: str = "require"
    
    @property
    def connection_string(self) -> str:
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}/{self.name}"


@dataclass
class SMTPConfig:
    """Konfigurace SMTP serveru"""
    server: str
    port: int
    user: str
    password: str
    sender_name: str = "Data Browser"


@dataclass
class AppConfig:
    """Hlavní konfigurace aplikace"""
    app_name: str
    app_url: str
    debug: bool
    log_level: str
    locale: str


class Settings:
    """Singleton pro přístup ke konfiguraci"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._load_config()
    
    def _load_config(self):
        """Načte konfiguraci ze Streamlit secrets"""
        # Database
        self.database = DatabaseConfig(
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            host=st.secrets["DB_HOST"],
            name=st.secrets["DB_NAME"]
        )
        
        # SMTP
        self.smtp = SMTPConfig(
            server=st.secrets.get("SMTP_SERVER", "smtp.gmail.com"),
            port=st.secrets.get("SMTP_PORT", 587),
            user=st.secrets.get("SMTP_USER", ""),
            password=st.secrets.get("SMTP_PASSWORD", ""),
            sender_name=st.secrets.get("SMTP_SENDER_NAME", "Data Browser")
        )
        
        # App
        self.app = AppConfig(
            app_name=st.secrets.get("APP_NAME", "RaSl Data Browser"),
            app_url=st.secrets.get("APP_URL", "http://localhost:8501"),
            debug=st.secrets.get("DEBUG", False),
            log_level=st.secrets.get("LOG_LEVEL", "INFO"),
            locale=st.secrets.get("LOCALE", "cs")
        )
    
    @property
    def is_smtp_configured(self) -> bool:
        """Zkontroluje, zda je SMTP nakonfigurováno"""
        return bool(self.smtp.user and self.smtp.password)


# Globální instance
settings = Settings()