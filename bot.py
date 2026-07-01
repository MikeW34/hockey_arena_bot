import asyncio
import logging
import os
import sys
import json
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from config import BOT_TOKEN
from game import load_players, get_players_by_position, get_player_by_id, load_team_by_name, get_all_teams, save_user_data, load_user_data, get_all_league_data

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
class UserStates(StatesGroup):
    waiting_for_team_name = State()
    waiting_for_league = State()
    waiting_for_match = State()

# ГЛАВНОЕ МЕНЮ - всегда висит внизу
def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏒 Сыграть матч", callback_data="play_match"),
            InlineKeyboardButton(text="📋 Состав команды", callback_data="show_team")
        ],
        [
            InlineKeyboardButton(text="🏆 Лиги", callback_data="show_leagues"),
            InlineKeyboardButton(text="🔄 Коллекция", callback_data="show_collection")
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="show_profile"),
            InlineKeyboardButton(text="⭐ Рейтинг", callback_data="show_rating")
        ],
        [
            InlineKeyboardButton(text="❓ Помощь", callback_data="show_help")
        ]
    ])
    return keyboard

# Клавиатура для выбора лиги (подменю)
def get_leagues_keyboard():
    leagues = get_all_league_data()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for league in leagues:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"🏒 {league['name']}", callback_data=f"league_{league['id']}")
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")
    ])
    return keyboard

# Клавиатура для выбора команды для просмотра состава (подменю)
def get_team_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🦅 Чёрные Вороны", callback_data="team_black"),
            InlineKeyboardButton(text="🦅 Красные Орлы", callback_data="team_red")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")
        ]
    ])
    return keyboard

