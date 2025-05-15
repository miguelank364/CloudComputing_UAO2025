class Config:
    SQL_HOST = 'miguelank-servidor-sql.database.windows.net:1433'
    SQL_USER = 'miguelank'
    SQL_PASSWORD = '#Ghytpoi9'
    SQL_DB = 'pruebaSQL'
    SQLALCHEMY_DATABASE_URI = f'mssql+pyodbc://{SQL_USER}:{SQL_PASSWORD}@{SQL_HOST}/{SQL_DB}?driver=ODBC Driver 18 for SQL Server'