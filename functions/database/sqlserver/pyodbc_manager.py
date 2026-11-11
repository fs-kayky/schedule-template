# Adaptador de conexão; as operações genéricas são herdadas de DatabaseManager.
import os

from functions.database.base_manager import DatabaseManager


class PyodbcManager(DatabaseManager):
    def __init__(self, conn_str=None):
        # Permite passar uma conexão explicitamente ou consultar o ambiente ao conectar.
        self.conn_str = conn_str

    def connect(self):
        # Uma string explícita não vazia tem preferência sobre a variável de ambiente.
        conn_str = self.conn_str or os.getenv("CONN_STR_SQLSERVER")
        if not conn_str:
            raise ValueError("Configure CONN_STR_SQLSERVER antes de usar o manager.")
        # Importação adiada: iniciar a schedule vazia não carrega o driver.
        import pyodbc
        return pyodbc.connect(conn_str, autocommit=False)


# Instância reutilizável: sua criação não abre conexão.
pyodbc_manager = PyodbcManager()
