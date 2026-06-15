import logging
import re
import time
from typing import List, Optional
from src.models import NewsItem
from src.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]


class AIAssistant:
    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key
        self.client = None
        if api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.warning(f"Gemini init failed: {e}")

    def enhance_news(self, items: List[NewsItem]) -> List[NewsItem]:
        if not self.client:
            logger.warning("Gemini not configured. Skipping AI enhancement.")
            return items

        batch_size = 5
        enhanced = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            try:
                result = self._enhance_batch(batch)
                enhanced.extend(result)
            except Exception as e:
                logger.warning(f"Batch enhancement failed for items {i}-{i+len(batch)-1}: {e}")
                enhanced.extend(batch)
        return enhanced

    def _generate_with_fallback(self, prompt: str) -> Optional[str]:
        last_error = None
        for model in FALLBACK_MODELS:
            max_retries = 3 if model == "gemini-2.5-flash" else 2
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )
                    if response.text:
                        if attempt > 0 or model != FALLBACK_MODELS[0]:
                            logger.info(f"Gemini model used: {model} (attempt {attempt+1})")
                        return response.text
                except Exception as e:
                    err_str = str(e)
                    last_error = e
                    if "503" in err_str or "UNAVAILABLE" in err_str:
                        wait = 2 * (attempt + 1)
                        time.sleep(wait)
                        continue
                    elif "429" in err_str or "quota" in err_str.lower():
                        break
                    else:
                        break
        logger.warning(f"All Gemini models failed. Last error: {last_error}")
        return None

    def _enhance_single(self, item: NewsItem) -> Optional[NewsItem]:
        prompt = f"""أنت مساعد متخصص في تنظيم وتحليل الأخبار التقنية باللغة العربية.

الخبر:
Title: {item.title}
Summary: {item.summary}
Source: {item.sourceName}
Category: {item.category}

المطلوب:
1. صياغة عنوان عربي احترافي للخبر
2. صياغة منشور قصير احترافي للتويتر بالعربية (max 200 حرف، بدون إيموجي)
3. تحليل أثر احترافي بالعربية
4. تصنيف الخبر ضمن: بحث/نموذج جديد/تحديث منصة/تحول صناعي/إطلاق منتج
5. 3-5 كلمات مفتاحية بالعربية

أعد النتيجة:
العنوان: [العنوان العربي]
المنشور: [منشور مقترح]
التحليل: [تحليل الأثر]
التصنيف: [التصنيف]
الكلمات: [كلمة1، كلمة2، كلمة3]"""

        text = self._generate_with_fallback(prompt)
        if not text:
            return None

        title_match = re.search(r"العنوان:\s*(.+?)(?:\n|$)", text)
        if title_match:
            item.title = title_match.group(1).strip()

        post_match = re.search(r"المنشور:\s*(.+?)(?:\nالتحليل:|\nالتصنيف:|\nالكلمات:|$)", text, re.DOTALL)
        if post_match:
            item.suggestedPost = post_match.group(1).strip()

        impact_match = re.search(r"التحليل:\s*(.+?)(?:\nالتصنيف:|\nالكلمات:|$)", text, re.DOTALL)
        if impact_match:
            item.impactAnalysis = impact_match.group(1).strip()

        kw_match = re.search(r"الكلمات:\s*(.+?)$", text)
        if kw_match:
            keywords = [k.strip() for k in kw_match.group(1).split("،")]
            item.keywords = keywords

        return item

    def _enhance_batch(self, items: List[NewsItem]) -> List[NewsItem]:
        prompt_parts = []
        for i, item in enumerate(items):
            prompt_parts.append(f"[الخبر {i+1}]\nالعنوان: {item.title}\nالملخص: {item.summary}\nالمصدر: {item.sourceName}")
        prompt = f"""أنت مساعد متخصص في تنظيم وتحليل الأخبار التقنية.

اقرأ الأخبار التالية ثم أعد لكل خبر بالعربية:
- عنوان احترافي
- منشور تويتر (max 200 حرف، بدون إيموجي)
- تحليل أثر
- تصنيف
- كلمات مفتاحية

الأخبار:
{chr(10).join(prompt_parts)}

أعد النتيجة بهذا الشكل لكل خبر:
=== الخبر 1 ===
العنوان: ...
المنشور: ...
التحليل: ...
التصنيف: ...
الكلمات: ..."""

        text = self._generate_with_fallback(prompt)
        if not text:
            return items

        blocks = re.split(r"=== الخبر \d+ ===", text)
        for i, block in enumerate(blocks):
            if i >= len(items):
                break
            title_m = re.search(r"العنوان:\s*(.+?)(?:\n|$)", block)
            if title_m:
                items[i].title = title_m.group(1).strip()
            post_m = re.search(r"المنشور:\s*(.+?)(?:\nالتحليل:|\nالتصنيف:|\nالكلمات:|$)", block, re.DOTALL)
            if post_m:
                items[i].suggestedPost = post_m.group(1).strip()
            impact_m = re.search(r"التحليل:\s*(.+?)(?:\nالتصنيف:|\nالكلمات:|$)", block, re.DOTALL)
            if impact_m:
                items[i].impactAnalysis = impact_m.group(1).strip()
            kw_m = re.search(r"الكلمات:\s*(.+?)$", block)
            if kw_m:
                items[i].keywords = [k.strip() for k in kw_m.group(1).split("،")]
        return items
