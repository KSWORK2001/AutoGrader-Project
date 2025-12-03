# backend/app/api/grade_routes.py

from fastapi import APIRouter
from app.models.schemas import GradeRequest, GradeResponse, QuestionScoreDTO

from app.core.grading_engine import grade_answer

router = APIRouter()


@router.post("/", response_model=GradeResponse)
async def grade_exam(req: GradeRequest):
    """
    Grades student answers using dynamically supplied expert answers.
    """

    per_q_scores = []
    total = 0

    for q in req.answers:

        result = grade_answer(
            question_text=q.question_text,
            expert_answers=q.expert_answers,
            student_answer=q.student_answer,
            max_score=q.max_score
        )

        per_q_scores.append(
            QuestionScoreDTO(
                question_id=q.question_id,
                score=result.score,
                explanation=result.explanation
            )
        )

        total += result.score

    return GradeResponse(
        student_id=req.student_id,
        total_score=total,
        per_question=per_q_scores
    )
