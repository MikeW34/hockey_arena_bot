import json
import os

def load_players():
    """Загружает список игроков из players.json"""
    # Путь к файлу players.json (рядом с bot.py)
    file_path = os.path.join(os.path.dirname(__file__), "players.json")
    
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    return data["players"]

def get_player_by_id(player_id):
    """Находит игрока по ID"""
    players = load_players()
    for player in players:
        if player["id"] == player_id:
            return player
    return None

def get_players_by_position(position):
    """Возвращает игроков определённой позиции"""
    players = load_players()
    return [p for p in players if p["position"] == position]