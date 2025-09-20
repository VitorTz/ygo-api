from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from src.globals import globals_get_enums
from psycopg import Connection, Cursor
from fastapi import UploadFile, File, Query, Depends
from fastapi import APIRouter
from fastapi import status
from src.s3 import YgoS3
from src.core import db


MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
CHUNKK = 1024 * 1024  # 1 MB
router = APIRouter()


@router.post("/cards")
async def create_card_image(file: UploadFile = File(...), card_type: str = Query(), depends = Depends(db.get_db)):
    conn: Connection = depends
    cur: Cursor = depends.cursor()
    s3 = YgoS3()
    content: bytes = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large")