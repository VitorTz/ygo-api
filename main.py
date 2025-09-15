from fastapi import FastAPI, status, Depends, Query
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from psycopg import Cursor
from src.util import normalize_card_sort_by, normalize_sort_order, normalize_card_sets_sort_by, extract_card_filters
import json
from src.db import db_migrate, get_db, get_card_by_id, db_get_enum_list, db_instance


ENUMS: dict[str, set[str]] = {}
CARDS: list[dict] = []


def load_enums() -> None:
    global ENUMS
    conn, cur = db_instance()
    ENUMS = {
        'archetype': set(db_get_enum_list(cur, "archetype_enum")),
        'attribute': set(db_get_enum_list(cur, "attribute_enum")),
        'frametype': set(db_get_enum_list(cur, "frametype_enum")),
        'race': set(db_get_enum_list(cur, "race_enum")),
        'type': set(db_get_enum_list(cur, "type_enum"))
    }
    cur.close()
    conn.close()

def load_all_cards() -> None:
    global CARDS
    with open("res/api/cards.json", "r", encoding="utf-8") as f:
        CARDS = json.load(f)    


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_migrate()
    load_enums()
    load_all_cards()
    yield
    print("SQLite closed")


app = FastAPI(title="Yu-Gi-Oh! API", lifespan=lifespan)


@app.get("/")
async def home():
    return status.HTTP_200_OK


@app.get("/cards/random")
async def get_random_card(db = Depends(get_db)):
    cur: Cursor = db.cursor()
    cur.execute("SELECT * FROM cards_mv ORDER BY RANDOM() LIMIT 1;")
    return JSONResponse(cur.fetchone(), status.HTTP_200_OK)    


@app.get("/cards")
async def get_cards(
    db = Depends(get_db),
    limit: int = Query(64, ge=1, le=999),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("name", description="sort by name, attack, defence, level or card_id"),
    sort_order: str = Query("asc", description="asc (ascending) or desc (descending) order"),
    card_id: int | None = Query(None, description='search for the card with the exact card_id'),
    search: str | None = Query(None, description="search=Magician will search for all cards with \"Magician\" in the name"),
    null_first: bool = Query(False),
    archetype: str | None = Query(None),
    race: str | None = Query(None),
    type: str | None = Query(None),
    attribute: str | None = Query(None),
    frametype: str | None = Query(None)
):
    cur: Cursor = db.cursor()

    sort_by = normalize_card_sort_by(sort_by)
    sort_order = normalize_sort_order(sort_order)
    where_clause, params = extract_card_filters(locals(), search) # archetype, attribute, race, type and frametype

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
        card: dict | None = get_card_by_id(cur, card_id)
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


@app.get("/all_cards")
async def get_cards():
    return JSONResponse(content={
        "total": len(CARDS),
        "results": CARDS
    })


@app.get("/attributes")
async def get_attributes(db = Depends(get_db)):
    cur: Cursor = db.cursor()
    rows: list[str] = db_get_enum_list(cur, "attribute_enum")
    return JSONResponse({"total": len(rows), "results": rows}, status.HTTP_200_OK)


@app.get("/archetypes")
async def get_archetypes(db = Depends(get_db)):
    cur: Cursor = db.cursor()
    rows: list[str] = db_get_enum_list(cur, "archetype_enum")
    return JSONResponse({"total": len(rows), "results": rows}, status.HTTP_200_OK)


@app.get("/frametypes")
async def get_frametypes(db = Depends(get_db)):
    cur: Cursor = db.cursor()
    rows: list[str] = db_get_enum_list(cur, "frametype_enum")
    return JSONResponse({"total": len(rows), "results": rows}, status.HTTP_200_OK)


@app.get("/races")
async def get_races(db = Depends(get_db)):
    cur: Cursor = db.cursor()
    rows: list[str] = db_get_enum_list(cur, "race_enum")
    return JSONResponse({"total": len(rows), "results": rows}, status.HTTP_200_OK)


@app.get("/types")
async def get_types(db = Depends(get_db)):
    cur: Cursor = db.cursor()
    rows: list[str] = db_get_enum_list(cur, "type_enum")
    return JSONResponse({"total": len(rows), "results": rows}, status.HTTP_200_OK)


@app.get("/sets")
async def get_sets(
    db = Depends(get_db),
    limit: int = Query(64, ge=1, le=999),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("card_set_code", description="sort by card_set_code, name or price"),
    sort_order: str = Query("asc", description="asc (ascending) or desc (descending) order")
):
    sort_order: str = normalize_sort_order(sort_order)
    sort_by: str = normalize_card_sets_sort_by(sort_by)

    cur: Cursor = db.cursor()
    cur.execute("SELECT count(*) as total FROM card_sets;")
    total: int = cur.fetchone()['total']

    cur.execute(
        f"""
            SELECT 
                cs.card_set_code, 
                cs.name, 
                sr.name as set_rarity, 
                sr.code as set_rarity_code,
                cs.price::float / 100.0 AS price
            FROM 
                card_sets cs
            JOIN
                set_rarity sr ON cs.set_rarity_id = sr.set_rarity_id
            ORDER BY 
                cs.{sort_by} {sort_order}
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


@app.get("/sets/cards")
async def get_card_sets(
    db = Depends(get_db),
    card_set_code: str = Query(),
    limit: int = Query(64, ge=1, le=999),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("name", description="sort by name, attack, defence, level or card_id"),
    sort_order: str = Query("asc", description="asc (ascending) or desc (descending) order")
):
    sort_order: str = normalize_sort_order(sort_order)
    sort_by: str = normalize_card_sort_by(sort_by)

    cur: Cursor = db.cursor()
    cur.execute(
        """
            SELECT 
                count(c.*) as total
            FROM 
                cards_in_sets cis
            JOIN 
                cards c ON cis.card_id = c.card_id
            JOIN 
                card_sets cs ON cis.card_set_code = cs.card_set_code
            WHERE 
                cs.card_set_code = %s;
        """,
        (card_set_code, )
    )
    total: int = cur.fetchone()['total']

    cur.execute(
        """
            SELECT 
                c.card_id,
                c.name,
                c.descr,
                c.attack,
                c.defence,
                c.level,
                c.archetype,
                c.attribute,
                c.frametype,
                c.race,
                c.type
            FROM 
                cards_in_sets cis
            JOIN 
                cards c ON cis.card_id = c.card_id
            JOIN 
                card_sets cs ON cis.card_set_code = cs.card_set_code
            WHERE 
                cs.card_set_code = %s
            LIMIT %s
            OFFSET %s;
        """,
        (card_set_code, limit, offset)
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


@app.get("/sets/rank")
async def get_card_sets(
    db = Depends(get_db),    
    limit: int = Query(64, ge=1, le=999),
    offset: int = Query(0, ge=0),    
    sort_order: str = Query("desc", description="asc (ascending) or desc (descending) order")
):
    sort_order: str = normalize_sort_order(sort_order)

    cur: Cursor = db.cursor()
    cur.execute(
        """
            SELECT 
                count(*) as total
            FROM 
                card_sets;
        """        
    )
    total: int = cur.fetchone()['total']

    cur.execute(
        f"""
            SELECT 
                cs.card_set_code,
                cs.name AS set_name,
                COUNT(cis.card_id) AS total_cards
            FROM 
                card_sets cs
            JOIN 
                cards_in_sets cis ON cs.card_set_code = cis.card_set_code
            GROUP BY 
                cs.card_set_code, cs.name
            ORDER BY 
                total_cards {sort_order}
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
