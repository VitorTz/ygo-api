from multiprocessing.pool import ThreadPool
from psycopg import Connection, Cursor
from threading import Lock
from pathlib import Path
from src.s3 import YgoS3
from src import util
from src.core import db
import json


data: list[dict] = []
card_sets: list[dict] = []
conn: Connection = None
cur: Cursor = None
lock = Lock()


def init_db() -> None:
    global conn, cur, data, card_sets
    data = util.load_ygoprodeck_data()
    card_sets = util.load_ygoprodeck_cardsets()
    db.db_migrate()
    conn, cur = db.db_instance()


def close_db() -> None:
    cur.close()
    conn.close()


def populate_enums() -> None:
    print("[POPULATING ENUMS]")
    archetypes: set[str] = set()
    attributes: set[str] = set()
    frametypes: set[str] = set()
    races: set[str] = set()
    types: set[str] = set()
    for card in data:
        if card.get("archetype"):
            archetypes.add(card['archetype'])
        if card.get("attribute"):
            attributes.add(card['attribute'])
        if card.get("frameType"):
            frametypes.add(card['frameType'])
        if card.get("race"):
            races.add(card['race'])
        if card.get("type"):
            types.add(card['type'])

    for archetype in archetypes:
        db.db_add_enum_value_if_not_exists(conn, cur, 'archetype_enum', archetype)
    
    for attribute in attributes:
        db.db_add_enum_value_if_not_exists(conn, cur, 'attribute_enum', attribute)
    
    for frametype in frametypes:
        db.db_add_enum_value_if_not_exists(conn, cur, 'frametype_enum', frametype)
    
    for race in races:
        db.db_add_enum_value_if_not_exists(conn, cur, 'race_enum', race)
    
    for card_type in types:
        db.db_add_enum_value_if_not_exists(conn, cur, 'type_enum', card_type)
        

def populate_cards() -> None:
    print("[POPULATING CARDS]")
    params = []
    for card in data:
        try:
            card_id: int = card['id']
            name: str = card['name'].strip()
            descr: str = card['desc'].strip()
            pend_descr: str | None = card.get("pend_desc")
            monster_descr: str | None = card.get("monster_desc")
            attack: int | None = card.get("atk")
            defence: int | None = card.get("def")
            level: int | None = card.get("level")
            archetype: str = card.get('archetype')
            attribute: str | None = card.get("attribute")
            frametype: str = card['frameType'].strip()
            race: str = card['race'].strip()
            type: str = card['type'].strip()
            
            if race == '':
                race = None
            
            if type == '':
                type = None

            if frametype == '':
                frametype = None

            params.append((
                card_id,
                name,
                descr,
                pend_descr,
                monster_descr,
                attack,
                defence,
                level,
                archetype,
                attribute,
                frametype,
                race,
                type
            ))
        except Exception as e:
            print(f"[EXCEPTION populate_cards] | {e}")
            print(card)
            return    

    try:
        cur.executemany(
            """
                INSERT INTO cards (
                    card_id,
                    name,
                    descr,
                    pend_descr,
                    monster_descr,
                    attack,
                    defence,
                    level,
                    archetype,
                    attribute,
                    frametype,
                    race,
                    type
                )
                VALUES 
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT
                    (card_id)
                DO NOTHING;
            """,
            params
        )
        conn.commit()
    except Exception as e:
        print(f"[EXCEPTION populate_cards] | {e}")
        conn.rollback()

    
