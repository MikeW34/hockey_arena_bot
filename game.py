import json
import os
import logging

logging.basicConfig(level=logging.DEBUG)

# Путь к файлу с данными пользователей
USER_DATA_FILE = 'users_data.json'

def load_user_data(user_id):
    """Загружает данные пользователя"""
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(user_id, {})
        return {}
    except Exception as e:
        logging.error(f"Ошибка загрузки данных пользователя: {e}")
        return {}

def save_user_data(user_id, data):
    """Сохраняет данные пользователя"""
    try:
        all_data = {}
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        
        if user_id in all_data:
            all_data[user_id].update(data)
        else:
            all_data[user_id] = data
        
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"Ошибка сохранения данных пользователя: {e}")
        return False

def get_all_league_data():
    """Возвращает данные о всех лигах"""
    return [
        {
            'id': 1,
            'name': 'КХЛ',
            'description': 'Континентальная Хоккейная Лига',
            'prize': 'Кубок Гагарина',
            'teams': 23,
            'countries': 'Россия, Беларусь, Казахстан, Китай'
        },
        {
            'id': 2,
            'name': 'НХЛ',
            'description': 'Национальная Хоккейная Лига',
            'prize': 'Кубок Стэнли',
            'teams': 32,
            'countries': 'США, Канада'
        },
        {
            'id': 3,
            'name': 'ВХЛ',
            'description': 'Высшая Хоккейная Лига',
            'prize': 'Кубок Петрова',
            'teams': 26,
            'countries': 'Россия'
        },
        {
            'id': 4,
            'name': 'МХЛ',
            'description': 'Молодёжная Хоккейная Лига',
            'prize': 'Кубок Харламова',
            'teams': 30,
            'countries': 'Россия'
        }
    ]

def load_team_by_name(team_name):
    """Загружает данные конкретной команды по названию"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'players.json')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            for team in data:
                if team.get('team_name') == team_name:
                    return team
        elif isinstance(data, dict):
            if data.get('team_name') == team_name:
                return data
        
        return None
        
    except Exception as e:
        logging.error(f"Ошибка загрузки: {e}", exc_info=True)
        return None

def load_players():
    """Загружает всех игроков из всех команд"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'players.json')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        all_players = []
        
        if isinstance(data, list):
            for team in data:
                players = team.get('players', [])
                for p in players:
                    p['team'] = team.get('team_name', 'Неизвестно')
                all_players.extend(players)
        elif isinstance(data, dict):
            players = data.get('players', [])
            for p in players:
                p['team'] = data.get('team_name', 'Неизвестно')
            all_players = players
        
        return all_players
        
    except Exception as e:
        logging.error(f"Ошибка загрузки игроков: {e}", exc_info=True)
        return []

def get_players_by_position(players, position):
    """Возвращает список игроков по позиции"""
    return [p for p in players if p.get('position') == position]

def get_player_by_id(players, player_id):
    """Возвращает игрока по ID"""
    for player in players:
        if player.get('id') == player_id:
            return player
    return None

def get_all_teams():
    """Возвращает список всех команд"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'players.json')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        return []
    except Exception as e:
        logging.error(f"Ошибка загрузки команд: {e}", exc_info=True)
        return []
