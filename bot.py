import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from config import BOT_TOKEN
from game import load_players, get_players_by_position

load_dotenv()

# Получаем токен из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logging.error("BOT_TOKEN не найден в переменных окружения!")
    sys.exit(1)

# Импортируем функции из game.py
from game import load_players, get_players_by_position, get_player_by_id

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Создаем экземпляры бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start - приветствие"""
    await message.answer(
        "🏒 Привет! Я хоккейный бот команды «Чёрные Вороны»!\n\n"
        "Доступные команды:\n"
        "/match - Начать матч\n"
        "/team - Состав команды\n"
        "/player [номер] - Карточка игрока\n"
        "/help - Помощь"
    )


@dp.message(Command("team"))
async def cmd_team(message: types.Message):
    """Показывает состав команды"""
    try:
        players = load_players()
        
        # Группируем по позициям
        goalies = get_players_by_position(players, "вратарь")
        defenders = get_players_by_position(players, "защитник")
        forwards = get_players_by_position(players, "нападающий")
        
        text = "🦅 <b>ЧЁРНЫЕ ВОРОНЫ - СОСТАВ</b>\n\n"
        
        if goalies:
            text += "🥅 <b>Вратари:</b>\n"
            for p in goalies:
                text += f"  #{p['number']} {p['name']} {p['surname']}\n"
        
        if defenders:
            text += "\n🛡️ <b>Защитники:</b>\n"
            for p in defenders:
                text += f"  #{p['number']} {p['name']} {p['surname']}\n"
        
        if forwards:
            text += "\n⚡ <b>Нападающие:</b>\n"
            for p in forwards:
                text += f"  #{p['number']} {p['name']} {p['surname']}\n"
        
        text += f"\n👨‍🏫 Тренер: Ивашка Тупоголовый"
        
        await message.answer(text, parse_mode="HTML")
    
    except Exception as e:
        logging.error(f"Ошибка в /team: {e}")
        await message.answer("❌ Произошла ошибка при загрузке состава. Попробуйте позже.")


@dp.message(Command("player"))
async def cmd_player(message: types.Message):
    """Показывает карточку игрока. Использование: /player 10"""
    try:
        # Получаем ID из команды
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "❌ Укажите номер игрока.\n"
                "Пример: /player 10"
            )
            return
        
        try:
            player_id = int(args[1])
        except ValueError:
            await message.answer(
                "❌ Номер игрока должен быть числом.\n"
                "Пример: /player 10"
            )
            return
        
        players = load_players()
        player = get_player_by_id(players, player_id)
        
        if player is None:
            await message.answer("❌ Игрок с таким номером не найден!")
            return
        
        s = player["stats"]
        
        # Определяем эмодзи для позиции
        position_emoji = {
            "вратарь": "🥅",
            "защитник": "🛡️",
            "нападающий": "⚡"
        }.get(player["position"], "🏒")
        
        text = (
            f"🏒 <b>КАРТОЧКА ИГРОКА</b>\n\n"
            f"{position_emoji} #{player['number']} "
            f"<b>{player['name']} {player['surname']}</b>\n"
            f"📍 {player['position'].capitalize()}\n\n"
            f"📊 <b>Характеристики:</b>\n"
            f"🎯 Бросок: {s['бросок']}\n"
            f"🔄 Пас: {s['пас']}\n"
            f"⚡ Скорость: {s['скорость']}\n"
            f"💪 Сила: {s['сила']}\n"
            f"🫁 Выносливость: {s['выносливость']}"
        )
        await message.answer(text, parse_mode="HTML")
    
    except Exception as e:
        logging.error(f"Ошибка в /player: {e}")
        await message.answer("❌ Произошла ошибка при загрузке игрока. Попробуйте позже.")


@dp.message(Command("match"))
async def cmd_match(message: types.Message):
    """Команда /match - начало матча"""
    await message.answer(
        "🏒 <b>МАТЧ НАЧИНАЕТСЯ!</b>\n\n"
        "Команда «Чёрные Вороны» выходит на лёд!\n"
        "Скоро здесь появится симуляция матча.\n\n"
        "⏳ Функция в разработке..."
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Команда /help - помощь"""
    help_text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "/start - Главное меню\n"
        "/match - Начать матч\n"
        "/team - Состав команды\n"
        "/player [номер] - Карточка игрока\n"
        "/help - Помощь\n\n"
        "🏒 <b>Чёрные Вороны</b>\n"
        "👨‍🏫 Тренер: Ивашка Тупоголовый"
    )
    await message.answer(help_text, parse_mode="HTML")


@dp.message()
async def unknown_command(message: types.Message):
    """Обработка неизвестных команд"""
    await message.answer(
        "❌ Неизвестная команда.\n"
        "Используйте /help для списка доступных команд."
    )


async def main():
    """Главная функция запуска бота"""
    logging.info("Бот запускается...")
    
    # Удаляем вебхук и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Webhook удален")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
        raise
    finally:
        await bot.session.close()
        logging.info("Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        sys.exit(1)
