from pydantic import BaseModel
from typing import Optional
from datetime import date


class CardSet(BaseModel):

    card_set_id: int
    set_name: str
    set_code: str
    num_of_cards: int
    tcg_date: Optional[date] = None
    set_image: Optional[str] = None