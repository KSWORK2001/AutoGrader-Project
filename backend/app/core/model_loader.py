# backend/app/core/model_loader.py

import torch
from transformers import AutoProcessor, AutoModelForVision2Seq

QWEN_PROCESSOR = None
QWEN_MODEL = None


def load_qwen3vl_model():
    global QWEN_PROCESSOR, QWEN_MODEL

    print("🔍 Loading Qwen3-VL-8B-Instruct...")

    model_name = "Qwen/Qwen3-VL-8B-Instruct"

    QWEN_PROCESSOR = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)

    QWEN_MODEL = AutoModelForVision2Seq.from_pretrained(
        model_name,
        trust_remote_code=True,
        device_map="auto",
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )

    print("✅ Qwen3-VL-8B-Instruct loaded.")


def load_all_models():
    load_qwen3vl_model()
