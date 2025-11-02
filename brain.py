"""
Мозг змейки - простая нейронная сеть с матрицей весов.
Преобразует входные данные (расстояния, направления) в действия.
"""

import numpy as np


class Brain:
    """Простой мозг на основе матричного умножения."""
    
    def __init__(self, input_size: int = 8, output_size: int = 4, weights: np.ndarray = None):
        """
        Args:
            input_size: количество входных признаков
            output_size: количество возможных действий
            weights: существующие веса (для клонирования)
        """
        if weights is not None:
            self.weights = weights.copy()
        else:
            # Инициализация весов в диапазоне [-1, 1]
            self.weights = np.random.uniform(-1, 1, (input_size, output_size))
    
    def think(self, inputs: np.ndarray) -> int:
        """
        Обработка входных данных и генерация действия.
        
        Args:
            inputs: массив входных данных (8 значений)
            
        Returns:
            индекс выбранного действия (0-3: вверх, вниз, влево, вправо)
        """
        # Нормализация входов для стабильности
        inputs = np.clip(inputs, -10, 10)
        
        # Линейное преобразование
        output = np.dot(inputs, self.weights)
        
        # Softmax для вероятностного выбора
        exp_output = np.exp(output - np.max(output))
        probabilities = exp_output / np.sum(exp_output)
        
        # Выбор действия на основе вероятностей
        return np.random.choice(len(output), p=probabilities)
    
    def mutate(self, mutation_rate: float = 0.1, mutation_strength: float = 0.2) -> 'Brain':
        """
        Создание мутированной версии мозга.
        
        Args:
            mutation_rate: вероятность мутации каждого веса (0-1)
            mutation_strength: сила мутации (стандартное отклонение)
            
        Returns:
            новый экземпляр Brain с мутированными весами
        """
        new_weights = self.weights.copy()
        
        # Мутация только части весов
        mutation_mask = np.random.random(self.weights.shape) < mutation_rate
        noise = np.random.normal(0, mutation_strength, self.weights.shape)
        new_weights[mutation_mask] += noise[mutation_mask]
        
        # Иногда добавляем сильную случайную мутацию (10% вероятность полной мутации)
        if np.random.random() < 0.1:
            # Сильная мутация: меняем ~30% весов радикально
            strong_mask = np.random.random(self.weights.shape) < 0.3
            new_weights[strong_mask] = np.random.uniform(-1, 1, size=np.sum(strong_mask))
        
        return Brain(weights=new_weights)
    
    def clone(self) -> 'Brain':
        """Создание точной копии мозга."""
        return Brain(weights=self.weights)