# Клавиатура для выбора команды для матча (подменю)
def get_match_team_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🦅 Чёрные Вороны", callback_data="match_black"),
            InlineKeyboardButton(text="🦅 Красные Орлы", callback_data="match_red")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")
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
    def __init__(self, team_a, team_b, user_team_name=None):
        self.team_a = team_a
        self.team_b = team_b
        self.user_team_name = user_team_name
        self.team_a_name = team_a['team_name']
        self.team_b_name = team_b['team_name']
        self.score_a = 0
        self.score_b = 0
        self.periods = []
        self.current_period = 0
        self.current_episode = 0
        self.total_episodes = 30
        self.is_finished = False
        self.period_scores = []
        self.key_events = []
        self.match_log = []
        self.period_events = []
        
        # Инициализируем рейтинги
        self.rating_a = self.calculate_team_rating(team_a)
        self.rating_b = self.calculate_team_rating(team_b)
        
        self.generate_periods()
    
    def calculate_team_rating(self, team):
        """Вычисляет рейтинг команды"""
        players = team.get('players', [])
        main_players = [p for p in players if p.get('is_main', False)]
        if main_players:
            total = sum(p['stats'].get('рейтинг', 0) for p in main_players[:6])
            return round(total / 6, 1)
        return 0
    
    def generate_periods(self):
        """Генерирует все периоды с эпизодами"""
        self.periods = []
        period_events = []
        
        for i in range(30):
            period = (i // 10) + 1
            episode_in_period = (i % 10) + 1
            minutes = episode_in_period * 2
            
            # Генерируем событие
            event, key = self.generate_event(period, minutes)
            
            if key:
                self.key_events.append({
                    'period': period,
                    'time': f"{minutes}'",
                    'event': event
                })
            
            period_events.append({
                'period': period,
                'time': f"{minutes}'",
                'episode': episode_in_period,
                'event': event,
                'is_key': key
            })
            
            # Если конец периода
            if episode_in_period == 10:
                period_events.append({
                    'period': period,
                    'time': f"20'",
                    'episode': episode_in_period,
                    'event': f"🔴 КОНЕЦ {period}-ГО ПЕРИОДА!",
                    'is_key': True,
                    'is_period_end': True
                })
                
                self.period_scores.append({
                    'period': period,
                    'score_a': self.score_a,
                    'score_b': self.score_b
                })
        
        self.periods = period_events
    
    def generate_event(self, period, minutes):
        """Генерирует событие матча с учетом вероятностей"""
        rating_diff = abs(self.rating_a - self.rating_b)
        underdog_chance = min(0.3, rating_diff / 200)
        
        if self.rating_a < self.rating_b:
            weaker_team = 'A'
        else:
            weaker_team = 'B'
        
        event_types = ['goal', 'penalty', 'shot', 'save', 'faceoff', 'duel']
        weights = [15, 10, 25, 15, 20, 15]
        
        if random.random() < underdog_chance:
            if weaker_team == 'A':
                return self.create_goal_event('A', period, minutes), True
            else:
                return self.create_goal_event('B', period, minutes), True
        
        event_type = random.choices(event_types, weights=weights)[0]
        
        if event_type == 'goal':
            if random.random() < self.rating_a / (self.rating_a + self.rating_b):
                return self.create_goal_event('A', period, minutes), True
            else:
                return self.create_goal_event('B', period, minutes), True
        
        elif event_type == 'penalty':
            return self.create_penalty_event(period, minutes), False
        
        elif event_type == 'shot':
            return self.create_shot_event(period, minutes), False
        
        elif event_type == 'save':
            return self.create_save_event(period, minutes), False
        
        elif event_type == 'duel':
            return self.create_duel_event(period, minutes), True
        
        else:
            return f"🔄 Вбрасывание в центре поля", False
    
    def create_goal_event(self, team, period, minutes):
        """Создает событие гола"""
        if team == 'A':
            players = [p for p in self.team_a['players'] if p.get('is_main', False)]
            scorer = random.choice([p for p in players if 'нападающий' in p['position']] or players)
            self.score_a += 1
            return f"🥅 ГОЛ! {scorer['name']} {scorer.get('surname', '')} ({self.team_a_name}) забивает!"
        else:
            players = [p for p in self.team_b['players'] if p.get('is_main', False)]
            scorer = random.choice([p for p in players if 'нападающий' in p['position']] or players)
            self.score_b += 1
            return f"🥅 ГОЛ! {scorer['name']} {scorer.get('surname', '')} ({self.team_b_name}) забивает!"
    
    def create_penalty_event(self, period, minutes):
        """Создает событие штрафа"""
        team = random.choice(['A', 'B'])
        if team == 'A':
            player = random.choice([p for p in self.team_a['players'] if p.get('is_main', False)])
            mins = random.choices([2, 5, 10], weights=[70, 20, 10])[0]
            return f"⛔ ШТРАФ {mins} МИН! {player['name']} {player.get('surname', '')} ({self.team_a_name})"
        else:
            player = random.choice([p for p in self.team_b['players'] if p.get('is_main', False)])
            mins = random.choices([2, 5, 10], weights=[70, 20, 10])[0]
            return f"⛔ ШТРАФ {mins} МИН! {player['name']} {player.get('surname', '')} ({self.team_b_name})"
    
    def create_shot_event(self, period, minutes):
        """Создает событие броска"""
        team = random.choice(['A', 'B'])
        if team == 'A':
            player = random.choice([p for p in self.team_a['players'] if p.get('is_main', False)])
            return f"🎯 БРОСОК! {player['name']} {player.get('surname', '')} ({self.team_a_name})"
        else:
            player = random.choice([p for p in self.team_b['players'] if p.get('is_main', False)])
            return f"🎯 БРОСОК! {player['name']} {player.get('surname', '')} ({self.team_b_name})"
    
    def create_save_event(self, period, minutes):
        """Создает событие сэйва вратаря"""
        team = random.choice(['A', 'B'])
        if team == 'A':
            goalie = random.choice([p for p in self.team_a['players'] if p['position'] == 'вратарь'])
            return f"🧤 СОХРАНЕНИЕ! {goalie['name']} {goalie.get('surname', '')} ({self.team_a_name}) отражает бросок!"
        else:
            goalie = random.choice([p for p in self.team_b['players'] if p['position'] == 'вратарь'])
            return f"🧤 СОХРАНЕНИЕ! {goalie['name']} {goalie.get('surname', '')} ({self.team_b_name}) отражает бросок!"
    
    def create_duel_event(self, period, minutes):
        """Создает дуэль между игроками"""
        team = random.choice(['A', 'B'])
        
        if team == 'A':
            player1 = random.choice([p for p in self.team_a['players'] if p.get('is_main', False) and 'нападающий' in p['position']])
            player2 = random.choice([p for p in self.team_a['players'] if p.get('is_main', False) and 'защитник' in p['position']])
            team_name = self.team_a_name
            
            if player1['stats']['рейтинг'] > player2['stats']['рейтинг']:
                return f"⚔️ ДУЭЛЬ! {player1['name']} {player1.get('surname', '')} побеждает {player2['name']} {player2.get('surname', '')} ({team_name})!"
            else:
                return f"⚔️ ДУЭЛЬ! {player2['name']} {player2.get('surname', '')} побеждает {player1['name']} {player1.get('surname', '')} ({team_name})!"
        else:
            player1 = random.choice([p for p in self.team_b['players'] if p.get('is_main', False) and 'нападающий' in p['position']])
            player2 = random.choice([p for p in self.team_b['players'] if p.get('is_main', False) and 'защитник' in p['position']])
            team_name = self.team_b_name
            
            if player1['stats']['рейтинг'] > player2['stats']['рейтинг']:
                return f"⚔️ ДУЭЛЬ! {player1['name']} {player1.get('surname', '')} побеждает {player2['name']} {player2.get('surname', '')} ({team_name})!"
            else:
                return f"⚔️ ДУЭЛЬ! {player2['name']} {player2.get('surname', '')} побеждает {player1['name']} {player1.get('surname', '')} ({team_name})!"
    
    def get_next_episode(self):
        """Возвращает следующий эпизод матча"""
        if self.current_episode >= len(self.periods):
            return None
        
        episode = self.periods[self.current_episode]
        self.current_episode += 1
        
        if self.current_episode >= len(self.periods):
            self.is_finished = True
        
        return episode
    
    def get_final_result(self):
        """Возвращает финальный результат"""
        winner = None
        if self.score_a > self.score_b:
            winner = self.team_a_name
        elif self.score_b > self.score_a:
            winner = self.team_b_name
        
        return {
            'team_a': self.team_a_name,
            'team_b': self.team_b_name,
            'score_a': self.score_a,
            'score_b': self.score_b,
            'winner': winner,
            'rating_a': self.rating_a,
            'rating_b': self.rating_b,
            'period_scores': self.period_scores,
            'key_events': self.key_events
        }

# Хранилище активных матчей
active_matches = {}

# Обработчики
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Команда /start - запрос названия команды"""
    user_id = str(message.from_user.id)
    user_data = load_user_data(user_id)
    
    if user_data and user_data.get('team_name'):
        # У пользователя уже есть команда
        await message.answer(
            f"🏒 <b>Добро пожаловать обратно, {message.from_user.first_name}!</b>\n\n"
            f"Ваша команда: <b>{user_data['team_name']}</b>\n\n"
            f"Выберите действие из меню ниже:",
            parse_mode="HTML",
            reply_markup=get_main_menu()
        )
    else:
        # Запрашиваем название команды
        await state.set_state(UserStates.waiting_for_team_name)
        await message.answer(
            "🏒 <b>Добро пожаловать в хоккейный бот!</b>\n\n"
            "Для начала создайте свою команду!\n"
            "Придумайте название для вашей команды:",
            parse_mode="HTML"
        )

@dp.message(UserStates.waiting_for_team_name)
async def process_team_name(message: types.Message, state: FSMContext):
    """Обработка ввода названия команды"""
    team_name = message.text.strip()
    
    if len(team_name) < 2:
        await message.answer("❌ Название команды должно содержать минимум 2 символа. Попробуйте еще раз:")
        return
    
    if len(team_name) > 50:
        await message.answer("❌ Название команды слишком длинное (максимум 50 символов). Попробуйте еще раз:")
        return
    
    # Сохраняем название команды
    user_id = str(message.from_user.id)
    save_user_data(user_id, {
        'team_name': team_name,
        'username': message.from_user.username or message.from_user.first_name
    })
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>Отлично!</b>\n\n"
        f"Ваша команда <b>«{team_name}»</b> успешно создана!\n\n"
        f"Теперь выберите действие из меню ниже:",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка нажатий на инлайн кнопки"""
    await callback.answer()
    
    # ======= ВСЕГДА ПОКАЗЫВАЕМ МЕНЮ СНИЗУ =======
    
    # 1. ЛИГИ
    if callback.data == "show_leagues":
        await callback.message.edit_text(
            "🏆 <b>ВЫБЕРИТЕ ЛИГУ</b>\n\n"
            "Нажмите на лигу, чтобы присоединиться:",
            parse_mode="HTML"
        )
        await callback.message.edit_reply_markup(reply_markup=get_leagues_keyboard())
        # Меню уже есть снизу
    
    elif callback.data.startswith("league_"):
        league_id = callback.data.replace("league_", "")
        leagues = get_all_league_data()
        league = next((l for l in leagues if str(l['id']) == league_id), None)
        
        if league:
            user_id = str(callback.from_user.id)
            save_user_data(user_id, {'current_league': league['name']})
            
            text = f"🏒 <b>ЛИГА: {league['name']}</b>\n\n"
            text += f"📋 {league['description']}\n\n"
            text += f"🏆 Главный приз: {league['prize']}\n"
            text += f"📊 Команды: {league['teams']}\n"
            text += f"🌍 Страны: {league['countries']}\n\n"
            text += "✅ Вы успешно присоединились к лиге!"
            
            await callback.message.edit_text(
                text,
                parse_mode="HTML"
            )
            await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад к лигам", callback_data="show_leagues")]
            ]))
            # Меню уже есть снизу
    
    # 2. СОСТАВ КОМАНДЫ
    elif callback.data == "show_team":
        await callback.message.edit_text(
            "📋 <b>Выберите команду для просмотра состава:</b>",
            parse_mode="HTML"
        )
        await callback.message.edit_reply_markup(reply_markup=get_team_keyboard())
        # Меню уже есть снизу
    
    elif callback.data == "team_black":
        await show_team(callback.message, "Чёрные Вороны")
    
    elif callback.data == "team_red":
        await show_team(callback.message, "Красные Орлы")
    
    # 3. СЫГРАТЬ МАТЧ
    elif callback.data == "play_match":
        await callback.message.edit_text(
            "🏒 <b>Выберите команду за которую будете играть:</b>",
            parse_mode="HTML"
        )
        await callback.message.edit_reply_markup(reply_markup=get_match_team_keyboard())
        # Меню уже есть снизу
    
    elif callback.data == "match_black":
        await start_match(callback.message, "Чёрные Вороны", "Красные Орлы")
    
    elif callback.data == "match_red":
        await start_match(callback.message, "Красные Орлы", "Чёрные Вороны")
    
    # 4. КОЛЛЕКЦИЯ
    elif callback.data == "show_collection":
        try:
            players = load_players()
            
            text = "🔄 <b>КОЛЛЕКЦИЯ ИГРОКОВ</b>\n\n"
            
            teams = {}
            for player in players:
                team = player.get('team', 'Неизвестно')
                if team not in teams:
                    teams[team] = []
                teams[team].append(player)
            
            for team_name, team_players in teams.items():
                main_players = [p for p in team_players if p.get('is_main', False)]
                reserve_players = [p for p in team_players if not p.get('is_main', False)]
                
                text += f"🏒 <b>{team_name}</b>\n"
                text += f"   Основной состав: {len(main_players)} игроков\n"
                text += f"   Запасные: {len(reserve_players)} игроков\n"
                text += f"   Всего: {len(team_players)} игроков\n\n"
            
            total_players = len(players)
            total_main = len([p for p in players if p.get('is_main', False)])
            total_reserve = total_players - total_main
            
            text += "📊 <b>Общая статистика:</b>\n"
            text += f"   Всего игроков: {total_players}\n"
            text += f"   В основном составе: {total_main}\n"
            text += f"   В запасе: {total_reserve}\n"
            
            await callback.message.edit_text(
                text,
                parse_mode="HTML"
            )
            await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
            ]))
            # Меню уже есть снизу
            
        except Exception as e:
            logging.error(f"Ошибка в show_collection: {e}", exc_info=True)
            await callback.message.edit_text(f"❌ Ошибка: {str(e)}")
    
    # 5. ПРОФИЛЬ
    elif callback.data == "show_profile":
        user_id = str(callback.from_user.id)
        user_data = load_user_data(user_id)
        username = callback.from_user.username or callback.from_user.first_name
        team_name = user_data.get('team_name', 'Не создана') if user_data else 'Не создана'
        league = user_data.get('current_league', 'Не выбрана') if user_data else 'Не выбрана'
        
        text = (
            f"👤 <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
            f"📌 Имя: {username}\n"
            f"🆔 ID: {user_id}\n"
            f"🏒 Команда: {team_name}\n"
            f"🏆 Лига: {league}\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"🏒 Сыграно матчей: {user_data.get('matches', 0) if user_data else 0}\n"
            f"🏆 Побед: {user_data.get('wins', 0) if user_data else 0}\n"
            f"⚽ Голов забито: {user_data.get('goals', 0) if user_data else 0}\n"
            f"🔄 Передач: {user_data.get('assists', 0) if user_data else 0}\n\n"
            f"⭐ Рейтинг: {user_data.get('rating', 1000) if user_data else 1000}"
        )
        await callback.message.edit_text(
            text,
            parse_mode="HTML"
        )
        await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
        ]))
        # Меню уже есть снизу
    
    # 6. РЕЙТИНГ
    elif callback.data == "show_rating":
        try:
            teams = get_all_teams()
            if not teams:
                await callback.message.edit_text("❌ Команды не найдены!")
                return
            
            text = "⭐ <b>РЕЙТИНГ КОМАНД</b>\n\n"
            
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
            
            await callback.message.edit_text(
                text,
                parse_mode="HTML"
            )
            await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
            ]))
            # Меню уже есть снизу
            
        except Exception as e:
            logging.error(f"Ошибка в show_rating: {e}", exc_info=True)
            await callback.message.edit_text(f"❌ Ошибка: {str(e)}")
    
    # 7. ПОМОЩЬ
    elif callback.data == "show_help":
        help_text = (
            "📋 <b>Помощь по боту</b>\n\n"
            "🏒 <b>Сыграть матч</b> - начать матч между командами\n"
            "📋 <b>Состав команды</b> - просмотр состава команд\n"
            "🏆 <b>Лиги</b> - выбор и просмотр лиг\n"
            "🔄 <b>Коллекция</b> - все игроки команд\n"
            "👤 <b>Профиль</b> - ваш профиль\n"
            "⭐ <b>Рейтинг</b> - рейтинг команд\n\n"
            "📌 <b>Как играть:</b>\n"
            "1. Создайте свою команду через /start\n"
            "2. Выберите лигу для участия\n"
            "3. Играйте матчи и побеждайте!\n\n"
            "🏆 <b>Доступные лиги:</b>\n"
            "• КХЛ - Кубок Гагарина\n"
            "• НХЛ - Кубок Стэнли\n"
            "• ВХЛ - Кубок Петрова\n"
            "• МХЛ - Кубок Харламова"
        )
        await callback.message.edit_text(
            help_text,
            parse_mode="HTML"
        )
        await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
        ]))
        # Меню уже есть снизу
    
    # НАЗАД В МЕНЮ - возвращает главное меню
    elif callback.data == "back_to_menu":
        await callback.message.edit_text(
            "🏒 <b>Главное меню:</b>\n\n"
            "Выберите действие:",
            parse_mode="HTML"
        )
        await callback.message.edit_reply_markup(reply_markup=get_main_menu())
        # Меню уже есть снизу
    
    # УПРАВЛЕНИЕ МАТЧЕМ
    elif callback.data == "next_episode":
        await show_next_episode(callback.message)
    
    elif callback.data == "end_match":
        await end_match(callback.message)

