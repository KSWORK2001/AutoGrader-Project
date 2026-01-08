# backend.py
import base64
import json
import tempfile
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, List
import os
from dotenv import load_dotenv
from openai import OpenAI 
load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SYSTEM_PROMPT = """
You are an AI exam evaluator acting like a strict university examiner.

You will receive:
- The exam question (optional)
- One student's handwritten answer (image or text)
- Three expert reference answers

Your tasks:
1. Understand the student's answer fully.
2. Compare it against ALL expert answers.
3. Identify:
   - Correct concepts
   - Missing points
   - Incorrect or vague explanations
4. Assign a score from 0 to 10.
5. Clearly justify the score.

IMPORTANT OUTPUT RULES:
- Always explain WHY marks were deducted.
- Explicitly mention which expert points were:
  - Covered
  - Partially covered
  - Missing
- Provide constructive suggestions to improve the answer.

Return STRICT JSON only in this format:

{
  "score": <integer>,
  "explanation": "Detailed explanation of evaluation",
  "coverage_summary": "Which expert points were covered or missed",
  "suggestions": "Concrete suggestions for improvement"
}
"""


@dataclass
class GradeResult:
    score: Optional[int]
    explanation: str
    coverage_summary: str
    suggestions: str
    raw_model_response: str


class Backend:
    """
    This class is exposed to the JS layer via pywebview (js_api=Backend()).
    Methods here can be called from JS as window.pywebview.api.<method>.
    """

    def __init__(self):
        pass

    # This is the function we'll call from JS: window.pywebview.api.grade_answer(payload)
    def grade_answer(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        payload is expected to have:
        {
          "question": str,
          "studentImageBase64": str,  // base64 of the handwritten image (no prefix)
          "expert1": str,
          "expert2": str,
          "expert3": str
        }
        """
        question = payload.get("question", "") or ""
        expert1 = payload.get("expert1", "") or ""
        expert2 = payload.get("expert2", "") or ""
        expert3 = payload.get("expert3", "") or ""
        student_image_b64 = payload.get("studentImageBase64", "")
        student_text = payload.get("studentText", "").strip()

        use_text_mode = bool(student_text)

        if not use_text_mode and not student_image_b64:
            return {"error": "No student answer provided. Upload an image or enter text."}
        # Build the user prompt text (we also still attach the image for extraction)
        user_prompt = self._build_user_prompt(
            question=question,
            expert_answers=[expert1, expert2, expert3],
            student_text=student_text
        )

        try:
            # TEXT MODE (Enter Text selected)
            if student_text:
                response = openai_client.responses.create(
                    model="gpt-5-mini",
                    input=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT.strip()
                        },
                        {
                            "role": "user",
                            "content": user_prompt.strip()
                        }
                    ]
                )

            # IMAGE MODE (Upload Image selected)
            else:
                response = openai_client.responses.create(
                    model="gpt-5-mini",
                    input=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT.strip()
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "input_text",
                                    "text": user_prompt.strip()
                                },
                                {
                                    "type": "input_image",
                                    "image_url": f"data:image/png;base64,{student_image_b64}"
                                }
                            ]
                        }
                    ]
                )

            raw_content = response.output_text

        except Exception as e:
            return {
                "error": f"Error calling OpenAI model: {e}"
            }
        parsed = self._parse_model_json(raw_content)
        def safe_str(value):
            # Nothing there
            if value is None:
                return ""

            # Already a simple string → trim & return
            if isinstance(value, str):
                return value.strip()

            # If value is a dict, pretty format it
            if isinstance(value, dict):
                output = []
                for key, items in value.items():
                    output.append(f"{key.capitalize()}:")
                    if isinstance(items, list):
                        for item in items:
                            output.append(f"  • {item}")
                    else:
                        output.append(f"  • {items}")
                    output.append("")  # spacing
                return "\n".join(output).strip()

            # If value is a list → bullet list
            if isinstance(value, list):
                return "\n".join([f"• {item}" for item in value])

            # Default fallback
            return str(value).strip()

        result = GradeResult(
            score=parsed.get("score"),
            explanation=safe_str(parsed.get("explanation")),
            coverage_summary=safe_str(parsed.get("coverage_summary")),
            suggestions=safe_str(parsed.get("suggestions")),
            raw_model_response=raw_content,
        )

        # Return a dict – pywebview will JSON-serialize this.
        return asdict(result)

    @staticmethod
    def _build_user_prompt(question: str, expert_answers: List[str], student_text: str = "") -> str:
        experts_text = []
        for i, ans in enumerate(expert_answers, start=1):
            label = f"EXPERT ANSWER {i}"
            experts_text.append(f"{label}:\n{ans.strip() or '[EMPTY]'}")

        prompt_parts = []

        if question.strip():
            prompt_parts.append(f"QUESTION:\n{question.strip()}\n")

        prompt_parts.append("\nREFERENCE EXPERT ANSWERS:\n" + "\n\n".join(experts_text))

        prompt_parts.append(
            f"""
    If a STUDENT TEXT ANSWER is provided, use it directly:
    STUDENT TEXT (IF ANY):
    {student_text if student_text else "[No direct text, use the image]"}
            
    If no student text is provided, extract the text from the image.
    After you have the final student answer, compare it with the expert answers and grade it.
    Remember to output STRICTLY the JSON format requested earlier.
    """.strip()
        )

        return "\n\n".join(prompt_parts)


    @staticmethod
    def _parse_model_json(raw_content: str) -> Dict[str, Any]:
        """
        Try to parse the model output as JSON. If it fails, wrap it as explanation.
        """
        try:
            # Some models might wrap JSON in text – try to extract the first {...} block.
            raw_content_stripped = raw_content.strip()
            # Quick & dirty brace matching:
            if raw_content_stripped.startswith("{") and raw_content_stripped.endswith("}"):
                return json.loads(raw_content_stripped)

            # Fallback: find first '{' and last '}'.
            first = raw_content_stripped.find("{")
            last = raw_content_stripped.rfind("}")
            if first != -1 and last != -1 and last > first:
                json_candidate = raw_content_stripped[first : last + 1]
                return json.loads(json_candidate)

        except Exception:
            pass

        # If all else fails, treat entire response as explanation
        return {
            "score": None,
            "explanation": raw_content,
            "coverage_summary": "",
            "suggestions": "",
        }
