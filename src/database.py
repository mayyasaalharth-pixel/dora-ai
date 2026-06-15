import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import List, Optional
from src.config import DB_PATH
from src.models import NewsItem

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT UNIQUE NOT NULL,
                    summary TEXT,
                    category TEXT,
                    importanceScore INTEGER DEFAULT 0,
                    publishedAt TEXT,
                    sourceName TEXT,
                    sourceUrl TEXT,
                    secondarySourceUrl TEXT DEFAULT '',
                    imageUrl TEXT DEFAULT '',
                    keywords TEXT DEFAULT '[]',
                    tags TEXT DEFAULT '[]',
                    suggestedPost TEXT DEFAULT '',
                    impactAnalysis TEXT DEFAULT '',
                    collectedAt TEXT NOT NULL,
                    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_category ON news(category)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_published ON news(publishedAt)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_score ON news(importanceScore)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS arabic_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    summary TEXT,
                    category TEXT,
                    importanceScore INTEGER DEFAULT 0,
                    publishedAt TEXT,
                    sourceName TEXT,
                    sourceUrl TEXT,
                    imageUrl TEXT DEFAULT '',
                    suggestedPost TEXT DEFAULT '',
                    impactAnalysis TEXT DEFAULT '',
                    collectedAt TEXT NOT NULL,
                    section_order INTEGER DEFAULT 0,
                    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_arabic_category ON arabic_news(category)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_arabic_collected ON arabic_news(collectedAt)
            """)
 
    def _connect(self):
        return sqlite3.connect(self.db_path)

    def insert_news(self, item: NewsItem) -> bool:
        with self._connect() as conn:
            try:
                cur = conn.execute("""
                    INSERT OR IGNORE INTO news
                    (title, summary, category, importanceScore, publishedAt,
                     sourceName, sourceUrl, secondarySourceUrl, imageUrl,
                     keywords, tags, suggestedPost, impactAnalysis, collectedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.title, item.summary, item.category, item.importanceScore,
                    item.publishedAt, item.sourceName, item.sourceUrl,
                    item.secondarySourceUrl, item.imageUrl,
                    json.dumps(item.keywords, ensure_ascii=False),
                    json.dumps(item.tags, ensure_ascii=False),
                    item.suggestedPost, item.impactAnalysis, item.collectedAt
                ))
                return cur.rowcount > 0
            except Exception as e:
                logger.error(f"Error inserting news: {e}")
                return False

    def insert_many(self, items: List[NewsItem]) -> int:
        count = 0
        for item in items:
            if self.insert_news(item):
                count += 1
        return count

    def get_all_news(self, limit: int = 50, offset: int = 0) -> List[NewsItem]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM news ORDER BY importanceScore DESC, publishedAt DESC
                LIMIT ? OFFSET ?
            """, (limit, offset)).fetchall()
            return [self._row_to_item(row) for row in rows]

    def get_news_by_category(self, category: str, limit: int = 20) -> List[NewsItem]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM news WHERE category = ?
                ORDER BY importanceScore DESC, publishedAt DESC LIMIT ?
            """, (category, limit)).fetchall()
            return [self._row_to_item(row) for row in rows]

    def get_today_news(self) -> List[NewsItem]:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM news WHERE collectedAt LIKE ? ORDER BY importanceScore DESC
            """, (f"{today}%",)).fetchall()
            return [self._row_to_item(row) for row in rows]

    def get_news_by_id(self, news_id: int) -> Optional[NewsItem]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM news WHERE id = ?", (news_id,)).fetchone()
            return self._row_to_item(row) if row else None

    def search_news(self, query: str, limit: int = 20) -> List[NewsItem]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM news WHERE title LIKE ? OR summary LIKE ? OR keywords LIKE ?
                ORDER BY importanceScore DESC LIMIT ?
            """, (f"%{query}%", f"%{query}%", f"%{query}%", limit)).fetchall()
            return [self._row_to_item(row) for row in rows]

    def _row_to_item(self, row) -> NewsItem:
        return NewsItem(
            id=row["id"],
            title=row["title"],
            summary=row["summary"],
            category=row["category"],
            importanceScore=row["importanceScore"],
            publishedAt=row["publishedAt"],
            sourceName=row["sourceName"],
            sourceUrl=row["sourceUrl"],
            secondarySourceUrl=row["secondarySourceUrl"] or "",
            imageUrl=row["imageUrl"] or "",
            keywords=json.loads(row["keywords"]) if row["keywords"] else [],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            suggestedPost=row["suggestedPost"] or "",
            impactAnalysis=row["impactAnalysis"] or "",
            collectedAt=row["collectedAt"],
        )

    def get_stats(self) -> dict:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM news").fetchone()[0]
            today = conn.execute(
                "SELECT COUNT(*) FROM news WHERE collectedAt LIKE ?",
                (f"{datetime.utcnow().strftime('%Y-%m-%d')}%",)
            ).fetchone()[0]
            categories = conn.execute(
                "SELECT category, COUNT(*) as cnt FROM news GROUP BY category ORDER BY cnt DESC"
            ).fetchall()
            return {
                "total": total,
                "today": today,
                "categories": {c[0]: c[1] for c in categories},
            }

    def save_arabic_news(self, items: List[NewsItem]) -> int:
        """يحفظ الأخبار العربية المترجمة في جدول منفصل"""
        with self._connect() as conn:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            conn.execute("DELETE FROM arabic_news WHERE collectedAt LIKE ?", (f"{today}%",))
            count = 0
            for i, item in enumerate(items):
                try:
                    conn.execute("""
                        INSERT INTO arabic_news
                        (title, summary, category, importanceScore, publishedAt,
                         sourceName, sourceUrl, imageUrl,
                         suggestedPost, impactAnalysis, collectedAt, section_order)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item.title, item.summary, item.category, item.importanceScore,
                        item.publishedAt, item.sourceName, item.sourceUrl,
                        item.imageUrl, item.suggestedPost, item.impactAnalysis,
                        item.collectedAt, i
                    ))
                    count += 1
                except Exception:
                    continue
            return count

    def get_organized_arabic_news(self) -> dict:
        """يعيد الأخبار العربية منظمة حسب التصنيفات"""
        from src.config import CATEGORIES
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM arabic_news
                ORDER BY section_order ASC
            """).fetchall()
            grouped = {}
            for row in rows:
                cat = row["category"]
                grouped.setdefault(cat, []).append({
                    "id": row["id"],
                    "title": row["title"],
                    "summary": row["summary"],
                    "category": cat,
                    "importanceScore": row["importanceScore"],
                    "publishedAt": row["publishedAt"],
                    "sourceName": row["sourceName"],
                    "sourceUrl": row["sourceUrl"],
                    "imageUrl": row["imageUrl"] or "",
                    "suggestedPost": row["suggestedPost"] or "",
                    "impactAnalysis": row["impactAnalysis"] or "",
                })
            ordered = {}
            for cat in CATEGORIES:
                if cat in grouped:
                    ordered[cat] = grouped.pop(cat)
            ordered.update(grouped)
            return {
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "categories": ordered,
                "total": len(rows),
            }
