import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
import os


load_dotenv()


DATABASE_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}


def get_db():
    conn = psycopg.connect(**DATABASE_CONFIG, cursor_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()

        
def db_migrate() -> None:
    conn = psycopg.connect(**DATABASE_CONFIG, row_factory=dict_row)
    cursor = conn.cursor()
    try:
        with open("db/migrate.sql", "r", encoding="utf-8") as f:
            sql_commands = f.read()
        cursor.execute(sql_commands)
        conn.commit()
    except Exception as e:
        print("exception when open commands", e)
        
    cursor.close()
    conn.close()
