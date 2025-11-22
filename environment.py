"""
Игровая среда для змейки.
"""

import random
import time
import numpy as np
from typing import Tuple, List
from snake import Snake


class Environment:
    """Игровая среда с едой и управлением."""
    
    def __init__(self, grid_size: int = 20):
        """
        Args:
            grid_size: размер игрового поля (grid_size x grid_size)
        """
        self.grid_size = grid_size
        self.food_positions = [(0, 0)]  # Список позиций еды
        self.generation = 0  # Текущее поколение для расчета сложности
        # Препятствия удалены - пустые списки для совместимости
        self.walls = []
        self.moving_walls = []
        self.poisons = []
        self.bonuses = []
    
    def reset_walls(self):
        """Генерация стен отключена - препятствия убраны."""
        self.walls = []
        self.moving_walls = []
    
    def reset_food(self, occupied: List[Tuple[int, int]] = None, num_food: int = 1):
        """Создание новой еды в случайных позициях."""
        if occupied is None:
            occupied = []
        
        # Получаем свободные позиции (стены удалены)
        free_positions = self.get_free_positions(occupied)
        
        self.food_positions = []
        # Количество еды зависит от поколения: больше поколение = больше еды
        num_food = max(1, min(3, 1 + self.generation // 50))  # 1-3 еды
        
        for _ in range(min(num_food, len(free_positions))):
            if free_positions:
                pos = random.choice(free_positions)
                self.food_positions.append(pos)
                free_positions.remove(pos)  # Убираем, чтобы не дублировать
        
        # Если нет свободных позиций, выбираем случайные
        if not self.food_positions:
            self.food_positions = [(
                random.randint(0, self.grid_size - 1),
                random.randint(0, self.grid_size - 1)
            )]
    
    def reset_poisons_and_bonuses(self, occupied: List[Tuple[int, int]] = None):
        """Генерация ядов и бонусов отключена - препятствия убраны."""
        self.poisons = []
        self.bonuses = []
    
    @property
    def food_pos(self):
        """Возвращает ближайшую еду для совместимости со старым кодом."""
        return self.food_positions[0] if self.food_positions else (0, 0)
    
    def play_game(self, snake: Snake, max_steps: int = 500) -> float:
        """
        Запуск игры для змейки.
        
        Args:
            snake: змейка для игры
            max_steps: максимальное количество шагов
            
        Returns:
            финальный fitness змейки
        """
        snake.reset()
        # Препятствия удалены - только еда
        self.reset_walls()
        # Убедимся, что начальная еда не на змейке
        self.reset_food(occupied=snake.body)
        # Яды и бонусы отключены
        self.reset_poisons_and_bonuses(occupied=snake.body)
        
        # Максимальный размер поля (для проверки победы)
        max_grid_size = self.grid_size * self.grid_size
        
        for step in range(max_steps):
            if not snake.alive:
                break
            
            # Проверка победы: змейка заполнила всё поле
            if len(snake.body) >= max_grid_size:
                # Огромный бонус за победу
                snake.fitness += 10000.0
                snake.alive = False  # Завершаем игру
                break
            
            # Проверка на смерть от голода (по времени, не по шагам)
            # Максимум 8 секунд без еды = смерть
            time_without_food = snake.get_time_without_food()
            if time_without_food > 8.0:
                snake.alive = False
                break
            
            # Для совместимости увеличиваем steps_without_food (но проверка по времени)
            snake.steps_without_food += 1
            
            # Получение входных данных для мозга (без препятствий)
            inputs = snake.get_view(self.food_pos, walls=[])
            
            # Мозг принимает решение
            action = snake.brain.think(inputs)
            
            # Движение (без препятствий)
            # Если движение неудачно, продолжаем цикл (голод уже увеличился)
            move_success = snake.move(action, walls=[])
            
            # Если змейка мертва после движения, выходим
            if not snake.alive:
                break
            
            # Проверка поедания еды (несколько еды одновременно)
            head_pos = snake.get_head()
            food_eaten = False
            for i, food_pos in enumerate(self.food_positions):
                if head_pos == food_pos:
                    snake.eat()
                    self.food_positions.pop(i)
                    food_eaten = True
                    if len(self.food_positions) < 2:
                        self.reset_food(occupied=snake.body)
                    break
            
            # Удаление хвоста только если движение было успешным и еда не съедена
            if move_success and not food_eaten:
                snake.remove_tail()
            
            # Обновление fitness (даже если змейка не двигалась)
            snake.update_fitness()
            
            # Дополнительная награда за приближение к еде (только если змейка жива)
            if snake.alive:
                head = snake.get_head()
                dist_to_food = abs(head[0] - self.food_pos[0]) + abs(head[1] - self.food_pos[1])
                # Уменьшенная награда за приближение (макс 5)
                snake.fitness += 5.0 / (dist_to_food + 1)
        
        return snake.get_fitness()
    
    def get_free_positions(self, occupied: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Получить список свободных позиций.
        
        Args:
            occupied: список занятых позиций
            
        Returns:
            список свободных позиций
        """
        free = []
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                if (x, y) not in occupied:
                    free.append((x, y))
        return free

