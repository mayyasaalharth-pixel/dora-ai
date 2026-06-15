import sys
sys.path.insert(0, '.')
from src.database import Database
db = Database()
items = db.get_all_news()
recent = sorted(items, key=lambda x: x.collectedAt, reverse=True)[:15]
print(f'Total: {len(items)} | Last 15:')
for i, item in enumerate(recent):
    img = 'IMG' if item.imageUrl else 'NOIMG'
    print(f'{i+1}. [{item.category}] {img} {item.importanceScore} {item.sourceName[:15]} - {item.title[:70]}')
