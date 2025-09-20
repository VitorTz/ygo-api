from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import HTTPException
from src.schemas.card import CardCreate
from fastapi import status
from psycopg import Cursor, Connection
from src.core import db
from src import globals
from src import util


def fetch_all_cards(cur: Cursor) -> JSONResponse:
    cards: list[dict] = []
    try:
        cards = globals.globals_get_cards()
    except Exception as e:
        print(e)
        return JSONResponse('error', status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    if not cards:
        try:
            cur.execute("SELECT * FROM cards_mv;")
            cards = cur.fetchall()
            globals.globals_set_cards(cards)
        except Exception as e:
            print(e)
            return JSONResponse('error', status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    response = {
        "total": len(cards),
        "limit": len(cards),
        "offset": 0,
        "page": 1,
        "pages": 1,
        "results": cards
    }
    return JSONResponse(response, status.HTTP_200_OK)


def fetch_card_by_id(cur: Cursor, card_id: int) -> JSONResponse:
    card: dict | None = db.get_card_by_id(cur, card_id)
    response = {
        "total": 1 if card is not None else 0,
        "limit": 1,
        "offset": 0,
        "page": 1,
        "pages": 1,
        "results": [card] if card is not None else []
    }
    http_status = status.HTTP_404_NOT_FOUND if card is None else status.HTTP_200_OK
    return JSONResponse(response, http_status)


def fetch_cards_by_name(
    cur: Cursor, 
    params: tuple[str], 
    where_clause: str, 
    search: str,
    limit: int,
    offset: int,
    sort_by: str,
    sort_order: str,
    null_first: bool
) -> JSONResponse:
    params.append(f"%{search}%")
    try:
        cur.execute(
            f"""
                SELECT 
                    COUNT(*) as total 
                FROM 
                    cards_mv 
                {where_clause}
            """, 
            tuple(params)
        )
    except Exception as e:
        print(e)
        return JSONResponse('error', status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    total = cur.fetchone()['total']

    # Pagination
    params.extend([limit, offset])
    query = f"""
        SELECT 
            *
        FROM 
            cards_mv
        {where_clause}
        ORDER BY 
            {sort_by} {sort_order} {"NULLS FIRST" if null_first else "NULLS LAST"}, card_id ASC
        LIMIT %s 
        OFFSET %s;
    """
    
    try:
        cur.execute(query, tuple(params))
    except Exception as e:
        return JSONResponse('error', status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": cur.fetchall()
    }

    return JSONResponse(response, status.HTTP_200_OK)


def _fetch_cards(
    cur: Cursor,
    params: tuple[str],
    where_clause: str,
    limit: int,
    offset: int,
    sort_by: str,
    sort_order: str,
    null_first: bool
) -> JSONResponse:
    try:
        cur.execute(
            f"""
                SELECT 
                    COUNT(*) as total 
                FROM 
                    cards_mv
                {where_clause};
            """,
            tuple(params)
        )            
    except Exception as e:
        print(e)
        return JSONResponse('error', status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    total = cur.fetchone()['total']
    params.extend([limit, offset])
    query = f"""
        SELECT 
            * 
        FROM 
            cards_mv
        {where_clause}
        ORDER BY 
            {sort_by} {sort_order} {"NULLS FIRST" if null_first else "NULLS LAST"}, card_id ASC
        LIMIT %s 
        OFFSET %s;
    """

    try:
        cur.execute(query, tuple(params))
    except Exception as e:
        print(e)
        return JSONResponse('error', status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": cur.fetchall()
    }

    return JSONResponse(response, status.HTTP_200_OK)


def fetch_cards(
    cur: Cursor,
    limit: int,
    offset: int,
    sort_by: str,
    sort_order: str,
    all_cards: bool,
    card_id: int | None,
    search: str | None,
    null_first: bool,
    archetype: str | None,
    race: str | None,
    type: str | None,
    attribute: str | None,
    frametype: str | None
) -> JSONResponse:
    if all_cards:
        return fetch_all_cards(cur)

    enums_response: JSONResponse | None = util.is_valid_enums(
        archetype,
        frametype,
        attribute,
        race,
        type
    )

    if enums_response is not None:
        return enums_response
    
    sort_by = util.normalize_card_sort_by(sort_by)
    sort_order = util.normalize_sort_order(sort_order, sort_by.lower() == 'random')
    where_clause, params = util.extract_card_filters(locals(), search)

    if card_id is not None:
        return fetch_card_by_id(cur, card_id)

    if search:
        return fetch_cards_by_name(
            cur, 
            params, 
            where_clause, 
            search, 
            limit, 
            offset, 
            sort_by, 
            sort_order, 
            null_first
        )
    
    return _fetch_cards(
        cur,
        params,
        where_clause,
        limit,
        offset,
        sort_by,
        sort_order,
        null_first
    )


def create_card_service(conn: Connection, cur: Cursor, card: CardCreate) -> Response | HTTPException:
    cur.execute("SELECT card_id FROM cards WHERE card_id = %s;", (card.card_id, ))
    r = cur.fetchone()
    if r is not None:
        return Response(status_code=status.HTTP_409_CONFLICT)
    
    enums_response: JSONResponse | None = util.is_valid_enums(
        card.archetype,
        card.attribute,
        card.frametype,
        card.race,
        card.type
    )
    
    if enums_response is not None:
        return enums_response    
    
    try:
        cur.execute(
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
            (
                card.card_id,
                card.name,
                card.descr,
                card.pend_descr,
                card.monster_descr,
                card.attack,
                card.defence,
                card.level,
                card.archetype,
                card.attribute,
                card.frametype,
                card.race,
                card.type
            )
        )
        conn.commit()
        return Response(status_code=status.HTTP_201_CREATED)
    except Exception as e:
        conn.rollback()
        print(f"[EXCEPTION create_card_service] |{e}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def delete_card_by_id(conn: Connection, cur: Cursor, card_id: int) -> Response | HTTPException:
    try:
        cur.execute("DELETE FROM cards WHERE card_id = %s;", (card_id, ))
        conn.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        print(f"[EXCEPTION delete_card] | {card_id} | {e}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)