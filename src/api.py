import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database import Database

logger = logging.getLogger(__name__)

db = Database()
app = FastAPI(
    title="AI News API",
    description="واجهة برمجية لجلب أخبار الذكاء الاصطناعي والتقنيات الرقمية",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "AI News API",
        "version": "1.0.0",
        "description": "نظام تجميع أخبار الذكاء الاصطناعي",
        "endpoints": {
            "/api/organized-news": "GET - [للمواقع] 40 خبر عربي منظم حسب التصنيفات",
        },
    }


@app.get("/api/organized-news")
def get_organized_news():
    """يعيد الأخبار العربية منظمة حسب التصنيفات - جاهز لمواقع الويب"""
    data = db.get_organized_arabic_news()
    return data


@app.get("/health")
def health():
    return {"status": "ok", "service": "AI News API"}
