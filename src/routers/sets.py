from src.schemas.pagination import CardSetPagination, CardPagination
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from src.services import sets_service
from psycopg import Cursor
from src.core import db


router = APIRouter()


@router.get("/", response_model=CardSetPagination)
async def get_sets(
    depends = Depends(db.get_db),
    search: str | None = Query(None),
    limit: int = Query(64, ge=1, le=999),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("card_set_code", description="sort by card_set_code, name or price"),
    sort_order: str = Query("asc", description="ascending or descending order")
) -> JSONResponse:
    cur: Cursor = depends.cursor()
    return sets_service.fetch_sets(
        cur, 
        search,
        limit, 
        offset, 
        sort_by, 
        sort_order
    )


@router.get("/cards", response_model=CardPagination)
async def get_card_sets(
    depends = Depends(db.get_db),
    set_name: str = Query(),
    limit: int = Query(64, ge=1, le=999),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("set_name", description="sort by set_name, set_code, num_of_cards or tcg_date"),
    sort_order: str = Query("asc", description="ascending or descending order")
) -> JSONResponse:
    cur: Cursor = depends.cursor()
    return sets_service.fetch_set_cards(
        cur, 
        set_name, 
        limit, 
        offset, 
        sort_by, 
        sort_order
    )
