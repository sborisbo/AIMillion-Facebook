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
        print("⚠️ GEMINI_API_KEY не найден в переменной окружения.")
        return None

    from google import genai
    client = genai.Client(api_key=gemini_key)
    
    # Список моделей, доступных в новом SDK на разных серверах
    candidate_models = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-3.8-flash"
    ]

    for model_name in candidate_models:
        print(f"--> [Gemini] Пробуем модель: {model_name}")
        for attempt in range(1, 3):
            try:
                chat = client.chats.create(model=model_name)
                response = chat.send_message(prompt)
                if response and response.text:
                    print(f"✅ УСПЕХ (Gemini {model_name})!")
                    return response.text.strip()
            except Exception as e:
                err_text = str(e)
                print(f"   ⚠️ Ошибка на {model_name} (попытка {attempt}): {err_text[:110]}...")
                if "404" in err_text or "NOT_FOUND" in err_text:
                    break  # Если модель не найдена, сразу переходим к следующей
                time.sleep(attempt * 5 + random.randint(2, 5))
                
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

def generate_post_with_openrouter(prompt: str) -> str:
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if not openrouter_key:
        return None

    print("\n---> 🌐 Переключаемся на бесплатный OpenRouter API...")
    try:
        import requests
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {openrouter_key}"},
            json={
                "model": "google/gemini-2.5-flash:free",
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        res_json = response.json()
        if "choices" in res_json and len(res_json["choices"]) > 0:
            print("✅ УСПЕХ (OpenRouter API)!")
            return res_json["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"   ⚠️ Ошибка OpenRouter API: {e}")

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

    # 1. Основная попытка — ротация моделей Gemini (2.5-flash, 2.5-flash-lite, 2.0-flash)
    result = generate_post_with_gemini(prompt)
    if result:
        return result

    # 2. Резерв №1 — Groq (если добавлен GROQ_API_KEY)
    result = generate_post_with_groq(prompt)
    if result:
        return result

    # 3. Резерв №2 — OpenRouter (если добавлен OPENROUTER_API_KEY)
    result = generate_post_with_openrouter(prompt)
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
