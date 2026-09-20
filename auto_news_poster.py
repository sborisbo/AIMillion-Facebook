import os
import time
import feedparser
from google import genai
from google.genai import types
from google.genai.errors import ServerError, APIError
import requests

# Чтение ключей из секретов GitHub
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_GROUP_ID = os.getenv("FB_GROUP_ID")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")

# RSS-ленты новостей
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=Artificial+Intelligence&hl=en-US&gl=US&ceid=US:en",
    "https://techcrunch.com/category/artificial-intelligence/feed/"
]

def fetch_top_news():
    """Сбор свежих новостей из RSS-лент."""
    articles = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:3]:
            articles.append(f"Заголовок: {entry.title}\nСсылка: {entry.link}\nSummary: {entry.get('summary', '')}")
    return "\n\n---\n\n".join(articles)

def generate_post_with_gemini(news_content):
    """Генерация поста через Gemini API с обработкой перегрузки."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    Ты — ведущий популярного сообщества "ИИ на Миллион".
    Вот свежие новости об ИИ из RSS-лент:
    
    {news_content}
    
    Напиши увлекательный и структурированный пост на русском языке для Facebook.
    Требования к посту:
    1. Цепляющий заголовок с эмодзи.
    2. Краткий разбор 2-3 самых интересных новостей.
    3. Призыв к обсуждению или вопрос в конце для вовлечения подписчиков.
    4. Пиши простым текстом с эмодзи и переносами строк, без символов Markdown (без # и без **).
    """
    
    models_to_try = ['gemini-3.6-flash', 'gemini-2.5-flash']
    
    for model_name in models_to_try:
        for attempt in range(3):
            try:
                print(f"Запрос к {model_name} (попытка {attempt + 1})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[]
                    )
                )
                return response.text
            except (ServerError, APIError) as e:
                print(f"Сервер перегружен ({e}). Ждем 5 секунд...")
                time.sleep(5)
    
    raise RuntimeError("Все модели Gemini перегружены или недоступны.")

def post_to_page(post_text):
    """Публикация поста на Facebook Page."""
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    payload = {
        "message": post_text,
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    
    response = requests.post(url, data=payload)
    result = response.json()
    
    if "id" in result:
        print(f"Успешно опубликовано на Странице! Post ID: {result['id']}")
        return result['id']
    else:
        print(f"Ошибка публикации на Странице: {result}")
        return None

def share_post_to_group(post_id):
    """Шеринг (перепост) публикации со страницы в группу."""
    url = f"https://graph.facebook.com/v19.0/{FB_GROUP_ID}/feed"
    
    # Ссылка на исходный пост страницы
    post_link = f"https://www.facebook.com/{post_id}"
    
    payload = {
        "link": post_link,
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    
    response = requests.post(url, data=payload)
    result = response.json()
    
    if "id" in result:
        print(f"Успешно расшарено в Группу! Share ID: {result['id']}")
    else:
        print(f"Ошибка при шеринге в Группу: {result}")

if __name__ == "__main__":
    print("1. Собираем свежие новости...")
    raw_news = fetch_top_news()
    
    print("2. Генерируем пост через Gemini API...")
    final_post = generate_post_with_gemini(raw_news)
    
    print("3. Публикуем на Facebook Page...")
    page_post_id = post_to_page(final_post)
    
    if page_post_id and FB_GROUP_ID:
        print("4. Делимся постом в Facebook Group...")
        share_post_to_group(page_post_id)
