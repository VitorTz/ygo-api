import psycopg
from psycopg import Connection, Cursor
from psycopg.rows import dict_row
from pathlib import Path
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


def db_instance() -> tuple[Connection, Cursor]:
    conn = psycopg.connect(**DATABASE_CONFIG, row_factory=dict_row)
    cursor = conn.cursor()
    return conn, cursor


def get_db():
    conn = psycopg.connect(**DATABASE_CONFIG, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()


def db_execute_sql_file(file: Path, conn, cursor) -> None:
    try:
        with open(file, "r", encoding="utf-8") as f:
            sql_commands = f.read()
        cursor.execute(sql_commands)
        conn.commit()
    except Exception as e:
        print(f"exception when open commands [{file}]", e)

        
def db_migrate() -> None:
    print("[DATABASE MIGRATE START]")
    conn = psycopg.connect(**DATABASE_CONFIG, row_factory=dict_row)
    cursor = conn.cursor()
    db_execute_sql_file(Path("db/extensions.sql"), conn, cursor)
    db_execute_sql_file(Path("db/enums.sql"), conn, cursor)
    db_execute_sql_file(Path("db/tables.sql"), conn, cursor)
    cursor.close()
    conn.close()
    print("[DATABASE MIGRATE END]")