async def show_team(message: types.Message, team_name: str):
    """Показывает состав выбранной команды"""
    try:
        team_data = load_team_by_name(team_name)
        if not team_data:
            await message.edit_text(f"❌ Команда '{team_name}' не найдена!")
            return
        
        players = team_data.get('players', [])
        team_name_display = team_data.get('team_name', team_name)
        coach = team_data.get('coach', 'Неизвестно')
        
        main_players = [p for p in players if p.get('is_main', False)]
        reserve_players = [p for p in players if not p.get('is_main', False)]
        
        goalies = [p for p in main_players if p['position'] == 'вратарь']
        defenders = [p for p in main_players if 'защитник' in p['position']]
        forwards = [p for p in main_players if 'нападающий' in p['position']]
        
        text = f"🦅 <b>{team_name_display.upper()}</b>\n"
        text += f"👨‍🏫 Тренер: {coach}\n\n"
        text += "🔴 <b>ОСНОВНОЙ СОСТАВ (6 игроков)</b>\n\n"
        
        if goalies:
            text += "🥅 <b>Вратари:</b>\n"
            for p in goalies:
                surname = p.get('surname', '')
                text += f"  #{p['number']} {p['name']} {surname} (Звено {p.get('line', 1)})\n"
            text += "\n"
        
        if defenders:
            text += "🛡️ <b>Защитники:</b>\n"
            for p in defenders:
                surname = p.get('surname', '')
                text += f"  #{p['number']} {p['name']} {surname} (Звено {p.get('line', 1)})\n"
            text += "\n"
        
        if forwards:
            text += "⚡ <b>Нападающие:</b>\n"
            for p in forwards:
                surname = p.get('surname', '')
                text += f"  #{p['number']} {p['name']} {surname} (Звено {p.get('line', 1)})\n"
            text += "\n"
        
        if reserve_players:
            text += f"🔄 <b>Запасные ({len(reserve_players)} игроков)</b>\n"
            for p in reserve_players[:15]:
                surname = p.get('surname', '')
                text += f"  #{p['number']} {p['name']} {surname} ({p['position']})\n"
            if len(reserve_players) > 15:
                text += f"  ... и ещё {len(reserve_players) - 15} игроков\n"
        
        await message.edit_text(
            text,
            parse_mode="HTML"
        )
        await message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к выбору команд", callback_data="show_team")]
        ]))
        # Меню уже есть снизу
    
    except Exception as e:
        logging.error(f"Ошибка в show_team: {e}", exc_info=True)
        await message.edit_text(f"❌ Ошибка: {str(e)}")

