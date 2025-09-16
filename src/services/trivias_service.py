from fastapi.responses import JSONResponse
from fastapi import status
from psycopg import Cursor
from src.core import db


def fetch_trivias(
    cur: Cursor,
    sort_by: str,
    limit: int,
    offset: int
) -> JSONResponse:
    
    total = db.db_count(cur, 'trivias')

    sort_by = "RANDOM()" if sort_by.lower() == 'random' else 't.trivia_id'

    cur.execute(
        f"""
            SELECT
                t.question,
                t.explanation,
                t.source,
                ARRAY_AGG(ta.answer ORDER BY ta.trivia_answer_id) AS answers,
                MAX(ta.answer) FILTER (WHERE ta.is_correct_answer) AS correct_answer
            FROM 
                trivias t
            JOIN 
                trivia_answers ta ON t.trivia_id = ta.trivia_id
            GROUP BY 
                t.trivia_id, t.question, t.explanation, t.source
            ORDER BY
                {sort_by}
            LIMIT %s
            OFFSET %s;
        """,
        (limit, offset)
    )

    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "page": (offset // limit) + 1,
        "pages": (total + limit - 1) // limit,
        "results": cur.fetchall()
    }

    return JSONResponse(response, status.HTTP_200_OK)