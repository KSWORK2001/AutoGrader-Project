# backend.py
import base64
import json
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, List

import webview
from openai import OpenAI

SYSTEM_PROMPT = """
You are an exam autograder.

You will be given:
- The exam question (optional).
- One student's handwritten answer (as extracted text).
- THREE separate expert reference answers.

Your job:

1. Carefully compare the student's answer to ALL THREE expert answers.
2. Check:
   - Does the student cover all the key points present across the expert answers?
   - Are important examples, edge cases, formulas, definitions, or steps included?
   - Are there any conceptual mistakes, contradictions, or missing reasoning steps?
3. Evaluate the student's answer on a scale from 0 to 10, where:
   - 10 = Fully correct, covers essentially all important points, very clear.
   - 8–9 = Mostly correct, minor omissions or minor clarity issues.
   - 6–7 = Some important points covered but noticeable gaps or issues.
   - 3–5 = Major missing content or conceptual errors, partial understanding.
   - 0–2 = Very little correct content, severely flawed or irrelevant.
4. Be strict but fair. Reward correct reasoning and penalize missing critical content.
5. Write a concise explanation of WHY you gave that score.
6. Summarize which expert points the student covered or missed.

OUTPUT FORMAT (IMPORTANT):
Return ONLY valid JSON in the following shape:

{
  "score": <integer 0-10>,
  "explanation": "short explanation of the grading decision",
  "coverage_summary": "what was covered vs missing compared to the expert answers",
  "suggestions": "what the student should improve or add to reach 10/10"
}

Do NOT include any text before or after the JSON. No markdown.
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

    def __init__(self, model_name: str = "gpt-5-nano"):
        self.model_name = model_name
        self._api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self._client = OpenAI(api_key=self._api_key) if self._api_key else None

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

        if not use_text_mode:
            # Validate image base64 early to fail fast with a clear error.
            try:
                base64.b64decode(student_image_b64)
            except Exception as e:
                return {
                    "error": f"Failed to decode student image base64: {e}"
                }

        # Build the user prompt text (we also still attach the image for extraction)
        user_prompt = self._build_user_prompt(
            question=question,
            expert_answers=[expert1, expert2, expert3],
            student_text=student_text
        )

        if not self._client:
            return {
                "error": "Missing OPENAI_API_KEY environment variable. Set it and restart the app."
            }

        try:
            if student_text:
                model_input = user_prompt.strip()
            else:
                model_input = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": user_prompt.strip()},
                            {
                                "type": "input_image",
                                "image_url": f"data:image/png;base64,{student_image_b64}",
                            },
                        ],
                    }
                ]

            response = self._client.responses.create(
                model=self.model_name,
                instructions=SYSTEM_PROMPT.strip(),
                input=model_input,
            )

        except Exception as e:
            return {
                "error": f"Error calling OpenAI / model: {e}"
            }

        raw_content = ""
        try:
            raw_content = response.output_text or ""
        except Exception:
            raw_content = ""

        if not raw_content:
            try:
                raw_content = response.output[0].content[0].text  # type: ignore[attr-defined]
            except Exception:
                raw_content = str(response)

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

    def save_pdf_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pdf_b64 = (payload.get("pdfBase64", "") or "").strip()
        suggested_filename = (payload.get("suggestedFilename", "") or "").strip()

        if not pdf_b64:
            return {"error": "Missing pdfBase64."}

        if not suggested_filename:
            suggested_filename = "examination-report.pdf"
        if not suggested_filename.lower().endswith(".pdf"):
            suggested_filename += ".pdf"

        try:
            pdf_bytes = base64.b64decode(pdf_b64)
        except Exception as e:
            return {"error": f"Failed to decode pdfBase64: {e}"}

        if not webview.windows:
            return {"error": "No active app window available to show a save dialog."}

        window = webview.windows[0]
        try:
            save_path = window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=suggested_filename,
                file_types=("PDF Files (*.pdf)",),
            )
        except Exception as e:
            return {"error": f"Failed to open save dialog: {e}"}

        if not save_path:
            return {"error": "Save cancelled."}

        if isinstance(save_path, (list, tuple)):
            save_path = save_path[0] if save_path else ""

        try:
            with open(save_path, "wb") as f:
                f.write(pdf_bytes)
        except Exception as e:
            return {"error": f"Failed to write PDF: {e}"}

        return {"ok": True, "path": save_path}

    def save_csv_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        csv_b64 = (payload.get("csvBase64", "") or "").strip()
        suggested_filename = (payload.get("suggestedFilename", "") or "").strip()

        if not csv_b64:
            return {"error": "Missing csvBase64."}

        if not suggested_filename:
            suggested_filename = "examination-report.csv"
        if not suggested_filename.lower().endswith(".csv"):
            suggested_filename += ".csv"

        try:
            csv_bytes = base64.b64decode(csv_b64)
        except Exception as e:
            return {"error": f"Failed to decode csvBase64: {e}"}

        if not webview.windows:
            return {"error": "No active app window available to show a save dialog."}

        window = webview.windows[0]
        try:
            save_path = window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=suggested_filename,
                file_types=("CSV Files (*.csv)",),
            )
        except Exception as e:
            return {"error": f"Failed to open save dialog: {e}"}

        if not save_path:
            return {"error": "Save cancelled."}

        if isinstance(save_path, (list, tuple)):
            save_path = save_path[0] if save_path else ""

        try:
            with open(save_path, "wb") as f:
                f.write(csv_bytes)
        except Exception as e:
            return {"error": f"Failed to write CSV: {e}"}

        return {"ok": True, "path": save_path}

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
