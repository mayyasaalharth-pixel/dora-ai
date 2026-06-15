import logging
from datetime import datetime, timezone
from typing import List, Dict
from src.config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_SUBREDDITS

logger = logging.getLogger(__name__)


class RedditScraper:
    def __init__(self):
        self.client_id = REDDIT_CLIENT_ID
        self.client_secret = REDDIT_CLIENT_SECRET
        self._reddit = None

    def _init_reddit(self):
        if self._reddit:
            return True
        if not self.client_id or not self.client_secret:
            logger.warning("Reddit API credentials not configured")
            return False
        try:
            import praw
            self._reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent="AI News Aggregator/1.0"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to init Reddit: {e}")
            return False

    def fetch_all(self) -> List[Dict]:
        if not self._init_reddit():
            return []
        items = []
        seen = set()
        for subreddit_name in REDDIT_SUBREDDITS:
            try:
                subreddit = self._reddit.subreddit(subreddit_name)
                for post in subreddit.hot(limit=5):
                    title_lower = post.title.lower()
                    if title_lower in seen:
                        continue
                    seen.add(title_lower)
                    items.append({
                        "title": post.title,
                        "description": post.selftext[:400] if post.selftext else "",
                        "url": post.url,
                        "source": f"Reddit r/{subreddit_name}",
                        "date": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat() if post.created_utc else "",
                        "score": post.score,
                        "isTrusted": True,
                        "imageUrl": "",
                        "thumbnail": "",
                    })
            except Exception as e:
                logger.warning(f"Reddit r/{subreddit_name} error: {e}")
                continue
        logger.info(f"Reddit: {len(items)} items from {len(REDDIT_SUBREDDITS)} subreddits")
        return items
