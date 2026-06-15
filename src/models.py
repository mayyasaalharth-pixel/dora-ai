from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional


@dataclass
class NewsItem:
    title: str
    summary: str
    category: str
    importanceScore: int
    publishedAt: str
    sourceName: str
    sourceUrl: str
    secondarySourceUrl: str
    imageUrl: str
    keywords: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    suggestedPost: str = ""
    impactAnalysis: str = ""
    id: Optional[int] = None
    collectedAt: str = ""

    def __post_init__(self):
        if not self.collectedAt:
            self.collectedAt = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
