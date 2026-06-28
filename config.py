import os
from dotenv import load_dotenv

load_dotenv()

def get_token() -> str:
    """Получает токен из .env и проверяет, что он есть"""
    token = os.getenv("BOT_TOKEN")
    if token is None:
        raise ValueError(
            "❌ Токен бота не найден!\n"
            "Проверьте, что в папке проекта есть файл .env\n"
            "и в нём написано: BOT_TOKEN=ваш_токен_сюда"
        )
    return token

BOT_TOKEN = get_token()