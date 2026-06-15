import logging
import re
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple
from src.config import (
    STRONG_AI_KEYWORDS, GENERAL_TECH_KEYWORDS, BAD_KEYWORDS, VALUABLE_KEYWORDS,
    CATEGORIES,
    VERIFICATION_SOURCES_MIN, HOURS_BACK, MIN_NEWS_COUNT, MAX_NEWS_COUNT,
)
from src.models import NewsItem

logger = logging.getLogger(__name__)


class NewsProcessor:
    def __init__(self):
        self.categories_ar_en = {
            "الذكاء الاصطناعي": ["ai", "artificial intelligence", "machine learning", "deep",
                                "neural", "gpt", "llm", "openai", "chatgpt", "gemini", "claude",
                                "diffusion", "transformer", "model", "algorithm", "robot",
                                "robotics", "automation", "agent",
                                "ذكاء اصطناعي", "تعلم آلة", "تعلم عميق", "روبوت"],
            "منصات التواصل الاجتماعي": ["social media", "facebook", "instagram", "tiktok",
                                         "twitter", "threads", "linkedin", "youtube", "platform",
                                         "meta", "content moderation", "algorithm",
                                         "فيسبوك", "انستقرام", "تيك توك", "يوتيوب", "تواصل"],
            "آخر أخبار العالم": ["world", "global", "international", "breaking news",
                                 "us news", "europe", "china", "russia", "war", "crisis",
                                 "president", "government", "policy", "regulation", "economy",
                                 "أخبار العالم", "عالمي", "دولي", "اقتصاد"],
            "آخر التحديات الرقمية": ["cyber", "security", "breach", "hack", "privacy",
                                       "data leak", "digital", "threat", "vulnerability",
                                       "encryption", "authentication",
                                       "أمان", "اختراق", "خصوصية", "تهديد رقمي"],
            "صناعة المحتوى": ["content", "creator", "youtuber", "influencer", "video",
                              "stream", "podcast", "monetize", "audience", "engagement",
                              "editing", "production", "thumbnail",
                              "صناعة محتوى", "يوتيوبر", "منتج محتوى", "تصميم"],
            "كتابة القصص": ["writing", "story", "fiction", "author", "narrative",
                            "script", "screenplay", "creative", "literary", "novel",
                            "كتابة", "قصة", "نشر", "تأليف", "رواية"],
            "التريندات العالمية": ["trend", "viral", "meme", "challenge", "hype",
                                    "pop culture", "internet culture", "phenomenon",
                                    "ترند", "تريند", "انتشار", "موضة"],
        }

    def process_all(self, youtube_items: List[Dict], web_items: List[Dict],
                    tools_items: List[Dict], community_items: List[Dict] = None,
                    reddit_items: List[Dict] = None, trends_items: List[Dict] = None) -> "tuple[List[NewsItem], List[NewsItem]]":
        """يعيد (كل الأخبار المصنفة, أفضل الأخبار المختارة)"""
        combined = self._merge_sources(youtube_items, web_items, tools_items, community_items, reddit_items, trends_items)

        filtered = self._filter_by_criteria(combined)

        verified = self._verify_sources(filtered)

        deduplicated = self._deduplicate(verified)

        classified = [self._classify_item(item) for item in deduplicated]

        scored = [self._score_item(item) for item in classified]

        all_items = [self._to_news_item(item) for item in scored]

        final = self._select_diverse(scored)

        result = final[:MAX_NEWS_COUNT]

        tools_count = sum(1 for r in result if "theneuron" in r.sourceUrl.lower() or r.sourceName == "The Neuron")
        if tools_count < 2 and tools_items:
            from_tools = [self._to_news_item(self._score_item(self._classify_item(t)))
                         for t in tools_items[:4]]
            for t_item in from_tools:
                if t_item not in result:
                    result.append(t_item)
                    tools_count += 1
                    if tools_count >= 2:
                        break

        return all_items, result[:MAX_NEWS_COUNT]

    def _select_diverse(self, items: List[Dict]) -> List[NewsItem]:
        by_category = {}
        for item in items:
            cat = item.get("_category", "أخبار")
            by_category.setdefault(cat, []).append(item)

        selected = []
        seen_urls = set()
        seen_sources = set()

        per_category = max(2, MAX_NEWS_COUNT // max(len(by_category), 1))

        for cat in CATEGORIES:
            cat_items = by_category.pop(cat, [])
            cat_items.sort(key=lambda x: x["importanceScore"], reverse=True)
            for item in cat_items[:per_category]:
                news_item = self._to_news_item(item)
                url = news_item.sourceUrl
                src = news_item.sourceName
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    seen_sources.add(src)
                    selected.append(news_item)

        remaining = []
        for cat_items in by_category.values():
            remaining.extend(cat_items)
        remaining.sort(key=lambda x: x["importanceScore"], reverse=True)

        source_types = {}
        source_counts = {}
        for item in items:
            st = item.get("_sourceType", "unknown")
            source_types.setdefault(st, 0)
        for item in remaining:
            st = item.get("_sourceType", "unknown")
            src = item.get("source", "") or item.get("sourceName", "") or ""
            if st not in source_counts:
                source_counts[st] = 0
            if src not in seen_sources:
                source_counts[st] = source_counts.get(st, 0) + 1

        min_per_source = max(1, MAX_NEWS_COUNT // max(len(source_types), 1))

        for st in source_types:
            st_items = [i for i in remaining if i.get("_sourceType") == st and
                        self._to_news_item(i).sourceUrl not in seen_urls]
            st_items.sort(key=lambda x: x["importanceScore"], reverse=True)
            for item in st_items[:min_per_source]:
                if len(selected) >= MAX_NEWS_COUNT:
                    break
                news_item = self._to_news_item(item)
                url = news_item.sourceUrl
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    selected.append(news_item)

        for item in remaining:
            if len(selected) >= MAX_NEWS_COUNT:
                break
            news_item = self._to_news_item(item)
            url = news_item.sourceUrl
            if url and url not in seen_urls:
                seen_urls.add(url)
                selected.append(news_item)

        return selected

    def _merge_sources(self, youtube: List[Dict], web: List[Dict],
                       tools: List[Dict], community: List[Dict] = None,
                       reddit: List[Dict] = None, trends: List[Dict] = None) -> List[Dict]:
        merged = []
        for item in youtube:
            item["_sourceType"] = "youtube"
            merged.append(item)
        for item in web:
            item["_sourceType"] = "web"
            merged.append(item)
        for item in tools:
            item["_sourceType"] = "tools"
            merged.append(item)
        if community:
            for item in community:
                item["_sourceType"] = "community"
                merged.append(item)
        if reddit:
            for item in reddit:
                item["_sourceType"] = "community"
                merged.append(item)
        if trends:
            for item in trends:
                item["_sourceType"] = "web"
                merged.append(item)
        return merged

    def _filter_by_criteria(self, items: List[Dict]) -> List[Dict]:
        filtered = []
        for item in items:
            title = item.get("title", "")
            desc = item.get("description", "") or item.get("snippet", "") or ""
            text = f"{title} {desc}".lower()

            bad_count = sum(1 for kw in BAD_KEYWORDS if kw in text)
            if bad_count >= 2:
                continue

            is_ai = any(kw in text for kw in STRONG_AI_KEYWORDS)
            is_general = sum(1 for kw in GENERAL_TECH_KEYWORDS if kw in text)

            if is_ai and is_general < 2:
                item["_isValid"] = True
                filtered.append(item)
                continue

            is_category_match = any(
                keyword in text
                for keywords in self.categories_ar_en.values()
                for keyword in keywords
            )
            if is_category_match and is_general < 2:
                item["_isValid"] = True
                filtered.append(item)

        return filtered

    def _verify_sources(self, items: List[Dict]) -> List[Dict]:
        title_groups = {}
        for item in items:
            norm_title = self._normalize_title(item.get("title", ""))
            words = set(norm_title.split())
            matched = False
            for existing_norm in list(title_groups.keys()):
                existing_words = set(existing_norm.split())
                if not words or not existing_words:
                    continue
                overlap = len(words & existing_words) / max(len(words), len(existing_words))
                if overlap > 0.5:
                    title_groups[existing_norm].append(item)
                    matched = True
                    break
            if not matched:
                title_groups[norm_title] = [item]

        verified = []
        for group in title_groups.values():
            sources = set()
            for item in group:
                src = item.get("source", "") or item.get("sourceName", "") or item.get("channelHandle", "")
                url = item.get("url", "") or item.get("link", "")
                if src:
                    sources.add(src)
                elif url:
                    from urllib.parse import urlparse
                    sources.add(urlparse(url).netloc)

            best_item = max(group, key=lambda x: len(x.get("description", "") or ""))

            if len(sources) >= VERIFICATION_SOURCES_MIN:
                best_item["_verified"] = True
                best_item["_sourceCount"] = len(sources)
            else:
                best_item["_verified"] = False
                best_item["_sourceCount"] = len(sources)

            verified.append(best_item)

        return verified

    def _deduplicate(self, items: List[Dict]) -> List[Dict]:
        seen = set()
        result = []
        for item in items:
            title = self._normalize_title(item.get("title", ""))
            if title not in seen:
                seen.add(title)
                result.append(item)
        return result

    def _classify_item(self, item: Dict) -> Dict:
        text = f"{item.get('title', '')} {item.get('description', '')} {item.get('snippet', '')}".lower()

        category_scores = {}
        for category, keywords in self.categories_ar_en.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                category_scores[category] = score

        ai_score = category_scores.get("الذكاء الاصطناعي", 0)
        non_ai_scores = {k: v for k, v in category_scores.items() if k != "الذكاء الاصطناعي"}

        if non_ai_scores:
            best_non_ai = max(non_ai_scores, key=non_ai_scores.get)
            if non_ai_scores[best_non_ai] >= ai_score:
                best_category = best_non_ai
            else:
                best_category = "الذكاء الاصطناعي"
        elif category_scores:
            best_category = max(category_scores, key=category_scores.get)
        elif item.get("_sourceType") == "tools":
            best_category = "الذكاء الاصطناعي"
        else:
            best_category = "آخر أخبار العالم"

        item["_category"] = best_category
        return item

    def _score_item(self, item: Dict) -> Dict:
        score = 50
        text = f"{item.get('title', '')} {item.get('description', '')}".lower()

        ai_count = sum(1 for kw in STRONG_AI_KEYWORDS if kw in text)
        score += min(ai_count * 5, 25)

        valuable_count = sum(1 for kw in VALUABLE_KEYWORDS if kw in text)
        score += min(valuable_count * 8, 30)

        if item.get("_verified"):
            score += 15
        if item.get("_sourceCount", 1) >= 2:
            score += 10

        trusted = item.get("isTrusted", False)
        if trusted:
            score += 10

        if item.get("_sourceType") == "web":
            score += 5

        desc_len = len(item.get("description", "") or "")
        if desc_len > 100:
            score += 5

        if re.search(r"(breakthrough|revolutionary|first-ever|major|huge|significant)", text):
            score += 5

        from urllib.parse import urlparse
        domain = urlparse(item.get("url", item.get("link", ""))).netloc.lower()
        if any(t in domain for t in ["arxiv", "nature", "science", "mit", "openai", "deepmind"]):
            score += 5

        item["importanceScore"] = min(score, 100)
        return item

    def _to_news_item(self, item: Dict) -> NewsItem:
        title = item.get("title", "")
        desc = item.get("description", "") or item.get("snippet", "") or ""
        summary = desc[:400] if len(desc) > 400 else desc

        keywords = []
        text_keywords = f"{title} {desc}".lower()
        for kw in STRONG_AI_KEYWORDS:
            if kw in text_keywords and kw not in keywords:
                keywords.append(kw)

        tags = self._generate_tags(item)

        suggested_post = self._generate_suggested_post(title, summary, item.get("url", item.get("link", "")))

        impact = self._generate_impact_analysis(title, item.get("_category", "الذكاء الاصطناعي"), item.get("importanceScore", 50))

        url = item.get("url", "") or item.get("link", "")
        secondary_url = ""
        if item.get("_sourceCount", 1) >= 2 and url:
            secondary_url = url

        image_url = item.get("imageUrl", "") or item.get("thumbnail", "")
        if not image_url:
            image_url = self._fetch_image(url)

        return NewsItem(
            title=title,
            summary=summary,
            category=item.get("_category", "الذكاء الاصطناعي"),
            importanceScore=item.get("importanceScore", 50),
            publishedAt=item.get("date", "") or item.get("publishedAt", ""),
            sourceName=item.get("sourceName", "") or item.get("source", "") or item.get("channelHandle", ""),
            sourceUrl=url,
            secondarySourceUrl=secondary_url,
            imageUrl=image_url,
            keywords=keywords[:8],
            tags=tags,
            suggestedPost=suggested_post,
            impactAnalysis=impact,
        )

    def _fetch_image(self, url: str) -> str:
        if not url:
            return ""
        try:
            resp = requests.get(url, timeout=(5, 8))
            if resp.status_code == 200:
                og = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', resp.text, re.IGNORECASE)
                if og:
                    return og.group(1)
                img = re.search(r'<img[^>]+src="([^"]+)"', resp.text)
                if img and not img.group(1).startswith("data:"):
                    return img.group(1)
        except Exception:
            pass
        return ""

    def _normalize_title(self, title: str) -> str:
        t = title.lower().strip()
        t = re.sub(r"[^\w\s]", "", t)
        t = re.sub(r"\s+", " ", t)
        stop_words = ["the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or", "is", "are", "this", "that", "with", "from", "by", "new", "top", "best"]
        words = [w for w in t.split() if w not in stop_words]
        return " ".join(words[:10])

    def _generate_tags(self, item: Dict) -> List[str]:
        tags = []
        type_keywords = {
            "أبحاث": "research",
            "نماذج جديدة": "new model",
            "تحولات جذرية": "breakthrough",
            "تحديثات منصات": "platform update",
            "مواقع جديدة": "new platform",
        }
        text = f"{item.get('title', '')} {item.get('description', '')}".lower()
        for tag, kw in type_keywords.items():
            if kw in text:
                tags.append(tag)
        if not tags:
            tags.append("أخبار")
        return tags[:3]

    def _generate_suggested_post(self, title: str, summary: str, url: str) -> str:
        clean_title = re.sub(r'[^\w\s]', '', title)
        short_summary = summary[:120] if len(summary) > 120 else summary
        return f"{clean_title}\n\n{short_summary}\n\nللمزيد: {url}"

    def _generate_impact_analysis(self, title: str, category: str, score: int) -> str:
        templates = {
            "الذكاء الاصطناعي": {
                "high": "هذا التطور في الذكاء الاصطناعي يعيد تشكيل المشهد التقني. يُتوقع أن يؤثر على طريقة عمل الشركات والمطورين في الأشهر القادمة، مع تداعيات محتملة على سوق العمل والابتكار.",
                "medium": "تحديث مهم في مجال الذكاء الاصطناعي يعكس التسارع المستمر في هذا القطاع. يستدعي المتابعة لرصد آثاره على المدى القريب.",
                "low": "خبر تقني في مجال الذكاء الاصطناعي، جزء من التدفق المستمر للابتكارات في هذا المجال الحيوي.",
            },
            "منصات التواصل الاجتماعي": {
                "high": "تغيير جذري في سياسات منصات التواصل الاجتماعي سيؤثر على ملايين المستخدمين وصناع المحتوى. قد يعيد تشكيل استراتيجيات التسويق الرقمي.",
                "medium": "تحديث مهم في عالم المنصات الاجتماعية. يستحق المتابعة لمعرفة تأثيره على تفاعل المستخدمين وخوارزميات العرض.",
                "low": "تغيير طفيف في إحدى منصات التواصل. قد يكون له تأثير تدريجي على تجربة المستخدم.",
            },
            "صناعة المحتوى": {
                "high": "تطور جذري في أدوات وتقنيات صناعة المحتوى. يفتح آفاقاً جديدة للمبدعين ويغير قواعد اللعبة في المشهد الرقمي.",
                "medium": "أداة أو منصة جديدة تدعم صناع المحتوى في إنتاج محتوى أفضل وأسرع. خطوة إيجابية نحو إتقان الحرفة.",
                "low": "إضافة مفيدة في أدوات صناعة المحتوى. قد تهم شريحة محددة من المنتجين.",
            },
            "آخر التحديات الرقمية": {
                "high": "تهديد أمني كبير يستدعي اتخاذ إجراءات فورية. يؤكد على أهمية الأمن السيبراني وحماية البيانات في العصر الرقمي.",
                "medium": "تطور مهم في مجال الأمن الرقمي. يستوجب مراجعة إجراءات الحماية ورفع الجاهزية.",
                "low": "تنبيه أمني يستحق الانتباه. جزء من المشهد المتطور للتحديات الرقمية.",
            },
        }

        cat_templates = templates.get(category, {
            "high": "تطور مهم في هذا المجال قد يؤثر على مسار الصناعة. يستحق المتابعة والتحليل.",
            "medium": "خبر يعكس حركة التطور المستمر في المجال. له دلالاته على المدى المتوسط.",
            "low": "إضافة جديدة للمجال. تهم المهتمين بمتابعة آخر المستجدات.",
        })

        if score >= 75:
            return cat_templates["high"]
        elif score >= 55:
            return cat_templates["medium"]
        else:
            return cat_templates["low"]
