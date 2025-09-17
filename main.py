from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from src.globals import globals_init
from src.routers import cards
from src.routers import enums
from src.routers import sets
from src.routers import trivias
from src.core import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[FASTAPI START]")
    db.db_migrate()
    globals_init()
    yield
    print("[FASTAPI CLOSE]")



app = FastAPI(title="Yu-Gi-Oh! API", lifespan=lifespan)
app.include_router(cards.router, prefix="/cards", tags=["cards"])
app.include_router(enums.router, prefix="/enums", tags=["enums"])
app.include_router(sets.router, prefix="/sets", tags=["sets"])
app.include_router(trivias.router, prefix="/trivias", tags=["trivias"])


@app.get("/")
async def home():
    return status.HTTP_200_OK