def populate_images() -> None:
    print("[POPULATING IMAGES]")
    Path("tmp").mkdir(exist_ok=True)
    s3 = YgoS3()
    cur.execute("SELECT card_id FROM card_images;")
    card_ids = {i['card_id'] for i in cur.fetchall()}
    total = len(card_ids)

    def populate(card: dict) -> None:
        nonlocal total
        images: list[dict] = card.get('card_images')
        if not images:  return

        for image in images:
            card_id: int = image["id"]
            if card_id in card_ids: continue

            image_url: str | None = image.get('image_url')
            if image_url:
                image_url_path = Path(f'tmp/{card_id}-image_url.jpg')
                image_url_path: Path = util.download_image(image_url_path, image_url)
                image_url: str = s3.upload_card(card_id, 'normal', image_url_path)
                util.delete_file(image_url_path)
                if 'http' not in image_url:
                    image_url = None

            image_url_cropped: str | None = image.get('image_url_cropped')
            if image_url_cropped:
                image_url_cropped_path = Path(f'tmp/{card_id}-image_url_cropped.jpg')
                image_url_cropped_path: Path = util.download_image(image_url_cropped_path, image_url_cropped)
                image_url_cropped: str = s3.upload_card(card_id, 'cropped', image_url_cropped_path)
                util.delete_file(image_url_cropped_path)
                if 'http' not in image_url_cropped:
                    image_url_cropped = None

            image_url_small: str | None = image.get('image_url_small')
            if image_url_small:
                image_url_small_path = Path(f'tmp/{card_id}-image_url_small.jpg')
                image_url_small_path: Path = util.download_image(image_url_small_path, image_url_small)
                image_url_small: str = s3.upload_card(card_id, 'small', image_url_small_path)
                util.delete_file(image_url_small_path)
                if 'http' not in image_url_small:
                    image_url_small = None

            try:
                cur.execute(
                    """
                        INSERT INTO card_images (
                            card_id,
                            image_url,
                            image_url_cropped,
                            image_url_small
                        )
                        VALUES 
                            (%s, %s, %s, %s)
                        ON CONFLICT
                            (card_id)
                        DO NOTHING;    
                    """,
                    (card_id, image_url, image_url_cropped, image_url_small)
                )
                conn.commit()
                print(f"[ADD CARD [{total}] {card['name']}]")
                lock.acquire()
                total += 1
                lock.release()
            except Exception as e:
                print(f"[EXCEPTION populate_images] | {e}")
                conn.rollback()
                return
            
    with ThreadPool(4) as pool:
        pool.map(populate, data)


def populate_sets() -> None:
    print("[POPULATING SETS]")

    params_card_sets: list[tuple] = []

    for card_set in card_sets:
        set_name: str = card_set['set_name']
        set_code: str = card_set['set_code']
        num_of_cards: int = card_set['num_of_cards']
        tcg_date: str | None = card_set.get("tcg_date")
        set_image: str | None = card_set.get("set_image")
        params_card_sets.append((
            set_name,
            set_code,
            num_of_cards,
            tcg_date,
            set_image
        ))

    try:
        cur.executemany(
            """
                INSERT INTO card_sets (
                    set_name,
                    set_code,
                    num_of_cards,
                    tcg_date,
                    set_image
                )
                VALUES 
                    (%s, %s, %s, %s, %s)
                ON CONFLICT
                    (set_name)
                DO NOTHING;
            """,
            (params_card_sets)
        )
        conn.commit()
    except Exception as e:
        print(f"[EXCEPTION populate_sets params_card_sets] {e}")
        conn.rollback()


def populate_cards_in_sets() -> None:
    print("[POPULATING CARDS IN SETS]")
    r = {}
    for card in data:
        card_id: int = card['id']
        card_sets = card.get("card_sets")
        if card_sets is None: continue
        for card_set in card_sets:
            k = (card_id, card_set['set_name'].strip().lower())
            r[k] = r.get(k, 0) + 1

    cur.execute("SELECT set_name, card_set_id FROM card_sets;")
    set_dict = {x['set_name'].strip().lower(): x['card_set_id'] for x in cur.fetchall()}

    params = []
    for k, v in r.items():
        params.append((
            k[0],
            set_dict[k[1]],
            v
        ))

    try:
        cur.executemany(
            """
                INSERT INTO cards_in_sets (
                    card_id,
                    card_set_id,
                    num_of_cards
                )
                VALUES 
                    (%s, %s, %s)
                ON CONFLICT
                    (card_id, card_set_id)
                DO UPDATE SET
                    num_of_cards = EXCLUDED.num_of_cards;
            """,
            params
        )
        conn.commit()
    except Exception as e:
        print(f"[EXCEPTION populate_cards_in_sets] | {e}")
        conn.rollback()



