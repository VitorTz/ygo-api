from psycopg import Cursor
from src.core import db

CARDS: list[dict] = []
ENUMS: dict = {}


def load_enums(cur: Cursor) -> None:
    global ENUMS
    archetypes = db.db_get_enum_list(cur, "archetype_enum")
    attributes = db.db_get_enum_list(cur, "attribute_enum")
    frametypes = db.db_get_enum_list(cur, "frametype_enum")
    races = db.db_get_enum_list(cur, "race_enum")
    types = db.db_get_enum_list(cur, "type_enum")
    ENUMS = {
        'archetype': {'set': set(archetypes), 'list': archetypes},
        'attribute': {'set': set(attributes), 'list': attributes},
        'frametype': {'set': set(frametypes), 'list': frametypes},
        'race': {'set': set(races), 'list': races},
        'type': {'types': set(types), 'list': types}
    }


def load_all_cards(cur: Cursor) -> None:
    global CARDS
    cur.execute("SELECT * FROM cards_mv;")
    CARDS = cur.fetchall()    


def globals_init() -> None:
    conn, cur = db.db_instance()
    load_enums(cur)
    load_all_cards(cur)
    cur.close()
    conn.close()    


def globals_get_cards() -> list[dict]:
    global CARDS
    return CARDS


def globals_get_enums() -> dict:
    global ENUMS
    return ENUMS