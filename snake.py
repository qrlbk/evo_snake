"""
Змейка с мозгом и логикой игры.
"""

import numpy as np
from typing import List, Tuple, Optional
from brain import Brain


class Snake:
    """Змейка с эволюционным мозгом."""
    
    # Направления движения
    DIRECTIONS = {
        0: (0, -1),  # Вверх
        1: (0, 1),   # Вниз
        2: (-1, 0),  # Влево
        3: (1, 0)    # Вправо
    }
    
    def __init__(self, brain: Optional[Brain] = None, grid_size: int = 20):
        """
        Args:
            brain: экземпляр Brain или None для случайного мозга
            grid_size: размер игрового поля
        """
        self.grid_size = grid_size
        self.brain = brain if brain else Brain()
        
        # Начальное состояние
        self.reset()
    
    def reset(self):
        """Сброс состояния змейки для нового раунда."""
        # Начальная позиция в центре
        center = self.grid_size // 2
        self.body = [(center, center), (center - 1, center), (center - 2, center)]
        self.direction = 3  # Движение вправо
        self.fitness = 0
        self.steps = 0
        self.steps_without_food = 0
        self.alive = True
        
    def get_head(self) -> Tuple[int, int]:
        """Получить позицию головы."""
        return self.body[0]
    
    def get_view(self, food_pos: Tuple[int, int], walls: List[Tuple[int, int]] = None) -> np.ndarray:
        """
        Получить входные данные для мозга (визуальное поле).
        
        Args:
            food_pos: позиция еды (x, y)
            walls: список позиций стен [(x, y), ...]
            
        Returns:
            массив из 8 значений:
            [направление до еды (4 значения),
             опасности по направлениям (4 значения)]
        """
        head_x, head_y = self.get_head()
        food_x, food_y = food_pos
        
        # Направление до еды (one-hot вектор)
        dx = food_x - head_x
        dy = food_y - head_y
        direction_to_food = np.zeros(4)
        if abs(dx) > abs(dy):
            direction_to_food[3 if dx > 0 else 2] = 1
        else:
            direction_to_food[1 if dy > 0 else 0] = 1
        
        # Опасности в каждом направлении (расстояние до стены/препятствия)
        dangers = np.zeros(4)
        
        if walls is None:
            walls = []
        
        for i, (dir_x, dir_y) in enumerate(self.DIRECTIONS.values()):
            dist = 0
            check_x, check_y = head_x, head_y
            
            while True:
                check_x += dir_x
                check_y += dir_y
                
                # Проверка границ
                if (check_x < 0 or check_x >= self.grid_size or 
                    check_y < 0 or check_y >= self.grid_size):
                    break
                
                # Проверка собственного тела
                if (check_x, check_y) in self.body:
                    break
                
                # Проверка стен
                if (check_x, check_y) in walls:
                    break
                
                dist += 1
            
            # Нормализация расстояния опасности
            dangers[i] = 1.0 / (1.0 + dist)
        
        return np.concatenate([direction_to_food, dangers])
    
    def move(self, action: int, walls: List[Tuple[int, int]] = None) -> bool:
        """
        Движение змейки на основе действия.
        
        Args:
            action: индекс направления (0-3)
            walls: список позиций стен [(x, y), ...]
            
        Returns:
            True если движение успешно, False если столкновение
        """
        if not self.alive:
            return False
        
        # Проверка на смерть от голода (>8 секунд без еды = 80 шагов при 10 fps)
        if self.steps_without_food > 80:
            self.alive = False
            return False
        
        self.direction = action
        dir_x, dir_y = self.DIRECTIONS[action]
        head_x, head_y = self.get_head()
        
        # Новая позиция головы
        new_head = (head_x + dir_x, head_y + dir_y)
        
        if walls is None:
            walls = []
        
        # Проверка столкновений
        if (new_head[0] < 0 or new_head[0] >= self.grid_size or
            new_head[1] < 0 or new_head[1] >= self.grid_size or
            new_head in self.body or
            new_head in walls):  # Проверка на стены
            # Столкновение - змейка мертва
            self.alive = False
            # ВАЖНО: увеличиваем время БЕЗ еды даже при смерти от стены
            # чтобы голод продолжал расти, показывая реальную ситуацию
            self.steps_without_food += 1
            return False
        
        # Добавление новой головы
        self.body.insert(0, new_head)
        
        self.steps += 1
        self.steps_without_food += 1
        
        return True
    
    def eat(self):
        """Змейка съедает еду."""
        # Увеличенная награда за еду + бонус за скорость
        base_reward = 150
        speed_bonus = max(0, 50 - self.steps_without_food)  # Бонус за быструю еду
        self.fitness += base_reward + speed_bonus
        self.steps_without_food = 0
        # Хвост не удаляется - змейка растёт
    
    def remove_tail(self):
        """Удаление хвоста (когда не съела еду)."""
        if len(self.body) > 3:  # Минимальный размер змейки
            self.body.pop()
    
    def update_fitness(self):
        """Обновление fitness с учётом времени выживания."""
        if self.alive:
            # Уменьшена награда за выживание (было 0.5, стало 0.2)
            self.fitness += 0.2
            # Штраф за бездействие (если не ест >50 шагов)
            if self.steps_without_food > 50:
                self.fitness -= 1.0  # Увеличено ×2
    
    def get_fitness(self) -> float:
        """Получить финальный fitness."""
        # Строгий штраф за чрезмерное блуждание без еды
        if self.steps_without_food > 70:
            # Критический штраф за полное застревание (максимальный штраф)
            self.fitness *= 0.5
        elif self.steps_without_food > 60:
            # Прогрессивный штраф: чем дольше, тем больше
            penalty = (self.steps_without_food - 60) * 0.6
            self.fitness -= penalty
        return max(0, self.fitness)  # Не может быть отрицательным
    
    def clone(self) -> 'Snake':
        """Создание копии змейки."""
        return Snake(brain=self.brain.clone(), grid_size=self.grid_size)

