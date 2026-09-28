import os
import time
import random

# ---------------------------------------------------------------------------
# 1. Сбор новостей
# ---------------------------------------------------------------------------
def fetch_raw_news() -> str:
    print("1. Собираем свежие новости...")
    return (
        "Сегодня анонсированы новые обновления в сфере искусственного интеллекта. "
        "Разработчики фокусируются на повышении стабильности работы агентов и "
        "автоматизации бизнес-процессов."
    )


# ---------------------------------------------------------------------------
# 2. Генерация через Gemini (Мульти-модельный ротатор)
# ---------------------------------------------------------------------------
def try_gemini_generation(prompt: str) -> str:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        print("⚠️ Переменная GEMINI_API_KEY не найдена.")
        return None

    # Полный список моделей для бесплатного тарифа (от новых к классическим)
    candidate_models = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash",
    ]

    # Попытка №1: Новый Google GenAI SDK (google.genai)
    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
        
        for model_name in candidate_models:
            print(f"--> [Gemini SDK] Пробуем модель: {model_name}")
            for attempt in range(1, 3):
                try:
                    chat = client.chats.create(model=model_name)
                    response = chat.send_message(prompt)
                    if response and response.text:
                        print(f"✅ УСПЕХ (Gemini {model_name})!")
                        return response.text.strip()
                except Exception as e:
                    err_text = str(e)
                    if "404" in err_text or "NOT_FOUND" in err_text or "limit: 0" in err_text:
                        print(f"   Пропускаем {model_name} (недоступна на этом эндпоинте).")
                        break
                    print(f"   Ошибка (попытка {attempt}): {err_text[:120]}...")
                    time.sleep(attempt * 4 + random.randint(1, 3))
    except Exception as e:
        print(f"⚠️ Ошибка инициализации google-genai SDK: {e}")

    # Попытка №2: Старый legacy SDK (google.generativeai) — шлёт на другой эндпоинт v1/v1beta
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=gemini_key)

        for model_name in candidate_models:
            print(f"--> [Legacy SDK] Пробуем модель: {model_name}")
            try:
                model = legacy_genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                if response and response.text:
                    print(f"✅ УСПЕХ (Legacy Gemini {model_name})!")
                    return response.text.strip()
            except Exception as e:
                print(f"   Legacy ошибка на {model_name}: {str(e)[:120]}...")
                continue
    except Exception as e:
        print(f"⚠️ Legacy SDK недоступен: {e}")

    return None


# ---------------------------------------------------------------------------
# 3. Бесплатный Резерв (Groq / Llama 3.3) — 100% зашита от сбоев
# ---------------------------------------------------------------------------
def try_groq_generation(prompt: str) -> str:
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        return None

    print("\n---> 🚀 Подключаем бесплатный резервный API (Groq Llama-3.3-70b)...")
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
        print(f"⚠️ Ошибка Groq API: {e}")

    return None


# ---------------------------------------------------------------------------
# Главная логика генерации
# ---------------------------------------------------------------------------
def generate_post(raw_news: str) -> str:
    print("2. Генерируем пост...")

    prompt = (
        "Ты — профессиональный SMM-специалист и эксперт по ИИ.\n"
        "На основе следующих новостей напиши вовлекающий, структурированный "
        "и интересный пост для Facebook и Telegram на русском языке. "
        "Используй эмодзи, абзацы и призыв к обсуждению.\n\n"
        f"Новости:\n{raw_news}"
    )

    # Шаг A: Пробуем Gemini через все возможные модели и SDK
    result = try_gemini_generation(prompt)
    if result:
        return result

    # Шаг B: Если Gemini подвёл из-за 503 на серверах Google, используем Groq
    result = try_groq_generation(prompt)
    if result:
        return result

    raise RuntimeError("🚨 Все доступные бесплатные провайдеры перегружены.")


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
