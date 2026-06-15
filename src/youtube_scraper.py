import logging
import re
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from bs4 import BeautifulSoup
from src.config import YOUTUBE_API_KEYS, YOUTUBE_CHANNELS

logger = logging.getLogger(__name__)


class YouTubeScraper:
    def __init__(self, api_keys: list = None):
        self.api_keys = api_keys or YOUTUBE_API_KEYS
        self.current_key_index = 0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def fetch_videos_from_all(self) -> List[Dict]:
        all_videos = []
        seen_titles = set()

        trending = self._fetch_trending()
        for v in trending:
            t = v.get("title", "").lower()
            if t and t not in seen_titles:
                seen_titles.add(t)
                all_videos.append(v)

        for handle in YOUTUBE_CHANNELS:
            for attempt in range(len(self.api_keys) + 1):
                try:
                    videos = self._fetch_channel_videos(handle)
                    if isinstance(videos, str) and videos == "QUOTA_EXCEEDED":
                        next_key = self._switch_api_key()
                        if next_key:
                            logger.info(f"مفتاح YouTube انتهت حصته، التبديل للمفتاح التالي")
                            continue
                        else:
                            logger.warning("جميع مفاتيح YouTube انتهت حصتها")
                            break
                    for v in videos:
                        title_lower = v.get("title", "").lower()
                        if title_lower and title_lower not in seen_titles:
                            seen_titles.add(title_lower)
                            all_videos.append(v)
                        desc = v.get("description", "")
                        if desc and len(desc) > 200:
                            parsed = self.parse_description_items(desc, handle)
                            for p in parsed:
                                pt = p.get("title", "").lower()
                                if pt and pt not in seen_titles:
                                    seen_titles.add(pt)
                                    all_videos.append(p)
                    break
                except Exception as e:
                    logger.error(f"YouTube channel error for {handle}: {e}")
                    break

        logger.info(f"YouTube: total {len(all_videos)} videos from {len(YOUTUBE_CHANNELS)} channels")
        return all_videos

    def _switch_api_key(self) -> bool:
        if not self.api_keys:
            return False
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return self.current_key_index != 0

    def _get_current_key(self) -> str:
        if not self.api_keys:
            return ""
        return self.api_keys[self.current_key_index]

    def _fetch_channel_videos(self, handle: str) -> List[Dict]:
        key = self._get_current_key()
        if key:
            return self._fetch_via_api(handle, key)
        return self._fetch_via_scrape(handle)

    def _fetch_via_api(self, handle: str, api_key: str):
        clean_handle = handle.lstrip("@")
        search_url = (
            "https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&q={clean_handle}&type=channel&key={api_key}"
        )
        resp = requests.get(search_url, timeout=10)
        if resp.status_code == 429:
            return "QUOTA_EXCEEDED"
        if resp.status_code != 200:
            return []
        data = resp.json()
        if not data.get("items"):
            return []
        channel_id = data["items"][0]["snippet"]["channelId"]

        uploads_url = (
            "https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&channelId={channel_id}"
            f"&order=date&maxResults=10&key={api_key}"
        )
        resp2 = requests.get(uploads_url, timeout=10)
        if resp2.status_code != 200:
            return []
        videos_data = resp2.json()

        results = []
        for item in videos_data.get("items", []):
            if item["id"]["kind"] != "youtube#video":
                continue
            snippet = item["snippet"]
            video_id = item["id"]["videoId"]
            results.append({
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "url": f"https://youtube.com/watch?v={video_id}",
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                "publishedAt": snippet.get("publishedAt", ""),
                "channelTitle": snippet.get("channelTitle", ""),
                "channelHandle": handle,
                "source": "YouTube",
            })
        return self._filter_recent(results)

    def _fetch_via_scrape(self, handle: str) -> List[Dict]:
        url = f"https://www.youtube.com/{handle}/videos"
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.text, "html.parser")
            scripts = soup.find_all("script")
            video_data = []

            for script in scripts:
                if "var ytInitialData" in script.text:
                    match = re.search(r"var ytInitialData\s*=\s*({.*?});", script.text, re.DOTALL)
                    if match:
                        import json
                        try:
                            data = json.loads(match.group(1))
                            tabs = (
                                data.get("contents", {})
                                .get("twoColumnBrowseResultsRenderer", {})
                                .get("tabs", [])
                            )
                            for tab in tabs:
                                tab_renderer = tab.get("tabRenderer", {})
                                if tab_renderer.get("title", "").lower() == "videos":
                                    contents = (
                                        tab_renderer.get("content", {})
                                        .get("richGridRenderer", {})
                                        .get("contents", [])
                                    )
                                    for content in contents:
                                        video = (
                                            content.get("richItemRenderer", {})
                                            .get("content", {})
                                            .get("videoRenderer", {})
                                        )
                                        if video:
                                            video_id = video.get("videoId", "")
                                            title_runs = (
                                                video.get("title", {})
                                                .get("runs", [])
                                            )
                                            title = ""
                                            if title_runs:
                                                title = title_runs[0].get("text", "")
                                            desc = (
                                                video.get("descriptionSnippet", {})
                                                .get("runs", [{}])[0]
                                                .get("text", "")
                                            )
                                            thumbnail = ""
                                            thumbnails = (
                                                video.get("thumbnail", {})
                                                .get("thumbnails", [])
                                            )
                                            if thumbnails:
                                                thumbnail = thumbnails[-1].get("url", "")
                                            published = (
                                                video.get("publishedTimeText", {})
                                                .get("simpleText", "")
                                            )
                                            video_data.append({
                                                "title": title,
                                                "description": desc,
                                                "url": f"https://youtube.com/watch?v={video_id}",
                                                "thumbnail": thumbnail,
                                                "publishedAt": published,
                                                "channelHandle": handle,
                                                "source": "YouTube",
                                            })
                        except json.JSONDecodeError:
                            pass
                    break
            return video_data
        except Exception as e:
            logger.error(f"Scrape error for {handle}: {e}")
            return []

    def _filter_recent(self, videos: List[Dict]) -> List[Dict]:
        filtered = []
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        for v in videos:
            is_recent = False
            pub = v.get("publishedAt", "")
            if pub:
                try:
                    pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                    if pub_dt > cutoff:
                        is_recent = True
                except (ValueError, AttributeError):
                    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                    if yesterday_str in pub or "hour" in pub or "minute" in pub:
                        is_recent = True
            if is_recent:
                filtered.append(v)
        return filtered

    def parse_description_items(self, description: str, channel_handle: str) -> List[Dict]:
        """استخراج أخبار منفردة من وصف فيديو يوتيوب"""
        if not description:
            return []
        items = []
        lines = description.split("\n")
        current_title = ""
        current_desc = []
        emoji_pattern = re.compile(r"[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF\u2B50]")

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if emoji_pattern.match(line) and len(line) < 150:
                if current_title:
                    items.append(self._make_youtube_item(current_title, " ".join(current_desc), channel_handle))
                current_title = line
                current_desc = []
            elif current_title:
                current_desc.append(line)

        if current_title:
            items.append(self._make_youtube_item(current_title, " ".join(current_desc), channel_handle))
        return items

    def _fetch_trending(self) -> List[Dict]:
        for attempt in range(len(self.api_keys) + 1):
            key = self._get_current_key()
            if not key:
                return []
            try:
                url = (
                    "https://www.googleapis.com/youtube/v3/videos"
                    f"?part=snippet,statistics&chart=mostPopular"
                    f"&regionCode=US&maxResults=10&key={key}"
                )
                resp = requests.get(url, timeout=10)
                if resp.status_code == 429:
                    if not self._switch_api_key():
                        return []
                    continue
                if resp.status_code != 200:
                    return []
                data = resp.json()
                results = []
                for item in data.get("items", []):
                    snippet = item["snippet"]
                    stats = item.get("statistics", {})
                    results.append({
                        "title": snippet.get("title", ""),
                        "description": snippet.get("description", ""),
                        "url": f"https://youtube.com/watch?v={item['id']}",
                        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                        "publishedAt": snippet.get("publishedAt", ""),
                        "channelTitle": snippet.get("channelTitle", ""),
                        "channelHandle": "",
                        "source": "YouTube Trending",
                        "views": stats.get("viewCount", 0),
                        "isTrusted": True,
                    })
                logger.info(f"YouTube Trending: {len(results)} items")
                return results
            except Exception as e:
                logger.warning(f"YouTube Trending error: {e}")
                return []
        return []

    def _make_youtube_item(self, title: str, desc: str, channel: str) -> Dict:
        return {
            "title": title,
            "description": desc,
            "snippet": desc[:300],
            "url": "",
            "link": "",
            "source": channel,
            "sourceName": channel,
            "date": datetime.now(timezone.utc).isoformat(),
            "isTrusted": False,
            "imageUrl": "",
            "_sourceType": "youtube",
        }
