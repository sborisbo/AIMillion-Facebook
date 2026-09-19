import os
import feedparser
import google.generativeai as genai
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=Artificial+Intelligence&hl=en-US&gl=US&ceid=US:en",
    "https://techcrunch.com/category/artificial-intelligence/feed/"
]

def fetch_top_news():
    articles = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:3]:
            articles.append(f"Заголовок: {entry.title}\nСсылка: {entry.link}\nSummary: {entry.get('summary', '')}")
    return "\n\n---\n\n".join(articles)

def generate_post_with_gemini(news_content):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
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
    
    response = model.generate_content(prompt)
    return response.text

def post_to_facebook_page(post_text):
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    payload = {
        "message": post_text,
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    
    response = requests.post(url, data=payload)
    result = response.json()
    
    if "id" in result:
        print(f"Успешно опубликовано! ID: {result['id']}")
    else:
        print(f"Ошибка Facebook API: {result}")

if __name__ == "__main__":
    print("1. Собираем новости...")
    raw_news = fetch_top_news()
    
    print("2. Генерируем пост через Gemini...")
    final_post = generate_post_with_gemini(raw_news)
    
    print("3. Публикуем в Facebook Page...")
    post_to_facebook_page(final_post)
