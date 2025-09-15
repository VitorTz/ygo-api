from fastapi import FastAPI, status, Depends, Query
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from psycopg import Cursor
from src.util import normalize_card_sort_by, normalize_sort_order, normalize_card_sets_sort_by, extract_card_filters
import json
from src.db import db_migrate, get_db, get_card_by_id, db_get_enum_list, db_instance


FILTERABLE_COLUMNS = {
    "archetype",
    "race",
    "type",
    "attribute",
    "frametype", 
}


ENUMS: dict[str, set[str]] = {}


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

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_migrate()
    load_enums()
    yield
    print("SQLite closed")


app = FastAPI(title="Yu-Gi-Oh! API", lifespan=lifespan)


@app.get("/")
async def home():
    return status.HTTP_200_OK


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
        return JSONResponse(content=response, status_code=status.HTTP_200_OK)

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
            return JSONResponse(content='error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
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
            return JSONResponse(content='error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response = {
            "total": total,
            "limit": limit,
            "offset": offset,
            "page": (offset // limit) + 1,
            "pages": (total + limit - 1) // limit,
            "results": cur.fetchall()
        }

        return JSONResponse(content=response, status_code=status.HTTP_200_OK)
        
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
        return JSONResponse(content='error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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
        return JSONResponse(content='error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": cur.fetchall()
    }

    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@app.get("/all_cards")
async def get_cards():
    with open("res/api/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(content=data)


@app.get("/attributes", response_model=list[str])
async def get_attributes(db = Depends(get_db)):
    cur: Cursor = db.cursor()
    rows = db_get_enum_list(cur, "attribute_enum")
    return JSONResponse(
        content=rows,
        status_code=status.HTTP_200_OK
    )


@app.get("/archetypes", response_model=list[str])
async def get_archetypes(db = Depends(get_db)):
    cur: Cursor = db.cursor()
    rows = db_get_enum_list(cur, "archetype_enum")
    return JSONResponse(
        content=rows,
        status_code=status.HTTP_200_OK
    )


@app.get("/frametypes", response_model=list[str])
async def get_frametypes(db = Depends(get_db)):
    cur: Cursor = db.cursor()
    rows = db_get_enum_list(cur, "frametype_enum")
    return JSONResponse(
        content=rows,
        status_code=status.HTTP_200_OK
    )


@app.get("/races", response_model=list[str])
async def get_races(db = Depends(get_db)):
    cur: Cursor = db.cursor()
    rows = db_get_enum_list(cur, "race_enum")
    return JSONResponse(
        content=rows,
        status_code=status.HTTP_200_OK
    )


@app.get("/types", response_model=list[str])
async def get_types(db = Depends(get_db)):
    cur: Cursor = db.cursor()
    rows = db_get_enum_list(cur, "type_enum")
    return JSONResponse(
        content=rows,
        status_code=status.HTTP_200_OK
    )


@app.get("/sets", response_model=list[str])
async def get_sets(
    db = Depends(get_db),
    limit: int = Query(64, ge=1, le=999),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("card_set_code", description="sort by card_set_code, name or price"),
    sort_order: str = Query("asc", description="asc (ascending) or desc (descending) order")
):
    sort_order = normalize_sort_order(sort_order)
    sort_by = normalize_card_sets_sort_by(sort_by)

    cur: Cursor = db.cursor()
    cur.execute("SELECT count(*) as total FROM card_sets;")
    total = cur.fetchone()['total']

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

    return JSONResponse(content=response, status_code=status.HTTP_200_OK)