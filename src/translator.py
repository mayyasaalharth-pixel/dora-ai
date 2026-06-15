import logging
from typing import List, Optional
from src.models import NewsItem

logger = logging.getLogger(__name__)


class Translator:
    def __init__(self):
        self._engine = None

    def _init_engine(self):
        if self._engine:
            return True
        try:
            from deep_translator import GoogleTranslator
            self._engine = GoogleTranslator(source="en", target="ar")
            return True
        except Exception as e:
            logger.warning(f"Translation engine init failed: {e}")
            return False

    def translate_text(self, text: str) -> str:
        if not text or len(text.strip()) < 5:
            return text
        if not self._init_engine():
            return text
        try:
            result = self._engine.translate(text[:2000])
            return result or text
        except Exception as e:
            logger.warning(f"Translation error: {e}")
            return text

    def translate_news(self, items: List[NewsItem]) -> List[NewsItem]:
        if not self._init_engine():
            logger.warning("Translator not available. Keeping original.")
            return items

        translated = []
        for item in items:
            try:
                item.title = self.translate_text(item.title) or item.title
                item.summary = self.translate_text(item.summary) or item.summary
                item.impactAnalysis = self.translate_text(item.impactAnalysis) or item.impactAnalysis
                item.suggestedPost = self.translate_text(item.suggestedPost) or item.suggestedPost
                translated.append(item)
            except Exception as e:
                logger.warning(f"Translation failed for '{item.title[:30]}': {e}")
                translated.append(item)
        return translated
