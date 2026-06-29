import json
import os
import logging

logging.basicConfig(level=logging.DEBUG)

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

def get_main_players(team_data):
    """Возвращает основной состав команды"""
    players = team_data.get('players', [])
    return [p for p in players if p.get('is_main', False)]

def get_reserve_players(team_data):
    """Возвращает запасных игроков команды"""
    players = team_data.get('players', [])
    return [p for p in players if not p.get('is_main', False)]
