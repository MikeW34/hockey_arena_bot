import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, 
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from config import BOT_TOKEN
from game import load_players, get_players_by_position, get_player_by_id, load_team_by_name, get_all_teams
from match import HockeyMatch
import random

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

# Состояния
class MatchStates(StatesGroup):
    waiting_for_match = State()

# ГЛАВНОЕ МЕНЮ - физические кнопки внизу
def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🏒 Играть матч"),
                KeyboardButton(text="📋 Состав команды")
            ],
            [
                KeyboardButton(text="⭐ Рейтинг"),
                KeyboardButton(text="🔄 Коллекция")
            ],
            [
                KeyboardButton(text="❓ Помощь")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
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

# Клавиатура для управления матчем
def get_match_control_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="▶️ Следующий эпизод", callback_data="next_episode")
        ],
        [
            InlineKeyboardButton(text="⏹️ Завершить матч", callback_data="end_match")
        ]
    ])
    return keyboard

# Класс для управления матчем
class MatchManager:
    def __init__(self, team_a, team_b):
        self.team_a = team_a
        self.team_b = team_b
        self.match = HockeyMatch(team_a, team_b)
        self.current_episode = 0
        self.total_episodes = 30  # 10 эпизодов * 3 тайма
        self.episodes = []
        self.is_finished = False
        self.generate_episodes()
    
    def generate_episodes(self):
        """Генерирует эпизоды матча"""
        self.episodes = []
        period = 1
        episode_in_period = 0
        
        for i in range(self.total_episodes):
            # Определяем период
            if i < 10:
                period = 1
                episode_in_period = i + 1
            elif i < 20:
                period = 2
                episode_in_period = i - 9
            else:
                period = 3
                episode_in_period = i - 19
            
            # Генерируем время эпизода (от 0 до 20 минут)
            minutes = random.randint(0, 20)
            
            # Генерируем событие
            event = self.generate_event(period, minutes, episode_in_period)
            
            # Проверка на конец периода
            if episode_in_period == 10:
                event = f"🔴 КОНЕЦ {period}-ГО ПЕРИОДА! Счёт: {self.match.team_a_name} {self.match.score_a} - {self.match.score_b} {self.match.team_b_name}"
            
            self.episodes.append({
                'period': period,
                'minutes': minutes,
                'episode': episode_in_period,
                'event': event,
                'is_period_end': episode_in_period == 10
            })
    
    def generate_event(self, period, minutes, episode):
        """Генерирует случайное событие матча"""
        event_types = [
            'goal_a', 'goal_b', 'penalty_a', 'penalty_b',
            'shot_a', 'shot_b', 'faceoff', 'save_a', 'save_b'
        ]
        
        # Вероятность событий
        weights = [15, 15, 8, 8, 20, 20, 10, 2, 2]
        event_type = random.choices(event_types, weights=weights)[0]
        
        # Получаем игроков
        players_a = self.match.team_a_on_ice
        players_b = self.match.team_b_on_ice
        
        if event_type == 'goal_a':
            scorer = random.choice([p for p in players_a if 'нападающий' in p['position']] or players_a)
            self.match.score_a += 1
            return f"🥅 ГОЛ! {scorer['name']} {scorer.get('surname', '')} ({self.match.team_a_name}) забивает!"
        
        elif event_type == 'goal_b':
            scorer = random.choice([p for p in players_b if 'нападающий' in p['position']] or players_b)
            self.match.score_b += 1
            return f"🥅 ГОЛ! {scorer['name']} {scorer.get('surname', '')} ({self.match.team_b_name}) забивает!"
        
        elif event_type == 'penalty_a':
            player = random.choice(players_a)
            minutes_penalty = random.choices([2, 5, 10], weights=[70, 20, 10])[0]
            return f"⛔ ШТРАФ {minutes_penalty} МИНУТ! {player['name']} {player.get('surname', '')} ({self.match.team_a_name})"
        
        elif event_type == 'penalty_b':
            player = random.choice(players_b)
            minutes_penalty = random.choices([2, 5, 10], weights=[70, 20, 10])[0]
            return f"⛔ ШТРАФ {minutes_penalty} МИНУТ! {player['name']} {player.get('surname', '')} ({self.match.team_b_name})"
        
        elif event_type == 'shot_a':
            player = random.choice([p for p in players_a if 'нападающий' in p['position']] or players_a)
            return f"🎯 БРОСОК! {player['name']} {player.get('surname', '')} ({self.match.team_a_name})"
        
        elif event_type == 'shot_b':
            player = random.choice([p for p in players_b if 'нападающий' in p['position']] or players_b)
            return f"🎯 БРОСОК! {player['name']} {player.get('surname', '')} ({self.match.team_b_name})"
        
        elif event_type == 'save_a':
            goalie = random.choice([p for p in players_a if p['position'] == 'вратарь'] or players_a)
            return f"🧤 СОХРАНЕНИЕ! {goalie['name']} {goalie.get('surname', '')} ({self.match.team_a_name}) отражает бросок!"
        
        elif event_type == 'save_b':
            goalie = random.choice([p for p in players_b if p['position'] == 'вратарь'] or players_b)
            return f"🧤 СОХРАНЕНИЕ! {goalie['name']} {goalie.get('surname', '')} ({self.match.team_b_name}) отражает бросок!"
        
        else:
            return f"🔄 Вбрасывание в центре поля"
    
    def get_next_episode(self):
        """Возвращает следующий эпизод"""
        if self.current_episode >= self.total_episodes:
            return None
        
        episode = self.episodes[self.current_episode]
        self.current_episode += 1
        
        # Проверяем, закончился ли матч
        if self.current_episode >= self.total_episodes:
            self.is_finished = True
        
        return episode
    
    def get_final_result(self):
        """Возвращает финальный результат"""
        winner = None
        if self.match.score_a > self.match.score_b:
            winner = self.match.team_a_name
        elif self.match.score_b > self.match.score_a:
            winner = self.match.team_b_name
        
        return {
            'team_a': self.match.team_a_name,
            'team_b': self.match.team_b_name,
            'score_a': self.match.score_a,
            'score_b': self.match.score_b,
            'winner': winner,
            'rating_a': self.match.team_a_rating,
            'rating_b': self.match.team_b_rating
        }

