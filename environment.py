"""
Игровая среда для змейки.
"""

import random
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
        self.walls = []  # Список стен (общих для всех змеек в одном поколении)
        self.generation = 0  # Текущее поколение для расчета сложности
        self.wall_density = 0.0  # Плотность стен (0-1)
        self.poisons = []  # Яды (смертельны)
        self.bonuses = []  # Бонусы (2x очки)
        self.moving_walls = []  # Движущиеся стены [(x, y, dir_x, dir_y), ...]
    
    def reset_walls(self):
        """Генерация стен на основе сложности поколения."""
        # Увеличиваем сложность постепенно: стены появляются с 0 поколения!
        # 0-20: 0-2 стен, 20-50: 3-8, 50-100: 8-15, 100+: до 25 стен
        if self.generation < 20:
            num_walls = self.generation // 10  # 0, 1, 2
        elif self.generation < 50:
            num_walls = 3 + (self.generation - 20) // 5  # 3-8
        elif self.generation < 100:
            num_walls = 8 + (self.generation - 50) // 7  # 8-15
        else:
            num_walls = min(25, 15 + (self.generation - 100) // 50)  # 15-25
        
        self.wall_density = num_walls / (self.grid_size * self.grid_size)
        
        # Генерация случайных стен
        self.walls = []
        self.moving_walls = []
        max_attempts = 100
        attempts = 0
        
        # Разделяем на статичные и движущиеся стены
        num_moving = max(0, (num_walls - 5) // 3) if self.generation > 30 else 0  # С поколения 30
        num_static = num_walls - num_moving
        
        while len(self.walls) < num_static and attempts < max_attempts:
            attempts += 1
            x = random.randint(0, self.grid_size - 1)
            y = random.randint(0, self.grid_size - 1)
            
            # Не ставим стену в центре (где начинается змейка)
            center = self.grid_size // 2
            if abs(x - center) < 3 and abs(y - center) < 3:
                continue
            
            # Не ставим стену там, где уже есть стена
            if (x, y) not in self.walls:
                self.walls.append((x, y))
        
        # Генерация движущихся стен
        attempts = 0
        while len(self.moving_walls) < num_moving and attempts < max_attempts:
            attempts += 1
            x = random.randint(1, self.grid_size - 2)
            y = random.randint(1, self.grid_size - 2)
            center = self.grid_size // 2
            if abs(x - center) < 3 and abs(y - center) < 3:
                continue
            
            # Случайное направление движения
            dir_x, dir_y = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            
            if (x, y) not in [w[:2] for w in self.moving_walls]:
                self.moving_walls.append((x, y, dir_x, dir_y))
    
    def reset_food(self, occupied: List[Tuple[int, int]] = None, num_food: int = 1):
        """Создание новой еды в случайных позициях."""
        if occupied is None:
            occupied = []
        
        # Добавляем стены в список занятых позиций
        occupied = list(occupied) + self.walls
        
        # Получаем свободные позиции
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
        """Генерация ядов и бонусов."""
        if occupied is None:
            occupied = []
        occupied = list(occupied) + self.walls + self.food_positions
        
        # Добавляем движущиеся стены в занятые
        for x, y, _, _ in self.moving_walls:
            occupied.append((x, y))
        
        free_positions = self.get_free_positions(occupied)
        
        # Яды появляются с поколения 40
        num_poisons = max(0, (self.generation - 40) // 20) if self.generation > 40 else 0
        self.poisons = []
        for _ in range(min(num_poisons, len(free_positions))):
            if free_positions:
                pos = random.choice(free_positions)
                self.poisons.append(pos)
                free_positions.remove(pos)
        
        # Бонусы появляются с поколения 50
        num_bonuses = max(0, (self.generation - 50) // 30) if self.generation > 50 else 0
        self.bonuses = []
        for _ in range(min(num_bonuses, len(free_positions))):
            if free_positions:
                pos = random.choice(free_positions)
                self.bonuses.append(pos)
                free_positions.remove(pos)
    
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
        # Генерируем стены для нового раунда
        self.reset_walls()
        # Убедимся, что начальная еда не на змейке и не на стенах
        self.reset_food(occupied=snake.body)
        # Генерируем яды и бонусы
        self.reset_poisons_and_bonuses(occupied=snake.body)
        
        for step in range(max_steps):
            if not snake.alive:
                break
            
            # Движение движущихся стен
            for i in range(len(self.moving_walls)):
                x, y, dir_x, dir_y = self.moving_walls[i]
                new_x, new_y = x + dir_x, y + dir_y
                
                # Отражение от границ
                if new_x < 1 or new_x >= self.grid_size - 1:
                    dir_x = -dir_x
                    new_x = x + dir_x
                if new_y < 1 or new_y >= self.grid_size - 1:
                    dir_y = -dir_y
                    new_y = y + dir_y
                
                self.moving_walls[i] = (new_x, new_y, dir_x, dir_y)
            
            # Получение входных данных для мозга
            all_walls = self.walls + [(x, y) for x, y, _, _ in self.moving_walls]
            inputs = snake.get_view(self.food_pos, walls=all_walls)
            
            # Мозг принимает решение
            action = snake.brain.think(inputs)
            
            # Движение
            if not snake.move(action, walls=all_walls):
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
            
            # Проверка ядов
            for poison_pos in self.poisons:
                if head_pos == poison_pos:
                    snake.alive = False  # Смерть от яда
                    break
            
            # Проверка бонусов
            for i, bonus_pos in enumerate(self.bonuses):
                if head_pos == bonus_pos:
                    # 2x очки
                    snake.fitness += snake.fitness * 0.5  # Бонус 50%
                    self.bonuses.pop(i)
                    break
            
            if not food_eaten:
                snake.remove_tail()
            
            # Обновление fitness
            snake.update_fitness()
            
            # Дополнительная награда за приближение к еде (уменьшена)
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

