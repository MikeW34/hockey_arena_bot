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
        self.break_duration = 15  # минут
        self.overtime_duration = 5  # минут
        
        # Состояние матча
        self.current_period = 0
        self.current_time = 0  # текущее время в периоде (секунды)
        self.is_overtime = False
        self.is_shootout = False
        self.is_running = False
        self.is_paused = False
        
        # Счет
        self.score_a = 0
        self.score_b = 0
        
        # События матча
        self.events = []
        
        # Игроки на льду
        self.team_a_on_ice = []
        self.team_b_on_ice = []
        
        # Штрафы
        self.penalties = []
        
        # Заполняем основной состав
        self._setup_lineups()
        
        # Вычисляем рейтинг команд
        self.team_a_rating = self._calculate_team_rating(team_a)
        self.team_b_rating = self._calculate_team_rating(team_b)
        
        # Результат матча
        self.match_result = None
        
        logging.info(f"Матч создан: {self.team_a_name} vs {self.team_b_name}")
        logging.info(f"Рейтинг {self.team_a_name}: {self.team_a_rating}")
        logging.info(f"Рейтинг {self.team_b_name}: {self.team_b_rating}")
    
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
            lineup.append(random.choice(goalies))
        
        # Выбираем защитников
        defenders = [p for p in players if 'защитник' in p['position']]
        if len(defenders) >= 2:
            lineup.extend(random.sample(defenders, 2))
        
        # Выбираем нападающих
        forwards = [p for p in players if 'нападающий' in p['position']]
        if len(forwards) >= 3:
            lineup.extend(random.sample(forwards, 3))
        
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
    
    def start_match(self) -> Dict:
        """Запускает матч и возвращает результат"""
        self.is_running = True
        self.events = []
        
        logging.info(f"Матч начался: {self.team_a_name} vs {self.team_b_name}")
        self._add_event(f"🏒 МАТЧ НАЧАЛСЯ! {self.team_a_name} vs {self.team_b_name}", 0, 0)
        self._add_event(f"📍 Начальное вбрасывание на центральной точке", 0, 0)
        
        # Основное время
        for period in range(1, self.periods + 1):
            self.current_period = period
            self.current_time = 0
            self._add_event(f"🔴 Начало {period}-го периода", 0, period)
            
            # Симуляция периода
            self._simulate_period(period)
            
            # Перерыв между периодами (кроме последнего)
            if period < self.periods:
                self._add_event(f"⏸️ Конец {period}-го периода. Перерыв 15 минут", 20*60, period)
                self._add_event(f"Счёт после {period}-го периода: {self.team_a_name} {self.score_a} - {self.score_b} {self.team_b_name}", 20*60, period)
        
        # Проверка на overtime
        if self.score_a == self.score_b:
            self._add_event(f"⚡ Ничья в основное время! Назначается овертайм!", 20*60, 3)
            self._simulate_overtime()
        
        # Проверка на буллиты
        if self.score_a == self.score_b:
            self._add_event(f"⚡ Ничья в овертайме! Назначаются буллиты!", self.overtime_duration*60, 3)
            self._simulate_shootout()
        
        self.is_running = False
        self._add_event(f"🏁 МАТЧ ОКОНЧЕН! Финальный счёт: {self.team_a_name} {self.score_a} - {self.score_b} {self.team_b_name}", 0, 3)
        
        # Определяем победителя
        winner = None
        if self.score_a > self.score_b:
            winner = self.team_a_name
        elif self.score_b > self.score_a:
            winner = self.team_b_name
        
        self.match_result = {
            'winner': winner,
            'score_a': self.score_a,
            'score_b': self.score_b,
            'team_a': self.team_a_name,
            'team_b': self.team_b_name,
            'events': self.events,
            'rating_a': self.team_a_rating,
            'rating_b': self.team_b_rating
        }
        
        return self.match_result
    
    def _simulate_period(self, period: int):
        """Симулирует один период"""
        period_seconds = self.period_duration * 60
        
        # Генерируем события в течение периода
        events_count = random.randint(3, 8)
        
        for i in range(events_count):
            event_time = random.randint(30, period_seconds - 30)
            self.current_time = event_time
            
            # Определяем тип события
            event_type = random.choices(
                ['goal', 'penalty', 'faceoff', 'shot'],
                weights=[20, 15, 30, 35]
            )[0]
            
            if event_type == 'goal':
                self._simulate_goal(period)
            elif event_type == 'penalty':
                self._simulate_penalty(period)
            elif event_type == 'faceoff':
                self._simulate_faceoff(period)
            elif event_type == 'shot':
                self._simulate_shot(period)
        
        # В конце периода добавляем итоговый счет
        self.current_time = period_seconds
    
    def _simulate_goal(self, period: int):
        """Симулирует гол"""
        # Определяем, какая команда забивает (учитывая рейтинг)
        if random.random() < self._get_goal_probability():
            scorer = self._get_random_player(self.team_a_on_ice, 'нападающий')
            self.score_a += 1
            team = self.team_a_name
            self._add_event(f"🥅 ГОЛ! {scorer['name']} {scorer.get('surname', '')} ({team}) забивает!", 
                          self.current_time, period)
        else:
            scorer = self._get_random_player(self.team_b_on_ice, 'нападающий')
            self.score_b += 1
            team = self.team_b_name
            self._add_event(f"🥅 ГОЛ! {scorer['name']} {scorer.get('surname', '')} ({team}) забивает!", 
                          self.current_time, period)
    
    def _get_goal_probability(self) -> float:
        """Возвращает вероятность гола для команды А"""
        total_rating = self.team_a_rating + self.team_b_rating
        if total_rating == 0:
            return 0.5
        return self.team_a_rating / total_rating
    
    def _simulate_penalty(self, period: int):
        """Симулирует нарушение"""
        teams = ['A', 'B']
        team_choice = random.choice(teams)
        
        if team_choice == 'A':
            player = self._get_random_player(self.team_a_on_ice)
            team = self.team_a_name
            penalty_minutes = random.choices([2, 5, 10], weights=[70, 20, 10])[0]
            self._add_event(f"⛔ {penalty_minutes} минуты штрафа! {player['name']} {player.get('surname', '')} ({team})", 
                          self.current_time, period)
        else:
            player = self._get_random_player(self.team_b_on_ice)
            team = self.team_b_name
            penalty_minutes = random.choices([2, 5, 10], weights=[70, 20, 10])[0]
            self._add_event(f"⛔ {penalty_minutes} минуты штрафа! {player['name']} {player.get('surname', '')} ({team})", 
                          self.current_time, period)
    
    def _simulate_faceoff(self, period: int):
        """Симулирует вбрасывание"""
        zones = ['центральная', 'зона А', 'зона Б']
        zone = random.choice(zones)
        self._add_event(f"🔄 Вбрасывание в {zone} зоне", self.current_time, period)
    
    def _simulate_shot(self, period: int):
        """Симулирует бросок"""
        if random.random() < 0.5:
            player = self._get_random_player(self.team_a_on_ice)
            team = self.team_a_name
            self._add_event(f"🎯 Бросок! {player['name']} {player.get('surname', '')} ({team})", 
                          self.current_time, period)
        else:
            player = self._get_random_player(self.team_b_on_ice)
            team = self.team_b_name
            self._add_event(f"🎯 Бросок! {player['name']} {player.get('surname', '')} ({team})", 
                          self.current_time, period)
    
    def _simulate_overtime(self):
        """Симулирует овертайм 3 на 3"""
        self.is_overtime = True
        overtime_seconds = self.overtime_duration * 60
        
        self._add_event(f"⚡ Начало овертайма! 3 на 3", 0, 0)
        
        # В овертайме играем до гола
        overtime_events = random.randint(1, 5)
        for i in range(overtime_events):
            event_time = random.randint(30, overtime_seconds - 30)
            self.current_time = event_time
            
            if random.random() < 0.3:  # Шанс гола в овертайме
                if random.random() < 0.5:
                    self.score_a += 1
                    self._add_event(f"🥅 ЗОЛОТОЙ ГОЛ! {self.team_a_name} побеждает в овертайме!", 
                                  event_time, 4)
                else:
                    self.score_b += 1
                    self._add_event(f"🥅 ЗОЛОТОЙ ГОЛ! {self.team_b_name} побеждает в овертайме!", 
                                  event_time, 4)
                break
        
        self.is_overtime = False
    
    def _simulate_shootout(self):
        """Симулирует буллиты"""
        self.is_shootout = True
        self._add_event(f"⚡ НАЧАЛО БУЛЛИТОВ!", 0, 0)
        
        # По 5 буллитов на команду
        shootout_a = 0
        shootout_b = 0
        
        for i in range(5):
            # Буллит команды А
            success_a = random.random() < 0.35
            if success_a:
                shootout_a += 1
                self.score_a += 1
                self._add_event(f"🎯 Буллит! {self.team_a_name} забивает!", 0, 0)
            else:
                self._add_event(f"❌ Буллит! {self.team_a_name} не забивает!", 0, 0)
            
            # Буллит команды Б
            success_b = random.random() < 0.35
            if success_b:
                shootout_b += 1
                self.score_b += 1
                self._add_event(f"🎯 Буллит! {self.team_b_name} забивает!", 0, 0)
            else:
                self._add_event(f"❌ Буллит! {self.team_b_name} не забивает!", 0, 0)
        
        self._add_event(f"🏆 Результат буллитов: {self.team_a_name} {shootout_a} - {shootout_b} {self.team_b_name}", 0, 0)
        self.is_shootout = False
    
    def _get_random_player(self, players: List[Dict], position: Optional[str] = None) -> Dict:
        """Возвращает случайного игрока из списка"""
        if position:
            filtered = [p for p in players if position in p['position']]
            if filtered:
                return random.choice(filtered)
        return random.choice(players) if players else {'name': 'Неизвестно', 'surname': ''}
    
    def _add_event(self, description: str, time: int, period: int):
        """Добавляет событие в историю матча"""
        minutes = time // 60
        seconds = time % 60
        
        if self.is_overtime:
            period_str = "OV"
        elif self.is_shootout:
            period_str = "SO"
        else:
            period_str = f"{period}"
        
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        event = {
            'time': time_str,
            'period': period_str,
            'description': description,
            'timestamp': datetime.now()
        }
        self.events.append(event)
        logging.info(f"[{time_str}] {description}")
    
    def get_match_summary(self) -> str:
        """Возвращает краткое описание матча"""
        if not self.match_result:
            return "Матч ещё не завершён"
        
        summary = f"🏒 <b>ИТОГИ МАТЧА</b>\n\n"
        summary += f"⚔️ {self.team_a_name} vs {self.team_b_name}\n"
        summary += f"📊 <b>{self.score_a} - {self.score_b}</b>\n\n"
        
        if self.match_result['winner']:
            summary += f"🏆 <b>Победитель: {self.match_result['winner']}</b>\n"
        else:
            summary += f"🤝 <b>Ничья</b>\n"
        
        summary += f"\n📈 Рейтинг команд:\n"
        summary += f"• {self.team_a_name}: {self.team_a_rating}\n"
        summary += f"• {self.team_b_name}: {self.team_b_rating}\n"
        
        return summary
    
    def get_events_log(self, limit: int = 20) -> str:
        """Возвращает лог событий"""
        if not self.events:
            return "Нет событий"
        
        events = self.events[-limit:] if len(self.events) > limit else self.events
        
        log = "📋 <b>СОБЫТИЯ МАТЧА</b>\n\n"
        for event in events:
            log += f"[{event['period']}:{event['time']}] {event['description']}\n"
        
        return log