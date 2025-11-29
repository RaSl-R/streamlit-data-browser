"""
Konstanty použité v celé aplikaci
"""

# Pagination
PAGE_SIZE = 50
DEFAULT_ROW_LIMIT = 10000

# Password
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

# Email
EMAIL_MAX_LENGTH = 120

# Token
TOKEN_EXPIRY_HOURS = 1
TOKEN_LENGTH = 32

# UI
FORM_WIDTH = "stretch"

# Cache TTL (seconds)
CACHE_TTL_SHORT = 300    # 5 minut
CACHE_TTL_MEDIUM = 1800  # 30 minut
CACHE_TTL_LONG = 3600    # 1 hodina

# Permissions
PERMISSION_READ = "read"
PERMISSION_WRITE = "write"

# SQL Validation
FORBIDDEN_SQL_KEYWORDS = [
    "DELETE", "UPDATE", "INSERT", "DROP", 
    "ALTER", "EXEC", "EXECUTE", "CREATE"
]
SQL_COMMENT_PATTERNS = [";", "--", "/*"]