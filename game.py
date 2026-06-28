import json
import os

def load_players():
    """Загружает список игроков из JSON файла"""
    try:
        # Получаем путь к файлу
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'players.json')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('players', [])
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
    """Возвращает игрока по ID"""
    for player in players:
        if player.get('id') == player_id:
            return player
    return None

def get_team_info():
    """Возвращает информацию о команде"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'players.json')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {
                'name': data.get('team_name', 'Чёрные Вороны'),
                'coach': data.get('coach', 'Ивашка Тупоголовый')
            }
    except:
        return {
            'name': 'Чёрные Вороны',
            'coach': 'Ивашка Тупоголовый'
        }
