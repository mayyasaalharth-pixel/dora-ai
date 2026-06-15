import logging
import re
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict
from src.config import PRODUCT_HUNT_TOKEN, GITHUB_TRENDING_COUNT, HACKER_NEWS_COUNT

logger = logging.getLogger(__name__)


class CommunityScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch_all(self) -> List[Dict]:
        items = []
        items.extend(self._fetch_product_hunt())
        items.extend(self._fetch_hacker_news())
        items.extend(self._fetch_github_trending())
        return items

    def _fetch_product_hunt(self) -> List[Dict]:
        if not PRODUCT_HUNT_TOKEN:
            logger.warning("Product Hunt token not configured, trying RSS fallback")
            return self._fetch_product_hunt_fallback()
        try:
            url = "https://api.producthunt.com/v2/api/graphql"
            headers = {
                **self.headers,
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {PRODUCT_HUNT_TOKEN}",
            }
            query = {
                "query": """
                {
                    posts(first: 20, order: VOTES, postedAfter: "2026-06-14T00:00:00Z") {
                        edges {
                            node {
                                id
                                name
                                tagline
                                url
                                votesCount
                                createdAt
                                description
                                thumbnail {
                                    url
                                }
                                topics {
                                    edges {
                                        node {
                                            name
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                """
            }
            resp = self.session.post(url, json=query, headers=headers, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"Product Hunt API returned {resp.status_code}: {resp.text[:200]}")
                return self._fetch_product_hunt_fallback()
            data = resp.json()
            if "errors" in data:
                logger.warning(f"Product Hunt API errors: {data['errors']}")
                return self._fetch_product_hunt_fallback()
            results = []
            for edge in data.get("data", {}).get("posts", {}).get("edges", []):
                node = edge["node"]
                topics = []
                for t_edge in node.get("topics", {}).get("edges", []):
                    t_name = t_edge.get("node", {}).get("name", "")
                    if t_name:
                        topics.append(t_name)
                description = node.get("description", "") or node.get("tagline", "")
                results.append({
                    "title": node.get("name", ""),
                    "description": description[:500],
                    "url": node.get("url", ""),
                    "thumbnail": node.get("thumbnail", {}).get("url", "") if node.get("thumbnail") else "",
                    "source": "Product Hunt",
                    "date": node.get("createdAt", ""),
                    "votes": node.get("votesCount", 0),
                    "isTrusted": True,
                    "imageUrl": node.get("thumbnail", {}).get("url", "") if node.get("thumbnail") else "",
                    "topics": topics,
                })
            logger.info(f"Product Hunt API: {len(results)} items")
            return results
        except Exception as e:
            logger.warning(f"Product Hunt API failed: {e}")
            return self._fetch_product_hunt_fallback()

    def _fetch_product_hunt_fallback(self) -> List[Dict]:
        try:
            resp = self.session.get("https://www.producthunt.com/feed", timeout=10)
            if resp.status_code != 200:
                return []
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.content, "xml")
            items = soup.find_all("item")
            results = []
            for item in items[:10]:
                title = item.find("title")
                link = item.find("link")
                desc = item.find("description")
                results.append({
                    "title": title.get_text(strip=True) if title else "",
                    "description": desc.get_text(strip=True) if desc else "",
                    "url": link.get_text(strip=True) if link else "",
                    "source": "Product Hunt",
                    "date": "",
                    "isTrusted": True,
                    "imageUrl": "",
                })
            logger.info(f"Product Hunt RSS: {len(results)} items")
            return results
        except Exception as e:
            logger.warning(f"Product Hunt RSS failed: {e}")
            return []

    def _fetch_hacker_news(self) -> List[Dict]:
        try:
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            resp = self.session.get(url, timeout=10)
            if resp.status_code != 200:
                return []
            story_ids = resp.json()[:HACKER_NEWS_COUNT]
            results = []
            for sid in story_ids:
                try:
                    item_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                    ir = self.session.get(item_url, timeout=5)
                    if ir.status_code != 200:
                        continue
                    story = ir.json()
                    title = story.get("title", "")
                    story_url = story.get("url", f"https://news.ycombinator.com/item?id={sid}")
                    desc = story.get("text", "") or ""
                    results.append({
                        "title": title,
                        "description": desc[:400],
                        "url": story_url,
                        "source": "Hacker News",
                        "date": datetime.fromtimestamp(story.get("time", 0), tz=timezone.utc).isoformat() if story.get("time") else "",
                        "score": story.get("score", 0),
                        "isTrusted": True,
                        "imageUrl": "",
                    })
                except Exception:
                    continue
            logger.info(f"Hacker News: {len(results)} items")
            return results
        except Exception as e:
            logger.warning(f"Hacker News failed: {e}")
            return []

    def _fetch_github_trending(self) -> List[Dict]:
        items = []
        items.extend(self._fetch_github_trending_page())
        items.extend(self._fetch_github_search())
        return items

    def _fetch_github_trending_page(self) -> List[Dict]:
        try:
            resp = self.session.get("https://github.com/trending?since=weekly", timeout=10)
            if resp.status_code != 200:
                return []
            html = resp.text
            repos = re.findall(
                r'<h2[^>]*>.*?<a[^>]*href="/([^"]+)"[^>]*>([^<]+)</a>',
                html,
                re.DOTALL,
            )
            results = []
            seen = set()
            for repo_path, repo_name in repos:
                repo_full = repo_path.strip()
                if repo_full in seen:
                    continue
                if "/" not in repo_full or repo_full.startswith("login"):
                    continue
                seen.add(repo_full)
                desc_match = re.search(
                    rf'<h2[^>]*>.*?<a[^>]*href="/{re.escape(repo_full)}"[^>]*>.*?</h2>.*?<p[^>]*>(.*?)</p>',
                    html,
                    re.DOTALL,
                )
                description = ""
                if desc_match:
                    description = re.sub(r"<.*?>", "", desc_match.group(1)).strip()
                results.append({
                    "title": f"{repo_full.split('/')[-1]} - {repo_full}",
                    "description": description,
                    "url": f"https://github.com/{repo_full}",
                    "source": "GitHub Trending",
                    "date": "",
                    "isTrusted": True,
                    "imageUrl": "",
                })
                if len(results) >= GITHUB_TRENDING_COUNT:
                    break
            logger.info(f"GitHub Trending page: {len(results)} items")
            return results
        except Exception as e:
            logger.warning(f"GitHub Trending page failed: {e}")
            return []

    def _fetch_github_search(self) -> List[Dict]:
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
            url = (
                "https://api.github.com/search/repositories"
                f"?q=stars:>500+created:>{cutoff}&sort=stars&order=desc&per_page=10"
            )
            headers = {**self.headers, "Accept": "application/vnd.github.v3+json"}
            resp = self.session.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"GitHub Search API returned {resp.status_code}")
                return []
            data = resp.json()
            results = []
            for repo in data.get("items", []):
                results.append({
                    "title": f"{repo['name']} - {repo['full_name']}",
                    "description": (repo.get("description") or "")[:400],
                    "url": repo.get("html_url", ""),
                    "source": "GitHub Search",
                    "date": repo.get("created_at", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "isTrusted": True,
                    "imageUrl": "",
                })
            logger.info(f"GitHub Search API: {len(results)} items")
            return results
        except Exception as e:
            logger.warning(f"GitHub Search API failed: {e}")
            return []
