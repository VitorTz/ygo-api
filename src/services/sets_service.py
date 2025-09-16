from psycopg import Cursor
from fastapi.responses import JSONResponse
from fastapi import status
from src import util
from src.core import db


def fetch_sets(
    cur: Cursor,
    limit: int,
    offset: int,
    sort_by: str,
    sort_order: str
) -> None:
    sort_order: str = util.normalize_sort_order(sort_order)
    sort_by: str = util.normalize_card_sets_sort_by(sort_by)
    total = db.db_count(cur, 'card_sets')    

    cur.execute(
        f"""
            SELECT 
                set_name, 
                set_code
                num_of_cards,
                tcg_date,
                set_image
            FROM 
                card_sets
            ORDER BY 
                {sort_by} {sort_order}
            LIMIT %s
            OFFSET %s;
        """,
        (limit, offset)
    )

    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": cur.fetchall()
    }

    return JSONResponse(response, status.HTTP_200_OK)


def fetch_set_cards(
    cur: Cursor,
    set_name: str,
    limit: int,
    offset: int,
    sort_by: str,
    sort_order: str
) -> JSONResponse:    
    cur.execute("SELECT card_set_id FROM card_sets WHERE set_name = %s;", (set_name, ))
    r = cur.fetchone()

    if r is None:
        return JSONResponse({"error": f"Invalid set_name -> {set_name}"}, status.HTTP_400_BAD_REQUEST)
    
    sort_order: str = util.normalize_sort_order(sort_order)
    sort_by: str = util.normalize_card_sort_by(sort_by)
    card_set_id: int = r['card_set_id']

    cur.execute(
        """
            SELECT 
                count(c.*) as total
            FROM 
                cards_in_sets
            WHERE 
                card_set_id = %s;
        """,
        (card_set_id, )
    )
    total: int = cur.fetchone()['total']

    cur.execute(
        """
            SELECT 
                c.*
            FROM 
                cards_in_sets cis
            JOIN 
                cards_mv c ON cis.card_id = c.card_id
            WHERE 
                cs.card_set_id = %s
            LIMIT %s
            OFFSET %s;
        """,
        (card_set_id, limit, offset)
    )

    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": cur.fetchall()
    }

    return JSONResponse(response, status.HTTP_200_OK)