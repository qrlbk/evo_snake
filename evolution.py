"""
Эволюционный алгоритм для популяции змеек.
"""

import numpy as np
from typing import List, Tuple
from snake import Snake
from environment import Environment


class Evolution:
    """Управление эволюцией популяции."""
    
    def __init__(
        self,
        population_size: int = 100,
        grid_size: int = 20,
        elite_size: int = 10,
        mutation_rate: float = 0.1,
        mutation_strength: float = 0.2,
        max_steps: int = 500
    ):
        """
        Args:
            population_size: размер популяции
            grid_size: размер игрового поля
            elite_size: количество лучших особей для размножения
            mutation_rate: вероятность мутации
            mutation_strength: сила мутации
            max_steps: максимальное количество шагов в игре
        """
        self.population_size = population_size
        self.grid_size = grid_size
        self.elite_size = elite_size
        self.mutation_rate = mutation_rate
        self.mutation_strength = mutation_strength
        self.max_steps = max_steps
        
        self.environment = Environment(grid_size)
        self.population = [Snake(grid_size=grid_size) for _ in range(population_size)]
        
        self.generation = 0
        self.best_fitness_history = []
        self.avg_fitness_history = []
        self.best_snake = None
        self.best_fitness_in_history = 0
        self.current_best_snake = None
        self.current_best_fitness = 0
    
    def evaluate_generation(self) -> List[float]:
        """
        Оценка всех особей в популяции.
        
        Returns:
            список fitness для каждой особи
        """
        # Адаптивный размер поля: уменьшается с поколением для усложнения
        # 20 -> 18 -> 16 -> 14 -> 12
        adaptive_grid = max(12, self.grid_size - (self.generation // 50))
        if adaptive_grid != self.environment.grid_size:
            # Меняем размер поля
            self.environment.grid_size = adaptive_grid
            for snake in self.population:
                snake.grid_size = adaptive_grid
        
        fitness_scores = []
        
        # Прогрессивное уменьшение max_steps по поколениям
        # 0-50 gen: 500 шагов, 50-100: 400, 100-150: 350, 150+: 300
        dynamic_steps = self.max_steps
        if self.generation > 150:
            dynamic_steps = 300
        elif self.generation > 100:
            dynamic_steps = 350
        elif self.generation > 50:
            dynamic_steps = 400
        
        for snake in self.population:
            fitness = self.environment.play_game(snake, dynamic_steps)
            fitness_scores.append(fitness)
        
        return fitness_scores
    
    def evolve(self):
        """Провести один цикл эволюции."""
        # Обновляем поколение в окружении для генерации стен
        self.environment.generation = self.generation
        
        # Оценка текущей популяции
        fitness_scores = self.evaluate_generation()
        
        # Статистика
        best_fitness = max(fitness_scores)
        avg_fitness = np.mean(fitness_scores)
        self.best_fitness_history.append(best_fitness)
        self.avg_fitness_history.append(avg_fitness)
        
        # Сортировка по fitness
        sorted_indices = np.argsort(fitness_scores)[::-1]
        
        # Сохраняем лучшую змейку и её fitness
        # Клонируем ДО создания нового поколения, т.к. после clone() мозг будет в чистом состоянии
        if best_fitness > self.best_fitness_in_history:
            self.best_snake = self.population[sorted_indices[0]].clone()
            self.best_fitness_in_history = best_fitness
        
        # Сохраняем текущего лучшего для последующего сохранения в БД
        self.current_best_snake = self.population[sorted_indices[0]]
        self.current_best_fitness = best_fitness
        
        # Элита (лучшие особи)
        elite = [self.population[i] for i in sorted_indices[:self.elite_size]]
        
        # Создание нового поколения
        new_population = []
        
        # Сохраняем элиту без мутаций (частично)
        for snake in elite[:self.elite_size // 2]:
            new_population.append(snake.clone())
        
        # Создаём потомков с мутациями
        while len(new_population) < self.population_size:
            # Выбор случайного родителя из элиты
            parent = np.random.choice(elite)
            
            # Клонирование и мутация
            child = parent.clone()
            child.brain = parent.brain.mutate(self.mutation_rate, self.mutation_strength)
            new_population.append(child)
        
        self.population = new_population
        self.generation += 1
        
        return best_fitness, avg_fitness
    
    def get_stats(self) -> Tuple[int, float, float]:
        """
        Получить статистику текущего поколения.
        
        Returns:
            (номер поколения, лучший fitness, средний fitness)
        """
        return (
            self.generation,
            self.best_fitness_history[-1] if self.best_fitness_history else 0,
            self.avg_fitness_history[-1] if self.avg_fitness_history else 0
        )
    
    def get_best_snake(self) -> Snake:
        """Получить лучшую змейку текущего поколения."""
        if self.best_snake is None:
            # Если ещё не оценено, возвращаем случайную
            return self.population[0]
        return self.best_snake
