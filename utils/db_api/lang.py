import sqlite3


def logger(statement):
    print(f"""
    --------------------------------------------------------
    Executing:
    {statement}
    --------------------------------------------------------
""")

class LanDB:
    def __init__(self, path_to_db="main.db"):
        self.path_to_db = path_to_db
        self.create_table_lang()

    @property
    def connection(self):
        return sqlite3.connect(self.path_to_db)

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = ()
        connection = self.connection
        connection.set_trace_callback(logger)
        cursor = connection.cursor()
        data = None
        cursor.execute(sql, parameters)

        if commit:
            connection.commit()
        if fetchall:
            data = cursor.fetchall()
        if fetchone:
            data = cursor.fetchone()
        connection.close()
        return data

    def create_table_lang(self):
        sql = """
        CREATE TABLE IF NOT EXISTS user_lang (
            tg_id INTEGER PRIMARY KEY,
            lang VARCHAR(10) NOT NULL
        );
        """
        self.execute(sql, commit=True)

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join([
            f"{item}=?" for item in parameters
        ])
        return sql, tuple(parameters.values())

    def filter(self, **kwargs):
        sql = "SELECT * FROM user_lang WHERE "
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters=parameters, fetchone=True)

    def update_lang(self, lang, tg_id):
        sql = """
        UPDATE user_lang
        SET lang=? WHERE tg_id=?
        """
        return self.execute(sql, parameters=(lang, tg_id), commit=True)

    def add_or_update_lang(self, tg_id: int, lang: str):
        sql = """
        INSERT INTO user_lang (tg_id, lang) VALUES (?, ?)
        ON CONFLICT(tg_id) DO UPDATE SET lang=excluded.lang;
        """
        return self.execute(sql, parameters=(tg_id, lang), commit=True)

    def get_lang(self, tg_id: int):
        sql = "SELECT lang FROM user_lang WHERE tg_id=?"
        result = self.execute(sql, parameters=(tg_id,), fetchone=True)
        return result[0] if result else None