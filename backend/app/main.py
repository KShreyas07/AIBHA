from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, get_logger

import app.models  # noqa: F401 - registers every model on Base.metadata before routes load

from app.api.v1 import auth, company, upload, analyze, predict, forecast, dashboard, recommendations, report, chat

setup_logging()
logger = get_logger(__name__)

Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.REPORTS_DIR).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("%s starting up in %s mode", settings.APP_NAME, settings.ENVIRONMENT)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI-powered Business Health Analyzer for SMEs — financial analysis, forecasting, "
    "risk detection, health scoring, and AI recommendations.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(company.router, prefix="/api/company", tags=["Company"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["Analyze"])
app.include_router(predict.router, prefix="/api/predict", tags=["Predict"])
app.include_router(forecast.router, prefix="/api/forecast", tags=["Forecast"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(report.router, prefix="/api/report", tags=["Report"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat Assistant"])


@app.get("/api/health", tags=["System"])
def health_check() -> dict:
    return {"status": "ok", "app": settings.APP_NAME}
