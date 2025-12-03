# backend/app/models/schemas.py

from pydantic import BaseModel
from typing import List


class QuestionGradeRequest(BaseModel):
    question_id: int
    question_text: str
    student_answer: str
    expert_answers: List[str]
    max_score: int = 10


class GradeRequest(BaseModel):
    student_id: int
    answers: List[QuestionGradeRequest]


class QuestionScoreDTO(BaseModel):
    question_id: int
    score: int
    explanation: str


class GradeResponse(BaseModel):
    student_id: int
    total_score: int
    per_question: List[QuestionScoreDTO]
