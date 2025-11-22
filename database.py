"""
База данных SQLite для сохранения прогресса эволюции.
"""

import sqlite3
import numpy as np
import json
from datetime import datetime
from typing import List, Tuple, Optional
import numpy as np


class EvolutionDB:
    """Управление базой данных эволюции."""
    
    def __init__(self, db_path: str = 'evolution.db'):
        """
        Args:
            db_path: путь к файлу базы данных
        """
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Инициализация схемы базы данных."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        # Таблица для сессий эволюции
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                population_size INTEGER,
                grid_size INTEGER,
                elite_size INTEGER,
                mutation_rate REAL,
                mutation_strength REAL,
                max_steps INTEGER,
                total_generations INTEGER,
                best_fitness REAL,
                notes TEXT
            )
        ''')
        
        # Таблица для истории поколений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                generation INTEGER,
                best_fitness REAL,
                avg_fitness REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        
        # Таблица для лучших змеек
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS best_snakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                generation INTEGER,
                fitness REAL,
                weights BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        
        # Индексы для ускорения запросов
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON generations(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_gen ON generations(session_id, generation)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_best_session ON best_snakes(session_id)')
        
        self.conn.commit()
    
    def create_session(
        self,
        population_size: int,
        grid_size: int,
        elite_size: int,
        mutation_rate: float,
        mutation_strength: float,
        max_steps: int,
        notes: str = ''
    ) -> int:
        """
        Создание новой сессии эволюции.
        
        Returns:
            ID созданной сессии
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sessions 
            (population_size, grid_size, elite_size, mutation_rate, 
             mutation_strength, max_steps, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (population_size, grid_size, elite_size, mutation_rate,
              mutation_strength, max_steps, notes))
        self.conn.commit()
        return cursor.lastrowid
    
    def save_generation(
        self,
        session_id: int,
        generation: int,
        best_fitness: float,
        avg_fitness: float
    ):
        """Сохранение данных поколения."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO generations (session_id, generation, best_fitness, avg_fitness)
            VALUES (?, ?, ?, ?)
        ''', (session_id, generation, best_fitness, avg_fitness))
        self.conn.commit()
    
    def save_best_snake(
        self,
        session_id: int,
        generation: int,
        fitness: float,
        weights,
        hidden_weights: np.ndarray = None
    ):
        """Сохранение лучшей змейки."""
        cursor = self.conn.cursor()
        # Сохраняем все слои весов (новый формат: 3 слоя)
        if hasattr(weights, 'weights1'):  # Новый формат с тремя слоями (объект Brain)
            # Объединяем все три слоя: weights1, weights2, weights3
            combined = np.concatenate([
                weights.weights1.flatten(),
                weights.weights2.flatten(),
                weights.weights3.flatten()
            ])
            weights_bytes = combined.tobytes()
        elif isinstance(weights, np.ndarray) and hidden_weights is not None:
            # Старый формат с двумя слоями
            combined_weights = np.concatenate([weights.flatten(), hidden_weights.flatten()])
            weights_bytes = combined_weights.tobytes()
        elif isinstance(weights, np.ndarray):
            # Старый формат (один слой) - для совместимости
            weights_bytes = weights.tobytes()
        else:
            # Если передан объект Brain напрямую
            brain = weights
            combined = np.concatenate([
                brain.weights1.flatten(),
                brain.weights2.flatten(),
                brain.weights3.flatten()
            ])
            weights_bytes = combined.tobytes()
        cursor.execute('''
            INSERT INTO best_snakes (session_id, generation, fitness, weights)
            VALUES (?, ?, ?, ?)
        ''', (session_id, generation, fitness, weights_bytes))
        self.conn.commit()
    
    def update_session(
        self,
        session_id: int,
        total_generations: int,
        best_fitness: float
    ):
        """Обновление финальной статистики сессии."""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE sessions 
            SET total_generations = ?, best_fitness = ?
            WHERE id = ?
        ''', (total_generations, best_fitness, session_id))
        self.conn.commit()
    
    def get_best_snakes(self, session_id: Optional[int] = None, limit: int = 10) -> List[Tuple]:
        """
        Получить лучшие змейки.
        
        Args:
            session_id: ID сессии (None для всех)
            limit: максимальное количество
            
        Returns:
            список кортежей (session_id, generation, fitness, weights)
        """
        cursor = self.conn.cursor()
        if session_id:
            cursor.execute('''
                SELECT session_id, generation, fitness, weights
                FROM best_snakes
                WHERE session_id = ?
                ORDER BY fitness DESC
                LIMIT ?
            ''', (session_id, limit))
        else:
            cursor.execute('''
                SELECT session_id, generation, fitness, weights
                FROM best_snakes
                ORDER BY fitness DESC
                LIMIT ?
            ''', (limit,))
        
        return cursor.fetchall()
    
    def load_snake_weights(self, weights_bytes: bytes, input_size: int = 16, output_size: int = 4, 
                          hidden1_size: int = 32, hidden2_size: int = 16, has_hidden: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """
        Загрузка весов из базы данных.
        
        Args:
            weights_bytes: сериализованные веса
            input_size: размер входа (16 для нового формата)
            output_size: размер выхода
            hidden1_size: размер первого скрытого слоя (32)
            hidden2_size: размер второго скрытого слоя (16)
            has_hidden: есть ли скрытый слой
            
        Returns:
            кортеж (weights1, combined_weights2_3) для нового формата или (weights, hidden_weights) для старого
        """
        weights = np.frombuffer(weights_bytes, dtype=np.float64)
        
        # Новый формат: три слоя (16->32->16->4)
        new_format_size = input_size * hidden1_size + hidden1_size * hidden2_size + hidden2_size * output_size
        
        if len(weights) == new_format_size:
            # Новый формат с тремя слоями
            offset = 0
            size1 = input_size * hidden1_size
            weights1 = weights[offset:offset+size1].reshape(input_size, hidden1_size)
            offset += size1
            
            size2 = hidden1_size * hidden2_size
            weights2 = weights[offset:offset+size2].reshape(hidden1_size, hidden2_size)
            offset += size2
            
            size3 = hidden2_size * output_size
            weights3 = weights[offset:offset+size3].reshape(hidden2_size, output_size)
            
            # Возвращаем weights1, weights2, weights3 отдельно
            return (weights1, weights2, weights3)
        elif has_hidden:
            # Старый формат: два слоя (12->16->4 или 8->4)
            # Пытаемся определить формат по размеру
            if len(weights) == 12 * 16 + 16 * 4:  # Старый улучшенный формат
                first_layer = weights[:12*16].reshape(12, 16)
                second_layer = weights[12*16:].reshape(16, 4)
                # Конвертируем в новый формат
                # Расширяем входы с 12 до 16 (добавляем случайные веса)
                if first_layer.shape[0] < input_size:
                    extra = np.random.uniform(-0.5, 0.5, (input_size - first_layer.shape[0], first_layer.shape[1]))
                    first_layer = np.concatenate([first_layer, extra], axis=0)
                # Расширяем скрытый слой с 16 до 32
                if first_layer.shape[1] < hidden1_size:
                    extra = np.random.uniform(-0.5, 0.5, (input_size, hidden1_size - first_layer.shape[1]))
                    first_layer = np.concatenate([first_layer, extra], axis=1)
                # Создаем второй скрытый слой
                weights2 = np.random.uniform(-0.5, 0.5, (hidden1_size, hidden2_size))
                weights3 = np.random.uniform(-0.5, 0.5, (hidden2_size, output_size))
                return (first_layer, weights2, weights3)
            else:
                # Очень старый формат (8->4) - создаем новый мозг
                old_input = 8 if len(weights) == 32 else 12
                old_weights = weights.reshape(old_input, output_size)
                # Создаем новый формат
                weights1 = np.random.uniform(-0.5, 0.5, (input_size, hidden1_size))
                weights2 = np.random.uniform(-0.5, 0.5, (hidden1_size, hidden2_size))
                weights3 = np.random.uniform(-0.5, 0.5, (hidden2_size, output_size))
                return (weights1, weights2, weights3)
        else:
            # Старый формат (один слой)
            old_input = len(weights) // output_size
            return (weights.reshape(old_input, output_size), None)
    
    def get_sessions(self, limit: int = 20) -> List[Tuple]:
        """
        Получить список сессий.
        
        Returns:
            список кортежей (id, created_at, total_generations, best_fitness, ...)
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, created_at, population_size, grid_size, elite_size,
                   mutation_rate, mutation_strength, max_steps, 
                   total_generations, best_fitness
            FROM sessions
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def get_generation_history(self, session_id: int) -> List[Tuple]:
        """
        Получить историю поколений сессии.
        
        Returns:
            список кортежей (generation, best_fitness, avg_fitness)
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT generation, best_fitness, avg_fitness
            FROM generations
            WHERE session_id = ?
            ORDER BY generation
        ''', (session_id,))
        return cursor.fetchall()
    
    def close(self):
        """Закрытие соединения с базой данных."""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Деструктор."""
        self.close()

