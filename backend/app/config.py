# backend/app/config.py

import torch

class Settings:
    """
    Global settings for model paths, device selection, and app behavior.
    """

    # Model names from HuggingFace Hub
    OCR_MODEL_NAME: str = "deepseek-ai/DeepSeek-OCR"
    QWEN_MODEL_NAME: str = "Qwen/Qwen3-8B"

    # Device setup
    DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"

    # Max tokens for Qwen outputs
    MAX_NEW_TOKENS: int = 256

    # Temperature for Qwen generation
    TEMPERATURE: float = 0.3

    # Verbose logging
    VERBOSE: bool = True


settings = Settings()
