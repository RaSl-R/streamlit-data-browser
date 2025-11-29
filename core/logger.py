"""
Konfigurace loggingu
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logger(
    name: str = "data_browser",
    log_level: str = "INFO",
    log_dir: str = "logs"
) -> logging.Logger:
    """
    Nastaví logger s rotací souborů.
    
    Args:
        name: Jméno loggeru
        log_level: Úroveň logování
        log_dir: Složka pro logy
        
    Returns:
        Logger instance
    """
    # Vytvoření složky pro logy
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler - obecný log
    file_handler = RotatingFileHandler(
        log_path / "app.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Error handler - pouze errors
    error_handler = RotatingFileHandler(
        log_path / "error.log",
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger


# Globální logger instance
logger = setup_logger()


def get_auth_logger() -> logging.Logger:
    """Speciální logger pro autentizaci"""
    auth_logger = logging.getLogger("data_browser.auth")
    
    if not auth_logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - AUTH - %(levelname)s - %(message)s'
        )
        
        handler = RotatingFileHandler(
            Path("logs") / "auth.log",
            maxBytes=10*1024*1024,
            backupCount=5
        )
        handler.setFormatter(formatter)
        auth_logger.addHandler(handler)
    
    return auth_logger