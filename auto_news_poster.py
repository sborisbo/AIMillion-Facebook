import os
import json
import hashlib
import requests
import feedparser
import anthropic
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Environment Variables
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")

POSTED_FILE = "posted_ids.json"

# RSS Feed sources
try:
    from feeds import RSS_FEEDS
except ImportError:
    RSS_FEEDS = [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://news.ycombinator.com/rss",
    ]

# ---------------------------------------------------------------------------
# Deduplication Logic
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
# RSS Article Fetcher
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
# Claude Post Generation (Anthropic API with fallback model names)
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

    models_to_try = [
        "claude-3-5-sonnet-20240620",
        "claude-3-haiku-20240307",
        "claude-3-opus-20240229"
    ]

    for model_name in models_to_try:
        try:
            response = client.messages.create(
                model=model_name,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            print(f"✅ Successfully generated post using model: {model_name}")
            return response.content[0].text.strip()
        except anthropic.NotFoundError:
            print(f"⚠️ Model {model_name} not found on this account, trying next...")
            continue

    raise RuntimeError("🚨 None of the specified Claude models are available for this API key.")

# ---------------------------------------------------------------------------
# Facebook Page Publishing (Graph API)
# ---------------------------------------------------------------------------
def post_to_facebook(text):
    if not FB_ACCESS_TOKEN or not FB_PAGE_ID:
        print("\n--- [TEST MODE: Facebook secrets not set] ---")
        print(text)
        print("---------------------------------------------\n")
        return True

    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    payload = {
        "message": text,
        "access_token": FB_ACCESS_TOKEN
    }
    response = requests.post(url, data=payload, timeout=30)
    res_data = response.json()
    
    if response.status_code == 200 and "id" in res_data:
        print(f"✅ Successfully posted to Facebook! Post ID: {res_data['id']}")
        return True
    else:
        print(f"❌ Facebook Graph API Error: {res_data}")
        return False

# ---------------------------------------------------------------------------
# Main Execution Flow
# ---------------------------------------------------------------------------
def main():
    print("1. Loading posted articles history...")
    posted = load_posted()
    
    print("2. Fetching fresh news from RSS feeds...")
    articles = fetch_recent_articles(hours=12)
    new_articles = [a for a in articles if a["id"] not in posted]

    if not new_articles:
        print("ℹ️ No new articles found in the last 12 hours.")
        return

    for article in new_articles[:1]:
        print(f"\n3. Processing article: {article['title']}")
        text = rewrite_with_claude(article)
        
        success = post_to_facebook(text)
        if success:
            posted.add(article["id"])

    save_posted(posted)
    print("\n🎉 Process completed successfully!")

if __name__ == "__main__":
    main()
