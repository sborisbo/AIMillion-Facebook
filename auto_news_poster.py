#!/usr/bin/env python3
"""
Автоматический генератор новостей и постов для Telegram
Использует Claude API для генерации контента
"""

import os
import re
import json
import time
import random
import requests
from datetime import datetime
from typing import Optional
import anthropic

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")  # e.g., "@ai_na_million"

# Файл для кэширования постов
CACHE_FILE = "posts_cache.json"
LOG_FILE = "posts_log.txt"

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ
# ============================================================================

if not CLAUDE_API_KEY:
    raise ValueError("❌ ОШИБКА: Не найдена переменная окружения ANTHROPIC_API_KEY!")

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


# ============================================================================
# ФУНКЦИИ РАБОТЫ С НОВОСТЯМИ
# ============================================================================

def fetch_raw_news() -> str:
    """
    Собирает свежие новости.
    Можно заменить на реальный парсер (RSS, web scraping, API, и т.д.)
    """
    print("📰 1. Собираем свежие новости...")
    
    # ВАРИАНТ 1: Жестко закодированные новости (для теста)
    news_list = [
        "Google выпустила Gemini 2.0 с улучшенной способностью к многошаговым рассуждениям.",
        "OpenAI обновила GPT-4o с новыми возможностями видеоанализа.",
        "Meta запустила программу для разработчиков с бесплатным доступом к моделям.",
        "Yandex представила новую нейросетевую модель для русского языка.",
        "Anthropic опубликовала исследование о безопасности больших языковых моделей.",
    ]
    
    # Выбираем случайную новость для разнообразия
    news = random.choice(news_list)
    
    # ВАРИАНТ 2: Если хотите парсить реальные новости, раскомментируйте:
    # news = fetch_from_rss()  # или другой источник
    
    print(f"   ✅ Найдена новость: {news[:60]}...")
    return news


def fetch_from_rss() -> str:
    """
    Опциональная функция для парсинга RSS-ленты с новостями об ИИ
    Требует: pip install feedparser
    """
    try:
        import feedparser
        
        # RSS лента с новостями об ИИ на русском
        feed_url = "https://habr.com/ru/rss/hub/ai/feed/"
        feed = feedparser.parse(feed_url)
        
        if feed.entries:
            latest = feed.entries[0]
            return f"{latest.title}: {latest.summary[:200]}"
    except ImportError:
        print("⚠️ feedparser не установлен. Используем встроенные новости.")
    except Exception as e:
        print(f"⚠️ Ошибка при парсинге RSS: {e}")
    
    return "Сегодня в мире ИИ произошли важные события."


# ============================================================================
# ФУНКЦИИ ГЕНЕРАЦИИ КОНТЕНТА ЧЕРЕЗ CLAUDE
# ============================================================================

def generate_post_with_claude(raw_news: str) -> str:
    """
    Генерирует пост через Claude API
    Это основной способ, так как Gemini Free Tier имеет ограничения
    """
    print("🤖 2. Генерируем пост через Claude API...")
    
    prompt = f"""Ты — профессиональный SMM-специалист и эксперт по искусственному интеллекту.

Напиши интересный, вовлекающий пост для Telegram-канала о новостях ИИ.
Требования:
- На русском языке
- 200-400 символов
- Используй эмодзи (2-3 штуки)
- Структурируй текст абзацами (максимум 3 абзаца)
- Добавь призыв к обсуждению в конце (вопрос или "что думаете?")
- Будь оптимистичным и информативным

НОВОСТЬ:
{raw_news}

Напиши ТОЛЬКО пост, без дополнительных комментариев."""

    try:
        print("   📡 Отправляем запрос к Claude...")
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        post_text = message.content[0].text.strip()
        print(f"   ✅ Пост успешно сгенерирован!")
        return post_text
        
    except anthropic.APIError as e:
        print(f"   ❌ Ошибка Claude API: {e}")
        raise


# ============================================================================
# ФУНКЦИИ РАБОТЫ С КЭШЕМ
# ============================================================================

