import os
import time
import google.genai as genai
from google.genai import types

# ---------------------------------------------------------------------------
# Настройка клиента Gemini API
# ---------------------------------------------------------------------------
# Ожидается, что GEMINI_API_KEY передан в переменные окружения (например, через GitHub Secrets)
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Не найдена переменная окружения GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


def fetch_raw_news() -> str:
    """
    1. Собираем свежие новости.
    Замените этот блок или функцию своей логикой сбора новостей (RSS, парсинг и т.д.).
    """
    print("1. Собираем свежие новости...")
    # Имитация сбора данных для примера
    sample_news = (
        "Сегодня ИИ-лаборатории анонсировали новые мультимодальные модели, "
        "способные решать сложные логические задачи с высокой точностью. "
        "Также появились обновления в библиотеках автоматизации."
    )
    return sample_news


def generate_post_with_gemini(raw_news: str) -> str:
    """
    2. Генерируем пост через Gemini API с обработкой ошибок и fallback-моделями.
    """
    print("2. Генерируем пост через Gemini API...")

    # Актуальный список моделей (заменили устаревшую 2.5-flash на 3.8-flash)
    models_to_try = [
        "gemini-3.6-flash",
        "gemini-3.8-flash",
        "gemini-1.5-flash"
    ]

    prompt = (
        "Ты — профессиональный SMM-специалист и эксперт по ИИ.\n"
        "На основе следующих сырых новостей напиши вовлекающий, структурированный "
        "и интересный пост для Facebook и Telegram на русском языке. "
        "Используй эмодзи, абзацы и призыв к обсуждению.\n\n"
        f"Сырые новости:\n{raw_news}"
    )

    max_attempts_per_model = 3

    for model_name in models_to_try:
        for attempt in range(1, max_attempts_per_model + 1):
            try:
                print(f"Запрос к {model_name} (попытка {attempt})...")

                # Использование чат-сессии предотвращает предупреждение о Direct AFC в generate_content
                chat = client.chats.create(model=model_name)
                response = chat.send_message(prompt)

                if response and response.text:
                    print(f"Успешно сгенерировано с помощью {model_name}!")
                    return response.text.strip()

            except Exception as e:
                error_str = str(e)
                # Вычисляем нарастающую паузу: 5s, 10s, 15s
                wait_time = attempt * 5
                
                print(f"Ошибка при обращении к {model_name}: {error_str}")
                
                if attempt < max_attempts_per_model:
                    print(f"Ждем {wait_time} секунд перед следующей попыткой...")
                    time.sleep(wait_time)
                else:
                    print(f"Модель {model_name} недоступна после {max_attempts_per_model} попыток. Переходим к следующей модели...\n")

    raise RuntimeError("Все модели Gemini перегружены или недоступны.")


def publish_to_facebook(post_text: str):
    """
    3. Публикуем сгенерированный пост в Facebook / Telegram.
    Замените здесь код на вашу логику работы с Facebook Graph API / Telegram Bot API.
    """
    print("3. Публикация поста...")
    print("---------------- ИТОГОВЫЙ ПОСТ ----------------")
    print(post_text)
    print("-----------------------------------------------")
    # Здесь добавляется ваш код отправки через requests / facebook-sdk


if __name__ == "__main__":
    try:
        raw_news = fetch_raw_news()
        final_post = generate_post_with_gemini(raw_news)
        publish_to_facebook(final_post)
        print("Скрипт успешно завершил работу.")
    except Exception as err:
        print(f"Критическая ошибка выполнения скрипта: {err}")
        exit(1)
