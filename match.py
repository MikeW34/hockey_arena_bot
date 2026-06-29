import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

logging.basicConfig(level=logging.INFO)

class HockeyMatch:
    def __init__(self, team_a: Dict, team_b: Dict):
        self.team_a = team_a
        self.team_b = team_b
        self.team_a_name = team_a['team_name']
        self.team_b_name = team_b['team_name']
        
        # Основные параметры матча
        self.periods = 3
        self.period_duration = 20  # минут
        
        # Состояние матча
        self.current_period = 0
        self.current_time = 0
        self.is_running = False
        
        # Счет
        self.score_a = 0
        self.score_b = 0
        
        # Игроки на льду
        self.team_a_on_ice = []
        self.team_b_on_ice = []
        
        # Заполняем основной состав
        self._setup_lineups()
        
        # Вычисляем рейтинг команд
        self.team_a_rating = self._calculate_team_rating(team_a)
        self.team_b_rating = self._calculate_team_rating(team_b)
    
    def _setup_lineups(self):
        """Формирует основной состав команд (6 игроков)"""
        # Для команды А
        main_players_a = [p for p in self.team_a['players'] if p.get('is_main', False)]
        self.team_a_on_ice = self._select_lineup(main_players_a)
        
        # Для команды Б
        main_players_b = [p for p in self.team_b['players'] if p.get('is_main', False)]
        self.team_b_on_ice = self._select_lineup(main_players_b)
    
    def _select_lineup(self, players: List[Dict]) -> List[Dict]:
        """Выбирает 6 игроков на поле"""
        lineup = []
        
        # Выбираем вратаря
        goalies = [p for p in players if p['position'] == 'вратарь']
        if goalies:
            lineup.append(goalies[0])  # Берем первого вратаря
        
        # Выбираем защитников
        defenders = [p for p in players if 'защитник' in p['position']]
        if len(defenders) >= 2:
            lineup.extend(defenders[:2])
        
        # Выбираем нападающих
        forwards = [p for p in players if 'нападающий' in p['position']]
        if len(forwards) >= 3:
            lineup.extend(forwards[:3])
        
        return lineup
    
    def _calculate_team_rating(self, team: Dict) -> float:
        """Вычисляет рейтинг команды на основе основного состава"""
        main_players = [p for p in team['players'] if p.get('is_main', False)]
        
        if not main_players:
            return 0.0
        
        # Берем 6 лучших игроков
        sorted_players = sorted(main_players, 
                               key=lambda p: p['stats'].get('рейтинг', 0), 
                               reverse=True)
        top_6 = sorted_players[:6]
        
        if not top_6:
            return 0.0
        
        total_rating = sum(p['stats'].get('рейтинг', 0) for p in top_6)
        return round(total_rating / 6, 1)