def load_cache() -> dict:
    """Загружает кэш постов из файла"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"posts": []}
    return {"posts": []}


def save_cache(cache: dict):
    """Сохраняет кэш постов в файл"""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def add_to_cache(post_text: str, news: str):
    """Добавляет пост в кэш"""
    cache = load_cache()
    cache["posts"].append({
        "timestamp": datetime.now().isoformat(),
        "news": news,
        "post": post_text,
        "published": False
    })
    save_cache(cache)
    print(f"   💾 Пост добавлен в кэш ({len(cache['posts'])} всего)")


def get_cached_post() -> Optional[str]:
    """Возвращает кэшированный пост, если нет доступа к API"""
    cache = load_cache()
    for item in reversed(cache["posts"]):
        if not item.get("published"):
            return item["post"]
    return None


# ============================================================================
# ФУНКЦИИ ПУБЛИКАЦИИ
# ============================================================================

def publish_to_telegram(post_text: str) -> bool:
    """
    Публикует пост в Telegram канал
    
    Требуется:
    - TELEGRAM_BOT_TOKEN: токен бота от @BotFather
    - TELEGRAM_CHANNEL_ID: ID канала (может быть @username)
    """
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        print("⚠️ Telegram не сконфигурирован. Переходим к локальному сохранению.")
        return False
    
    print("📤 3. Публикуем пост в Telegram...")
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": post_text,
        "parse_mode": "HTML"  # или "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            message_id = data.get("result", {}).get("message_id")
            print(f"   ✅ Пост опубликован! ID сообщения: {message_id}")
            return True
        else:
            print(f"   ❌ Ошибка Telegram API: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Ошибка подключения к Telegram: {e}")
        return False


def publish_to_console(post_text: str):
    """Выводит пост в консоль (для тестирования)"""
    print("\n" + "="*60)
    print("📋 ИТОГОВЫЙ ПОСТ:")
    print("="*60)
    print(post_text)
    print("="*60 + "\n")


def save_to_file(post_text: str, news: str):
    """Сохраняет пост в текстовый файл"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"[{timestamp}]\n")
        f.write(f"НОВОСТЬ: {news}\n")
        f.write(f"ПОСТ:\n{post_text}\n")
        f.write(f"{'='*60}\n")
    
    print(f"   💾 Пост сохранён в файл: {LOG_FILE}")


# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def main():
    """Главная функция скрипта"""
    
    print("\n" + "🚀 "*10)
    print("АВТОМАТИЧЕСКИЙ ГЕНЕРАТОР НОВОСТЕЙ И ПОСТОВ")
    print("🚀 "*10 + "\n")
    
    try:
        # 1. Собираем новости
        raw_news = fetch_raw_news()
        
        # 2. Генерируем пост через Claude
        try:
            final_post = generate_post_with_claude(raw_news)
        except Exception as e:
            print(f"⚠️ Ошибка при генерации: {e}")
            print("   📖 Пробуем использовать кэшированный пост...")
            cached = get_cached_post()
            if cached:
                final_post = cached
                print(f"   ✅ Используем кэшированный пост")
            else:
                print("   ❌ Кэшированные посты не найдены!")
                raise
        
        # 3. Добавляем в кэш
        add_to_cache(final_post, raw_news)
        
        # 4. Публикуем пост
        publish_to_console(final_post)
        
        # Пробуем опубликовать в Telegram
        telegram_success = publish_to_telegram(final_post)
        
        # В любом случае сохраняем в файл
        save_to_file(final_post, raw_news)
        
        # Финальное сообщение
        print("\n✨ " + "="*56 + " ✨")
        if telegram_success:
            print("🎉 ВСЁ УСПЕШНО! Пост опубликован в Telegram")
        else:
            print("⚠️ Пост сгенерирован и сохранён, но Telegram недоступен")
        print("✨ " + "="*56 + " ✨\n")
        
        return 0
        
    except Exception as err:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {err}\n")
        return 1


# ============================================================================
# ЗАПУСК
# ============================================================================

if __name__ == "__main__":
    import sys
    sys.exit(main())
