import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from config import BOT_TOKEN
from game import load_players, get_players_by_position, get_player_by_id, load_team_by_name

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Проверка токена
if not BOT_TOKEN:
    logging.error("BOT_TOKEN не найден в переменных окружения!")
    sys.exit(1)

# Создаем экземпляры бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния для выбора команды
class TeamChoice(StatesGroup):
    selecting = State()

# Клавиатура для выбора команды
def get_team_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🦅 Чёрные Вороны", callback_data="team_black"),
            InlineKeyboardButton(text="🦅 Красные Орлы", callback_data="team_red")
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
        ]
    ])
    return keyboard

# Функция для отображения состава команды
async def show_team(message: types.Message, team_name: str):
    """Показывает состав выбранной команды"""
    try:
        team_data = load_team_by_name(team_name)
        if not team_data:
            await message.answer(f"❌ Команда '{team_name}' не найдена!")
            return
        
        players = team_data.get('players', [])
        team_name_display = team_data.get('team_name', team_name)
        coach = team_data.get('coach', 'Неизвестно')
        
        # Группируем по позициям
        goalies = get_players_by_position(players, "вратарь")
        defenders = get_players_by_position(players, "защитник")
        forwards = get_players_by_position(players, "нападающий")
        
        # Выбираем эмодзи для команды
        icon = "🦅"
        
        text = f"{icon} <b>{team_name_display.upper()} - СОСТАВ</b>\n\n"
        
        if goalies:
            text += "🥅 <b>Вратари:</b>\n"
            for p in goalies:
                # ИСПРАВЛЕНО: проверяем наличие фамилии
                surname = p.get('surname', '')
                if surname:
                    text += f"  #{p['number']} {p['name']} {surname}\n"
                else:
                    text += f"  #{p['number']} {p['name']}\n"
        
        if defenders:
            text += "\n🛡️ <b>Защитники:</b>\n"
            for p in defenders:
                # ИСПРАВЛЕНО: проверяем наличие фамилии
                surname = p.get('surname', '')
                if surname:
                    text += f"  #{p['number']} {p['name']} {surname}\n"
                else:
                    text += f"  #{p['number']} {p['name']}\n"
        
        if forwards:
            text += "\n⚡ <b>Нападающие:</b>\n"
            for p in forwards:
                # ИСПРАВЛЕНО: проверяем наличие фамилии
                surname = p.get('surname', '')
                if surname:
                    text += f"  #{p['number']} {p['name']} {surname}\n"
                else:
                    text += f"  #{p['number']} {p['name']}\n"
        
        text += f"\n👨‍🏫 Тренер: {coach}"
        
        # Добавляем кнопку для просмотра другой команды
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Показать другую команду", callback_data="show_teams")
            ]
        ])
        
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    
    except Exception as e:
        logging.error(f"Ошибка в show_team: {e}")
        await message.answer("❌ Произошла ошибка при загрузке состава. Попробуйте позже.")

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Команда /start - приветствие"""
    await state.set_state(TeamChoice.selecting)
    await message.answer(
        "🏒 <b>Добро пожаловать в хоккейный бот!</b>\n\n"
        "Выберите команду, чтобы просмотреть её состав:\n"
        "Или используйте другие команды:\n"
        "/match - Начать матч\n"
        "/player [номер] - Карточка игрока\n"
        "/help - Помощь",
        parse_mode="HTML",
        reply_markup=get_team_keyboard()
    )

@dp.message(Command("team"))
async def cmd_team(message: types.Message):
    """Команда /team - выбор команды"""
    await message.answer(
        "🏒 <b>Выберите команду:</b>",
        parse_mode="HTML",
        reply_markup=get_team_keyboard()
    )

@dp.message(Command("team_black"))
async def cmd_team_black(message: types.Message):
    """Показывает состав Чёрных Воронов"""
    await show_team(message, "Чёрные Вороны")

@dp.message(Command("team_red"))
async def cmd_team_red(message: types.Message):
    """Показывает состав Красных Орлов"""
    await show_team(message, "Красные Орлы")

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
        
        # Загружаем всех игроков из всех команд
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
        
        # Определяем команду игрока
        team_name = player.get('team', 'Неизвестно')
        
        # ИСПРАВЛЕНО: проверяем наличие фамилии
        surname = player.get('surname', '')
        full_name = f"{player['name']} {surname}" if surname else player['name']
        
        text = (
            f"🏒 <b>КАРТОЧКА ИГРОКА</b>\n\n"
            f"{position_emoji} #{player['number']} "
            f"<b>{full_name}</b>\n"
            f"📍 {player['position'].capitalize()}\n"
            f"🏷️ Команда: {team_name}\n\n"
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
        "⚔️ <b>Чёрные Вороны</b> vs <b>Красные Орлы</b>\n\n"
        "Скоро здесь появится симуляция матча.\n"
        "⏳ Функция в разработке...",
        parse_mode="HTML"
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Команда /help - помощь"""
    help_text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "/start - Главное меню\n"
        "/team - Выбор команды для просмотра состава\n"
        "/team_black - Состав Чёрных Воронов\n"
        "/team_red - Состав Красных Орлов\n"
        "/match - Начать матч\n"
        "/player [номер] - Карточка игрока\n"
        "/help - Помощь\n\n"
        "🏒 <b>Доступные команды:</b>\n"
        "🦅 Чёрные Вороны (тренер: Ивашка Тупоголовый)\n"
        "🦅 Красные Орлы (тренер: Павел Ихтиандрович)"
    )
    await message.answer(help_text, parse_mode="HTML")

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка нажатий на кнопки"""
    await callback.answer()
    
    if callback.data == "team_black":
        await show_team(callback.message, "Чёрные Вороны")
        await callback.message.delete()
    
    elif callback.data == "team_red":
        await show_team(callback.message, "Красные Орлы")
        await callback.message.delete()
    
    elif callback.data == "show_teams":
        await callback.message.answer(
            "🏒 <b>Выберите команду:</b>",
            parse_mode="HTML",
            reply_markup=get_team_keyboard()
        )
    
    elif callback.data == "cancel":
        await callback.message.answer("❌ Действие отменено.")
        await callback.message.delete()
        await state.clear()

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
