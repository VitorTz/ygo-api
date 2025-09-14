import json
from psycopg import Connection, Cursor
from src.db import db_migrate, db_instance
from src.util import download_image, delete_file
from pathlib import Path
from src.s3 import YgoS3
from multiprocessing.pool import ThreadPool
from threading import Lock


data: list[dict] = None
conn: Connection = None
cur: Cursor = None
lock = Lock()


def load_data() -> None:
    global data
    with open("res/data.json") as file:
        data = json.load(file)


def init_db() -> None:
    global conn, cur
    db_migrate()
    conn, cur = db_instance()


def close_db() -> None:
    cur.close()
    conn.close()


def card_exists(card_id: int) -> bool:
    cur.execute("SELECT card_id FROM cards WHERE card_id = %s;", (card_id, ))
    r = cur.fetchone()
    return r is not None


def populate_cards() -> None:
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

def show_all_cards() -> None:
    cur.execute("SELECT card_id, name FROM cards;")
    r = cur.fetchall()
    for card in r:
        print(card)
    print(len(r))

    
def populate_images() -> None:
    Path("tmp").mkdir(exist_ok=True)
    s3 = YgoS3()
    cur.execute("SELECT card_id FROM card_images;")
    card_ids = {i['card_id'] for i in cur.fetchall()}
    
    for card in data:
        images: list[dict] = card.get('card_images')
        if not images:  return

        for image in images:
            card_id: int = image["id"]
            if card_id in card_ids: continue

            image_url: str | None = image.get('image_url')
            if image_url:
                image_url_path = Path(f'tmp/{card_id}-image_url.jpg')
                image_url_path: Path = download_image(image_url_path, image_url)
                image_url: str = s3.upload_card(card_id, 'normal', image_url_path)
                delete_file(image_url_path)
                if 'http' not in image_url:
                    image_url = None

            image_url_cropped: str | None = image.get('image_url_cropped')
            if image_url_cropped:
                image_url_cropped_path = Path(f'tmp/{card_id}-image_url_cropped.jpg')
                image_url_cropped_path: Path = download_image(image_url_cropped_path, image_url_cropped)
                image_url_cropped: str = s3.upload_card(card_id, 'cropped', image_url_cropped_path)
                delete_file(image_url_cropped_path)
                if 'http' not in image_url_cropped:
                    image_url_cropped = None

            image_url_small: str | None = image.get('image_url_small')
            if image_url_small:
                image_url_small_path = Path(f'tmp/{card_id}-image_url_small.jpg')
                image_url_small_path: Path = download_image(image_url_small_path, image_url_small)
                image_url_small: str = s3.upload_card(card_id, 'small', image_url_small_path)
                delete_file(image_url_small_path)
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
                print(f"[ADD CARD {card['name']}]")
            except Exception as e:
                print(f"[EXCEPTION populate_images] | {e}")
                conn.rollback()
                return
        

def populate_sets() -> None:
    pass


def main() -> None:
    load_data()
    init_db()

    populate_cards()
    populate_images()
    populate_sets()
    show_all_cards()

    close_db()


if __name__ == "__main__":
    main()