import logging
import re
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from src.config import FLAT_NEWS_SOURCES, TRUSTED_SOURCES, HOURS_BACK

logger = logging.getLogger(__name__)


class WebScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch_from_all_sources(self) -> List[Dict]:
        all_articles = []
        seen_urls = set()

        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self._fetch_rss, url): url for url in FLAT_NEWS_SOURCES}
            for future in as_completed(futures, timeout=110):
                url = futures[future]
                try:
                    articles = future.result()
                    for article in articles:
                        url_lower = article.get("url", article.get("link", "")).lower()
                        if url_lower and url_lower not in seen_urls:
                            seen_urls.add(url_lower)
                            all_articles.append(article)
                except Exception as e:
                    logger.error(f"RSS error {url}: {e}")

        return all_articles

    def _fetch_rss(self, feed_url: str) -> List[Dict]:
        try:
            resp = self.session.get(feed_url, timeout=15)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.content, "xml")
            items = soup.find_all("item")
            parsed = []
            for item in items:
                article = self._parse_rss_item(item)
                if article:
                    parsed.append(article)
            return parsed
        except Exception as e:
            logger.error(f"RSS fetch error {feed_url}: {e}")
            return []

    def _parse_rss_item(self, item) -> Optional[Dict]:
        try:
            title_tag = item.find("title")
            link_tag = item.find("link")
            desc_tag = item.find("description")
            pub_tag = item.find("pubDate") or item.find("dc:date") or item.find("published")

            title = title_tag.get_text(strip=True) if title_tag else ""
            if not title or len(title) < 10:
                return None

            link = ""
            if link_tag:
                link = link_tag.get_text(strip=True) if hasattr(link_tag, "get_text") else str(link_tag)

            desc = ""
            if desc_tag:
                desc = desc_tag.get_text(strip=True)
                desc = re.sub(r"<.*?>", "", desc)
                if len(desc) > 500:
                    desc = desc[:500] + "..."

            pub_date = pub_tag.get_text(strip=True) if pub_tag else ""

            domain = self._extract_domain(link)
            is_trusted = any(src in domain for src in TRUSTED_SOURCES)

            return {
                "title": title,
                "description": desc,
                "snippet": desc[:300] if desc else "",
                "url": link,
                "link": link,
                "source": domain,
                "date": pub_date,
                "isTrusted": is_trusted,
                "imageUrl": self._extract_image(item),
            }
        except Exception as e:
            return None

    def _extract_image(self, item) -> str:
        media = item.find("media:content") or item.find("media:thumbnail")
        if media and media.get("url"):
            return media["url"]
        enclosure = item.find("enclosure")
        if enclosure and "image" in enclosure.get("type", ""):
            return enclosure.get("url", "")
        content = item.find("content:encoded") or item.find("description")
        if content:
            match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', str(content))
            if match:
                return match.group(1)
        return ""

    def _extract_domain(self, url: str) -> str:
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.replace("www.", "")
        except Exception:
            return url

    @staticmethod
    def is_recent(date_str: str, hours: int = HOURS_BACK) -> bool:
        if not date_str:
            return False
        from dateutil import parser as dateparser
        try:
            dt = dateparser.parse(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            return dt > cutoff
        except Exception:
            return True
