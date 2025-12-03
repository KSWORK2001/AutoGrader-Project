# backend/app/core/ocr_engine.py

from PIL import Image
import io
from app.core.model_loader import OCR_PIPELINE


def run_ocr(image_bytes: bytes) -> str:
    """
    Runs DeepSeek OCR on a single image (JPEG/PNG/PDF-page).
    """
    if OCR_PIPELINE is None:
        raise RuntimeError("OCR model is not loaded!")

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    result = OCR_PIPELINE(image)

    if isinstance(result, list) and len(result) > 0:
        return result[0].get("generated_text", "").strip()

    return ""
