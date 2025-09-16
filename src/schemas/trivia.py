from typing import Optional, List
from pydantic import BaseModel


class Trivia(BaseModel):
        
    question: str
    explanation: str
    source: Optional[str] = None
    answers: List[str]
    correct_answer: str