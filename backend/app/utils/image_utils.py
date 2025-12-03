# backend/app/utils/image_utils.py

from PIL import Image, ImageOps, ImageEnhance
import io
import fitz  # PyMuPDF for PDF -> image conversion
import numpy as np
import cv2


def load_image_from_bytes(data: bytes) -> Image.Image:
    """
    Loads image from raw bytes, detects if PDF or image.
    Returns a PIL Image.
    """
    try:
        # Try open as image
        return Image.open(io.BytesIO(data)).convert("RGB")
    except:
        # Try PDF -> image fallback
        return pdf_page_to_image(data)


def pdf_page_to_image(pdf_bytes: bytes, dpi=200) -> Image.Image:
    """
    Converts the FIRST page of a PDF to a PIL Image.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    pix = page.get_pixmap(dpi=dpi)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img


def deskew_image(pil_img: Image.Image) -> Image.Image:
    """
    Fixes slight rotation/tilt using OpenCV.
    Improves OCR accuracy significantly.
    """
    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
    cv_img = cv2.bitwise_not(cv_img)

    coords = np.column_stack(np.where(cv_img > 0))
    if len(coords) < 10:
        return pil_img  # Not enough info to deskew

    angle = cv2.minAreaRect(coords)[-1]

    # Correct angle
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = cv_img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    deskewed = cv2.warpAffine(cv_img, M, (w, h), flags=cv2.INTER_CUBIC)

    return Image.fromarray(deskewed).convert("RGB")


def enhance_for_ocr(pil_img: Image.Image) -> Image.Image:
    """
    Boosts contrast & sharpness for OCR improvements.
    """
    enhancer = ImageEnhance.Contrast(pil_img)
    pil_img = enhancer.enhance(1.5)

    enhancer = ImageEnhance.Sharpness(pil_img)
    pil_img = enhancer.enhance(2.0)

    return pil_img


def preprocess_image(image_bytes: bytes) -> Image.Image:
    """
    Full pipeline: load → deskew → enhance → return PIL.
    """
    img = load_image_from_bytes(image_bytes)
    img = deskew_image(img)
    img = enhance_for_ocr(img)
    return img
