# Base compartilhada pelos drivers: execução, transação e fechamento de recursos.
from contextlib import contextmanager


class DatabaseManager:
    """Operações genéricas. Queries e parâmetros são fornecidos pelo chamador."""

    def connect(self):
        # Cada subclasse deve devolver uma conexão do seu próprio driver.
        raise NotImplementedError

    # Não depende de estado da instância e aceita uma conexão ausente.
    @staticmethod
    def disconnect(conn):
        if conn is not None:
            conn.close()

    # Permite usar "with manager.session() as cursor" para uma única transação.
    @contextmanager
    def session(self):
        # A conexão só é aberta ao usar uma operação, nunca ao importar o manager.
        conn = self.connect()
        cursor = None
        try:
            cursor = conn.cursor()
            # Entrega o cursor ao bloco with e retoma quando esse bloco termina.
            yield cursor
            # Confirma as alterações apenas quando o bloco termina sem erro.
            conn.commit()
        except Exception:
            # Desfaz a transação atual; raise propaga o erro para quem chamou.
            conn.rollback()
            raise
        # Recursos são liberados mesmo quando a consulta falha.
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            finally:
                # A conexão é fechada mesmo se o fechamento do cursor falhar.
                self.disconnect(conn)

    # Para consultas com resultado: lista de dicionários (lista vazia se não houver linhas).
    # Use nomes/aliases únicos nas colunas para não sobrescrever chaves no dicionário.
    def fetch_all(self, query, params=()):
        with self.session() as cursor:
            # Valores ficam separados do SQL e são tratados pelo driver.
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Executa uma instrução e retorna a contagem informada pelo driver (pode ser -1).
    def execute(self, query, params=()):
        with self.session() as cursor:
            # Valores ficam separados do SQL e são tratados pelo driver.
            cursor.execute(query, params)
            return cursor.rowcount

    # Repete a mesma instrução para várias sequências de parâmetros em uma transação.
    def execute_many(self, query, rows):
        with self.session() as cursor:
            cursor.executemany(query, rows)
            return cursor.rowcount
