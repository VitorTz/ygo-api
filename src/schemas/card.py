from src.schemas.linkmarker import LinkMarker
from src.schemas.card_price import CardPrice
from src.schemas.card_set import CardSet
from src.schemas.banlist import Banlist
from src.schemas.image import Image
from typing import Optional, List
from pydantic import BaseModel


class Card(BaseModel):
    
    card_id: int
    name: str
    descr: str
    pend_descr: Optional[str] = None
    monster_descr: Optional[str] = None
    attack: Optional[int] = None
    defence: Optional[int] = None
    level: Optional[int] = None
    archetype: str
    attribute: Optional[str] = None
    frametype: str
    race: Optional[str] = None
    type: Optional[str] = None
    card_sets: List[CardSet]
    linkmarkers: List[LinkMarker]
    banlists: List[Banlist]
    images: List[Image]
    card_prices: List[CardPrice]


class CardCreate(BaseModel):
    
    card_id: int
    name: str
    descr: str
    pend_descr: Optional[str] = None
    monster_descr: Optional[str] = None
    attack: Optional[int] = None
    defence: Optional[int] = None
    level: Optional[int] = None
    archetype: str
    attribute: Optional[str] = None
    frametype: str
    race: Optional[str] = None
    type: Optional[str] = None