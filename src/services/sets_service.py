from fastapi.responses import JSONResponse
from psycopg import Cursor
from fastapi import status
from src import util


def fetch_set_by_id(
    cur: Cursor, 
    card_set_id: int, 
    limit: int, 
    offset: int
) -> JSONResponse:
    cur.execute(
        """
            SELECT 
                card_set_id,
                set_name, 
                set_code,
                num_of_cards,
                COALESCE(TO_CHAR(tcg_date, 'YYYY-MM-DD'), '') AS tcg_date,
                set_image
            FROM 
                card_sets 
            WHERE 
                card_set_id = %s;
            """, 
        (card_set_id, )
    )
    r: dict | None = cur.fetchone()
    total = 1 if r is not None else 0
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": r
    }

    htttp_status = status.HTTP_200_OK if r is not None else status.HTTP_204_NO_CONTENT
    return JSONResponse(response, htttp_status)


def fetch_set_by_code(cur: Cursor, set_code: str, limit: int, offset: int) -> JSONResponse:
    cur.execute(
        """
            SELECT 
                card_set_id,
                set_name, 
                set_code,
                num_of_cards,
                COALESCE(TO_CHAR(tcg_date, 'YYYY-MM-DD'), '') AS tcg_date,
                set_image
            FROM 
                card_sets 
            WHERE 
                set_code = %s;
            """, 
        (set_code, )
    )
    r: dict | None = cur.fetchone()
    total = 1 if r is not None else 0
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": r
    }

    htttp_status = status.HTTP_200_OK if r is not None else status.HTTP_204_NO_CONTENT
    return JSONResponse(response, htttp_status)


def fetch_sets(
    cur: Cursor,
    search: str | None,
    card_set_id: int | None,
    set_code: str,
    limit: int,
    offset: int,
    sort_by: str,
    sort_order: str
) -> JSONResponse:
    
    if card_set_id:
        return fetch_set_by_id(cur, card_set_id, limit, offset)
    
    if set_code is not None:
        return fetch_set_by_code(cur, set_code, limit, offset)

    sort_order: str = util.normalize_sort_order(sort_order)
    sort_by: str = util.normalize_card_sets_sort_by(sort_by)
    where_clause = "WHERE set_name ILIKE %s" if search is not None else ''

    if search is not None:
        params = [f"%{search}%", limit, offset]
    else:
        params = [limit, offset]
    
    cur.execute(
        f"SELECT count(*) as total FROM card_sets {where_clause};",
        (f"%{search}%", ) if search is not None else None
    )
    total = cur.fetchone()['total']
    
    cur.execute(
        f"""
            SELECT
                card_set_id,
                set_name, 
                set_code,
                num_of_cards,
                COALESCE(TO_CHAR(tcg_date, 'YYYY-MM-DD'), '') AS tcg_date,
                set_image
            FROM 
                card_sets
            {where_clause}
            ORDER BY 
                {sort_by} {sort_order}
            LIMIT %s
            OFFSET %s;
        """,
        tuple(params)
    )

    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": cur.fetchall()
    }

    http_status = status.HTTP_204_NO_CONTENT if total == 0 else status.HTTP_200_OK
    return JSONResponse(response, http_status)



def fetch_set_cards(
    cur: Cursor,
    set_name: str | None,
    card_set_id: int | None,
    set_code: str | None,
    order_by,
    sort_order,
    limit: int,
    offset: int
) -> JSONResponse:
    
    if set_name is None and set_code is None and card_set_id is None:
        return JSONResponse({"error": "you need to provide the set you whant the cards"}, status.HTTP_400_BAD_REQUEST)
        
    params = []
    where_clause = ''
    if card_set_id is not None:
        params.append(card_set_id)
        where_clause = "WHERE card_set_id = %s"
    
    if set_name is not None:
        params.append(f"%{set_name}%")
        where_clause = "WHERE set_name ILIKE %s"

    if set_code is not None:
        params.append(set_code)
        where_clause = "WHERE set_code = %s;"

    cur.execute(f"SELECT count(*) as total FROM card_sets_mv {where_clause};", tuple(params))
    total = cur.fetchone()['total']

    params.extend([limit, offset])
    cur.execute(
        f"""
            SELECT 
                *
            FROM 
                card_sets_mv
            {where_clause}
            ORDER BY
                {order_by} {sort_order}, card_set_id ASC
            LIMIT %s
            OFFSET %s;
        """,
        tuple(params)
    )
    
    r = cur.fetchall()
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": r
    }

    http_status = status.HTTP_204_NO_CONTENT if len(r) == 0 else status.HTTP_200_OK

    return JSONResponse(response, http_status)