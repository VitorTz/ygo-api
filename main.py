from src.schemas.pagination import CardPagination, CardSetPagination, TriviaPagination
from src.schemas.stringlist import StringListResponse
from fastapi import FastAPI, status, Depends, Query
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from src.schemas.card import Card
from psycopg import Cursor
from typing import List
from src import util
from src import db


ENUMS: dict[str, set[str]] = {}
CARDS: list[dict] = []


def load_enums() -> None:
    global ENUMS
    conn, cur = db.db_instance()
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
    cur.close()
    conn.close()


def load_all_cards() -> None:
    global CARDS
    conn, cur = db.db_instance()
    cur.execute("SELECT * FROM cards_mv;")
    CARDS = cur.fetchall()
    cur.close()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.db_migrate()
    load_enums()
    load_all_cards()
    yield
    print("SQLite closed")


app = FastAPI(title="Yu-Gi-Oh! API", lifespan=lifespan)


@app.get("/")
async def home():
    return status.HTTP_200_OK


@app.get("/cards/random", response_model=List[Card])
async def get_random_card(
    depends = Depends(db.get_db),
    limit: int = Query(64, ge=1, le=999)    
):
    cur: Cursor = depends.cursor()
    total = db.db_count(cur, "cards_mv")
    cur.execute("SELECT * FROM cards_mv ORDER BY RANDOM() LIMIT %s;", (limit, ))
    response = {
        "total": total,
        "limit": limit,
        "offset": 0,
        "page": (0 // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": cur.fetchall()
    }

    return JSONResponse(response, status.HTTP_200_OK)


@app.get("/cards", response_model=CardPagination)
async def get_cards(
    depends = Depends(db.get_db),
    limit: int = Query(64, ge=1, le=999),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("name", description="sort by name, attack, defence, level or card_id"),
    sort_order: str = Query("asc", description="ascending or descending order"),
    card_id: int | None = Query(None, description='search for the card with the exact card_id'),
    search: str | None = Query(None, description="search=Magician will search for all cards with \"Magician\" in the name"),
    null_first: bool = Query(False),
    archetype: str | None = Query(None),
    race: str | None = Query(None),
    type: str | None = Query(None),
    attribute: str | None = Query(None),
    frametype: str | None = Query(None)
):
    cur: Cursor = depends.cursor()

    sort_by = util.normalize_card_sort_by(sort_by)
    sort_order = util.normalize_sort_order(sort_order)
    where_clause, params = util.extract_card_filters(locals(), search) # archetype, attribute, race, type and frametype

    if archetype and archetype not in ENUMS['archetype']:
        return JSONResponse(content={'error': f'invalid archetype -> {archetype}'}, status_code=status.HTTP_400_BAD_REQUEST)
    
    if attribute and attribute not in ENUMS['attribute']:
        return JSONResponse(content={'error': f'invalid attribute -> {attribute}'}, status_code=status.HTTP_400_BAD_REQUEST)

    if frametype and frametype not in ENUMS['frametype']:
        return JSONResponse(content={'error': f'invalid frametype -> {frametype}'}, status_code=status.HTTP_400_BAD_REQUEST)
    
    if race and race not in ENUMS['race']:
        return JSONResponse(content={'error': f'invalid race -> {race}'}, status_code=status.HTTP_400_BAD_REQUEST)
    
    if type and type not in ENUMS['type']:
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


@app.get("/cards/all", response_model=CardPagination)
async def get_cards():
    response = {
        "total": len(CARDS),
        "limit": len(CARDS),
        "offset": 0,
        "page": 1,
        "pages": 1,
        "results": CARDS
    }
    return JSONResponse(response, status.HTTP_200_OK)


@app.get("/attributes", response_model=StringListResponse)
async def get_attributes():
    return JSONResponse({"total": len(ENUMS['attribute']['list']), "results": ENUMS['attribute']['list']}, status.HTTP_200_OK)


@app.get("/archetypes", response_model=StringListResponse)
async def get_archetypes():
    return JSONResponse({"total": len(ENUMS['archetype']['list']), "results": ENUMS['archetype']['list']}, status.HTTP_200_OK)


@app.get("/frametypes", response_model=StringListResponse)
async def get_frametypes():
    return JSONResponse({"total": len(ENUMS['frametype']['list']), "results": ENUMS['frametype']['list']}, status.HTTP_200_OK)


@app.get("/races", response_model=StringListResponse)
async def get_races():
    return JSONResponse({"total": len(ENUMS['race']['list']), "results": ENUMS['race']['list']}, status.HTTP_200_OK)


@app.get("/types", response_model=StringListResponse)
async def get_types():
    return JSONResponse({"total": len(ENUMS['type']['list']), "results": ENUMS['type']['list']}, status.HTTP_200_OK)


@app.get("/sets", response_model=CardSetPagination)
async def get_sets(
    depends = Depends(db.get_db),
    limit: int = Query(64, ge=1, le=999),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("card_set_code", description="sort by card_set_code, name or price"),
    sort_order: str = Query("asc", description="ascending or descending order")
):
    sort_order: str = util.normalize_sort_order(sort_order)
    sort_by: str = util.normalize_card_sets_sort_by(sort_by)

    cur: Cursor = depends.cursor()
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


@app.get("/sets/cards", response_model=CardPagination)
async def get_card_sets(
    depends = Depends(db.get_db),
    set_name: str = Query(),
    limit: int = Query(64, ge=1, le=999),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("set_name", description="sort by set_name, set_code, num_of_cards or tcg_date"),
    sort_order: str = Query("asc", description="ascending or descending order")
):
    cur: Cursor = depends.cursor()
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


@app.get("/trivias", response_model=TriviaPagination)
async def get_trivias(
    depends = Depends(db.get_db),
    limit: int = Query(64, ge=1, le=999),
    offset: int = Query(0, ge=0)
):
    cur: Cursor = depends.cursor()    

    total = db.db_count(cur, 'trivias')

    cur.execute(
        """
            SELECT
                t.question,
                t.explanation,
                t.source,
                ARRAY_AGG(ta.answer ORDER BY ta.trivia_answer_id) AS answers,
                MAX(ta.answer) FILTER (WHERE ta.is_correct_answer) AS correct_answer
            FROM 
                trivias t
            JOIN 
                trivia_answers ta ON t.trivia_id = ta.trivia_id
            GROUP BY 
                t.trivia_id, t.question, t.explanation, t.source
            ORDER BY
                t.trivia_id ASC
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


@app.get("/trivias/random", response_model=TriviaPagination)
async def get_trivias(
    depends = Depends(db.get_db),
    limit: int = Query(64, ge=1, le=999),
    offset: int = Query(0, ge=0)
):
    cur: Cursor = depends.cursor()    
    total = db.db_count(cur, 'trivias')
    
    cur.execute(
        """
            SELECT
                t.question,
                t.explanation,
                t.source,
                ARRAY_AGG(ta.answer ORDER BY ta.trivia_answer_id) AS answers,
                MAX(ta.answer) FILTER (WHERE ta.is_correct_answer) AS correct_answer
            FROM 
                trivias t
            JOIN 
                trivia_answers ta ON t.trivia_id = ta.trivia_id
            GROUP BY 
                t.trivia_id, t.question, t.explanation, t.source
            ORDER BY
                RANDOM()
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
    