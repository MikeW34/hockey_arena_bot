import json
import os
import logging

logging.basicConfig(level=logging.DEBUG)

def get_all_teams():
    """Возвращает список всех команд"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'players.json')
        
        logging.info(f"Загрузка файла: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logging.info(f"Тип данных: {type(data)}")
        
        # Если это список команд
        if isinstance(data, list):
            return data
        # Если это одна команда
        elif isinstance(data, dict) and 'team_name' in data:
            return [data]
        return []
    except Exception as e:
        logging.error(f"Ошибка загрузки команд: {e}", exc_info=True)
        return []

def load_team_by_name(team_name):
    """Загружает данные конкретной команды по названию"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'players.json')
        
        logging.info(f"Поиск команды: {team_name}")
        logging.info(f"Путь к файлу: {file_path}")
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            logging.error(f"Файл не найден: {file_path}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logging.info(f"Тип данных в файле: {type(data)}")
        logging.info(f"Содержимое: {data}")
        
        # Если данные - это список команд
        if isinstance(data, list):
            logging.info(f"Это список из {len(data)} команд")
            for team in data:
                logging.info(f"Проверяем команду: {team.get('team_name')}")
                if team.get('team_name') == team_name:
                    logging.info(f"Команда найдена: {team}")
                    return team
            logging.warning(f"Команда '{team_name}' не найдена в списке!")
            return None
        
        # Если данные - это одна команда
        elif isinstance(data, dict):
            logging.info("Это одна команда")
            if data.get('team_name') == team_name:
                logging.info(f"Команда найдена: {data}")
                return data
            else:
                logging.warning(f"Имя команды не совпадает: {data.get('team_name')} != {team_name}")
                return None
        
        else:
            logging.error(f"Неизвестный тип данных: {type(data)}")
            return None
            
    except FileNotFoundError:
        logging.error(f"Файл players.json не найден!")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка в формате JSON файла: {e}", exc_info=True)
        return None
    except Exception as e:
        logging.error(f"Неизвестная ошибка: {e}", exc_info=True)
        return None

def load_players():
    """Загружает всех игроков из всех команд"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'players.json')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        all_players = []
        
        # Если это список команд
        if isinstance(data, list):
            for team in data:
                players = team.get('players', [])
                team_name = team.get('team_name', 'Неизвестно')
                for p in players:
                    p['team'] = team_name
                all_players.extend(players)
            logging.info(f"Загружено {len(all_players)} игроков из {len(data)} команд")
            return all_players
        
        # Если это одна команда
        elif isinstance(data, dict) and 'players' in data:
            players = data['players']
            team_name = data.get('team_name', 'Неизвестно')
            for p in players:
                p['team'] = team_name
            logging.info(f"Загружено {len(players)} игроков из одной команды")
            return players
        
        logging.warning("Не удалось загрузить игроков")
        return []
        
    except Exception as e:
        logging.error(f"Ошибка загрузки игроков: {e}", exc_info=True)
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
