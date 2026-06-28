import json
import os

def load_team_by_name(team_name):
    """Загружает данные конкретной команды по названию"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'players.json')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Проверяем, есть ли в файле поле team_name
        if data.get('team_name') == team_name:
            return data
        
        # Или ищем в массиве команд
        if isinstance(data, list):
            for team in data:
                if team.get('team_name') == team_name:
                    return team
        
        return None
    except FileNotFoundError:
        print("Файл players.json не найден!")
        return None
    except json.JSONDecodeError:
        print("Ошибка в формате JSON файла!")
        return None

def load_players():
    """Загружает всех игроков из всех команд"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'players.json')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Если это одна команда
        if isinstance(data, dict) and 'players' in data:
            players = data['players']
            for p in players:
                p['team'] = data.get('team_name', 'Неизвестно')
            return players
        
        # Если это список команд
        if isinstance(data, list):
            all_players = []
            for team in data:
                players = team.get('players', [])
                for p in players:
                    p['team'] = team.get('team_name', 'Неизвестно')
                all_players.extend(players)
            return all_players
        
        return []
    except FileNotFoundError:
        print("Файл players.json не найден!")
        return []
    except json.JSONDecodeError:
        print("Ошибка в формате JSON файла!")
        return []

def get_players_by_position(players, position):
    """Возвращает список игроков по позиции"""
    return [p for p in players if p.get('position') == position]

def get_player_by_id(players, player_id):
    """Возвращает игрока по ID (ищет во всех командах)"""
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
        
        if isinstance(data, dict) and 'team_name' in data:
            return [data]
        elif isinstance(data, list):
            return data
        return []
    except:
        return []
