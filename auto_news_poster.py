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
        return None

    from google import genai
    from google.genai.errors import APIError
    
    client = genai.Client(api_key=gemini_key)
    model_name = "gemini-3.8-flash"  # Единственная корректная модель для нового SDK
    
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"--> [Gemini] Пробуем {model_name} (попытка {attempt}/{max_attempts})...")
            chat = client.chats.create(model=model_name)
            response = chat.send_message(prompt)
            if response and response.text:
                print("✅ УСПЕХ (Gemini API)!")
                return response.text.strip()
        except APIError as e:
            err_text = str(e)
            print(f"   ⚠️ Ошибка Gemini (503/лимит): {err_text[:100]}...")
            if attempt < max_attempts:
                wait_time = attempt * 15 + random.randint(3, 7)
                print(f"   ⏳ Ждем {wait_time} секунд перед повтором...")
                time.sleep(wait_time)
        except Exception as e:
            print(f"   ⚠️ Непредвиденная ошибка Gemini: {e}")
            break
            
    return None

def generate_post_with_groq(prompt: str) -> str:
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        return None

    print("\n---> 🚀 Переключаемся на резервный Groq API (Llama-3.3-70b)...")
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
            print("✅ УСПЕХ (Groq API)!")
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

    # 1. Сначала пробуем официальный Gemini
    result = generate_post_with_gemini(prompt)
    if result:
        return result

    # 2. Если Gemini выдал 503, бесшовно подключаем Groq
    result = generate_post_with_groq(prompt)
    if result:
        return result

    raise RuntimeError("🚨 Не удалось сгенерировать пост: все провайдеры недоступны.")

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