def populate_card_prices() -> None:
    print("[POPULATING CARD PRICES]")
    params = []
    for card in data:
        card_id: int = card['id']
        card_prices: list[dict] = card.get("card_prices")
        if not card_prices: continue
        try:
            params.append((
                card_id,
                float(card_prices[0].get("amazon_price", 0)) * 100,
                float(card_prices[0].get("cardmarket_price", 0)) * 100,
                float(card_prices[0].get("coolstuffinc_price", 0)) * 100,
                float(card_prices[0].get("ebay_price", 0)) * 100,
                float(card_prices[0].get("tcgplayer_price", 0)) * 100
            ))
        except Exception as e:
            print(f"[EXCEPTION populate_card_prices] | {e}")
            print(card)
            return

    try:
        cur.executemany(
            """
                INSERT INTO card_prices (
                    card_id,
                    amazon_price,
                    cardmarket_price,
                    coolstuffinc_price,
                    ebay_price,
                    tcgplayer_price
                )
                VALUES 
                    (%s, %s, %s, %s, %s, %s)
                ON CONFLICT
                    (card_id)
                DO NOTHING;
            """,
            params
        )
        conn.commit()
    except Exception as e:
        print(f"[EXCEPTION populate_card_prices] | {e}")
        conn.rollback()


def populate_linkmarkers() -> None:
    print("[POPULATING LINKMARKERS]")
    params = []
    for card in data:
        card_id: int = card['id']
        linkmarkers: list[str] = card.get('linkmarkers')
        if not linkmarkers: continue
        for linkmarker in linkmarkers:
            params.append((card_id, linkmarker))
    
    try:
        cur.executemany(
            """
                INSERT INTO linkmarkers (
                    card_id,
                    position
                )
                VALUES
                    (%s, %s)
                ON CONFLICT
                    (card_id, position)
                DO NOTHING;
            """,
            (params)
        )
        conn.commit()
    except Exception as e:
        print(f"[EXCEPTION populate_linkmarkers] | {e}")
        conn.rollback()


def populate_banlist() -> None:
    print("[POPULATE BANLIST]")
    params = []
    for card in data:
        card_id: int = card['id']
        banlist_info: dict[str, str] | None = card.get("banlist_info")
        if not banlist_info: continue
        for k, v in banlist_info.items():    
            params.append((card_id, k.replace("ban_", "").strip(), v))

    try:
        cur.execute("DELETE FROM banlist;")
        conn.commit()
    except Exception as e:
        print(f"[EXCEPTION populate_banlist DELETE] | {e}")
        conn.rollback()

    try:
        cur.executemany(
            """
                INSERT INTO banlist (
                    card_id,
                    ban_org,
                    ban_type
                )
                VALUES 
                    (%s, %s, %s)
                ON CONFLICT
                    (card_id, ban_org, ban_type)
                DO NOTHING;
            """,
            (params)
        )
        conn.commit()
    except Exception as e:
        print(f"[EXCEPTION populate_banlist] | {e}")
        conn.rollback()


def populate_trivias() -> None:
    with open("db/trivias.json", "r") as file:
        trivias = json.load(file)
    
    params = []    

    for trivia in trivias:
        params.append((
            trivia['question'],
            trivia['explanation'],
            trivia['source']
        ))

    try:
        cur.executemany(
            """
                INSERT INTO trivias (
                    question,
                    explanation,
                    source
                )
                VALUES 
                    (%s, %s, %s)
                ON CONFLICT
                    (question)
                DO NOTHING;
            """,
            (params)
        )
        conn.commit()
    except Exception as e:
        print(f"[EXCEPTION populate_trivias] | {e}")
        return
    
    cur.execute("SELECT trivia_id, question FROM trivias;")
    questions = {}
    for trivia in cur.fetchall():
        questions[trivia['question']] = trivia['trivia_id']

    
    params = []
    for trivia in trivias:
        num_correct_answers = 0
        for answers in trivia['answers']:
            if answers['is_correct_answer']:
                num_correct_answers += 1
            params.append((
                questions[trivia['question']], # trivia_id
                answers['answer'],
                answers['is_correct_answer']
            ))
        if num_correct_answers != 1:
            print(f"[EXCEPTION populate_trivias] | CORRECT_ANSWERS {num_correct_answers} | {trivia}")
            return
    
    try:
        cur.executemany(
            """
                INSERT INTO trivia_answers (
                    trivia_id,
                    answer,
                    is_correct_answer
                )
                VALUES 
                    (%s, %s, %s)
                ON CONFLICT
                    (trivia_id, answer)
                DO NOTHING;
            """,
            params
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[EXCEPTION populate_trivias] | {e}")


def main() -> None:
    init_db()
    populate_enums()
    populate_cards()
    # populate_sets()
    # populate_cards_in_sets()
    populate_card_prices()
    populate_linkmarkers()
    populate_banlist()
    populate_trivias()
    populate_images()
    db.db_size(cur)
    for i in db.db_archetype_rank(cur):
        print(i)
    close_db()


if __name__ == "__main__":
    main()