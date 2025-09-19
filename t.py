from src.core import db
from src.s3 import YgoS3
from psycopg import Cursor
from pathlib import Path
from multiprocessing.pool import ThreadPool
from src.util import download_image, delete_file


class CardSet:

    def __init__(self, card_set_id: int, set_image: str):
        self.card_set_id = card_set_id
        self.set_image = set_image


def get_sets(cur: Cursor) -> list[CardSet]:
    cur.execute("SELECT card_set_id, set_image FROM card_sets WHERE set_image is not NULL;")
    return [CardSet(s['card_set_id'], s['set_image']) for s in cur.fetchall()]


def main() -> None:
    s3 = YgoS3()
    conn, cur = db.db_instance()
    card_sets: list[CardSet] = get_sets(cur)

    params = []

    def upload(data: tuple[CardSet, int]) -> None:
        card_set, index = data
        tmp = Path(f"tmp/{card_set.card_set_id}.jpg")
        set_image: Path = download_image(tmp, card_set.set_image)
        set_image_url: str = s3.upload_set_image(set_image)
        delete_file(set_image)
        if set_image_url is None:
            print(f"[INVALID SET IMAGE] | {data}")
            params[index] = (None, None)
            return
        print(f"[IMAGE {card_set.set_image} UPLOADED]")
        params[index] = (set_image_url, card_set.card_set_id)

    for card_set in card_sets:
        params.append((card_set, len(params)))
    
    with ThreadPool(4) as pool:
        pool.map(upload, params)

    try:
        cur.executemany(
            """
                UPDATE 
                    card_sets
                SET
                    set_image = %s
                WHERE
                    card_set_id = %s;
            """,
            params
        )
        conn.commit()
    except Exception as e:
        print(f"[EXCEPTION main] | {e}")
        conn.rollback()

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()