import logging
import requests
from datetime import datetime, timezone
from typing import List, Dict
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class TrendsScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def fetch_all(self) -> List[Dict]:
        items = []
        items.extend(self._fetch_trends_rss())
        items.extend(self._fetch_google_news_trends())
        logger.info(f"Google Trends: {len(items)} items")
        return items

    def _fetch_trends_rss(self) -> List[Dict]:
        try:
            url = "https://trends.google.com/trending/rss?geo=US"
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.content, "xml")
            feed_items = soup.find_all("item")
            results = []
            for item in feed_items[:15]:
                title = item.find("title")
                ht = item.find("ht:approx_traffic")
                desc = item.find("description")
                link = item.find("link")
                t = title.get_text(strip=True) if title else ""
                if not t:
                    continue
                traffic = ht.get_text(strip=True) if ht else ""
                d = desc.get_text(strip=True) if desc else ""
                l = link.get_text(strip=True) if link else ""
                results.append({
                    "title": t,
                    "description": f"{traffic} searches - {d}" if traffic else d,
                    "url": l or f"https://www.google.com/search?q={t.replace(' ', '+')}",
                    "source": "Google Trends",
                    "date": datetime.now(timezone.utc).isoformat(),
                    "isTrusted": True,
                    "imageUrl": "",
                    "thumbnail": "",
                })
            logger.info(f"Google Trends RSS: {len(results)} items")
            return results
        except Exception as e:
            logger.warning(f"Google Trends RSS failed: {e}")
            return []

    def _fetch_google_news_trends(self) -> List[Dict]:
        try:
            url = "https://news.google.com/rss/search?q=trending+now+2026&hl=en-US&gl=US&ceid=US:en"
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.content, "xml")
            feed_items = soup.find_all("item")
            results = []
            seen = set()
            for item in feed_items[:10]:
                title = item.find("title")
                link = item.find("link")
                t = title.get_text(strip=True) if title else ""
                if not t or t.lower() in seen:
                    continue
                seen.add(t.lower())
                l = link.get_text(strip=True) if link else ""
                results.append({
                    "title": t,
                    "description": f"Google News Trending: {t}",
                    "url": l,
                    "source": "Google News Trends",
                    "date": datetime.now(timezone.utc).isoformat(),
                    "isTrusted": True,
                    "imageUrl": "",
                    "thumbnail": "",
                })
            logger.info(f"Google News Trends: {len(results)} items")
            return results
        except Exception as e:
            logger.warning(f"Google News Trends failed: {e}")
            return []
