from src.services.cards_service import fetch_cards, delete_card_by_id, create_card_service
from src.schemas.pagination import CardPagination
from fastapi.responses import JSONResponse, Response
from fastapi import APIRouter, Depends, Query
from src.schemas.card import CardCreate
from src.globals import globals_get_token
from fastapi import HTTPException
from fastapi import status
from psycopg import Cursor, Connection
from src.core import db


router = APIRouter()


@router.get("/", response_model=CardPagination)
async def get_cards(
    depends=Depends(db.get_db),
    limit: int = Query(64, ge=1, le=999),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None, description='you can search cards by name. search=magician will return all cards with magician in name'),
    card_id: int | None = Query(None, description='will search for a especific card by it card_id'),
    sort_by: str = Query("name", description="sort by name, attack, defence, level, card_id or random"),
    sort_order: str = Query("asc", description="ascending (asc) or descending (desc) order"),
    all_cards: bool = Query(False, description='if true, will return all cards'),
    null_first: bool = Query(False),
    archetype: str | None = Query(None),
    race: str | None = Query(None),
    type: str | None = Query(None),
    attribute: str | None = Query(None),
    frametype: str | None = Query(None)
) -> JSONResponse:
    cur: Cursor = depends.cursor()
    return fetch_cards(
        cur,
        limit, 
        offset, 
        sort_by, 
        sort_order,
        all_cards, 
        card_id, 
        search, 
        null_first, 
        archetype, 
        race, 
        type, 
        attribute, 
        frametype
    )


@router.post("/")
def create_card(card: CardCreate, token: str = Query(), depends=Depends(db.get_db)):
    if token != globals_get_token():
        return Response("Now allowed", status.HTTP_401_UNAUTHORIZED)
    conn: Connection = depends
    cur: Cursor = conn.cursor()
    return create_card_service(conn, cur, card)


@router.delete("/")
def delete_card(
    card_id: int = Query(),
    token: str = Query(),
    depends=Depends(db.get_db)
) -> Response:
    if token != globals_get_token():
        return Response("Now allowed", status.HTTP_401_UNAUTHORIZED)
    conn: Connection = depends
    cur: Cursor = conn.cursor()
    return delete_card_by_id(conn, cur, card_id)
    