import os
import time
import random
from google import genai
from google.genai.errors import APIError

# ---------------------------------------------------------------------------
# Инициализация API Ключа
# ---------------------------------------------------------------------------
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("ОШИБКА: Не найдена переменная окружения GEMINI_API_KEY!")

client = genai.Client(api_key=api_key)


def fetch_raw_news() -> str:
    print("1. Собираем свежие новости...")
    return (
        "Сегодня анонсировали новые обновления в сфере искусственного интеллекта. "
        "Модели стали быстрее и эффективнее в решении повседневных задач автоматизации."
    )


def generate_post_with_gemini(raw_news: str) -> str:
    print("2. Генерируем пост через Gemini API...")

    # ТОЧНЫЕ АКТУАЛЬНЫЕ МОДЕЛИ, КОТОРЫЕ ТРЕБУЕТ GOOGLE API
    models_to_try = [
        "gemini-3.8-flash",
        "gemini-2.0-flash",
        "gemini-3.1-pro-preview",
    ]

    prompt = (
        "Ты — профессиональный SMM-специалист и эксперт по ИИ.\n"
        "На основе следующих новостей напиши вовлекающий, структурированный "
        "и интересный пост для Facebook и Telegram на русском языке. "
        "Используй эмодзи, абзацы и призыв к обсуждению.\n\n"
        f"Новости:\n{raw_news}"
    )

    max_attempts = 3

    for model_name in models_to_try:
        print(f"\n---> Пробуем модель: {model_name}")
        
        for attempt in range(1, max_attempts + 1):
            try:
                print(f"Запрос к {model_name} (попытка {attempt} из {max_attempts})...")

                # Используем chat.send_message вместо models.generate_content:
                # Это убирает предупреждение AFC и более устойчиво к таймаутам
                chat = client.chats.create(model=model_name)
                response = chat.send_message(prompt)

                if response and response.text:
                    print(f"✅ УСПЕХ! Пост сгенерирован с помощью {model_name}.")
                    return response.text.strip()

            except APIError as e:
                error_msg = str(e)
                print(f"⚠️ Ошибка Gemini API ({model_name}): {error_msg}")

                # Если модель не найдена (404), сразу переходим к следующей модели
                if "404" in error_msg or "NOT_FOUND" in error_msg:
                    print(f"❌ Модель {model_name} недоступна (404). Пропускаем...")
                    break

                # При перегрузке (503 / 429 / UNAVAILABLE) делаем паузу
                if attempt < max_attempts:
                    wait_time = (attempt * 15) + random.randint(3, 7)
                    print(f"⏳ Сервер перегружен. Ждём {wait_time} секунд...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Модель {model_name} исчерпала все попытки.")

            except Exception as e:
                print(f"⚠️ Непредвиденная ошибка с {model_name}: {e}")
                break

    raise RuntimeError("🚨 Все актуальные модели Gemini временно недоступны из-за высокой нагрузки.")


def publish_to_facebook(post_text: str):
    print("\n3. Публикация поста...")
    print("------------------- ИТОГОВЫЙ ПОСТ -------------------")
    print(post_text)
    print("-----------------------------------------------------")


if __name__ == "__main__":
    try:
        raw_news = fetch_raw_news()
        final_post = generate_post_with_gemini(raw_news)
        publish_to_facebook(final_post)
        print("\n🎉 Скрипт успешно завершил работу!")
    except Exception as err:
        print(f"\n💥 Критическая ошибка: {err}")
        exit(1)
