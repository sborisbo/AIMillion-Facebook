import os
import time
import random
import requests

def fetch_raw_news() -> str:
    print("1. Собираем свежие новости...")
    return (
        "Сегодня анонсированы новые обновления в сфере искусственного интеллекта. "
        "Разработчики фокусируются на повышении стабильности работы агентов и "
        "автоматизации бизнес-процессов."
    )

def generate_with_direct_gemini_api(prompt: str) -> str:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        print("⚠️ GEMINI_API_KEY не найден в переменных окружения.")
        return None

    # Список ВСЕХ возможных алиасов Gemini на бесплатном тарифе
    # Они обслуживаются РАЗНЫМИ пулами серверов Google
    models_to_try = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.5-flash",
        "gemini-3.8-flash"
    ]

    for model in models_to_try:
        print(f"--> [Direct REST API] Пробуем модель: {model}")
        
        # Используем прямой REST endpoint, чтобы обнулить баги SDK
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        for attempt in range(1, 3):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                data = response.json()

                if response.status_code == 200:
                    text = data['candidates'][0]['content']['parts'][0]['text']
                    print(f"✅ УСПЕХ (Модель: {model})!")
                    return text.strip()

                # Если модель не найдена (404) — сразу берем следующую
                if response.status_code == 404:
                    print(f"   Пропускаем {model} (404 Not Found).")
                    break

                # Если сервер перегружен (503) или лимит (429)
                if response.status_code in [503, 429]:
                    print(f"   ⚠️ Ошибка {response.status_code} на {model} (Попытка {attempt})...")
                    time.sleep(attempt * 4 + random.randint(1, 3))
                else:
                    print(f"   ⚠️ Ошибка API ({response.status_code}): {data}")
                    break

            except Exception as e:
                print(f"   ⚠️ Сетевая ошибка: {e}")
                time.sleep(3)

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

    result = generate_with_direct_gemini_api(prompt)
    if result:
        return result

    raise RuntimeError("🚨 Все модели Gemini временно недоступны из-за высокой нагрузки Google.")

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
