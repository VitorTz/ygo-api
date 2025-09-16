from src.services.trivias_service import fetch_trivias
from src.schemas.pagination import TriviaPagination
from fastapi import APIRouter, Depends, Query
from psycopg import Cursor
from src.core import db


router = APIRouter()


@router.get("/", response_model=TriviaPagination)
async def get_trivias(
    depends = Depends(db.get_db),
    sort_by: str = Query("trivia_id", description='order by trivia_id or random'),
    limit: int = Query(64, ge=1, le=999),
    offset: int = Query(0, ge=0)
):
    cur: Cursor = depends.cursor()
    return fetch_trivias(
        cur, 
        sort_by,
        limit,
        offset
    )