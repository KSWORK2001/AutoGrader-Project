# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.model_loader import load_all_models
from app.api.ocr_routes import router as ocr_router
from app.api.grade_routes import router as grade_router


def create_app() -> FastAPI:
    """
    Creates the FastAPI application and loads models at startup.
    """
    app = FastAPI(
        title="Exam Grading Backend",
        description="OCR + Reasoning Engine for Automated Exam Grading",
        version="1.0.0",
    )

    # ---------------------------
    # CORS (important for Tauri)
    # ---------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],         # for local demo
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---------------------------
    # Router Registration
    # ---------------------------
    app.include_router(ocr_router, prefix="/ocr", tags=["OCR"])
    app.include_router(grade_router, prefix="/grade", tags=["Grading"])

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    # ---------------------------
    # Startup Event: Load models
    # ---------------------------
    @app.on_event("startup")
    async def startup_event():
        print("🔥 Starting backend... loading models into memory...")
        load_all_models()  # DeepSeek OCR + Qwen3 reasoning
        print("🚀 Models loaded successfully!")

    return app


# Entry point for Uvicorn
app = create_app()
