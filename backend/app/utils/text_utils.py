# backend/app/utils/text_utils.py

import re


def normalize_whitespace(text: str) -> str:
    """
    Remove excessive spaces, fix line breaks.
    """
    text = re.sub(r"\s+", " ", text)       # collapse whitespace
    return text.strip()


def fix_ocr_artifacts(text: str) -> str:
    """
    Removes common OCR errors such as stray characters.
    """
    replacements = {
        "0": "o",
        "1": "l",
        "|": "l",
        "\u2014": "-",  # em dash
        "\u2013": "-",  # en dash
    }

    for bad, good in replacements.items():
        text = text.replace(bad, good)

    # Remove weird characters
    text = re.sub(r"[^a-zA-Z0-9.,;:?!()\-\'\" ]+", "", text)

    return text


def clean_ocr_text(text: str) -> str:
    """
    Master function for OCR cleanup.
    """
    text = normalize_whitespace(text)
    text = fix_ocr_artifacts(text)
    return text
