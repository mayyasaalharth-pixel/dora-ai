import logging
import asyncio
from datetime import datetime, time, timedelta
from typing import Optional
from src.config import SCHEDULE_TIME
from src.database import Database
from src.news_processor import NewsProcessor
from src.youtube_scraper import YouTubeScraper
from src.web_scraper import WebScraper
from src.tools_scraper import ToolsScraper
from src.community_scraper import CommunityScraper
from src.reddit_scraper import RedditScraper
from src.trends_scraper import TrendsScraper
from src.google_sheets import GoogleSheetsWriter
from src.translator import Translator
from src.ai_assistant import AIAssistant

logger = logging.getLogger(__name__)


class DailyScheduler:
    def __init__(self):
        self.db = Database()
        self.processor = NewsProcessor()
        self.youtube_scraper = YouTubeScraper()
        self.web_scraper = WebScraper()
        self.tools_scraper = ToolsScraper()
        self.community_scraper = CommunityScraper()
        self.reddit_scraper = RedditScraper()
        self.trends_scraper = TrendsScraper()
        self.sheets_writer = GoogleSheetsWriter()
        self.translator = Translator()
        self.ai_assistant = AIAssistant()
        self._running = False

    async def _scrape_with_timeout(self, scraper_func, name: str, timeout: int):
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(scraper_func), timeout=timeout
            )
            logger.info(f"{name}: {len(result)} عنصر")
            return result
        except asyncio.TimeoutError:
            logger.warning(f"{name}: انتهت المهلة")
            return []
        except Exception as e:
            logger.error(f"{name}: خطأ - {e}")
            return []

    async def run_daily_pipeline(self):
        logger.info("=" * 60)
        logger.info("بدء دورة جلب الأخبار اليومية")
        logger.info("=" * 60)

        youtube_items = await self._scrape_with_timeout(
            self.youtube_scraper.fetch_videos_from_all, "يوتيوب", 120
        )
        web_items = await self._scrape_with_timeout(
            self.web_scraper.fetch_from_all_sources, "الويب", 120
        )
        tools_items = await self._scrape_with_timeout(
            self.tools_scraper.fetch_latest_tools, "theneuron.ai", 30
        )
        community_items = await self._scrape_with_timeout(
            self.community_scraper.fetch_all, "مجتمعات", 60
        )
        reddit_items = await self._scrape_with_timeout(
            self.reddit_scraper.fetch_all, "Reddit", 60
        )
        trends_items = await self._scrape_with_timeout(
            self.trends_scraper.fetch_all, "Google Trends", 60
        )

        total = len(youtube_items) + len(web_items) + len(tools_items) + len(community_items) + len(reddit_items) + len(trends_items)
        if total == 0:
            logger.warning("لم يتم العثور على أي أخبار من أي مصدر")
            return

        # معالجة وتصفية - الآن تعيد (كل_الأخبار, أفضل_الأخبار)
        all_news_items: List[NewsItem] = []
        selected_items: List[NewsItem] = []
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self.processor.process_all, youtube_items, web_items, tools_items, community_items, reddit_items, trends_items
                ),
                timeout=120,
            )
            all_news_items, selected_items = result
        except asyncio.TimeoutError:
            logger.warning("انتهت مهلة معالجة الأخبار - استمرار مع أي نتائج متوفرة")
        except Exception as e:
            logger.error(f"خطأ في معالجة الأخبار: {e}")

        if not selected_items:
            logger.warning("لا توجد أخبار للمتابعة")
            return

        logger.info(f"كل الأخبار الخام: {len(all_news_items)} - المختارة: {len(selected_items)}")

        # حفظ المختارة فقط في قاعدة البيانات
        saved = await asyncio.to_thread(self.db.insert_many, selected_items)
        logger.info(f"تم حفظ {saved} خبر جديد في قاعدة البيانات")

        # الشيت الإنجليزي = كل الأخبار الخام (مخزن بيانات)
        try:
            sheets_success = await asyncio.to_thread(
                self.sheets_writer.write_raw_news, all_news_items
            )
            if sheets_success:
                logger.info(f"تم إرسال كل الأخبار الخام ({len(all_news_items)}) إلى الشيت الإنجليزي")
            else:
                logger.warning("لم يتم الإرسال إلى الشيت الإنجليزي")
        except Exception as e:
            logger.warning(f"فشل كتابة الشيت الإنجليزي: {e}")

        # ترجمة
        arabic_items = selected_items
        try:
            logger.info("جاري ترجمة الأخبار إلى العربية...")
            arabic_items = await asyncio.to_thread(
                self.translator.translate_news, selected_items
            )
            logger.info(f"تمت ترجمة {len(arabic_items)} خبر")
        except Exception as e:
            logger.warning(f"فشلت الترجمة: {e}")

        # تحسين بالعربية باستخدام Gemini
        try:
            logger.info("جاري تحسين الصياغة باستخدام Gemini...")
            arabic_items = await asyncio.to_thread(
                self.ai_assistant.enhance_news, arabic_items
            )
            logger.info(f"تم تحسين {len(arabic_items)} خبر")
        except Exception as e:
            logger.warning(f"فشل تحسين Gemini: {e}")

        # حفظ العربية في قاعدة البيانات
        try:
            arabic_saved = await asyncio.to_thread(
                self.db.save_arabic_news, arabic_items
            )
            logger.info(f"تم حفظ {arabic_saved} خبر عربي في قاعدة البيانات")
        except Exception as e:
            logger.warning(f"فشل حفظ العربية في قاعدة البيانات: {e}")

        # شيت عربي = أفضل 40 مرتبة بتصنيفات
        try:
            arabic_sheets_success = await asyncio.to_thread(
                self.sheets_writer.write_arabic_news, arabic_items
            )
            if arabic_sheets_success:
                logger.info(f"تم إرسال {len(arabic_items)} خبر مترجم إلى الشيت العربي")
            else:
                logger.warning("لم يتم الإرسال إلى الشيت العربي")
        except Exception as e:
            logger.warning(f"فشل كتابة الشيت العربي: {e}")

        logger.info("=" * 60)
        logger.info("اكتملت دورة جلب الأخبار اليومية بنجاح")
        logger.info(f"إجمالي الأخبار المحفوظة: {saved}")
        logger.info("=" * 60)

    async def run_continuously(self):
        self._running = True
        logger.info(f"المجدول اليومي يعمل - موعد الإرسال: {SCHEDULE_TIME}")

        while self._running:
            try:
                now = datetime.now()
                hour, minute = map(int, SCHEDULE_TIME.split(":"))
                target = time(hour=hour, minute=minute, second=0)
                target_dt = datetime.combine(now.date(), target)

                if now >= target_dt:
                    target_dt += timedelta(days=1)

                wait_seconds = (target_dt - now).total_seconds()
                logger.info(
                    f"الوقت المتبقي للإرسال التالي: {int(wait_seconds / 3600)} ساعة و {int((wait_seconds % 3600) / 60)} دقيقة"
                )

                await asyncio.sleep(wait_seconds)
                await self.run_daily_pipeline()

            except asyncio.CancelledError:
                logger.info("تم إيقاف المجدول")
                break
            except Exception as e:
                logger.error(f"خطأ في المجدول: {e}")
                await asyncio.sleep(60)

    def stop(self):
        self._running = False
