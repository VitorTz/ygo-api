from fastapi import FastAPI, Request, status, Depends
from contextlib import asynccontextmanager
from src import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.db_migrate()
    yield
    print("SQLite closed")


app = FastAPI(title="Yu-Gi-Oh! API", lifespan=lifespan)


@app.get("/")
async def home():
    return status.HTTP_200_OK


@app.get("/cards")
async def get_cards(db = Depends(db.get_db)):
    pass
