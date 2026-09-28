import os
import json
import hashlib
import requests
import feedparser
import anthropic
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Переменные окружения
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")

POSTED_FILE = "posted_ids.json"

# Список RSS-лент (если нет отдельного файла feeds.py)
try:
    from feeds import RSS_FEEDS
except ImportError:
    RSS_FEEDS = [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://news.ycombinator.com/rss",
    ]

# ---------------------------------------------------------------------------
# Логика работы с дедупликацией (чтобы не постить одно и то же)
# ---------------------------------------------------------------------------
def load_posted():
    try:
        with open(POSTED_FILE) as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_posted(ids):
    with open(POSTED_FILE, "w") as f:
        json.dump(list(ids), f)

# ---------------------------------------------------------------------------
# Сбор свежих статей из RSS
# ---------------------------------------------------------------------------
def fetch_recent_articles(hours=8):
    articles = []
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            pub = entry.get("published_parsed")
            if pub:
                pub_dt = datetime(*pub[:6])
                if pub_dt < cutoff:
                    continue
            articles.append({
                "id": hashlib.md5(entry.link.encode()).hexdigest(),
                "title": entry.title,
                "summary": entry.get("summary", "")[:800],
                "link": entry.link,
            })
    return articles

# ---------------------------------------------------------------------------
# Генерация через Claude (Anthropic)
# ---------------------------------------------------------------------------
def rewrite_with_claude(article):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""Ты — редактор экспертного сообщества об ИИ и автоматизации для русскоязычной аудитории.

Перепиши эту новость как вовлекающий, качественный пост для Facebook (3-5 абзацев):
- На русском языке
- Живо, легко и понятно, без канцелярита
- Объясни практическую пользу для бизнеса, карьеры или автоматизации
- Используй структурированный формат (абзацы, эмодзи, списки)
- В конце добавь ссылку на источник: {article['link']}
- НЕ добавляй служебные заголовки вроде "Вот ваш пост" — сразу начинай с сути.

Заголовок оригинала: {article['title']}
Краткое содержание: {article['summary']}
"""
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()

# ---------------------------------------------------------------------------
# Публикация на Страницу Facebook (через Graph API)
# ---------------------------------------------------------------------------
def post_to_facebook(text):
    if not FB_ACCESS_TOKEN or not FB_PAGE_ID:
        print("\n--- [ТЕСТОВЫЙ РЕЖИМ: FB ключи не заданы] ---")
        print(text)
        print("-------------------------------------------\n")
        return True

    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    payload = {
        "message": text,
        "access_token": FB_ACCESS_TOKEN
    }
    response = requests.post(url, data=payload, timeout=30)
    res_data = response.json()
    
    if response.status_code == 200 and "id" in res_data:
        print(f"✅ Успешно опубликовано в Facebook! Post ID: {res_data['id']}")
        return True
    else:
        print(f"❌ Ошибка публикации в Facebook: {res_data}")
        return False

# ---------------------------------------------------------------------------
# Главная функция
# ---------------------------------------------------------------------------
def main():
    print("1. Загрузка истории опубликованных постов...")
    posted = load_posted()
    
    print("2. Сбор свежих новостей из RSS...")
    articles = fetch_recent_articles(hours=12)
    new_articles = [a for a in articles if a["id"] not in posted]

    if not new_articles:
        print("ℹ️ Новых статей за последние 12 часов не найдено.")
        return

    # Берем одну самую свежую необработанную новость
    for article in new_articles[:1]:
        print(f"\n3. Обработка новости: {article['title']}")
        text = rewrite_with_claude(article)
        
        success = post_to_facebook(text)
        if success:
            posted.add(article["id"])

    save_posted(posted)
    print("\n🎉 Работа завершена успешно!")

if __name__ == "__main__":
    main()
