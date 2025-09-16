from src.services.cards_service import fetch_cards
from src.schemas.pagination import CardPagination
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from psycopg import Cursor
from src.core import db


router = APIRouter()


@router.get("/", response_model=CardPagination)
async def get_cards(
    depends=Depends(db.get_db),
    limit: int = Query(64, ge=1, le=999),
    offset: int = Query(0, ge=0),
    search: str | None = None,
    card_id: int | None = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    all_cards: bool = False,
    null_first: bool = False,
    archetype: str | None = None,
    race: str | None = None,
    type: str | None = None,
    attribute: str | None = None,
    frametype: str | None = None
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