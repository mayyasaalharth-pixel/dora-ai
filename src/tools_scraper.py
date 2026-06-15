import logging
import re
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ToolsScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.source_url = "https://www.theneuron.ai/top-tools/"

    def fetch_latest_tools(self) -> List[Dict]:
        try:
            resp = requests.get(self.source_url, headers=self.headers, timeout=20)
            if resp.status_code != 200:
                logger.warning(f"theneuron.ai returned {resp.status_code}")
                return self._fallback_tools()
            tools = self._parse_page(resp.text)
            return tools[:20] if tools else self._fallback_tools()
        except Exception as e:
            logger.error(f"Error fetching theneuron.ai: {e}")
            return self._fallback_tools()

    def _parse_page(self, html: str) -> List[Dict]:
        soup = BeautifulSoup(html, "html.parser")
        tools = []
        seen_titles = set()

        sections = soup.find_all("section")
        if not sections:
            sections = soup.find_all("div", class_=re.compile(r"(section|block|container)", re.I))

        for section in sections:
            section_text = section.get_text(strip=True)
            if len(section_text) < 200:
                continue

            headings = section.find_all(["h1", "h2", "h3", "h4", "strong", "b"])
            for heading in headings:
                title = heading.get_text(strip=True)
                if not title or len(title) < 3 or len(title) > 120:
                    continue
                if title in seen_titles:
                    continue

                parent = heading.find_parent(["div", "article", "section"])
                if not parent:
                    parent = heading.parent

                paragraphs = parent.find_all("p")
                description = ""
                for p in paragraphs:
                    p_text = p.get_text(strip=True)
                    if len(p_text) > 30 and len(p_text) < 800:
                        description = p_text
                        break

                if not description:
                    all_text = parent.get_text(strip=True)
                    after = all_text[all_text.find(title) + len(title):].strip()
                    if after and len(after) > 30:
                        description = after[:600]

                link = ""
                link_el = parent.find("a", href=True)
                if link_el:
                    link = link_el["href"]
                    if link.startswith("/"):
                        link = "https://www.theneuron.ai" + link

                seen_titles.add(title)

                tool = {
                    "title": title,
                    "description": description[:600],
                    "url": link,
                    "source": "theneuron.ai",
                    "sourceName": "The Neuron",
                    "date": datetime.now(timezone.utc).isoformat(),
                    "imageUrl": self._get_category_image(title),
                    "category": self._detect_category(title, description),
                }
                tools.append(tool)

        return tools

    def _get_category_image(self, title: str) -> str:
        t = title.lower()
        if any(w in t for w in ["elevenlabs", "audio"]):
            return "https://images.unsplash.com/photo-1611339555312-e607c8352fd7?w=400"
        if any(w in t for w in ["descript", "video", "runway", "heygen", "luma"]):
            return "https://images.unsplash.com/photo-1536240478700-b869070f9279?w=400"
        if any(w in t for w in ["cursor", "github", "bolt", "v0", "code", "windsurf", "lovable"]):
            return "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=400"
        if any(w in t for w in ["chatgpt", "openai", "claude", "gemini", "grok", "copilot"]):
            return "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400"
        if any(w in t for w in ["midjourney", "firefly", "imagen", "stable", "image"]):
            return "https://images.unsplash.com/photo-1547954575-855750c57bd3?w=400"
        if any(w in t for w in ["notion", "clickup", "zapier", "fathom", "productivity"]):
            return "https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=400"
        if any(w in t for w in ["notebooklm", "perplexity", "consensus", "search"]):
            return "https://images.unsplash.com/photo-1488190211105-8b0e65b80b4e?w=400"
        if any(w in t for w in ["suno", "udio", "music"]):
            return "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=400"
        return "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400"

    def _detect_category(self, title: str, description: str) -> str:
        text = f"{title} {description}".lower()
        if any(w in text for w in ["ai", "chatbot", "llm", "model", "intelligence", "machine learning"]):
            return "الذكاء الاصطناعي"
        if any(w in text for w in ["social media", "content", "video", "audio", "podcast", "creator"]):
            return "صناعة المحتوى"
        if any(w in text for w in ["writing", "story", "fiction", "script", "narrative"]):
            return "كتابة القصص"
        if any(w in text for w in ["code", "developer", "software", "engineering", "api"]):
            return "الذكاء الاصطناعي"
        if any(w in text for w in ["productivity", "meeting", "automation", "workflow"]):
            return "آخر التحديات الرقمية"
        return "الذكاء الاصطناعي"

    def _fallback_tools(self) -> List[Dict]:
        return [
            {
                "title": "OpenAI Operator - وكيل ذكاء اصطناعي لأتمتة المهام",
                "description": "OpenAI Operator يمثل قفزة نحو الحوسبة بدون استخدام اليدين، حيث يقوم بأتمتة التفاعلات الكاملة على الويب. يعمل بشكل رائع للمهام المتكررة والمنظمة.",
                "url": "https://theneuron.ai/top-tools/openai-operator",
                "source": "theneuron.ai",
                "sourceName": "The Neuron",
                "date": datetime.now(timezone.utc).isoformat(),
                "imageUrl": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400",
                "category": "الذكاء الاصطناعي",
            },
            {
                "title": "Project Astra - وكيل جوجل ديب مايند متعدد الوسائط",
                "description": "Project Astra يمثل رؤية Google DeepMind الكاملة لعامل حوسبة، يمزج الإدراك والاستدلال والعمل عبر خدمات جوجل.",
                "url": "https://theneuron.ai/top-tools/project-astra",
                "source": "theneuron.ai",
                "sourceName": "The Neuron",
                "date": datetime.now(timezone.utc).isoformat(),
                "imageUrl": "https://images.unsplash.com/photo-1573804633927-bfcbcd909acd?w=400",
                "category": "الذكاء الاصطناعي",
            },
            {
                "title": "Claude (Anthropic) - أفضل كاتب ومبرمج",
                "description": "أفضل روبوت محادثة للكتابة والبرمجة. كلاود من أنثروبيك يتميز بقدرات كتابة إبداعية وبرمجة متقدمة.",
                "url": "https://theneuron.ai/top-tools/claude",
                "source": "theneuron.ai",
                "sourceName": "The Neuron",
                "date": datetime.now(timezone.utc).isoformat(),
                "imageUrl": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400",
                "category": "الذكاء الاصطناعي",
            },
        ]
