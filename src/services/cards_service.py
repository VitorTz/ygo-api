from fastapi.responses import JSONResponse
from fastapi import status
from psycopg import Cursor
from src.core import db
from src import util
from src import globals


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
        cards: list[dict] = globals.globals_get_cards()
        response = {
            "total": len(cards),
            "limit": len(cards),
            "offset": 0,
            "page": 1,
            "pages": 1,
            "results": cards
        }
        return JSONResponse(response, status.HTTP_200_OK)

    enums: dict = globals.globals_get_enums()
    sort_by = 'RANDOM()' if sort_by.lower() == 'random' else util.normalize_card_sort_by(sort_by)
    sort_order = '' if sort_by.lower() else util.normalize_sort_order(sort_order)
    where_clause, params = util.extract_card_filters(locals(), search) # archetype, attribute, race, type and frametype

    if archetype and archetype not in enums['archetype']['set']:
        return JSONResponse(content={'error': f'invalid archetype -> {archetype}'}, status_code=status.HTTP_400_BAD_REQUEST)
    
    if attribute and attribute not in enums['attribute']['set']:
        return JSONResponse(content={'error': f'invalid attribute -> {attribute}'}, status_code=status.HTTP_400_BAD_REQUEST)

    if frametype and frametype not in enums['frametype']['set']:
        return JSONResponse(content={'error': f'invalid frametype -> {frametype}'}, status_code=status.HTTP_400_BAD_REQUEST)
    
    if race and race not in enums['race']['set']:
        return JSONResponse(content={'error': f'invalid race -> {race}'}, status_code=status.HTTP_400_BAD_REQUEST)
    
    if type and type not in enums['type']['set']:
        return JSONResponse(content={'error': f'invalid type -> {type}'}, status_code=status.HTTP_400_BAD_REQUEST)

    if card_id is not None:
        card: dict | None = db.get_card_by_id(cur, card_id)
        response = {
            "total": 1 if card is not None else 0,
            "limit": limit,
            "offset": offset,
            "page": 1,
            "pages": 1,
            "results": [card] if card is not None else []
        }
        return JSONResponse(response, status.HTTP_200_OK)

    if search:
        params.append(f"%{search}%")
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

        # Pagination
        params.extend([limit, offset])
        query = f"""
            SELECT 
                *
            FROM 
                cards_mv
            {where_clause}
            ORDER BY 
                {sort_by} {sort_order} {"NULLS FIRST" if null_first else "NULLS LAST"}
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
            {sort_by} {sort_order} {"NULLS FIRST" if null_first else "NULLS LAST"}
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