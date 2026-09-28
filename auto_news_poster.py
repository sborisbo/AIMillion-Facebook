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

def generate_post_with_gemini(prompt: str) -> str:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        print("⚠️ GEMINI_API_KEY не найден в GitHub Secrets.")
        return None

    print("2. Генерируем пост через Google Gemini...")

    # Модели Gemini для бесплатного тарифа (от более легких к тяжелым)
    models = ["gemini-2.5-flash", "gemini-3.8-flash"]
    
    for model in models:
        print(f"--> Пробуем модель: {model}")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        # Делаем до 5 попыток с паузой, если сервер Google занят (503)
        for attempt in range(1, 6):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    text = data['candidates'][0]['content']['parts'][0]['text']
                    print(f"✅ УСПЕХ: Пост сгенерирован через {model}!")
                    return text.strip()
                
                elif response.status_code in [503, 429]:
                    wait_time = attempt * 5 + random.randint(2, 5)
                    print(f"   ⏳ Сервер занят (код {response.status_code}). Попытка {attempt}/5, ждем {wait_time} сек...")
                    time.sleep(wait_time)
                else:
                    print(f"   ⚠️ Ошибка API ({response.status_code}): {response.text[:150]}")
                    break
            except Exception as e:
                print(f"   ⚠️ Ошибка сети: {e}")
                time.sleep(3)

    return None

def publish_to_facebook(post_text: str):
    print("\n3. Публикация поста...")
    print("------------------- ИТОГОВЫЙ ПОСТ -------------------")
    print(post_text)
    print("-----------------------------------------------------")

if __name__ == "__main__":
    try:
        raw_news = fetch_raw_news()
        
        prompt = (
            "Ты — профессиональный SMM-специалист и эксперт по ИИ.\n"
            "На основе следующих новостей напиши вовлекающий, структурированный "
            "и интересный пост для Facebook и Telegram на русском языке. "
            "Используй эмодзи, абзацы и призыв к обсуждению.\n\n"
            f"Новости:\n{raw_news}"
        )

        final_post = generate_post_with_gemini(prompt)
        
        if not final_post:
            raise RuntimeError("🚨 Gemini не ответил после всех попыток.")

        publish_to_facebook(final_post)
        print("\n🎉 Скрипт успешно завершил работу!")

    except Exception as err:
        print(f"\n💥 Критическая ошибка: {err}")
        exit(1)
