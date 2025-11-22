"""
Мозг змейки - простая нейронная сеть с матрицей весов.
Преобразует входные данные (расстояния, направления) в действия.
"""

import numpy as np


class Brain:
    """Улучшенный мозг с двумя скрытыми слоями для более сложного мышления."""
    
    def __init__(self, input_size: int = 16, hidden1_size: int = 32, hidden2_size: int = 16, output_size: int = 4, 
                 weights: np.ndarray = None, hidden_weights: np.ndarray = None,
                 hidden1_weights: np.ndarray = None, hidden2_weights: np.ndarray = None,
                 weights2: np.ndarray = None, weights3: np.ndarray = None):
        """
        Args:
            input_size: количество входных признаков (увеличено до 16)
            hidden1_size: размер первого скрытого слоя (32 нейрона)
            hidden2_size: размер второго скрытого слоя (16 нейронов)
            output_size: количество возможных действий
            weights: веса первого слоя (input -> hidden1) - для обратной совместимости
            hidden_weights: веса выходного слоя (hidden -> output) - для обратной совместимости
            hidden1_weights: веса первого скрытого слоя (input -> hidden1)
            hidden2_weights: объединенные веса (hidden1 -> hidden2 -> output) - устаревший формат
            weights2: веса второго скрытого слоя (hidden1 -> hidden2) - новый формат
            weights3: веса выходного слоя (hidden2 -> output) - новый формат
        """
        self.input_size = input_size
        self.hidden1_size = hidden1_size
        self.hidden2_size = hidden2_size
        self.output_size = output_size
        
        # Новый формат: weights2 и weights3 переданы отдельно
        if weights2 is not None and weights3 is not None:
            self.weights1 = hidden1_weights.copy() if hidden1_weights is not None else np.random.uniform(-1, 1, (input_size, hidden1_size))
            self.weights2 = weights2.copy()
            self.weights3 = weights3.copy()
        # Обратная совместимость: старый формат (weights, hidden_weights)
        elif weights is not None and hidden_weights is not None:
            # Старый формат: один скрытый слой
            old_hidden_size = weights.shape[1]
            # Конвертируем в новый формат
            self.weights1 = weights.copy()  # input -> hidden1 (расширяем если нужно)
            if self.weights1.shape[1] != hidden1_size:
                # Расширяем до нового размера
                if self.weights1.shape[1] < hidden1_size:
                    extra = np.random.uniform(-0.5, 0.5, (input_size, hidden1_size - self.weights1.shape[1]))
                    self.weights1 = np.concatenate([self.weights1, extra], axis=1)
                else:
                    self.weights1 = self.weights1[:, :hidden1_size]
            # Создаем второй скрытый слой
            self.weights2 = np.random.uniform(-0.5, 0.5, (hidden1_size, hidden2_size))
            # Выходной слой из старого формата
            if hidden_weights.shape[0] == old_hidden_size:
                # Адаптируем старые веса
                self.weights3 = np.random.uniform(-0.5, 0.5, (hidden2_size, output_size))
            else:
                self.weights3 = np.random.uniform(-0.5, 0.5, (hidden2_size, output_size))
        elif hidden1_weights is not None and hidden2_weights is not None:
            # Старый формат объединения: hidden2_weights содержит оба слоя
            # Это устаревший формат, но поддерживаем для обратной совместимости
            self.weights1 = hidden1_weights.copy()  # input -> hidden1
            # hidden2_weights должен иметь форму (hidden1_size, hidden2_size + output_size)
            # Но это неправильно, поэтому создаем новые веса
            if hidden2_weights.shape == (hidden1_size, hidden2_size + output_size):
                self.weights2 = hidden2_weights[:, :hidden2_size].copy()
                self.weights3 = hidden2_weights[:, hidden2_size:].copy()
            else:
                # Неправильный формат - создаем новые веса
                self.weights2 = np.random.uniform(-0.5, 0.5, (hidden1_size, hidden2_size))
                self.weights3 = np.random.uniform(-0.5, 0.5, (hidden2_size, output_size))
        else:
            # Инициализация весов в диапазоне [-1, 1]
            # Первый скрытый слой: input_size -> hidden1_size
            self.weights1 = np.random.uniform(-1, 1, (input_size, hidden1_size))
            # Второй скрытый слой: hidden1_size -> hidden2_size
            self.weights2 = np.random.uniform(-1, 1, (hidden1_size, hidden2_size))
            # Выходной слой: hidden2_size -> output_size
            self.weights3 = np.random.uniform(-1, 1, (hidden2_size, output_size))
    
    def think(self, inputs: np.ndarray) -> int:
        """
        Обработка входных данных через два скрытых слоя и генерация действия.
        
        Args:
            inputs: массив входных данных (16 значений)
            
        Returns:
            индекс выбранного действия (0-3: вверх, вниз, влево, вправо)
        """
        # Нормализация входов для стабильности
        inputs = np.clip(inputs, -10, 10)
        
        # Первый скрытый слой: входы -> hidden1 (с активацией ReLU)
        hidden1 = np.dot(inputs, self.weights1)
        hidden1 = np.maximum(0, hidden1)  # ReLU активация
        
        # Второй скрытый слой: hidden1 -> hidden2 (с активацией ReLU)
        hidden2 = np.dot(hidden1, self.weights2)
        hidden2 = np.maximum(0, hidden2)  # ReLU активация
        
        # Выходной слой: hidden2 -> выходы
        output = np.dot(hidden2, self.weights3)
        
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
        # Мутация первого слоя (input -> hidden1)
        new_weights1 = self.weights1.copy()
        mutation_mask1 = np.random.random(self.weights1.shape) < mutation_rate
        noise1 = np.random.normal(0, mutation_strength, self.weights1.shape)
        new_weights1[mutation_mask1] += noise1[mutation_mask1]
        
        # Мутация второго слоя (hidden1 -> hidden2)
        new_weights2 = self.weights2.copy()
        mutation_mask2 = np.random.random(self.weights2.shape) < mutation_rate
        noise2 = np.random.normal(0, mutation_strength, self.weights2.shape)
        new_weights2[mutation_mask2] += noise2[mutation_mask2]
        
        # Мутация выходного слоя (hidden2 -> output)
        new_weights3 = self.weights3.copy()
        mutation_mask3 = np.random.random(self.weights3.shape) < mutation_rate
        noise3 = np.random.normal(0, mutation_strength, self.weights3.shape)
        new_weights3[mutation_mask3] += noise3[mutation_mask3]
        
        # Иногда добавляем сильную случайную мутацию (10% вероятность)
        if np.random.random() < 0.1:
            # Сильная мутация всех слоев
            for weights, new_weights in [(self.weights1, new_weights1), 
                                         (self.weights2, new_weights2), 
                                         (self.weights3, new_weights3)]:
                strong_mask = np.random.random(weights.shape) < 0.3
                new_weights[strong_mask] = np.random.uniform(-1, 1, size=np.sum(strong_mask))
        
        return Brain(hidden1_weights=new_weights1, weights2=new_weights2, weights3=new_weights3)
    
    def clone(self) -> 'Brain':
        """Создание точной копии мозга."""
        return Brain(hidden1_weights=self.weights1, weights2=self.weights2, weights3=self.weights3)

