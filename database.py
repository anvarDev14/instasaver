import sqlite3
from datetime import datetime
import logging

# Logging sozlamasi
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def log_sql(statement):
    """SQL so'rovlarini konsolda chiqarish uchun funksiya."""
    print(f"""
_____________________________________________________        
Executing: 
{statement}
_____________________________________________________
""")

class Database:
    def __init__(self, path_to_db="main.db"):
        self.path_to_db = path_to_db
        self.create_table_users()

    @property
    def connection(self):
        """Ma'lumotlar bazasiga ulanish."""
        return sqlite3.connect(self.path_to_db)

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        """SQL so'rovini bajarish."""
        if not parameters:
            parameters = ()
        connection = self.connection
        connection.set_trace_callback(log_sql)  # logger o'rniga log_sql ishlatiladi
        cursor = connection.cursor()
        data = None
        try:
            cursor.execute(sql, parameters)
            if commit:
                connection.commit()
            if fetchall:
                data = cursor.fetchall()
            if fetchone:
                data = cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            connection.rollback()
            raise
        finally:
            connection.close()
        return data

    @staticmethod
    def format_args(sql, parameters: dict):
        """SQL so'rovi uchun parametrlarni formatlash."""
        sql += " AND ".join([f"{item} = ?" for item in parameters])
        return sql, tuple(parameters.values())

    # --- Users jadvali uchun metodlar ---
    def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            is_admin INTEGER DEFAULT 0
        );
        """
        self.execute(sql, commit=True)

    def add_user(self, user_id: int, username: str, is_admin: int = 0):
        sql = """
        INSERT OR IGNORE INTO Users (id, username, is_admin) VALUES (?, ?, ?)
        """
        return self.execute(sql, parameters=(user_id, username, is_admin), commit=True)

    def get_user(self, user_id: int):
        sql = "SELECT * FROM Users WHERE id = ?"
        return self.execute(sql, parameters=(user_id,), fetchone=True)

    def check_if_admin(self, user_id: int):
        sql = "SELECT is_admin FROM Users WHERE id = ?"
        result = self.execute(sql, parameters=(user_id,), fetchone=True)
        return result[0] == 1 if result else False

    def get_all_users(self):
        sql = "SELECT * FROM Users"
        return self.execute(sql, fetchall=True)

    def delete_user(self, user_id: int):
        sql = "DELETE FROM Users WHERE id = ?"
        return self.execute(sql, parameters=(user_id,), commit=True)
