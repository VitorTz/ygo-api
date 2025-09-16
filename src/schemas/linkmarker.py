from pydantic import BaseModel


class LinkMarker(BaseModel):

    card_id: int
    position: str