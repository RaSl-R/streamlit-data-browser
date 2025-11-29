"""
Database engine a connection management
"""
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from contextlib import contextmanager
from config.settings import settings
from core.logger import logger


@st.cache_resource
def get_engine() -> Engine:
    """
    Vytvoří a cachuje database engine.
    
    Returns:
        Engine: SQLAlchemy engine instance
    """
    logger.info("Creating database engine")
    conn_str = settings.database.connection_string
    return create_engine(
        conn_str,
        connect_args={"sslmode": settings.database.sslmode}
    )


@contextmanager
def get_db_connection():
    """
    Context manager pro bezpečné získání DB connection.
    
    Yields:
        Connection: SQLAlchemy connection
        
    Example:
        with get_db_connection() as conn:
            result = conn.execute(query)
    """
    engine = get_engine()
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_db_transaction():
    """
    Context manager pro transakci.
    Automaticky commituje nebo rollbackuje.
    
    Yields:
        Connection: SQLAlchemy connection v transakci
    """
    engine = get_engine()
    with engine.begin() as conn:
        try:
            yield conn
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            raise