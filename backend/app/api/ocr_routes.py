# backend/app/api/ocr_routes.py

from fastapi import APIRouter, UploadFile, File
from typing import List

from app.core.ocr_engine import run_ocr

router = APIRouter()

@router.post("/")
async def ocr_endpoint(files: List[UploadFile] = File(...)):
    """
    Accepts one or multiple images/PDF pages and returns OCR text.
    """
    ocr_results = []

    for f in files:
        content = await f.read()
        text = run_ocr(image_bytes=content)
        ocr_results.append({
            "filename": f.filename,
            "text": text
        })

    return {"pages": ocr_results}
