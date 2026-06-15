# Dora AI - نظام تجميع أخبار الذكاء الاصطناعي

نظام آلي يجمع آخر أخبار الذكاء الاصطناعي والتقنيات الرقمية يومياً من مصادر متعددة، يترجمها للعربية، ويقدمها عبر REST API.

## المصادر

- **يوتيوب**: 7 قنوات (PythonArab, ePreneurs, procoder09, ArabianAiSchool, harshitdynamite, AmirDiscoveries, josephs_ai) + YouTube Trending US
- **RSS**: 35+ مصدر إخباري (AI, creator economy, social trends, AI tools, startups, Arabic)
- **Hacker News**: أفضل 15 قصة
- **GitHub Trending**: الصفحة + GitHub Search API
- **Product Hunt**: 20 أداة عبر GraphQL API
- **Reddit**: 8 subreddits (artificial, MachineLearning, ChatGPT, OpenAI, technology, InternetIsBeautiful, SideProject, startups)
- **Google Trends**: RSS feed للترندات

## الميزات

- **جمع يومي آلي** الساعة 09:00 صباحاً
- **ترجمة إنجليزية ← عربية** عبر deep-translator
- **تحسين عربي** عبر Gemini API (صياغة عربية، منشور مقترح، تحليل تأثير)
- **تصنيف في 7 فئات** (AI، منصات، العالم، تقنيات رقمية، محتوى، قصص، ترندات)
- **تقييم ذكي** + فلترة محتوى سيء
- **تنوع المصادر** (إجباري: web, youtube, community, tools)
- **Google Sheets**: English sheet (جميع الأخبار) + Arabic sheet (40 منظمة)
- **SQLite** للتخزين المؤقت + API
- **REST API كامل** مع CORS
- **دعم عربي كامل**

## الإعداد السريع

```bash
pip install -r requirements.txt
cp .env.example .env
# عدل .env بمفاتيحك
python main.py
```

## API

| المسار | الوصف |
|--------|-------|
| `GET /` | معلومات API |
| `GET /api/organized-news` | أخبار اليوم منظمة حسب الفئات |
| `GET /news` | جميع الأخبار |
| `GET /news/today` | أخبار اليوم |
| `GET /health` | حالة الخدمة |

## متغيرات البيئة

- `YOUTUBE_API_KEY` + `YOUTUBE_API_KEY_2` - مفاتيح YouTube
- `GEMINI_API_KEY` - مفتاح Gemini للتحسين العربي
- `PRODUCT_HUNT_TOKEN` - توكن Product Hunt API
- `GOOGLE_SHEETS_CREDENTIALS` - محتوى JSON service account
- `GOOGLE_SHEET_ID` + `GOOGLE_SHEET_ID_ARABIC` - معرفات Google Sheets
- `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` - مفاتيح Reddit API
- `SCHEDULE_TIME` - وقت الجدولة (09:00)
