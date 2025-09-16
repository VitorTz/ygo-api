from pydantic import BaseModel


class Banlist(BaseModel):

    ban_id: int
    card_id: int
    ban_org: str
    ban_type: str