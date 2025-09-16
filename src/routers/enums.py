from src.schemas.stringlist import StringListResponse
from fastapi.responses import JSONResponse
from src.globals import globals_get_enums
from fastapi import APIRouter
from fastapi import status


router = APIRouter()


@router.get("/attributes", response_model=StringListResponse)
async def get_attributes() -> JSONResponse:
    enums: dict = globals_get_enums()
    return JSONResponse({"total": len(enums['attribute']['list']), "results": enums['attribute']['list']}, status.HTTP_200_OK)


@router.get("/archetypes", response_model=StringListResponse)
async def get_archetypes() -> JSONResponse:
    enums: dict = globals_get_enums()
    return JSONResponse({"total": len(enums['archetype']['list']), "results": enums['archetype']['list']}, status.HTTP_200_OK)


@router.get("/frametypes", response_model=StringListResponse)
async def get_frametypes() -> JSONResponse:
    enums: dict = globals_get_enums()
    return JSONResponse({"total": len(enums['frametype']['list']), "results": enums['frametype']['list']}, status.HTTP_200_OK)


@router.get("/races", response_model=StringListResponse)
async def get_races() -> JSONResponse:
    enums: dict = globals_get_enums()
    return JSONResponse({"total": len(enums['race']['list']), "results": enums['race']['list']}, status.HTTP_200_OK)


@router.get("/types", response_model=StringListResponse)
async def get_types() -> JSONResponse:
    enums: dict = globals_get_enums()
    return JSONResponse({"total": len(enums['type']['list']), "results": enums['type']['list']}, status.HTTP_200_OK)
