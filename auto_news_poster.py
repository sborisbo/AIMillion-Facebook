import os
import requests

def fetch_raw_news() -> str:
    print("1. Собираем свежие новости...")
    return (
        "Сегодня анонсированы новые обновления в сфере искусственного интеллекта. "
        "Разработчики фокусируются на повышении стабильности работы агентов и "
        "автоматизации бизнес-процессов."
    )

def generate_post_with_groq(prompt: str) -> str:
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        print("⚠️ Ошибка: GROQ_API_KEY не найден в GitHub Secrets.")
        return None

    print("2. Генерируем пост через Groq (Llama-3.3-70b)...")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Ты профессиональный SMM-специалист и эксперт по ИИ."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            text = data['choices'][0]['message']['content']
            print("✅ УСПЕХ: Пост успешно сгенерирован!")
            return text.strip()
        else:
            print(f"⚠️ Ошибка Groq API ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"⚠️ Сетевая ошибка при запросе к Groq: {e}")

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
            "На основе следующих новостей напиши вовлекающий, структурированный "
            "и интересный пост для Facebook и Telegram на русском языке. "
            "Используй эмодзи, абзацы и призыв к обсуждению.\n\n"
            f"Новости:\n{raw_news}"
        )

        final_post = generate_post_with_groq(prompt)
        
        if not final_post:
            raise RuntimeError("🚨 Не удалось сгенерировать пост через Groq.")

        publish_to_facebook(final_post)
        print("\n🎉 Скрипт успешно завершил работу!")

    except Exception as err:
        print(f"\n💥 Критическая ошибка: {err}")
        exit(1)
