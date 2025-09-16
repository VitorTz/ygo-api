from pydantic import BaseModel
from typing import List


class StringListResponse(BaseModel):
    total: int
    results: List[str]