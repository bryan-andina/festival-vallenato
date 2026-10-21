"""
Vallenato Festival Project Initialization.
Ensures pure-Python PyMySQL is registered as the MySQLdb driver for Django,
providing robust, cross-platform MySQL connectivity without C-compiler prerequisites.
"""
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
