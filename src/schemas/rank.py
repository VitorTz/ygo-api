from pydantic import BaseModel


class Rank(BaseModel):

    name: str
    total: str
    position: int