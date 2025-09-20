from psycopg import Connection, Cursor
from src.schemas.image import ImageType
from src.core import db
from src.s3 import YgoS3
from pathlib import Path
from src.util import delete_file


def create_image_service(
    conn: Connection,
    cur: Cursor,
    card_id: int, 
    file: bytes, 
    type: ImageType
) -> None:
    s3 = YgoS3()
    path = Path("tmp")
    path.mkdir(exist_ok=True)
    path = path / f"{card_id}.webp"
    with open(path, "wb") as img_file:
        img_file.write(file)

    image_url: str = s3.upload_card(card_id, ImageType.to_string(type), path)
    delete_file(path)

    column = "image_url"
    if type == ImageType.Cropped:
        column = "image_url_cropped"
    elif type == ImageType.Small:
        column = "image_url_small"
    
    try:
        cur.execute(
            f"""
                INSERT INTO card_images (
                    card_id,
                    {column}
                )
                VALUES 
                    (%s, %s)
                ON CONFLICT
                    (card_id)
                DO UPDATE SET
                    {column} = EXCLUDED.{column}
            """,
            (card_id, image_url)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[EXCEPTION create_image_service] | {e}")