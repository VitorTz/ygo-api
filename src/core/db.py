from psycopg import Connection, Cursor
from psycopg.rows import dict_row
from dotenv import load_dotenv
from pathlib import Path
from psycopg import sql
from src.schemas.card import Card
from src.schemas.rank import Rank
import psycopg
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


def db_count(cur: Cursor, table: str) -> int:
    cur.execute(f"SELECT count(*) as total FROM {table}")
    return cur.fetchone()['total']


def db_execute_sql_file(file: Path, conn: Connection, cursor: Cursor) -> None:
    try:
        with open(file, "r", encoding="utf-8") as f:
            sql_commands = f.read()
        cursor.execute(sql_commands)
        conn.commit()
    except Exception as e:
        print(f"exception when open commands [{file}]", e)

        
def db_migrate() -> None:
    print("[DATABASE MIGRATE START]")
    conn = psycopg.connect(**DATABASE_CONFIG)
    cursor = conn.cursor()
    db_execute_sql_file(Path("db/extensions.sql"), conn, cursor)
    db_execute_sql_file(Path("db/enums.sql"), conn, cursor)
    db_execute_sql_file(Path("db/tables.sql"), conn, cursor)
    db_execute_sql_file(Path("db/views.sql"), conn, cursor)
    cursor.close()
    conn.close()
    print("[DATABASE MIGRATE END]")


def db_size(cur: Cursor) -> None:
    cur.execute(
        """
            SELECT 
                relname AS table_name,
                pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
                pg_size_pretty(pg_relation_size(relid)) AS data_size,
                pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) AS index_size
            FROM 
                pg_catalog.pg_statio_user_tables
            ORDER BY 
                pg_total_relation_size(relid) DESC;
        """
    )
    [print(i) for i in cur.fetchall()]

    
def get_card_by_id(cur: Cursor, card_id: int) -> Card:
    cur.execute("SELECT * FROM cards_mv WHERE card_id = %s;", (card_id, ))
    return cur.fetchone()


def db_enum_value_exists(cur: Cursor, enum: str, value: str) -> bool:
    cur.execute(
        f"""
            SELECT 
                e.enumlabel
            FROM 
                pg_type t
            JOIN 
                pg_enum e ON t.oid = e.enumtypid
            WHERE 
                t.typname = '{enum}' AND 
                e.enumlabel = %s;
        """,
        (value, )
    )
    r = cur.fetchone()
    return r is not None


def db_add_enum_value_if_not_exists(conn: Connection, cur: Cursor, enum: str, value: str) -> None:
    try:        
        check_query = """
            SELECT enumlabel
            FROM pg_enum
            JOIN pg_type ON pg_enum.enumtypid = pg_type.oid
            WHERE pg_type.typname = %s AND enumlabel = %s;
        """
        cur.execute(check_query, (enum, value))
        exists = cur.fetchone()

        if exists: return
        
        query = sql.SQL("ALTER TYPE {enum} ADD VALUE {value}").format(
            enum=sql.Identifier(enum),
            value=sql.Literal(value)
        )
        print(f"[TRY ADD ENUM VALUE] {enum}:{value}")
        cur.execute(query)
        conn.commit()
        print(f"[NEW ENUM VALUE ADDED] {enum}:{value}")
    except Exception as e:
        print(f"[EXCEPTION db_add_enum_value] | {e}")
        conn.rollback()


def db_archetype_rank(cur: Cursor) -> list[Rank]:
    cur.execute(
        """
            SELECT 
                archetype as name,
                COUNT(*) AS total,
                ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) - 1 AS position
            FROM 
                cards
            WHERE 
                archetype IS NOT NULL
            GROUP BY 
                archetype
            ORDER BY 
                total DESC;
        """
    )
    return cur.fetchall()


def db_get_enum_list(cur: Cursor, enum: str) -> list[str]:
    cur.execute(
        f"""
        SELECT
            enumlabel AS name
        FROM 
            pg_enum
        JOIN 
            pg_type ON pg_enum.enumtypid = pg_type.oid
        WHERE 
            pg_type.typname = '{enum}'
        ORDER BY 
            enumlabel ASC;
        """
    )
    return [x['name'] for x in cur.fetchall()]


def db_show_all(cur: Cursor, table: str) -> None:
    print(f"############### {table} ###############")
    cur.execute(f"SELECT * FROM {table};")
    [print(i) for i in cur.fetchall()]


def db_card_exists(cur: Cursor, card_id: int) -> bool:
    cur.execute("SELECT card_id FROM cards WHERE card_id = %s;", (card_id, ))
    r = cur.fetchone()
    return r is not None


def db_count(cur: Cursor, table: str) -> int:
    cur.execute(f"SELECT count(*) as total FROM {table};")
    r = cur.fetchone()
    if r: return r['total']
    return 0


def db_refresh_cards_materialized_view(conn: Connection, cur: Cursor) -> None:
    cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY cards_mv;")
    conn.commit()


def db_refresh_cards_sets_materialized_view(conn: Connection, cur: Cursor) -> None:
    cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY card_sets_mv;")
    conn.commit()