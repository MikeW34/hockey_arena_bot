import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from game import load_players, get_players_by_position

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я хоккейный бот. Напиши /match чтобы начать матч!")

@dp.message(Command("team"))
async def cmd_team(message: types.Message):
    """Показывает состав команды"""
    players = load_players()
    
    # Группируем по позициям
    goalies = get_players_by_position("вратарь")
    defenders = get_players_by_position("защитник")
    forwards = get_players_by_position("нападающий")
    
    text = "🦅 <b>КРАСНЫЕ ОРЛЫ - СОСТАВ</b>\n\n"
    
    text += "🥅 <b>Вратари:</b>\n"
    for p in goalies:
        text += f"  #{p['number']} {p['name']} {p['surname']}\n"
    
    text += "\n🛡️ <b>Защитники:</b>\n"
    for p in defenders:
        text += f"  #{p['number']} {p['name']} {p['surname']}\n"
    
    text += "\n⚡ <b>Нападающие:</b>\n"
    for p in forwards:
        text += f"  #{p['number']} {p['name']} {p['surname']}\n"
    
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("player"))
async def cmd_player(message: types.Message):
    """Показывает карточку игрока. Использование: /player 10"""
    from game import get_player_by_id
    
    # Проверяем, что message.text существует
    if message.text is None:
        await message.answer("Ошибка: пустое сообщение")
        return
    
    # Получаем ID из команды
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажите номер игрока. Пример: /player 10")
        return
    
    try:
        player_id = int(args[1])
    except ValueError:
        await message.answer("Номер игрока должен быть числом. Пример: /player 10")
        return
    
    player = get_player_by_id(player_id)
    
    if player is None:
        await message.answer("Игрок не найден!")
        return
    
    s = player["stats"]
    text = (
        f"🏒 <b>КАРТОЧКА ИГРОКА</b>\n\n"
        f"#{player['number']} <b>{player['name']} {player['surname']}</b>\n"
        f"📍 {player['position'].capitalize()}\n\n"
        f"📊 <b>Характеристики:</b>\n"
        f"🎯 Бросок: {s['бросок']}\n"
        f"🔄 Пас: {s['пас']}\n"
        f"⚡ Скорость: {s['скорость']}\n"
        f"💪 Сила: {s['сила']}\n"
        f"🫁 Выносливость: {s['выносливость']}"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("match"))
async def cmd_match(message: types.Message):
    await message.answer("Матч начинается! Пока заглушка, но скоро будет игра.")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "/start - Главное меню\n"
        "/match - Начать матч\n"
        "/team - Состав команды\n"
        "/player [ID] - Карточка игрока\n"
        "/help - Помощь"
    )
    await message.answer(help_text, parse_mode="HTML")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())