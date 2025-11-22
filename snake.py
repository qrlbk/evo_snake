"""
Змейка с мозгом и логикой игры.
"""

import numpy as np
import time
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
        self.steps_without_food = 0  # Оставляем для совместимости
        self.last_food_time = time.time()  # Время последнего поедания еды (в секундах)
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
            массив из 12 значений:
            [направление до еды (4 значения),
             опасности по направлениям (4 значения),
             длина змейки (нормализованная),
             время без еды (нормализованное),
             расстояние до еды (нормализованное),
             свободное пространство (нормализованное)]
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
                
                # Оптимизация: проверка собственного тела (исключаем хвост для скорости)
                body_without_tail = self.body[:-1] if len(self.body) > 1 else []
                if (check_x, check_y) in body_without_tail:
                    break
                
                # Проверка стен
                if (check_x, check_y) in walls:
                    break
                
                dist += 1
            
            # Нормализация расстояния опасности
            dangers[i] = 1.0 / (1.0 + dist)
        
        # Дополнительная информация для "мышления"
        # Длина змейки (нормализованная: 0-1, где 1 = максимальная длина)
        max_length = self.grid_size * self.grid_size
        normalized_length = len(self.body) / max_length
        
        # Время без еды (нормализованное: 0-1, где 1 = голоден до смерти)
        time_without_food = self.get_time_without_food()
        normalized_hunger = min(1.0, time_without_food / 8.0)
        
        # Расстояние до еды (нормализованное: 0-1, где 0 = еда рядом)
        dist_to_food = abs(dx) + abs(dy)
        max_dist = self.grid_size * 2
        normalized_distance = min(1.0, dist_to_food / max_dist)
        
        # Свободное пространство (сколько клеток свободно вокруг)
        free_space = 0
        for check_dir in self.DIRECTIONS.values():
            check_x = head_x + check_dir[0]
            check_y = head_y + check_dir[1]
            if (0 <= check_x < self.grid_size and 0 <= check_y < self.grid_size and
                (check_x, check_y) not in self.body):
                free_space += 1
        normalized_space = free_space / 4.0  # Максимум 4 направления
        
        # Объединяем все входы
        additional_info = np.array([
            normalized_length,
            normalized_hunger,
            normalized_distance,
            normalized_space
        ])
        
        return np.concatenate([direction_to_food, dangers, additional_info])
    
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
        
        # ПРИМЕЧАНИЕ: Проверка голода теперь в environment.py, чтобы голод рос даже при остановке
        
        self.direction = action
        dir_x, dir_y = self.DIRECTIONS[action]
        head_x, head_y = self.get_head()
        
        # Новая позиция головы
        new_head = (head_x + dir_x, head_y + dir_y)
        
        if walls is None:
            walls = []
        
        # Проверка столкновений
        # ВАЖНО: Проверяем столкновение с телом, ИСКЛЮЧАЯ хвост (последний элемент),
        # потому что хвост будет удален после движения, если не съедена еда
        body_without_tail = self.body[:-1] if len(self.body) > 1 else []
        
        if (new_head[0] < 0 or new_head[0] >= self.grid_size or
            new_head[1] < 0 or new_head[1] >= self.grid_size or
            new_head in body_without_tail or
            new_head in walls):  # Проверка на стены
            # Столкновение - змейка мертва
            self.alive = False
            # ПРИМЕЧАНИЕ: steps_without_food теперь увеличивается в environment.py на каждом шаге
            return False
        
        # Добавление новой головы
        self.body.insert(0, new_head)
        
        self.steps += 1
        # ПРИМЕЧАНИЕ: steps_without_food теперь увеличивается в environment.py на каждом шаге
        
        return True
    
    def eat(self):
        """Змейка съедает еду."""
        # Увеличенная награда за еду + бонус за скорость
        base_reward = 150
        # Бонус за быструю еду (по времени, не по шагам)
        time_without_food = self.get_time_without_food()
        speed_bonus = max(0, 50 - int(time_without_food * 10))  # Бонус уменьшается со временем
        self.fitness += base_reward + speed_bonus
        self.steps_without_food = 0
        self.last_food_time = time.time()  # Обновляем время последнего поедания
        # Хвост не удаляется - змейка растёт
    
    def get_time_without_food(self) -> float:
        """Получить время без еды в секундах."""
        # Оптимизация: используем кэшированное время если доступно
        check_time = getattr(self, '_current_time', time.time())
        return check_time - self.last_food_time
    
    def get_hunger_percent(self, max_hunger_seconds: float = 8.0) -> float:
        """
        Получить процент голода (0.0 = сыт, 1.0 = голоден до смерти).
        
        Args:
            max_hunger_seconds: максимальное время без еды в секундах до смерти
        """
        time_without = self.get_time_without_food()
        return min(1.0, time_without / max_hunger_seconds)
    
    def remove_tail(self):
        """Удаление хвоста (когда не съела еду)."""
        if len(self.body) > 3:  # Минимальный размер змейки
            self.body.pop()
    
    def update_fitness(self):
        """Обновление fitness с учётом времени выживания."""
        if self.alive:
            # Уменьшена награда за выживание (было 0.5, стало 0.2)
            self.fitness += 0.2
            # Штраф за бездействие (если не ест >5 секунд)
            time_without = self.get_time_without_food()
            if time_without > 5.0:
                self.fitness -= 1.0 * (time_without - 5.0)  # Штраф растёт со временем
    
    def get_fitness(self) -> float:
        """Получить финальный fitness."""
        # Строгий штраф за чрезмерное блуждание без еды (по времени)
        time_without = self.get_time_without_food()
        if time_without > 7.0:
            # Критический штраф за полное застревание (максимальный штраф)
            self.fitness *= 0.5
        elif time_without > 6.0:
            # Прогрессивный штраф: чем дольше, тем больше
            penalty = (time_without - 6.0) * 10.0
            self.fitness -= penalty
        return max(0, self.fitness)  # Не может быть отрицательным
    
    def clone(self) -> 'Snake':
        """Создание копии змейки."""
        return Snake(brain=self.brain.clone(), grid_size=self.grid_size)

