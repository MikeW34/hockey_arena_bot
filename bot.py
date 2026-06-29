import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from config import BOT_TOKEN
from game import load_players, get_players_by_position, get_player_by_id, load_team_by_name, get_all_teams
from match import HockeyMatch

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

# Главное меню
def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🏒 Сыграть матч"),
                KeyboardButton(text="📋 Состав команды")
            ],
            [
                KeyboardButton(text="🏆 Лиги"),
                KeyboardButton(text="❓ Помощь")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

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

# Клавиатура для выбора команды для матча
def get_match_team_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🦅 Чёрные Вороны", callback_data="match_black"),
            InlineKeyboardButton(text="🦅 Красные Орлы", callback_data="match_red")
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
        
        # Разделяем основной состав и запасных
        main_players = [p for p in players if p.get('is_main', False)]
        reserve_players = [p for p in players if not p.get('is_main', False)]
        
        # Группируем по позициям
        goalies = get_players_by_position(main_players, "вратарь")
        defenders = get_players_by_position(main_players, "защитник")
        forwards = get_players_by_position(main_players, "нападающий")
        
        icon = "🦅"
        
        text = f"{icon} <b>{team_name_display.upper()} - СОСТАВ</b>\n\n"
        text += f"👨‍🏫 Тренер: {coach}\n\n"
        
        text += "🔴 <b>ОСНОВНОЙ СОСТАВ (6 игроков)</b>\n\n"
        
        if goalies:
            text += "🥅 <b>Вратари:</b>\n"
            for p in goalies:
                surname = p.get('surname', '')
                text += f"  #{p['number']} {p['name']} {surname}\n"
        
        if defenders:
            text += "\n🛡️ <b>Защитники:</b>\n"
            for p in defenders:
                surname = p.get('surname', '')
                text += f"  #{p['number']} {p['name']} {surname}\n"
        
        if forwards:
            text += "\n⚡ <b>Нападающие:</b>\n"
            for p in forwards:
                surname = p.get('surname', '')
                text += f"  #{p['number']} {p['name']} {surname}\n"
        
        if reserve_players:
            text += f"\n🔄 <b>Запасные ({len(reserve_players)} игроков)</b>\n"
            for p in reserve_players[:5]:  # Показываем первых 5
                surname = p.get('surname', '')
                text += f"  #{p['number']} {p['name']} {surname} ({p['position']})\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Показать другую команду", callback_data="show_teams")
            ]
        ])
        
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    
    except Exception as e:
        logging.error(f"Ошибка в show_team: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Команда /start - приветствие"""
    await state.set_state(TeamChoice.selecting)
    await message.answer(
        "🏒 <b>Добро пожаловать в хоккейный бот!</b>\n\n"
        "Выберите действие из меню ниже:",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )

@dp.message(lambda message: message.text == "🏒 Сыграть матч")
async def play_match(message: types.Message):
    """Кнопка Сыграть матч"""
    await message.answer(
        "🏒 <b>Выберите команду для матча:</b>\n\n"
        "Выберите команду, за которую будете играть:",
        parse_mode="HTML",
        reply_markup=get_match_team_keyboard()
    )

@dp.message(lambda message: message.text == "📋 Состав команды")
async def show_team_menu(message: types.Message):
    """Кнопка Состав команды"""
    await message.answer(
        "📋 <b>Выберите команду для просмотра состава:</b>",
        parse_mode="HTML",
        reply_markup=get_team_keyboard()
    )

@dp.message(lambda message: message.text == "🏆 Лиги")
async def show_leagues(message: types.Message):
    """Кнопка Лиги"""
    text = (
        "🏆 <b>ХОККЕЙНЫЕ ЛИГИ</b>\n\n"
        "📍 <b>КХЛ (Континентальная Хоккейная Лига)</b>\n"
        "• Страны: Россия, Беларусь, Казахстан, Китай\n"
        "• Количество команд: 23\n"
        "• Главный приз: Кубок Гагарина\n"
        "• Сезон: Регулярный чемпионат → Плей-офф\n\n"
        "📌 <b>Другие лиги в разработке:</b>\n"
        "• НХЛ (Национальная Хоккейная Лига)\n"
        "• ВХЛ (Высшая Хоккейная Лига)\n"
        "• МХЛ (Молодёжная Хоккейная Лига)\n\n"
        "⚡ Регулярный чемпионат: команды играют друг с другом за очки\n"
        "🏆 Плей-офф: матчи на выбывание, победитель получает Кубок"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(lambda message: message.text == "❓ Помощь")
async def show_help(message: types.Message):
    """Кнопка Помощь"""
    help_text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "🏒 <b>Сыграть матч</b> - начать матч между командами\n"
        "📋 <b>Состав команды</b> - просмотр состава команд\n"
        "🏆 <b>Лиги</b> - информация о хоккейных лигах\n"
        "❓ <b>Помощь</b> - это сообщение\n\n"
        "📌 <b>Дополнительные команды:</b>\n"
        "/team_black - Состав Чёрных Воронов\n"
        "/team_red - Состав Красных Орлов\n"
        "/player [номер] - Карточка игрока\n\n"
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
    
    elif callback.data == "match_black":
        await start_match(callback.message, "Чёрные Вороны", "Красные Орлы")
        await callback.message.delete()
    
    elif callback.data == "match_red":
        await start_match(callback.message, "Красные Орлы", "Чёрные Вороны")
        await callback.message.delete()
    
    elif callback.data == "show_teams":
        await callback.message.answer(
            "📋 <b>Выберите команду для просмотра состава:</b>",
            parse_mode="HTML",
            reply_markup=get_team_keyboard()
        )
    
    elif callback.data == "cancel":
        await callback.message.answer("❌ Действие отменено.")
        await callback.message.delete()
        await state.clear()

async def start_match(message: types.Message, team_a_name: str, team_b_name: str):
    """Запускает матч между командами"""
    try:
        # Загружаем данные команд
        team_a = load_team_by_name(team_a_name)
        team_b = load_team_by_name(team_b_name)
        
        if not team_a or not team_b:
            await message.answer("❌ Одна из команд не найдена!")
            return
        
        # Создаем матч
        match = HockeyMatch(team_a, team_b)
        
        # Отправляем сообщение о начале матча
        await message.answer(
            f"🏒 <b>МАТЧ НАЧАЛСЯ!</b>\n\n"
            f"⚔️ {team_a_name} vs {team_b_name}\n"
            f"📊 Рейтинг {team_a_name}: {match.team_a_rating}\n"
            f"📊 Рейтинг {team_b_name}: {match.team_b_rating}\n\n"
            f"⏳ Идёт симуляция матча...",
            parse_mode="HTML"
        )
        
        # Запускаем матч
        result = match.start_match()
        
        # Формируем отчет о матче
        report = "🏒 <b>ОТЧЕТ О МАТЧЕ</b>\n\n"
        report += f"⚔️ {result['team_a']} vs {result['team_b']}\n"
        report += f"📊 <b>{result['score_a']} - {result['score_b']}</b>\n\n"
        
        if result['winner']:
            report += f"🏆 <b>ПОБЕДИТЕЛЬ: {result['winner']}</b>\n\n"
        else:
            report += f"🤝 <b>НИЧЬЯ</b>\n\n"
        
        report += "📈 <b>Статистика:</b>\n"
        report += f"• {result['team_a']}: {result['rating_a']}\n"
        report += f"• {result['team_b']}: {result['rating_b']}\n\n"
        
        # Добавляем последние события
        events = match.get_events_log(limit=10)
        report += events
        
        await message.answer(report, parse_mode="HTML")
        
        # Полный лог событий (опционально)
        # full_log = match.get_events_log(limit=50)
        # await message.answer(f"📋 Полный лог матча:\n{full_log}", parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"Ошибка в start_match: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка при проведении матча: {str(e)}")

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
        
        position_emoji = {
            "вратарь": "🥅",
            "защитник": "🛡️",
            "нападающий": "⚡"
        }.get(player["position"], "🏒")
        
        team_name = player.get('team', 'Неизвестно')
        surname = player.get('surname', '')
        full_name = f"{player['name']} {surname}" if surname else player['name']
        
        text = (
            f"🏒 <b>КАРТОЧКА ИГРОКА</b>\n\n"
            f"{position_emoji} #{player['number']} "
            f"<b>{full_name}</b>\n"
            f"📍 {player['position'].capitalize()}\n"
            f"🏷️ Команда: {team_name}\n"
            f"📋 Статус: {'Основной состав' if player.get('is_main', False) else 'Запасной'}\n\n"
            f"📊 <b>Характеристики:</b>\n"
            f"🎯 Бросок: {s['бросок']}\n"
            f"🔄 Пас: {s['пас']}\n"
            f"⚡ Скорость: {s['скорость']}\n"
            f"💪 Сила: {s['сила']}\n"
            f"🫁 Выносливость: {s['выносливость']}\n"
            f"⭐ Рейтинг: {s.get('рейтинг', 0)}"
        )
        await message.answer(text, parse_mode="HTML")
    
    except Exception as e:
        logging.error(f"Ошибка в /player: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message()
async def unknown_command(message: types.Message):
    """Обработка неизвестных команд"""
    await message.answer(
        "❌ Неизвестная команда.\n"
        "Используйте меню для навигации или /help для списка команд.",
        reply_markup=get_main_menu()
    )

async def main():
    """Главная функция запуска бота"""
    logging.info("Бот запускается...")
    
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Webhook удален")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}", exc_info=True)
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
        logging.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)
