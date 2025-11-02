"""
Визуализация эволюции змеек в pygame.
"""

import pygame
import numpy as np
from typing import Tuple
from evolution import Evolution
import copy


class Visualizer:
    """Визуализатор для pygame."""
    
    # Цвета в стиле "цифровой жизни"
    COLORS = {
        'background': (11, 12, 16),
        'background_gradient': (15, 17, 22),
        'grid': (31, 40, 51),
        'grid_highlight': (40, 50, 65),
        'snake_gen1': (51, 255, 87),      # Gen <100
        'snake_gen2': (0, 255, 255),      # Gen 100-500
        'snake_gen3': (108, 99, 255),     # Gen 500+
        'snake_head_glow': (150, 255, 200),
        'snake_outline': (20, 80, 20),
        'snake_trail': (51, 255, 87),
        'food': (255, 46, 99),
        'food_glow': (255, 180, 200),
        'food_flash': (255, 255, 255),
        'text': (0, 255, 255),
        'text_accent': (255, 215, 0),
        'text_scan': (0, 255, 100),
        'ui_bg': (20, 25, 35),
        'ui_border': (50, 60, 80),
        'neural_trace': (100, 255, 255),
        'generation_flash': (255, 255, 255),
        'wall': (80, 80, 100),
        'wall_glow': (120, 120, 150),
        'moving_wall': (120, 60, 100),
        'poison': (150, 50, 150),
        'poison_glow': (255, 0, 255),
        'bonus': (255, 215, 0),
        'bonus_glow': (255, 255, 200)
    }
    
    def __init__(self, evolution: Evolution, cell_size: int = 20):
        """
        Args:
            evolution: объект Evolution
            cell_size: размер одной клетки в пикселях
        """
        self.evolution = evolution
        self.cell_size = cell_size
        self.grid_size = evolution.grid_size
        self.width = self.grid_size * cell_size + 350  # +350 для статистики
        self.height = self.grid_size * cell_size + 100
        
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('🐍 Эволюционная Змейка')
        
        # Улучшенные шрифты
        try:
            self.font_large = pygame.font.Font(None, 32)
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 20)
            self.tiny_font = pygame.font.Font(None, 16)
        except:
            # Fallback если шрифты не найдены
            self.font_large = self.font = self.small_font = self.tiny_font = pygame.font.Font(None, 24)
        
        self.clock = pygame.time.Clock()
        
        # Состояние демо-змейки для анимации
        self.demo_snake = None
        self.demo_food_positions = []  # Список позиций еды для демо
        self.demo_step = 0
        self.demo_max_steps = 10000  # Увеличен лимит для длинных игр
        self.demo_last_food_step = 0  # Шаг когда последний раз ела
        
        # Таймер для авторежима
        self.auto_timer = 0
        self.auto_delay = 10000  # 10 секунд в миллисекундах
        
        # Эффекты цифровой симуляции
        self.food_flash_alpha = 0
        self.food_flash_radius = 0
        self.trails = []  # Следы змеек
        
        # Эффект поколения
        self.generation_flash = 0
        self.generation_text = None
        
        # Звуковые эффекты
        self.sound_enabled = True
        self.last_sound_gen = -1  # Для отслеживания смены поколения
        self.last_sound_eat = False  # Для еды
        self.last_sound_death = False  # Для смерти
        self.last_sound_stuck = False  # Для застревания
    
    def generate_beep(self, frequency: int, duration: int, volume: float = 0.3):
        """Генерация простого звукового сигнала."""
        sample_rate = 22050
        n_samples = int(duration * sample_rate / 1000)
        arr = np.zeros((n_samples, 2), dtype=np.int16)
        max_sample = 2**(16 - 1) - 1
        
        for i in range(n_samples):
            wave = 4096 * np.sin(2 * np.pi * frequency * i / sample_rate) * volume
            arr[i][0] = int(wave)
            arr[i][1] = int(wave)
        
        return pygame.sndarray.make_sound(arr)
    
    def play_sound_food(self):
        """Звук поедания еды."""
        if self.sound_enabled and not self.last_sound_eat:
            sound = self.generate_beep(800, 50, 0.2)
            sound.play()
            self.last_sound_eat = True
    
    def play_sound_death(self):
        """Звук смерти."""
        if self.sound_enabled and not self.last_sound_death:
            sound = self.generate_beep(200, 300, 0.5)
            sound.play()
            self.last_sound_death = True
    
    def play_sound_stuck(self):
        """Звук застревания."""
        if self.sound_enabled and not self.last_sound_stuck:
            sound = self.generate_beep(400, 200, 0.3)
            sound.play()
            self.last_sound_stuck = True
    
    def play_sound_generation(self):
        """Звук смены поколения."""
        if self.sound_enabled and self.last_sound_gen != self.evolution.generation:
            # Восходящий звук
            for i, freq in enumerate([400, 600, 800]):
                sound = self.generate_beep(freq, 100, 0.2)
                sound.play()
                pygame.time.wait(50)
            self.last_sound_gen = self.evolution.generation
    
    def draw_grid(self):
        """Отрисовка сетки в стиле цифровой лаборатории."""
        grid_width = self.grid_size * self.cell_size
        grid_height = self.grid_size * self.cell_size
        
        # Фон поля
        grid_rect = pygame.Rect(0, 0, grid_width, grid_height)
        pygame.draw.rect(self.screen, self.COLORS['background'], grid_rect)
        
        # Тонкие нейросетевые прожилки (случайные линии) - редко
        import random
        current_time = pygame.time.get_ticks()
        if current_time % 10000 < 100:  # Только в первые 100мс каждой секунды
            random.seed(current_time // 10000)
            for _ in range(3):
                x1 = random.randint(0, grid_width)
                y1 = random.randint(0, grid_height)
                x2 = x1 + random.randint(-50, 50)
                y2 = y1 + random.randint(-50, 50)
                if 0 <= x2 <= grid_width and 0 <= y2 <= grid_height:
                    alpha = int(10 * random.random())
                    color = tuple(min(255, c + alpha) for c in self.COLORS['background'])
                    pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), 1)
        
        # Едва заметная сетка
        for x in range(0, self.grid_size + 1):
            start_pos = (x * self.cell_size, 0)
            end_pos = (x * self.cell_size, grid_height)
            pygame.draw.line(self.screen, self.COLORS['grid'], start_pos, end_pos, 1)
        
        for y in range(0, self.grid_size + 1):
            start_pos = (0, y * self.cell_size)
            end_pos = (grid_width, y * self.cell_size)
            pygame.draw.line(self.screen, self.COLORS['grid'], start_pos, end_pos, 1)
        
        # Акцентные линии каждые 5 клеток
        for x in range(0, self.grid_size + 1, 5):
            if x > 0 and x < self.grid_size:
                start_pos = (x * self.cell_size, 0)
                end_pos = (x * self.cell_size, grid_height)
                pygame.draw.line(self.screen, self.COLORS['grid_highlight'], start_pos, end_pos, 1)
        
        for y in range(0, self.grid_size + 1, 5):
            if y > 0 and y < self.grid_size:
                start_pos = (0, y * self.cell_size)
                end_pos = (grid_width, y * self.cell_size)
                pygame.draw.line(self.screen, self.COLORS['grid_highlight'], start_pos, end_pos, 1)
    
    def draw_snake(self, snake):
        """Отрисовка змейки в стиле цифрового организма."""
        # Определяем цвет на основе поколения
        gen = self.evolution.generation if hasattr(self.evolution, 'generation') else 0
        if gen < 100:
            snake_color = self.COLORS['snake_gen1']
            glow_color = (100, 255, 150)
        elif gen < 500:
            snake_color = self.COLORS['snake_gen2']
            glow_color = (100, 200, 255)
        else:
            snake_color = self.COLORS['snake_gen3']
            glow_color = (200, 150, 255)
        
        # Анимация пульсации энергии
        pulse = abs(np.sin(pygame.time.get_ticks() / 200))
        pulse_offset = int(pulse * 2)
        
        for i, (x, y) in enumerate(snake.body):
            # Позиция в пикселях
            px = x * self.cell_size
            py = y * self.cell_size
            margin = 2
            
            if i == 0:  # Голова - фокус энергии
                # Многослойное свечение головы
                for glow_layer in range(3, 0, -1):
                    glow_size = self.cell_size + pulse_offset + glow_layer * 2
                    glow_rect = pygame.Rect(
                        px + margin - (glow_size - self.cell_size) // 2,
                        py + margin - (glow_size - self.cell_size) // 2,
                        glow_size - margin * 2,
                        glow_size - margin * 2
                    )
                    alpha = 1.0 / (glow_layer + 1) * 0.3
                    glow_col = tuple(int(c * alpha) for c in glow_color)
                    pygame.draw.rect(self.screen, glow_col, glow_rect, width=1, border_radius=5)
                
                # Голова
                head_rect = pygame.Rect(
                    px + margin, py + margin,
                    self.cell_size - margin * 2, self.cell_size - margin * 2
                )
                pygame.draw.rect(self.screen, snake_color, head_rect, border_radius=5)
                
                # Глаза-сенсоры (два ярких пикселя)
                pygame.draw.circle(self.screen, (255, 255, 255), 
                                  (px + 5, py + 5), 3)
                pygame.draw.circle(self.screen, (255, 255, 255), 
                                  (px + self.cell_size - 5, py + 5), 3)
                pygame.draw.circle(self.screen, (0, 255, 200), 
                                  (px + 5, py + 5), 2)
                pygame.draw.circle(self.screen, (0, 255, 200), 
                                  (px + self.cell_size - 5, py + 5), 2)
            else:
                # Тело - энергетические сегменты
                body_rect = pygame.Rect(
                    px + margin, py + margin,
                    self.cell_size - margin * 2, self.cell_size - margin * 2
                )
                
                # Свечение тела
                pygame.draw.rect(self.screen, tuple(int(c * 0.3) for c in snake_color), 
                               body_rect, width=1, border_radius=3)
                
                # Основной цвет
                pygame.draw.rect(self.screen, snake_color, body_rect, border_radius=3)
                
                # Центральная точка энергии
                center = (px + self.cell_size // 2, py + self.cell_size // 2)
                brighter = tuple(min(255, int(c * 1.5)) for c in snake_color)
                pygame.draw.circle(self.screen, brighter, center, 2)
                
                # Тонкая светящаяся линия для связи сегментов
                if i > 0:
                    prev_pos = snake.body[i-1]
                    prev_px = prev_pos[0] * self.cell_size + self.cell_size // 2
                    prev_py = prev_pos[1] * self.cell_size + self.cell_size // 2
                    curr_px = x * self.cell_size + self.cell_size // 2
                    curr_py = y * self.cell_size + self.cell_size // 2
                    pygame.draw.line(self.screen, tuple(int(c * 0.4) for c in snake_color),
                                    (prev_px, prev_py), (curr_px, curr_py), 1)
    
    def draw_walls(self, walls):
        """Отрисовка статичных стен (препятствий)."""
        for x, y in walls:
            px = x * self.cell_size
            py = y * self.cell_size
            rect = pygame.Rect(px, py, self.cell_size, self.cell_size)
            
            # Внешнее свечение
            pygame.draw.rect(self.screen, self.COLORS['wall_glow'], 
                           (px - 2, py - 2, self.cell_size + 4, self.cell_size + 4), 
                           width=1)
            
            # Основной блок стены
            pygame.draw.rect(self.screen, self.COLORS['wall'], rect)
            
            # Внутренняя тень
            pygame.draw.rect(self.screen, (60, 60, 80), 
                           (px + 2, py + 2, self.cell_size - 4, self.cell_size - 4))
            
            # Рваный эффект (случайные штрихи)
            import random
            random.seed(x * 100 + y)
            for _ in range(3):
                start_x = px + random.randint(0, self.cell_size)
                start_y = py + random.randint(0, self.cell_size)
                end_x = px + random.randint(0, self.cell_size)
                end_y = py + random.randint(0, self.cell_size)
                pygame.draw.line(self.screen, (40, 40, 60), 
                               (start_x, start_y), (end_x, end_y), 1)
    
    def draw_moving_walls(self, moving_walls):
        """Отрисовка движущихся стен."""
        for x, y, dir_x, dir_y in moving_walls:
            px = x * self.cell_size
            py = y * self.cell_size
            rect = pygame.Rect(px, py, self.cell_size, self.cell_size)
            
            # Динамическое свечение для движущихся стен
            pulse = abs(np.sin(pygame.time.get_ticks() / 500))
            glow_mult = 1.0 + pulse * 0.3
            
            # Внешнее пульсирующее свечение
            glow_col = tuple(min(255, int(c * glow_mult)) for c in self.COLORS['moving_wall'])
            pygame.draw.rect(self.screen, glow_col, 
                           (px - 2, py - 2, self.cell_size + 4, self.cell_size + 4), 
                           width=2)
            
            # Основной блок стены
            pygame.draw.rect(self.screen, self.COLORS['moving_wall'], rect)
            
            # Внутренняя тень
            pygame.draw.rect(self.screen, (80, 40, 70), 
                           (px + 2, py + 2, self.cell_size - 4, self.cell_size - 4))
            
            # Стрелка направления
            center = (px + self.cell_size // 2, py + self.cell_size // 2)
            arrow_size = 3
            if dir_x == 1:  # Вправо
                pygame.draw.line(self.screen, (200, 150, 200), center, (center[0] + arrow_size, center[1]), 2)
                pygame.draw.polygon(self.screen, (200, 150, 200), 
                                  [(center[0] + arrow_size, center[1]), 
                                   (center[0] + arrow_size - 2, center[1] - 2),
                                   (center[0] + arrow_size - 2, center[1] + 2)])
            elif dir_x == -1:  # Влево
                pygame.draw.line(self.screen, (200, 150, 200), center, (center[0] - arrow_size, center[1]), 2)
                pygame.draw.polygon(self.screen, (200, 150, 200), 
                                  [(center[0] - arrow_size, center[1]), 
                                   (center[0] - arrow_size + 2, center[1] - 2),
                                   (center[0] - arrow_size + 2, center[1] + 2)])
            elif dir_y == 1:  # Вниз
                pygame.draw.line(self.screen, (200, 150, 200), center, (center[0], center[1] + arrow_size), 2)
                pygame.draw.polygon(self.screen, (200, 150, 200), 
                                  [(center[0], center[1] + arrow_size), 
                                   (center[0] - 2, center[1] + arrow_size - 2),
                                   (center[0] + 2, center[1] + arrow_size - 2)])
            elif dir_y == -1:  # Вверх
                pygame.draw.line(self.screen, (200, 150, 200), center, (center[0], center[1] - arrow_size), 2)
                pygame.draw.polygon(self.screen, (200, 150, 200), 
                                  [(center[0], center[1] - arrow_size), 
                                   (center[0] - 2, center[1] - arrow_size + 2),
                                   (center[0] + 2, center[1] - arrow_size + 2)])
    
    def draw_poisons(self, poisons):
        """Отрисовка ядов."""
        for x, y in poisons:
            px = x * self.cell_size
            py = y * self.cell_size
            center = (px + self.cell_size // 2, py + self.cell_size // 2)
            
            # Пульсирующее зловещее свечение
            pulse = abs(np.sin(pygame.time.get_ticks() / 400))
            pulse_size = int(pulse * 6)
            
            # Магнитное свечение яда (5 слоёв)
            for layer in range(5, 0, -1):
                radius = self.cell_size // 2 + pulse_size + layer * 2
                alpha = 1.0 / (layer + 1) * 0.15
                glow_col = tuple(int(c * alpha) for c in self.COLORS['poison_glow'])
                pygame.draw.circle(self.screen, glow_col, center, radius, width=1)
            
            # Основной круг яда
            pygame.draw.circle(self.screen, self.COLORS['poison'], center, 
                              self.cell_size // 2 + pulse_size - 2, width=2)
            
            # Центральное ядро
            core_radius = self.cell_size // 2 - 4
            pygame.draw.circle(self.screen, self.COLORS['poison'], center, core_radius)
            
            # Крест смерти
            cross_size = int(pulse_size + 5)
            pygame.draw.line(self.screen, self.COLORS['poison_glow'],
                           (center[0] - cross_size, center[1]),
                           (center[0] + cross_size, center[1]), 3)
            pygame.draw.line(self.screen, self.COLORS['poison_glow'],
                           (center[0], center[1] - cross_size),
                           (center[0], center[1] + cross_size), 3)
            
            # Центральная точка
            pygame.draw.circle(self.screen, (255, 0, 255), center, 3)
    
    def draw_bonuses(self, bonuses):
        """Отрисовка бонусов (2x очки)."""
        for x, y in bonuses:
            px = x * self.cell_size
            py = y * self.cell_size
            center = (px + self.cell_size // 2, py + self.cell_size // 2)
            
            # Яркое золотое свечение
            pulse = abs(np.sin(pygame.time.get_ticks() / 250))
            pulse_size = int(pulse * 8)
            
            # Световое свечение (5 слоёв)
            for layer in range(5, 0, -1):
                radius = self.cell_size // 2 + pulse_size + layer * 3
                alpha = 1.0 / (layer + 1) * 0.3
                glow_col = tuple(int(c * alpha) for c in self.COLORS['bonus_glow'])
                pygame.draw.circle(self.screen, glow_col, center, radius, width=1)
            
            # Звёздный эффект (8 лучей)
            for angle in range(0, 360, 45):
                import math
                rad = math.radians(angle)
                start_x = center[0] + int(math.cos(rad) * (self.cell_size // 2 - 2))
                start_y = center[1] + int(math.sin(rad) * (self.cell_size // 2 - 2))
                end_x = center[0] + int(math.cos(rad) * (self.cell_size // 2 + pulse_size))
                end_y = center[1] + int(math.sin(rad) * (self.cell_size // 2 + pulse_size))
                pygame.draw.line(self.screen, self.COLORS['bonus'],
                               (start_x, start_y), (end_x, end_y), 2)
            
            # Золотой круг
            pygame.draw.circle(self.screen, self.COLORS['bonus'], center, 
                              self.cell_size // 2 - 2, width=2)
            
            # Центральная точка "2x"
            bonus_text = self.tiny_font.render('2x', True, self.COLORS['bonus'])
            bonus_rect = bonus_text.get_rect(center=center)
            pygame.draw.circle(self.screen, self.COLORS['bonus_glow'], center, 6)
            self.screen.blit(bonus_text, bonus_rect)
    
    def draw_food(self, food_pos):
        """Отрисовка еды-энергии с эффектом вспышки."""
        x, y = food_pos
        px = x * self.cell_size
        py = y * self.cell_size
        center = (px + self.cell_size // 2, py + self.cell_size // 2)
        
        # Плавная пульсация
        pulse = abs(np.sin(pygame.time.get_ticks() / 300))
        pulse_size = int(pulse * 5)
        
        # Магнитное свечение (5 слоёв для эффекта притяжения)
        for layer in range(5, 0, -1):
            radius = self.cell_size // 2 + pulse_size + layer * 3
            alpha = 1.0 / (layer + 1) * 0.25
            glow_col = tuple(int(c * alpha) for c in self.COLORS['food_glow'])
            pygame.draw.circle(self.screen, glow_col, center, radius, width=1)
        
        # Основной импульсный круг
        pygame.draw.circle(self.screen, self.COLORS['food'], center, 
                          self.cell_size // 2 + pulse_size - 1, width=1)
        
        # Ядро энергии
        core_radius = self.cell_size // 2 - 3
        pygame.draw.circle(self.screen, self.COLORS['food'], center, core_radius)
        
        # Внутреннее свечение с градиентом
        inner_radius = core_radius - 3
        pygame.draw.circle(self.screen, (255, 150, 180), center, inner_radius)
        
        # Световой крест для эффекта "излучения"
        cross_size = int(pulse_size + 3)
        pygame.draw.line(self.screen, self.COLORS['food_flash'],
                        (center[0] - cross_size, center[1]),
                        (center[0] + cross_size, center[1]), 2)
        pygame.draw.line(self.screen, self.COLORS['food_flash'],
                        (center[0], center[1] - cross_size),
                        (center[0], center[1] + cross_size), 2)
        
        # Яркая центральная точка
        pygame.draw.circle(self.screen, (255, 255, 255), center, 2)
        
        # Эффект вспышки (если только что появилась)
        if self.food_flash_alpha > 0:
            pygame.draw.circle(self.screen, self.COLORS['food_flash'], 
                             center, self.food_flash_radius, width=1)
            self.food_flash_alpha = max(0, self.food_flash_alpha - 5)
            self.food_flash_radius += 2
    
    def draw_game_status_bar(self, snake):
        """Отрисовка статус-бара внизу игрового поля (счёт и голод)."""
        grid_size_px = self.grid_size * self.cell_size
        bar_y = grid_size_px
        bar_height = self.height - grid_size_px
        bar_width = grid_size_px
        
        # Фон статус-бара
        pygame.draw.rect(self.screen, self.COLORS['ui_bg'], 
                        (0, bar_y, bar_width, bar_height))
        
        # Разделительная линия сверху
        pygame.draw.line(self.screen, (0, 255, 255), 
                        (0, bar_y), (bar_width, bar_y), 2)
        
        padding = 20
        y_offset = bar_y + padding
        
        # Счёт
        score_text = self.small_font.render('SCORE:', True, self.COLORS['text'])
        self.screen.blit(score_text, (padding, y_offset))
        
        score_value = int(snake.get_fitness())
        score_display = self.font_large.render(f'{score_value}', True, self.COLORS['text_accent'])
        self.screen.blit(score_display, (padding, y_offset + 25))
        
        x_mid = bar_width // 2
        
        # Голод (индикатор)
        hunger_text = self.small_font.render('HUNGER:', True, self.COLORS['text'])
        self.screen.blit(hunger_text, (x_mid, y_offset))
        
        # Прогресс-бар голода
        hunger_bar_x = x_mid
        hunger_bar_y = y_offset + 25
        hunger_bar_width = bar_width // 2 - padding
        hunger_bar_height = 30
        
        # Макс голод = 80 шагов (8 секунд)
        max_hunger = 80
        hunger_level = max(0, max_hunger - snake.steps_without_food)
        hunger_percent = hunger_level / max_hunger
        
        # Фон прогресс-бара
        pygame.draw.rect(self.screen, (30, 30, 40), 
                        (hunger_bar_x, hunger_bar_y, hunger_bar_width, hunger_bar_height))
        
        # Заполнение прогресс-бара (цвет зависит от уровня голода)
        fill_width = int(hunger_bar_width * hunger_percent)
        if hunger_percent > 0.5:
            hunger_color = (0, 255, 100)  # Зелёный
        elif hunger_percent > 0.3:
            hunger_color = (255, 215, 0)  # Жёлтый
        else:
            hunger_color = (255, 50, 50)  # Красный
        
        if fill_width > 0:
            pygame.draw.rect(self.screen, hunger_color, 
                           (hunger_bar_x, hunger_bar_y, fill_width, hunger_bar_height))
            
            # Анимация пульсации при критическом уровне
            if hunger_percent < 0.3:
                pulse = abs(np.sin(pygame.time.get_ticks() / 200))
                pulse_alpha = int(50 + pulse * 30)
                pulse_overlay = pygame.Surface((fill_width, hunger_bar_height))
                pulse_overlay.fill(hunger_color)
                pulse_overlay.set_alpha(pulse_alpha)
                self.screen.blit(pulse_overlay, (hunger_bar_x, hunger_bar_y))
        
        # Граница прогресс-бара
        pygame.draw.rect(self.screen, self.COLORS['text'], 
                        (hunger_bar_x, hunger_bar_y, hunger_bar_width, hunger_bar_height), 
                        width=2)
        
        # Текст уровня голода
        hunger_level_text = self.tiny_font.render(f'{int(hunger_percent * 100)}%', True, 
                                                 self.COLORS['text'])
        hunger_level_rect = hunger_level_text.get_rect(
            center=(hunger_bar_x + hunger_bar_width // 2, 
                   hunger_bar_y + hunger_bar_height // 2))
        self.screen.blit(hunger_level_text, hunger_level_rect)
    
    def draw_stats(self, generation: int, best_fitness: float, avg_fitness: float):
        """Отрисовка улучшенной статистики."""
        x_offset = self.grid_size * self.cell_size
        y_offset = 0
        panel_width = self.width - x_offset
        
        # Фон панели статистики (цифровой терминал)
        pygame.draw.rect(self.screen, self.COLORS['ui_bg'], 
                        (x_offset, 0, panel_width, self.height))
        
        # Сканирующая линия UI
        scan_y = int(pygame.time.get_ticks() / 50) % self.height
        pygame.draw.line(self.screen, self.COLORS['text_scan'], 
                        (x_offset + 10, scan_y), (x_offset + panel_width - 10, scan_y), 1)
        
        # Разделительная линия терминала
        pygame.draw.line(self.screen, (0, 255, 255), 
                        (x_offset, 0), (x_offset, self.height), 2)
        pygame.draw.line(self.screen, (0, 150, 150), 
                        (x_offset - 1, 0), (x_offset - 1, self.height), 1)
        
        # Заголовок
        x_offset += 20
        y_offset += 30
        
        # Заголовок в стиле терминала
        title_text = f'[{generation}] СИСТЕМА'
        title = self.font_large.render(title_text, True, self.COLORS['text'])
        self.screen.blit(title, (x_offset, y_offset))
        
        # Мигающая курсорная линия
        if (pygame.time.get_ticks() // 500) % 2:
            cursor_x = x_offset + title.get_width()
            pygame.draw.line(self.screen, self.COLORS['text_scan'],
                           (cursor_x, y_offset),
                           (cursor_x, y_offset + title.get_height()), 2)
        
        y_offset += 50
        
        # Данные в стиле терминала
        stats_items = [
            ('Gen:', f'{generation}'),
            ('Best IQ:', f'{best_fitness:.1f}'),
            ('Avg IQ:', f'{avg_fitness:.1f}'),
        ]
        
        for idx, (label, value) in enumerate(stats_items):
            # Мигающая подсветка строки (эффект сканирования)
            if scan_y - 20 <= y_offset <= scan_y + 20:
                highlight_rect = pygame.Rect(x_offset - 10, y_offset - 2, panel_width - 20, 32)
                pygame.draw.rect(self.screen, (0, 50, 50), highlight_rect, border_radius=2)
            
            # Метка
            label_text = self.small_font.render(label, True, self.COLORS['text'])
            self.screen.blit(label_text, (x_offset, y_offset))
            
            # Значение с эффектом свечения
            value_text = self.font.render(value, True, self.COLORS['text_accent'])
            self.screen.blit(value_text, (x_offset + 120, y_offset))
            y_offset += 35
        
        y_offset += 20
        
        # Инструкции (более компактно)
        if self.demo_snake is None:
            instructions = [
                '⏭️  SPACE - след. поколение',
                '⏹️  ESC - выход',
                '',
                '🤖 Демо-анимация',
                '   следующего поколения'
            ]
        else:
            instructions = [
                '⏸️  PAUSE - пауза',
                '⏹️  ESC - выход',
                '',
                f'🎮 Шагов: {self.demo_step}/{self.demo_max_steps}'
            ]
        
        # Разделительная линия терминала
        pygame.draw.line(self.screen, (0, 100, 100), 
                        (x_offset - 20, y_offset - 10), 
                        (self.grid_size * self.cell_size + panel_width - 30, y_offset - 10), 1)
        y_offset -= 10
        
        for instr in instructions:
            text = self.tiny_font.render(instr, True, (0, 150, 150))
            self.screen.blit(text, (x_offset, y_offset))
            y_offset += 22
        
        # График прогресса
        if len(self.evolution.best_fitness_history) > 1:
            y_offset += 20
            chart_title = self.small_font.render('EVOLUTION GRAPH:', True, self.COLORS['text'])
            self.screen.blit(chart_title, (x_offset, y_offset))
            y_offset += 25
            
            self.draw_mini_chart(x_offset, y_offset, 300, 80)
    
    def draw_mini_chart(self, x, y, width, height):
        """Отрисовка мини-графика в стиле терминала."""
        if len(self.evolution.best_fitness_history) < 2:
            return
        
        # Фон графика (осциллограф)
        pygame.draw.rect(self.screen, (5, 10, 15), (x, y, width, height))
        pygame.draw.rect(self.screen, (0, 150, 150), (x, y, width, height), 2)
        
        # Сетка осциллографа
        for grid_y in range(y + 10, y + height - 10, 20):
            pygame.draw.line(self.screen, (0, 50, 50), (x + 5, grid_y), (x + width - 5, grid_y), 1)
        
        # Данные
        history = self.evolution.best_fitness_history[-50:]  # Последние 50 поколений
        max_val = max(history) if history else 1
        
        if len(history) > 1:
            points = []
            for i, val in enumerate(history):
                px = x + int(i * width / (len(history) - 1))
                py = y + height - int(val * height / max_val) - 2
                points.append((px, py))
            
            if len(points) > 1:
                # Тень линии
                shadow_points = [(px, py + 1) for px, py in points]
                pygame.draw.lines(self.screen, (0, 20, 20), False, shadow_points, 2)
                
                # Основная линия с эффектом свечения
                pygame.draw.lines(self.screen, (0, 255, 200), False, points, 2)
                
                # Эффект "развёртки" для конца линии
                pulse = abs(np.sin(pygame.time.get_ticks() / 400))
                if points:
                    last_px, last_py = points[-1]
                    end_glow = int(4 + pulse * 2)
                    pygame.draw.circle(self.screen, (0, 255, 200), (last_px, last_py), end_glow)
                    pygame.draw.circle(self.screen, (0, 150, 150), (last_px, last_py), 3)
                    pygame.draw.circle(self.screen, (100, 255, 255), (last_px, last_py), 2)
    
    def animate_best_snake(self):
        """Анимация лучшей змейки, показывающая как она играет."""
        if self.demo_snake is None:
            return
        
        # Один шаг игры
        if self.demo_step < self.demo_max_steps and self.demo_snake.alive:
            # Получение входных данных для мозга (для совместимости берём первую еду)
            food_pos = self.demo_food_positions[0] if self.demo_food_positions else (5, 5)
            all_walls = self.evolution.environment.walls + [(x, y) for x, y, _, _ in self.evolution.environment.moving_walls]
            inputs = self.demo_snake.get_view(food_pos, walls=all_walls)
            
            # Мозг принимает решение
            action = self.demo_snake.brain.think(inputs)
            
            # Движение
            move_success = self.demo_snake.move(action, walls=all_walls)
            
            if move_success:
                # Проверка поедания еды (несколько еды одновременно)
                head_pos = self.demo_snake.get_head()
                food_eaten = False
                for i, food_pos in enumerate(self.demo_food_positions):
                    if head_pos == food_pos:
                        self.demo_snake.eat()
                        self.demo_last_food_step = self.demo_step
                        self.play_sound_food()
                        self.demo_food_positions.pop(i)
                        food_eaten = True
                        # Добавляем новую еду, если осталось мало
                        if len(self.demo_food_positions) < 2:
                            free_positions = self.evolution.environment.get_free_positions(self.demo_snake.body)
                            if free_positions:
                                import random
                                self.demo_food_positions.append(random.choice(free_positions))
                        break
                
                # Проверка ядов
                for poison_pos in self.evolution.environment.poisons:
                    if head_pos == poison_pos:
                        self.demo_snake.alive = False
                        break
                
                # Проверка бонусов
                for i, bonus_pos in enumerate(self.evolution.environment.bonuses):
                    if head_pos == bonus_pos:
                        self.demo_snake.fitness += self.demo_snake.fitness * 0.5
                        break
                
                if not food_eaten:
                    self.demo_snake.remove_tail()
                
                self.demo_snake.update_fitness()
            else:
                # Движение неудачно (стена/голод) - но время всё равно идёт
                # steps_without_food уже увеличен в move() при неудаче
                pass
            
            self.demo_step += 1
    
    def visualize_generation(self, auto_mode: bool = False):
        """Визуализация текущего поколения с анимацией."""
        running = True
        paused = False
        self.auto_timer = pygame.time.get_ticks()  # Сброс таймера
        
        # Подготовка демо-змейки для анимации
        if self.demo_snake is None:
            # Эффект вспышки нового поколения
            self.generation_flash = 255
            self.generation_text = self.evolution.generation
            
            # Генерируем стены для демо (важно для визуализации)
            self.evolution.environment.reset_walls()
            
            best_snake = self.evolution.get_best_snake()
            if best_snake:
                from snake import Snake
                from brain import Brain
                # Создаём копию лучшей змейки
                self.demo_snake = Snake(brain=best_snake.brain.clone(), grid_size=self.grid_size)
                self.demo_snake.reset()
                
                # Устанавливаем начальную еду
                self.evolution.environment.reset_food(occupied=self.demo_snake.body)
                self.demo_food_positions = list(self.evolution.environment.food_positions)
                self.evolution.environment.reset_poisons_and_bonuses(occupied=self.demo_snake.body)
                self.demo_step = 0
                self.demo_last_food_step = 0
        
        while running:
            # Проверка событий (неблокирующий режим для авто)
            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False  # Выход при закрытии окна
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            # Следующее поколение - сброс демо
                            self.demo_snake = None
                            self.demo_step = 0
                            return True
                        elif event.key == pygame.K_ESCAPE:
                            return False
                        elif event.key == pygame.K_p:
                            paused = not paused
            except:
                pass  # Игнорируем ошибки событий
            
            # Авторежим - переход к следующему поколению только при смерти или застревании
            if auto_mode and not paused:
                # Проверка условий для перехода к следующему поколению
                should_advance = False
                
                # Если змейка умерла
                if self.demo_snake and not self.demo_snake.alive:
                    self.play_sound_death()  # Звук смерти
                    should_advance = True
                
                # Если змейка застряла (не ест >10 секунд = 100 шагов при 10 fps)
                if self.demo_snake and self.demo_step > 30:
                    steps_without_food = self.demo_step - self.demo_last_food_step
                    if steps_without_food > 100:  # 10 секунд при 10 fps
                        self.play_sound_stuck()  # Звук застревания
                        should_advance = True
                
                if should_advance:
                    self.demo_snake = None
                    self.demo_step = 0
                    self.demo_last_food_step = 0
                    # Сброс флагов звуков
                    self.last_sound_eat = False
                    self.last_sound_death = False
                    self.last_sound_stuck = False
                    return True
            
            # Очистка экрана
            self.screen.fill(self.COLORS['background'])
            
            # Отрисовка сетки
            self.draw_grid()
            
            # Отрисовка стен
            self.draw_walls(self.evolution.environment.walls)
            
            # Отрисовка движущихся стен
            self.draw_moving_walls(self.evolution.environment.moving_walls)
            
            # Отрисовка ядов и бонусов
            self.draw_poisons(self.evolution.environment.poisons)
            self.draw_bonuses(self.evolution.environment.bonuses)
            
            # Отрисовка демо-змейки или статичной лучшей
            if self.demo_snake:
                self.draw_snake(self.demo_snake)
                # Отрисовка множественной еды
                for food_pos in self.demo_food_positions:
                    self.draw_food(food_pos)
                
                # Анимация если не на паузе
                if not paused:
                    self.animate_best_snake()
                
                # Статус-бар внизу игрового поля
                self.draw_game_status_bar(self.demo_snake)
            else:
                # Статичная отрисовка
                best_snake = self.evolution.get_best_snake()
                if best_snake:
                    self.draw_snake(best_snake)
                # Множественная еда
                for food_pos in self.evolution.environment.food_positions:
                    self.draw_food(food_pos)
                if best_snake:
                    self.draw_game_status_bar(best_snake)
            
            # Статистика
            gen, best_fit, avg_fit = self.evolution.get_stats()
            self.draw_stats(gen, best_fit, avg_fit)
            
            # Индикатор паузы
            if paused:
                pause_text = self.font.render('[PAUSED]', True, (255, 255, 0))
                pause_rect = pause_text.get_rect(center=(self.width // 2, 30))
                # Фон для паузы
                pygame.draw.rect(self.screen, (0, 0, 0, 180), 
                                (pause_rect.x - 10, pause_rect.y - 5, 
                                 pause_rect.width + 20, pause_rect.height + 10))
                self.screen.blit(pause_text, pause_rect)
            
            # Эффект вспышки поколения
            if self.generation_flash > 0:
                self.play_sound_generation()  # Звук смены поколения
                gen_text = f'GENERATION {self.generation_text}'
                flash_text = self.font_large.render(gen_text, True, 
                                                   (self.generation_flash, self.generation_flash, self.generation_flash))
                flash_rect = flash_text.get_rect(center=(self.width // 2, self.height // 2))
                
                # Вспышка фона
                alpha = self.generation_flash // 10
                overlay = pygame.Surface((self.width, self.height))
                overlay.fill((self.generation_flash, self.generation_flash, self.generation_flash))
                overlay.set_alpha(alpha)
                self.screen.blit(overlay, (0, 0))
                
                # Текст
                shadow = self.font_large.render(gen_text, True, (0, 0, 0))
                self.screen.blit(shadow, (flash_rect.x + 2, flash_rect.y + 2))
                self.screen.blit(flash_text, flash_rect)
                
                self.generation_flash = max(0, self.generation_flash - 10)
            
            pygame.display.flip()
            self.clock.tick(10 if auto_mode else 15)  # Скорость анимации
        
        return False
    
    def quit(self):
        """Закрытие pygame."""
        pygame.quit()

