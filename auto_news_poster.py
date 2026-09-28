import os
import time
import random

def fetch_raw_news() -> str:
    print("1. Собираем свежие новости...")
    return (
        "Сегодня анонсированы новые обновления в сфере искусственного интеллекта. "
        "Разработчики фокусируются на повышении стабильности работы агентов и "
        "автоматизации бизнес-процессов."
    )

def generate_post_with_gemini(prompt: str) -> str:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        print("⚠️ GEMINI_API_KEY не найден.")
        return None

    from google import genai
    client = genai.Client(api_key=gemini_key)
    
    # Модель gemini-3.8-flash — единственная актуальная в новом SDK
    model_name = "gemini-3.8-flash"
    max_attempts = 4

    for attempt in range(1, max_attempts + 1):
        print(f"--> [Gemini] Пробуем {model_name} (попытка {attempt}/{max_attempts})...")
        try:
            chat = client.chats.create(model=model_name)
            response = chat.send_message(prompt)
            if response and response.text:
                print("✅ УСПЕХ (Gemini API)!")
                return response.text.strip()
        except Exception as e:
            err_text = str(e)
            print(f"   ⚠️ Ошибка Gemini (503/High Demand): {err_text[:110]}...")
            if attempt < max_attempts:
                wait_time = attempt * 10 + random.randint(2, 5)
                print(f"   ⏳ Сервер перегружен. Ждем {wait_time} сек перед повтором...")
                time.sleep(wait_time)

    return None

def generate_post_with_groq(prompt: str) -> str:
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        print("⚠️ GROQ_API_KEY не установлен в Secrets. Резервный провайдер пропущен.")
        return None

    print("\n---> 🚀 Переключаемся на бесплатный Groq API (Llama-3.3-70b)...")
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Ты профессиональный SMM-редактор."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        if response and response.choices:
            print("✅ УСПЕХ (Groq API — Llama 3.3)!")
            return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"   ⚠️ Ошибка Groq API: {e}")

    return None

def generate_post(raw_news: str) -> str:
    print("2. Генерируем пост...")

    prompt = (
        "Ты — профессиональный SMM-специалист и эксперт по ИИ.\n"
        "На основе следующих новостей напиши вовлекающий, структурированный "
        "и интересный пост для Facebook и Telegram на русском языке. "
        "Используй эмодзи, абзацы и призыв к обсуждению.\n\n"
        f"Новости:\n{raw_news}"
    )

    # 1. Попытка через Gemini
    result = generate_post_with_gemini(prompt)
    if result:
        return result

    # 2. Мгновенный перехват через Groq (если Gemini выдает 503)
    result = generate_post_with_groq(prompt)
    if result:
        return result

    raise RuntimeError("🚨 Все провайдеры недоступны. Добавьте GROQ_API_KEY в Secrets для 100% защиты.")

def publish_to_facebook(post_text: str):
    print("\n3. Публикация поста...")
    print("------------------- ИТОГОВЫЙ ПОСТ -------------------")
    print(post_text)
    print("-----------------------------------------------------")

if __name__ == "__main__":
    try:
        raw_news = fetch_raw_news()
        final_post = generate_post(raw_news)
        publish_to_facebook(final_post)
        print("\n🎉 Скрипт успешно завершил работу!")
    except Exception as err:
        print(f"\n💥 Критическая ошибка: {err}")
        exit(1)