# Хранилище активных матчей
active_matches = {}

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
        
        text = f"{icon} <b>{team_name_display.upper()}</b>\n"
        text += f"👨‍🏫 Тренер: {coach}\n\n"
        
        text += "🔴 <b>ОСНОВНОЙ СОСТАВ (6 игроков)</b>\n\n"
        
        if goalies:
            text += "🥅 <b>Вратари:</b>\n"
            for p in goalies:
                surname = p.get('surname', '')
                line = p.get('line', '')
                text += f"  #{p['number']} {p['name']} {surname} (Звено {line})\n"
        
        if defenders:
            text += "\n🛡️ <b>Защитники:</b>\n"
            for p in defenders:
                surname = p.get('surname', '')
                line = p.get('line', '')
                text += f"  #{p['number']} {p['name']} {surname} (Звено {line})\n"
        
        if forwards:
            text += "\n⚡ <b>Нападающие:</b>\n"
            for p in forwards:
                surname = p.get('surname', '')
                line = p.get('line', '')
                text += f"  #{p['number']} {p['name']} {surname} (Звено {line})\n"
        
        if reserve_players:
            text += f"\n🔄 <b>Запасные ({len(reserve_players)} игроков)</b>\n"
            for p in reserve_players[:10]:
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
async def cmd_start(message: types.Message):
    """Команда /start - приветствие с меню"""
    await message.answer(
        "🏒 <b>Добро пожаловать в хоккейный бот!</b>\n\n"
        "Выберите действие из меню ниже:",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    """Команда /menu - показать меню"""
    await message.answer(
        "📋 <b>Главное меню:</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )

# Обработчики кнопок меню
@dp.message(lambda message: message.text == "🏒 Играть матч")
async def play_match(message: types.Message):
    """Кнопка Играть матч"""
    await message.answer(
        "🏒 <b>Выберите команду за которую будете играть:</b>",
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

@dp.message(lambda message: message.text == "⭐ Рейтинг")
async def show_rating(message: types.Message):
    """Кнопка Рейтинг"""
    try:
        teams = get_all_teams()
        if not teams:
            await message.answer("❌ Команды не найдены!")
            return
        
        text = "⭐ <b>РЕЙТИНГ КОМАНД</b>\n\n"
        
        # Сортируем по рейтингу
        team_ratings = []
        for team in teams:
            players = team.get('players', [])
            main_players = [p for p in players if p.get('is_main', False)]
            if main_players:
                total = sum(p['stats'].get('рейтинг', 0) for p in main_players[:6])
                rating = round(total / 6, 1)
            else:
                rating = 0
            team_ratings.append({
                'name': team.get('team_name', 'Неизвестно'),
                'rating': rating
            })
        
        team_ratings.sort(key=lambda x: x['rating'], reverse=True)
        
        for i, team in enumerate(team_ratings, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} <b>{team['name']}</b> - {team['rating']}\n"
        
        await message.answer(text, parse_mode="HTML")
    
    except Exception as e:
        logging.error(f"Ошибка в show_rating: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(lambda message: message.text == "🔄 Коллекция")
async def show_collection(message: types.Message):
    """Кнопка Коллекция"""
    try:
        players = load_players()
        
        text = "🔄 <b>КОЛЛЕКЦИЯ ИГРОКОВ</b>\n\n"
        
        # Группируем по командам
        teams = {}
        for player in players:
            team = player.get('team', 'Неизвестно')
            if team not in teams:
                teams[team] = []
            teams[team].append(player)
        
        for team_name, team_players in teams.items():
            text += f"🏒 <b>{team_name}</b> ({len(team_players)} игроков)\n"
            for p in team_players[:5]:
                surname = p.get('surname', '')
                text += f"  #{p['number']} {p['name']} {surname} - {p['position']}\n"
            if len(team_players) > 5:
                text += f"  ... и ещё {len(team_players) - 5} игроков\n"
            text += "\n"
        
        await message.answer(text, parse_mode="HTML")
    
    except Exception as e:
        logging.error(f"Ошибка в show_collection: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(lambda message: message.text == "❓ Помощь")
async def show_help(message: types.Message):
    """Кнопка Помощь"""
    help_text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "🏒 <b>Играть матч</b> - начать матч между командами\n"
        "📋 <b>Состав команды</b> - просмотр состава команд\n"
        "⭐ <b>Рейтинг</b> - рейтинг команд\n"
        "🔄 <b>Коллекция</b> - все игроки\n"
        "❓ <b>Помощь</b> - это сообщение\n\n"
        "📌 <b>Дополнительные команды:</b>\n"
        "/menu - Показать главное меню\n"
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
        await start_match(callback.message, "Чёрные Вороны", "Красные Орлы", "Чёрные Вороны")
        await callback.message.delete()
    
    elif callback.data == "match_red":
        await start_match(callback.message, "Красные Орлы", "Чёрные Вороны", "Красные Орлы")
        await callback.message.delete()
    
    elif callback.data == "show_teams":
        await callback.message.answer(
            "📋 <b>Выберите команду для просмотра состава:</b>",
            parse_mode="HTML",
            reply_markup=get_team_keyboard()
        )
    
    elif callback.data == "next_episode":
        await show_next_episode(callback.message)
    
    elif callback.data == "end_match":
        await end_match(callback.message)
    
    elif callback.data == "cancel":
        await callback.message.answer(
            "❌ Действие отменено.",
            reply_markup=get_main_menu()
        )
        await callback.message.delete()
        await state.clear()

async def start_match(message: types.Message, team_a_name: str, team_b_name: str, user_team: str):
    """Запускает матч с пошаговым показом"""
    try:
        # Загружаем данные команд
        team_a = load_team_by_name(team_a_name)
        team_b = load_team_by_name(team_b_name)
        
        if not team_a or not team_b:
            await message.answer("❌ Одна из команд не найдена!")
            return
        
        # Создаем менеджер матча
        match_manager = MatchManager(team_a, team_b)
        
        # Сохраняем в активные матчи
        chat_id = message.chat.id
        active_matches[chat_id] = match_manager
        
        # Показываем первый эпизод
        await show_next_episode(message)
        
    except Exception as e:
        logging.error(f"Ошибка в start_match: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка при проведении матча: {str(e)}")

async def show_next_episode(message: types.Message):
    """Показывает следующий эпизод матча"""
    chat_id = message.chat.id
    
    if chat_id not in active_matches:
        await message.answer("❌ Матч не найден!")
        return
    
    match_manager = active_matches[chat_id]
    episode = match_manager.get_next_episode()
    
    if episode is None:
        # Матч закончился
        await end_match(message)
        return
    
    # Формируем текст эпизода
    period_names = {1: "ПЕРВЫЙ", 2: "ВТОРОЙ", 3: "ТРЕТИЙ"}
    period_name = period_names.get(episode['period'], str(episode['period']))
    
    text = f"🏒 <b>{period_name} ПЕРИОД - Эпизод {episode['episode']}</b>\n"
    text += f"⏱️ {episode['minutes']}' минута\n\n"
    text += episode['event']
    
    # Проверка на конец периода
    if episode['is_period_end'] and episode['episode'] == 10:
        text += f"\n\n📊 Счёт после периода: {match_manager.match.team_a_name} {match_manager.match.score_a} - {match_manager.match.score_b} {match_manager.match.team_b_name}"
        text += "\n\n⏸️ ПЕРЕРЫВ 15 МИНУТ"
    elif episode['period'] == 3 and episode['episode'] == 10:
        text += f"\n\n🏁 КОНЕЦ МАТЧА!\n\n📊 Финальный счёт: {match_manager.match.team_a_name} {match_manager.match.score_a} - {match_manager.match.score_b} {match_manager.match.team_b_name}"
    
    # Проверяем, закончился ли матч
    if match_manager.is_finished:
        await message.answer(text, parse_mode="HTML")
        await end_match(message)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=get_match_control_keyboard())

async def end_match(message: types.Message):
    """Завершает матч и показывает результат"""
    chat_id = message.chat.id
    
    if chat_id not in active_matches:
        await message.answer("❌ Матч не найден!")
        return
    
    match_manager = active_matches[chat_id]
    result = match_manager.get_final_result()
    
    text = "🏒 <b>ИТОГИ МАТЧА</b>\n\n"
    text += f"⚔️ {result['team_a']} vs {result['team_b']}\n"
    text += f"📊 <b>{result['score_a']} - {result['score_b']}</b>\n\n"
    
    if result['winner']:
        text += f"🏆 <b>ПОБЕДИТЕЛЬ: {result['winner']}</b>\n\n"
    else:
        text += f"🤝 <b>НИЧЬЯ</b>\n\n"
    
    text += "📈 <b>Рейтинг команд:</b>\n"
    text += f"• {result['team_a']}: {result['rating_a']}\n"
    text += f"• {result['team_b']}: {result['rating_b']}\n"
    
    # Удаляем матч из активных
    del active_matches[chat_id]
    
    await message.answer(text, parse_mode="HTML")
    
    # Возвращаем главное меню
    await message.answer(
        "🏒 <b>Главное меню:</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )

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
            f"📋 Статус: {'Основной состав' if player.get('is_main', False) else 'Запасной'}\n"
            f"🔢 Звено: {player.get('line', 'Не указано')}\n\n"
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
        "Используйте меню для навигации.",
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
