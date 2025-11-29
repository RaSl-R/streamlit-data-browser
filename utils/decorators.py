"""
Dekorátory pro aplikaci
"""
import time
from functools import wraps
from typing import Callable
from core.logger import logger

def log_errors(func: Callable) -> Callable:
    """
    Dekorátor pro logování chyb.
    
    Usage:
        @log_errors
        def my_function():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}: {str(e)}",
                exc_info=True
            )
            raise
    return wrapper

def timing(func: Callable) -> Callable:
    """
    Dekorátor pro měření času vykonávání funkce.
    
    Usage:
        @timing
        def slow_function():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        elapsed = end_time - start_time
        logger.info(f"{func.__name__} executed in {elapsed:.4f}s")
        
        return result
    return wrapper

def retry(max_attempts: int = 3, delay: float = 1.0):
    """
    Dekorátor pro opakování volání při selhání.
    
    Args:
        max_attempts: Maximální počet pokusů
        delay: Prodleva mezi pokusy (sekundy)
    
    Usage:
        @retry(max_attempts=3, delay=2.0)
        def unstable_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {str(e)}"
                    )
                    
                    if attempt < max_attempts:
                        time.sleep(delay)
            
            logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            raise last_exception
        
        return wrapper
    return decorator

def cache_result(ttl: int = 300):
    """
    Jednoduchý in-memory cache dekorátor.
    
    Args:
        ttl: Time to live v sekundách
    
    Usage:
        @cache_result(ttl=600)
        def expensive_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_times = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Vytvoření cache klíče
            cache_key = (args, tuple(sorted(kwargs.items())))
            current_time = time.time()
            
            # Kontrola, zda je cache platná
            if cache_key in cache:
                cache_time = cache_times.get(cache_key, 0)
                if current_time - cache_time < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cache[cache_key]
            
            # Volání funkce a uložení do cache
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            cache[cache_key] = result
            cache_times[cache_key] = current_time
            
            return result
        
        # Přidání metody pro vyčištění cache
        wrapper.clear_cache = lambda: (cache.clear(), cache_times.clear())
        
        return wrapper
    return decorator