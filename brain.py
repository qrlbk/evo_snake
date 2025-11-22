"""
Мозг змейки - простая нейронная сеть с матрицей весов.
Преобразует входные данные (расстояния, направления) в действия.
"""

import numpy as np


class Brain:
    """Улучшенный мозг с скрытым слоем для более сложного мышления."""
    
    def __init__(self, input_size: int = 12, hidden_size: int = 16, output_size: int = 4, 
                 weights: np.ndarray = None, hidden_weights: np.ndarray = None):
        """
        Args:
            input_size: количество входных признаков (увеличено до 12)
            hidden_size: размер скрытого слоя (16 нейронов для "мышления")
            output_size: количество возможных действий
            weights: веса скрытого слоя (input -> hidden)
            hidden_weights: веса выходного слоя (hidden -> output)
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        if weights is not None and hidden_weights is not None:
            # Загрузка существующих весов
            self.weights = weights.copy()  # input -> hidden
            self.hidden_weights = hidden_weights.copy()  # hidden -> output
        else:
            # Инициализация весов в диапазоне [-1, 1]
            # Скрытый слой: input_size -> hidden_size
            self.weights = np.random.uniform(-1, 1, (input_size, hidden_size))
            # Выходной слой: hidden_size -> output_size
            self.hidden_weights = np.random.uniform(-1, 1, (hidden_size, output_size))
    
    def think(self, inputs: np.ndarray) -> int:
        """
        Обработка входных данных через скрытый слой и генерация действия.
        
        Args:
            inputs: массив входных данных (12 значений)
            
        Returns:
            индекс выбранного действия (0-3: вверх, вниз, влево, вправо)
        """
        # Нормализация входов для стабильности
        inputs = np.clip(inputs, -10, 10)
        
        # Первый слой: входы -> скрытый слой (с активацией ReLU для "мышления")
        hidden = np.dot(inputs, self.weights)
        hidden = np.maximum(0, hidden)  # ReLU активация
        
        # Второй слой: скрытый -> выходы
        output = np.dot(hidden, self.hidden_weights)
        
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
        # Мутация первого слоя (input -> hidden)
        new_weights = self.weights.copy()
        mutation_mask = np.random.random(self.weights.shape) < mutation_rate
        noise = np.random.normal(0, mutation_strength, self.weights.shape)
        new_weights[mutation_mask] += noise[mutation_mask]
        
        # Мутация второго слоя (hidden -> output)
        new_hidden_weights = self.hidden_weights.copy()
        mutation_mask_hidden = np.random.random(self.hidden_weights.shape) < mutation_rate
        noise_hidden = np.random.normal(0, mutation_strength, self.hidden_weights.shape)
        new_hidden_weights[mutation_mask_hidden] += noise_hidden[mutation_mask_hidden]
        
        # Иногда добавляем сильную случайную мутацию (10% вероятность)
        if np.random.random() < 0.1:
            # Сильная мутация первого слоя
            strong_mask = np.random.random(self.weights.shape) < 0.3
            new_weights[strong_mask] = np.random.uniform(-1, 1, size=np.sum(strong_mask))
            # Сильная мутация второго слоя
            strong_mask_hidden = np.random.random(self.hidden_weights.shape) < 0.3
            new_hidden_weights[strong_mask_hidden] = np.random.uniform(-1, 1, size=np.sum(strong_mask_hidden))
        
        return Brain(weights=new_weights, hidden_weights=new_hidden_weights)
    
    def clone(self) -> 'Brain':
        """Создание точной копии мозга."""
        return Brain(weights=self.weights, hidden_weights=self.hidden_weights)

