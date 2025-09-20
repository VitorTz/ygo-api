from src.core import db
from dotenv import load_dotenv
import os


load_dotenv()


TOKEN = os.getenv("TOKEN")
CARDS: list[dict] = []
ENUMS: dict = {}


def globals_init() -> None:
    global ENUMS, CARDS

    # INIT DB
    conn, cur = db.db_instance()
    
    # ENUMS
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
        'type': {'set': set(types), 'list': types}
    }

    # CARDS
    cur.execute("SELECT * FROM cards_mv;")
    CARDS = cur.fetchall()

    # CLOSE DB
    cur.close()
    conn.close()    


def globals_get_cards() -> list[dict]:
    global CARDS
    return CARDS


def globals_set_cards(cards: list[dict]) -> None:
    global CARDS
    CARDS = cards


def globals_get_token() -> str:
    global TOKEN
    return TOKEN

def globals_get_enums() -> dict:
    global ENUMS
    return ENUMS