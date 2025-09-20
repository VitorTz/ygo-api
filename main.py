from contextlib import asynccontextmanager
from src.globals import globals_init
from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from fastapi import status
from src.routers import trivias
from src.routers import cards
from src.routers import enums
from src.routers import sets
from src.core import db


MAX_BODY_SIZE = 2 * 1024 * 1024


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


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    body = await request.body()
    if len(body) > MAX_BODY_SIZE:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": f"Request body too large. Max {MAX_BODY_SIZE} bytes."}
        )
    return await call_next(request)


@app.get("/")
async def home():
    return status.HTTP_200_OK