async def start_match(message: types.Message, team_a_name: str, team_b_name: str):
    """Запускает матч с пошаговым показом"""
    try:
        user_id = str(message.chat.id)
        user_data = load_user_data(user_id)
        user_team_name = user_data.get('team_name', 'Ваша команда') if user_data else 'Ваша команда'
        
        team_a = load_team_by_name(team_a_name)
        team_b = load_team_by_name(team_b_name)
        
        if not team_a or not team_b:
            await message.edit_text("❌ Одна из команд не найдена!")
            return
        
        match_manager = MatchManager(team_a, team_b, user_team_name)
        
        chat_id = message.chat.id
        active_matches[chat_id] = match_manager
        
        # Сначала показываем информацию о матче
        await message.edit_text(
            f"🏒 <b>МАТЧ НАЧИНАЕТСЯ!</b>\n\n"
            f"⚔️ {team_a_name} vs {team_b_name}\n"
            f"📊 Рейтинг {team_a_name}: {match_manager.rating_a}\n"
            f"📊 Рейтинг {team_b_name}: {match_manager.rating_b}\n\n"
            f"⏳ Сейчас начнутся эпизоды матча...",
            parse_mode="HTML"
        )
        
        # Показываем первый эпизод
        await show_next_episode(message)
        
    except Exception as e:
        logging.error(f"Ошибка в start_match: {e}", exc_info=True)
        await message.edit_text(f"❌ Ошибка при проведении матча: {str(e)}")

