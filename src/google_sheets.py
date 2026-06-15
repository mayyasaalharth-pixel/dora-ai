import logging
import json
import os
from typing import List, Optional
from src.models import NewsItem
from src.config import GOOGLE_SHEETS_CREDENTIALS, GOOGLE_SHEET_ID, GOOGLE_SHEET_ID_ARABIC, CATEGORIES, MAX_RAW_SHEET_ITEMS

logger = logging.getLogger(__name__)


class GoogleSheetsWriter:
    def __init__(self, credentials_json: Optional[str] = None, sheet_id: Optional[str] = None,
                 sheet_id_arabic: Optional[str] = None):
        self.credentials_json = credentials_json or GOOGLE_SHEETS_CREDENTIALS
        self.sheet_id = sheet_id or GOOGLE_SHEET_ID
        self.sheet_id_arabic = sheet_id_arabic or GOOGLE_SHEET_ID_ARABIC
        self.client = None

    def _init_client(self):
        if self.client:
            return True
        if not self.credentials_json:
            logger.warning("Google Sheets credentials not configured")
            return False
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            if os.path.isfile(self.credentials_json):
                creds = Credentials.from_service_account_file(
                    self.credentials_json,
                    scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                )
            else:
                creds = Credentials.from_service_account_info(
                    json.loads(self.credentials_json),
                    scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                )
            self.client = gspread.authorize(creds)
            return True
        except ImportError:
            logger.error("gspread not installed. Install with: pip install gspread google-auth")
            return False
        except Exception as e:
            logger.error(f"Error initializing Google Sheets: {e}")
            return False

    def write_raw_news(self, items: List[NewsItem]) -> bool:
        """يكتب كل الأخبار الخام (بعد التصفية وقبل التنويع) إلى الشيت الإنجليزي"""
        if not self._init_client():
            return False
        try:
            sheet = self.client.open_by_key(self.sheet_id)
            worksheet = sheet.sheet1

            worksheet.clear()

            headers = [
                "#", "Title", "Summary", "Category", "Score", "Source Type",
                "SourceName", "SourceUrl", "PublishedAt", "Keywords"
            ]
            worksheet.update("A1", [headers])

            rows = []
            for i, item in enumerate(items[:MAX_RAW_SHEET_ITEMS], 1):
                rows.append([
                    i,
                    item.title,
                    item.summary[:200],
                    item.category,
                    item.importanceScore,
                    item.sourceName,
                    item.sourceUrl,
                    item.publishedAt,
                    ", ".join(item.keywords[:5]),
                ])
            if rows:
                worksheet.update(f"A2", rows)
            logger.info(f"English sheet: {len(rows)} raw items written")
            return True
        except Exception as e:
            logger.error(f"Error writing raw to English sheet: {e}")
            return False

    def write_arabic_news(self, items: List[NewsItem]) -> bool:
        """يكتب أفضل 40 خبر مرتبة بتصنيفاتها إلى الشيت العربي"""
        if not self.sheet_id_arabic:
            logger.warning("Arabic sheet ID not configured. Skipping.")
            return False
        if not self._init_client():
            return False
        try:
            sheet = self.client.open_by_key(self.sheet_id_arabic)
            worksheet = sheet.sheet1

            worksheet.clear()
            grouped = {}
            for item in items:
                grouped.setdefault(item.category, []).append(item)

            all_rows = []

            for cat in CATEGORIES:
                cat_items = grouped.pop(cat, [])
                if not cat_items:
                    continue
                all_rows.append([f"■ {cat}"])
                all_rows.append([
                    "العنوان", "الملخص", "درجة الأهمية", "تاريخ النشر",
                    "المصدر", "الرابط", "صورة", "منشور مقترح", "تحليل الأثر"
                ])
                for item in cat_items:
                    all_rows.append([
                        item.title, item.summary, item.importanceScore,
                        item.publishedAt, item.sourceName, item.sourceUrl,
                        item.imageUrl, item.suggestedPost, item.impactAnalysis,
                    ])
                all_rows.append([])

            for cat, cat_items in grouped.items():
                all_rows.append([f"■ {cat}"])
                all_rows.append([
                    "العنوان", "الملخص", "درجة الأهمية", "تاريخ النشر",
                    "المصدر", "الرابط", "صورة", "منشور مقترح", "تحليل الأثر"
                ])
                for item in cat_items:
                    all_rows.append([
                        item.title, item.summary, item.importanceScore,
                        item.publishedAt, item.sourceName, item.sourceUrl,
                        item.imageUrl, item.suggestedPost, item.impactAnalysis,
                    ])
                all_rows.append([])

            if all_rows:
                worksheet.update("A1", all_rows)

            logger.info(f"Arabic sheet: {len(items)} items organized by {len(grouped) + sum(1 for c in CATEGORIES if c in {i.category for i in items})} categories")
            return True
        except Exception as e:
            logger.error(f"Error writing to Arabic sheet: {e}")
            return False
