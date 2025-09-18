from src.schemas.card_set import CardSet
from src.schemas.trivia import Trivia
from src.schemas.card import Card
from pydantic import BaseModel
from typing import List


class CardPagination(BaseModel):
    
    total: int
    limit: int
    offset: int
    page: int
    pages: int
    results: List[Card]


class CardSetPagination(BaseModel):
    
    total: int
    limit: int
    offset: int
    page: int
    pages: int
    results: List[CardSet]


class TriviaPagination(BaseModel):
    
    total: int
    limit: int
    offset: int
    page: int
    pages: int
    results: List[Trivia]