async def show_next_episode(message: types.Message):
    """Показывает следующий эпизод матча отдельным сообщением"""
    chat_id = message.chat.id
    
    if chat_id not in active_matches:
        await message.answer("❌ Матч не найден!")
        return
    
    match_manager = active_matches[chat_id]
    episode = match_manager.get_next_episode()
    
    if episode is None:
        await end_match(message)
        return
    
    # Формируем текст эпизода
    period_names = {1: "ПЕРВЫЙ", 2: "ВТОРОЙ", 3: "ТРЕТИЙ"}
    period_name = period_names.get(episode['period'], str(episode['period']))
    
    text = f"🏒 <b>{period_name} ПЕРИОД</b>\n"
    text += f"⏱️ {episode['time']}\n\n"
    
    if episode.get('is_period_end'):
        text += episode['event']
        text += f"\n\n📊 Счёт: {match_manager.team_a_name} {match_manager.score_a} - {match_manager.score_b} {match_manager.team_b_name}"
        text += "\n\n⏸️ ПЕРЕРЫВ 15 МИНУТ"
    else:
        if episode.get('is_key'):
            text += f"⭐ <b>КЛЮЧЕВОЙ МОМЕНТ!</b>\n"
        text += episode['event']
    
    # Отправляем новое сообщение с эпизодом
    await message.answer(text, parse_mode="HTML")
    
    # Если матч закончился
    if match_manager.is_finished:
        await end_match(message)
    else:
        # Показываем кнопки управления после каждого эпизода
        await message.answer(
            "▶️ Нажмите для следующего эпизода:",
            reply_markup=get_match_control_keyboard()
        )

