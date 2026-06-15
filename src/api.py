import logging
import json
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
        "endpoints": {
            "/news": "GET - جميع الأخبار",
            "/news/today": "GET - أخبار اليوم",
            "/news/{id}": "GET - خبر محدد",
            "/news/category/{category}": "GET - أخبار حسب التصنيف",
            "/news/search?q=": "GET - بحث في الأخبار",
            "/stats": "GET - إحصائيات",
            "/api/organized-news": "GET - أخبار عربية منظمة حسب التصنيف (للمواقع)",
        },
    }


@app.get("/news")
def get_news(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    items = db.get_all_news(limit=limit, offset=offset)
    return {"count": len(items), "results": [item.to_dict() for item in items]}


@app.get("/news/today")
def get_today_news():
    items = db.get_today_news()
    return {"count": len(items), "results": [item.to_dict() for item in items], "date": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%d")}


@app.get("/news/{news_id}")
def get_news_by_id(news_id: int):
    item = db.get_news_by_id(news_id)
    if not item:
        raise HTTPException(status_code=404, detail="الخبر غير موجود")
    return item.to_dict()


@app.get("/news/category/{category}")
def get_news_by_category(category: str, limit: int = Query(20, ge=1, le=100)):
    items = db.get_news_by_category(category, limit=limit)
    return {"category": category, "count": len(items), "results": [item.to_dict() for item in items]}


@app.get("/news/search")
def search_news(q: str = Query(..., min_length=2)):
    items = db.search_news(q)
    return {"query": q, "count": len(items), "results": [item.to_dict() for item in items]}


@app.get("/stats")
def get_stats():
    return db.get_stats()


@app.get("/health")
def health():
    return {"status": "ok", "service": "AI News API"}


@app.get("/api/organized-news")
def get_organized_news():
    """يعيد الأخبار العربية منظمة حسب التصنيفات - جاهز لمواقع الويب"""
    data = db.get_organized_arabic_news()
    return data
