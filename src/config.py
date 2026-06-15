import os
from dotenv import load_dotenv

load_dotenv()

SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "09:00")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
YOUTUBE_API_KEY_2 = os.getenv("YOUTUBE_API_KEY_2", "")
YOUTUBE_API_KEYS = [k for k in [YOUTUBE_API_KEY, YOUTUBE_API_KEY_2] if k]
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_SHEET_ID_ARABIC = os.getenv("GOOGLE_SHEET_ID_ARABIC", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PRODUCT_HUNT_TOKEN = os.getenv("PRODUCT_HUNT_TOKEN", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")

YOUTUBE_CHANNELS = [
    "@PythonArab",
    "@ePreneurs",
    "@procoder09",
    "@ArabianAiSchool",
    "@harshitdynamite",
    "@AmirDiscoveries",
    "@josephs_ai",
]

CATEGORIES = [
    "الذكاء الاصطناعي",
    "منصات التواصل الاجتماعي",
    "آخر أخبار العالم",
    "آخر التحديات الرقمية",
    "صناعة المحتوى",
    "كتابة القصص",
    "التريندات العالمية",
]

STRONG_AI_KEYWORDS = [
    "artificial intelligence", "machine learning", "deep learning",
    "neural network", "llm", "large language model", "gpt", "chatgpt",
    "claude", "gemini", "bert", "transformer", "diffusion model",
    "generative ai", "ai model", "ai research", "openai", "deepmind",
    "anthropic", "hugging face", "tensorflow", "pytorch",
    "ai breakthrough", "ai innovation", "multimodal", "reasoning",
    "agi", "alignment", "foundation model", "agentic", "ai tool",
    "robot", "robotics", "humanoid", "automation",
    "ذكاء اصطناعي", "تعلم آلة", "تعلم عميق",
]

GENERAL_TECH_KEYWORDS = [
    "smartphone", "laptop", "gaming", "crypto", "bitcoin",
    "electric vehicle", "tesla", "apple", "samsung",
    "iphone", "android", "smartwatch", "wearable", "playstation",
    "xbox", "nintendo", "sale", "review", "unboxing", "discount",
    "price", "buy", "shop", "shopping", "black friday",
]

BAD_KEYWORDS = [
    "killed", "dies", "death", "died", "murder", "shooting", "stab",
    "kidnap", "arrest", "prison", "jail", "lawsuit", "sue", "sued",
    "accused", "allegation", "scandal", "affair", "divorce",
    "employee.*hate", "internal memo", "toxic work", "fired", "laid off",
    "قتل", "مقتل", "وفاة", "حادث", "جريمة", "اختطاف", "سجن",
    "دعوى", "فضيحة", "طلاق", "اتهام",
]

VALUABLE_KEYWORDS = [
    "free", "open source", "api", "benchmark", "release", "launch",
    "new model", "new tool", "platform", "framework", "sdk", "library",
    "tutorial", "guide", "how to", "مجاني", "مفتوح المصدر",
    "أداة", "منصة", "إطلاق", "تجربة", "اختبار",
    "benchmark", "swe-bench", "frontier", "score", "ranking",
    "مقارنة", "الفرق بين", "أفضل", "شرح",
]

TRUSTED_SOURCES = [
    "arxiv.org", "techcrunch.com", "theverge.com", "wired.com",
    "mit.edu", "nature.com", "science.org", "deepmind.com",
    "openai.com", "anthropic.com", "venturebeat.com",
    "theneuron.ai", "reuters.com", "apnews.com", "bbc.com",
    "bbc.co.uk", "cnn.com", "nytimes.com", "theguardian.com",
    "bloomberg.com", "wsj.com", "technologyreview.com",
    "zdnet.com", "cnet.com", "forbes.com", "cnbc.com",
    "aljazeera.com", "arabic.cnn.com", "bbc.com/arabic",
]

NEWS_SOURCES = {
    "ai_news": [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://venturebeat.com/category/ai/feed/",
        "https://www.wired.com/feed/tag/ai/latest/rss",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "https://www.technologyreview.com/feed/",
        "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=new+AI+model+launch+2026&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=AI+open+source+free+API&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=AI+startup+funding+launch&hl=en-US&gl=US&ceid=US:en",
        "https://blog.google/technology/ai/rss",
        "https://the-decoder.com/feed/",
    ],
    "creator_economy": [
        "https://www.tubefilter.com/feed/",
        "https://www.socialmediatoday.com/rss",
        "https://blog.hootsuite.com/feed/",
        "https://news.google.com/rss/search?q=content+creator+AI+tool+2026&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=YouTube+creator+update+monetization&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=influencer+marketing+trend+2026&hl=en-US&gl=US&ceid=US:en",
    ],
    "social_trends": [
        "https://news.google.com/rss/search?q=social+media+trend+viral+2026&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=TikTok+Instagram+new+feature+update&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=SEO+algorithm+update+Google&hl=en-US&gl=US&ceid=US:en",
    ],
    "ai_tools": [
        "https://news.google.com/rss/search?q=AI+tool+free+launch&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=AI+productivity+tool+new&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=AI+writing+video+image+tool&hl=en-US&gl=US&ceid=US:en",
    ],
    "startups": [
        "https://news.google.com/rss/search?q=startup+launch+funding+AI&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=new+platform+AI+2026&hl=en-US&gl=US&ceid=US:en",
    ],
    "arabic": [
        "https://news.google.com/rss/search?q=أخبار+الذكاء+الاصطناعي&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=أدوات+ذكاء+اصطناعي+مجانية&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=منصة+ذكاء+اصطناعي+جديدة&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=صناعة+المحتوى+الرقمي+2026&hl=ar&gl=SA&ceid=SA:ar",
    ],
}

FLAT_NEWS_SOURCES = [url for urls in NEWS_SOURCES.values() for url in urls]

REDDIT_SUBREDDITS = [
    "Artificial", "MachineLearning", "ChatGPT", "OpenAI",
    "technology", "InternetIsBeautiful", "SideProject", "startups",
]

PRODUCT_HUNT_FETCH_COUNT = 20
GITHUB_TRENDING_COUNT = 15
HACKER_NEWS_COUNT = 15
YOUTUBE_TRENDING_COUNT = 10
GOOGLE_TRENDS_COUNT = 15

MIN_NEWS_COUNT = 9
MAX_NEWS_COUNT = 40
MAX_RAW_SHEET_ITEMS = 200
VERIFICATION_SOURCES_MIN = 2
HOURS_BACK = 24

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "news.db")