async def end_match(message: types.Message):
    """Завершает матч и показывает результат"""
    chat_id = message.chat.id
    
    if chat_id not in active_matches:
        await message.answer("❌ Матч не найден!")
        return
    
    match_manager = active_matches[chat_id]
    result = match_manager.get_final_result()
    
    text = "🏒 <b>ИТОГИ МАТЧА</b>\n\n"
    text += f"⚔️ {result['team_a']} vs {result['team_b']}\n\n"
    
    # Результат по периодам
    text += "📊 <b>Счет по периодам:</b>\n"
    for ps in result['period_scores']:
        text += f"  Период {ps['period']}: {ps['score_a']} - {ps['score_b']}\n"
    
    text += f"\n📊 <b>ФИНАЛЬНЫЙ СЧЁТ: {result['score_a']} - {result['score_b']}</b>\n\n"
    
    if result['winner']:
        text += f"🏆 <b>ПОБЕДИТЕЛЬ: {result['winner']}</b>\n\n"
    else:
        text += f"🤝 <b>НИЧЬЯ</b>\n\n"
    
    text += "📈 <b>Рейтинг команд:</b>\n"
    text += f"• {result['team_a']}: {result['rating_a']}\n"
    text += f"• {result['team_b']}: {result['rating_b']}\n\n"
    
    # Ключевые моменты матча
    if result['key_events']:
        text += "⭐ <b>КЛЮЧЕВЫЕ МОМЕНТЫ:</b>\n"
        for event in result['key_events'][:5]:
            text += f"  {event['time']} - {event['event']}\n"
    
    # Обновляем статистику пользователя
    user_id = str(message.chat.id)
    user_data = load_user_data(user_id)
    if user_data:
        user_data['matches'] = user_data.get('matches', 0) + 1
        if result['winner'] == user_data.get('team_name'):
            user_data['wins'] = user_data.get('wins', 0) + 1
        save_user_data(user_id, user_data)
    
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
    """Показывает карточку игрока"""
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
