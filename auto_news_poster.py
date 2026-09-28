import os
import json
import hashlib
import requests
import feedparser
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Переменные окружения
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")

POSTED_FILE = "posted_ids.json"

try:
    from feeds import RSS_FEEDS
except ImportError:
    RSS_FEEDS = [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://news.ycombinator.com/rss",
    ]

# ---------------------------------------------------------------------------
# База данных опубликованных новостей
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
# Сбор RSS
# ---------------------------------------------------------------------------
def fetch_recent_articles(hours=12):
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
# Генерация текста через прямой REST API
# ---------------------------------------------------------------------------
def rewrite_with_claude_direct(article):
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    models_url = "https://api.anthropic.com/v1/models"
    available_models = []
    
    try:
        m_res = requests.get(models_url, headers=headers, timeout=15)
        if m_res.status_code == 200:
            m_data = m_res.json()
            available_models = [m["id"] for m in m_data.get("data", [])]
            print(f"📋 Доступные модели на вашем аккаунте: {available_models}")
    except Exception as e:
        print(f"⚠️ Не удалось загрузить список моделей: {e}")

    if not available_models:
        available_models = ["claude-haiku-4-5-20251001", "claude-sonnet-4-5-20250929"]

    prompt = f"""Ты — редактор экспертного сообщества об ИИ и автоматизации для русскоязычной аудитории.

Перепиши эту новость как вовлекающий, качественный пост для Facebook (3-5 абзацев):
- На русском языке
- Живо, легко и понятно, без канцелярита
- Объясни практическую пользу для бизнеса, карьеры или автоматизации
- Используй структурированный формат (абзацы, эмодзи, списки)
- В конце добавь ссылку на источник: {article['link']}
- НЕ добавляй служебные заголовки — сразу начинай с сути.

Заголовок оригинала: {article['title']}
Краткое содержание: {article['summary']}
"""

    messages_url = "https://api.anthropic.com/v1/messages"

    for model_name in available_models:
        print(f"--> Пробуем модель: {model_name}")
        payload = {
            "model": model_name,
            "max_tokens": 800,
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(messages_url, headers=headers, json=payload, timeout=30)
        data = response.json()

        if response.status_code == 200:
            # Безопасный парсинг любого формата ответа
            content_blocks = data.get("content", [])
            full_text = ""
            for block in content_blocks:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        full_text += block.get("text", "")
                    elif "text" in block:
                        full_text += block.get("text", "")

            if full_text.strip():
                print(f"✅ Успешно сгенерировано через: {model_name}")
                return full_text.strip()

            print(f"⚠️ Пустой ответ от {model_name}, пробуем следующую...")
        else:
            print(f"   ⚠️ Модель {model_name} не ответила ({response.status_code}): {data}")

    raise RuntimeError("🚨 Не удалось извлечь текст ни из одной доступной модели Claude.")

# ---------------------------------------------------------------------------
# Публикация в Facebook
# ---------------------------------------------------------------------------
def post_to_facebook(text):
    if not FB_ACCESS_TOKEN or not FB_PAGE_ID:
        print("\n--- [ТЕСТОВЫЙ ВЫВОД ПОСТА] ---")
        print(text)
        print("------------------------------\n")
        return True

    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    payload = {
        "message": text,
        "access_token": FB_ACCESS_TOKEN
    }
    response = requests.post(url, data=payload, timeout=30)
    res_data = response.json()

    if response.status_code == 200 and "id" in res_data:
        print(f"✅ Успешно опубликовано в Facebook! ID: {res_data['id']}")
        return True
    else:
        print(f"❌ Ошибка Facebook Graph API: {res_data}")
        return False

# ---------------------------------------------------------------------------
# Главная логика
# ---------------------------------------------------------------------------
def main():
    print("1. Загрузка истории постов...")
    posted = load_posted()

    print("2. Сбор новостей...")
    articles = fetch_recent_articles(hours=12)
    new_articles = [a for a in articles if a["id"] not in posted]

    if not new_articles:
        print("ℹ️ Новых статей не найдено.")
        return

    for article in new_articles[:1]:
        print(f"\n3. Обработка статьи: {article['title']}")
        text = rewrite_with_claude_direct(article)

        success = post_to_facebook(text)
        if success:
            posted.add(article["id"])

    save_posted(posted)
    print("\n🎉 Успешно завершено!")

if __name__ == "__main__":
    main()
