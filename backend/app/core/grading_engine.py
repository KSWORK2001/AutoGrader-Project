# backend/app/core/grading_engine.py

import json
import torch
from transformers import TextStreamer

from app.core.model_loader import QWEN_MODEL, QWEN_TOKENIZER


class GradeResult:
    def __init__(self, score: int, explanation: str):
        self.score = score
        self.explanation = explanation


def build_prompt(question_text, expert_answers, student_answer, max_score=10):
    expert_block = "\n\n".join(
        [f"Expert Answer {i+1}:\n{txt}" for i, txt in enumerate(expert_answers)]
    )

    return f"""
You are a strict exam grader.

Rules:
- You may ONLY use the expert answers as the source of truth.
- Do NOT use external knowledge.
- Score the student's answer from 1 to {max_score}.
- Provide a brief explanation (2–3 sentences).
- Respond ONLY in JSON.

Question:
{question_text}

Expert Answers:
{expert_block}

Student Answer:
{student_answer}

Return JSON:
{{
  "score": <1-{max_score}>,
  "explanation": "..."
}}
""".strip()


def call_qwen(prompt: str) -> dict:
    """
    Runs Qwen3-8B inference.
    """
    if QWEN_MODEL is None or QWEN_TOKENIZER is None:
        raise RuntimeError("Qwen model is not loaded!")

    inputs = QWEN_TOKENIZER(prompt, return_tensors="pt").to("cuda")

    output_ids = QWEN_MODEL.generate(
        **inputs,
        max_new_tokens=256,
        do_sample=True,
        temperature=0.3,
    )

    output_text = QWEN_TOKENIZER.decode(output_ids[0], skip_special_tokens=True)

    # Strip the prompt from the beginning
    cleaned = output_text[len(prompt):].strip()

    # Try parse JSON
    try:
        json_start = cleaned.index("{")
        json_str = cleaned[json_start:]
        data = json.loads(json_str)
        return data
    except Exception:
        return {"score": 1, "explanation": "Could not parse model output."}


def grade_answer(question_text, expert_answers, student_answer, max_score=10):
    """
    Main scoring function.
    """
    prompt = build_prompt(question_text, expert_answers, student_answer, max_score)
    res = call_qwen(prompt)

    score = int(res.get("score", 1))
    score = max(1, min(max_score, score))

    explanation = res.get("explanation", "No explanation provided.")

    return GradeResult(score, explanation)
