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
    
    # СТРИМ-ДИЗАЙН: Яркая неоновая палитра для максимальной видимости
    COLORS = {
        # Фон - глубокий черный с легким синим оттенком
        'background': (5, 5, 10),
        'background_gradient': (10, 8, 15),
        'background_pattern': (15, 12, 20),
        
        # Сетка - яркая неоновая с эффектом свечения
        'grid': (0, 255, 255),              # Яркий циан (неон)
        'grid_dim': (0, 100, 120),          # Приглушенный для обычных линий
        'grid_highlight': (255, 0, 255),    # Яркий пурпурный для акцентов
        'grid_glow': (0, 200, 255),         # Свечение сетки
        
        # Змейка - эволюция цветов по поколениям (яркие неоновые)
        'snake_gen1': (0, 255, 100),        # Яркий неоновый зеленый
        'snake_gen2': (100, 255, 255),     # Яркий циан
        'snake_gen3': (255, 100, 255),     # Яркий пурпурный
        'snake_gen4': (255, 255, 100),     # Яркий желтый (для элиты)
        'snake_head_glow': (255, 255, 255), # Белое свечение головы
        'snake_body_glow': (0, 255, 200),   # Свечение тела
        'snake_trail': (0, 200, 150),       # След змейки
        
        # Еда - яркий неоновый розовый/красный
        'food': (255, 50, 100),             # Яркий неоновый розовый
        'food_glow': (255, 150, 200),       # Свечение еды
        'food_core': (255, 255, 255),       # Белое ядро
        'food_flash': (255, 255, 0),        # Желтая вспышка
        'food_particles': (255, 100, 150),  # Частицы еды
        
        # UI - стеклянный эффект с неоновыми акцентами
        'ui_bg': (10, 10, 20),              # Темный фон
        'ui_bg_solid': (15, 15, 25),        # Непрозрачный вариант
        'ui_bg_glow': (25, 25, 40),         # Свечение фона
        'ui_border': (0, 255, 255),         # Неоновая граница
        'ui_border_glow': (0, 200, 255),    # Свечение границы
        'ui_glass': (20, 20, 35),           # Стеклянный эффект
        
        # Текст - яркий и контрастный
        'text': (255, 255, 255),            # Белый текст
        'text_accent': (255, 200, 0),       # Золотой акцент
        'text_highlight': (0, 255, 255),   # Циан для выделения
        'text_dim': (150, 150, 150),        # Приглушенный текст
        'text_scan': (0, 255, 150),         # Зеленое сканирование
        
        # График и прогресс-бары
        'chart_line': (0, 255, 255),        # Яркая линия графика
        'chart_glow': (0, 200, 255),        # Свечение графика
        'chart_bg': (5, 10, 15),            # Фон графика
        'progress_bar': (0, 255, 150),      # Зеленый прогресс
        'progress_bar_warning': (255, 200, 0), # Желтый предупреждение
        'progress_bar_danger': (255, 50, 50),  # Красный опасность
        'progress_bar_bg': (20, 20, 30),    # Фон прогресс-бара
        
        # Эффекты
        'victory': (255, 255, 0),           # Золотой для победы
        'victory_glow': (255, 200, 0),      # Свечение победы
        'death': (255, 0, 0),               # Красный для смерти
        'generation_flash': (255, 255, 255), # Белая вспышка поколения
        'particle': (255, 255, 255),        # Белые частицы
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
        self.width = self.grid_size * cell_size + 400  # +400 для улучшенной статистики
        self.height = self.grid_size * cell_size + 120  # +120 для статус-бара
        
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('🐍 Эволюционная Змейка')
        
        # Анимационные переменные для улучшенной змеи
        self.snake_animation_time = 0
        self.snake_wave_offset = 0
        self.snake_particles = []  # Частицы энергии для змеи
        
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
        self.demo_last_food_step = 0  # Шаг когда последний раз ела (для совместимости)
        self.death_timer = 0  # Таймер для задержки после смерти
        
        # Таймер для авторежима
        self.auto_timer = 0
        self.auto_delay = 10000  # 10 секунд в миллисекундах
        
        # Эффекты цифровой симуляции
        self.food_flash_alpha = 0
        self.food_flash_radius = 0
        self.trails = []  # Следы змеек
        self.particles = []  # Частицы для эффектов
        
        # Эффект поколения
        self.generation_flash = 0
        self.generation_text = None
        
        # Анимационные параметры
        self.time_offset = 0
        
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
        """СТРИМ-ДИЗАЙН: Яркая неоновая сетка с эффектом свечения."""
        grid_width = self.grid_size * self.cell_size
        grid_height = self.grid_size * self.cell_size
        
        # Глубокий черный фон
        grid_rect = pygame.Rect(0, 0, grid_width, grid_height)
        pygame.draw.rect(self.screen, self.COLORS['background'], grid_rect)
        
        # Анимированный паттерн фона (движущиеся точки)
        current_time = pygame.time.get_ticks()
        import math
        for i in range(20):
            x = int((current_time / 50 + i * 37) % grid_width)
            y = int((current_time / 70 + i * 23) % grid_height)
            alpha = abs(math.sin(current_time / 1000.0 + i)) * 0.1
            dot_color = tuple(int(c * alpha) for c in (0, 100, 150))
            pygame.draw.circle(self.screen, dot_color, (x, y), 1)
        
        # Яркие неоновые линии сетки
        pulse = abs(np.sin(current_time / 1500.0)) * 0.3 + 0.7
        
        # Основные линии - яркий циан с пульсацией
        for x in range(0, self.grid_size + 1):
            alpha = 0.3 * pulse
            grid_color = tuple(int(c * alpha) for c in self.COLORS['grid'])
            start_pos = (x * self.cell_size, 0)
            end_pos = (x * self.cell_size, grid_height)
            pygame.draw.line(self.screen, grid_color, start_pos, end_pos, 1)
        
        for y in range(0, self.grid_size + 1):
            alpha = 0.3 * pulse
            grid_color = tuple(int(c * alpha) for c in self.COLORS['grid'])
            start_pos = (0, y * self.cell_size)
            end_pos = (grid_width, y * self.cell_size)
            pygame.draw.line(self.screen, grid_color, start_pos, end_pos, 1)
        
        # Яркие акцентные линии каждые 5 клеток - пурпурный неон
        glow_pulse = abs(np.sin(current_time / 1000.0)) * 0.5 + 0.5
        for x in range(0, self.grid_size + 1, 5):
            if x > 0 and x < self.grid_size:
                # Основная линия
                highlight_color = tuple(int(c * glow_pulse * 0.8) for c in self.COLORS['grid_highlight'])
                start_pos = (x * self.cell_size, 0)
                end_pos = (x * self.cell_size, grid_height)
                pygame.draw.line(self.screen, highlight_color, start_pos, end_pos, 2)
                # Многослойное свечение
                for glow_layer in range(3, 0, -1):
                    glow_alpha = 0.3 / glow_layer * glow_pulse
                    glow_color = tuple(int(c * glow_alpha) for c in self.COLORS['grid_highlight'])
                    offset = glow_layer
                    pygame.draw.line(self.screen, glow_color, 
                                   (x * self.cell_size - offset, 0), 
                                   (x * self.cell_size - offset, grid_height), 1)
                    pygame.draw.line(self.screen, glow_color, 
                                   (x * self.cell_size + offset, 0), 
                                   (x * self.cell_size + offset, grid_height), 1)
        
        for y in range(0, self.grid_size + 1, 5):
            if y > 0 and y < self.grid_size:
                highlight_color = tuple(int(c * glow_pulse * 0.8) for c in self.COLORS['grid_highlight'])
                start_pos = (0, y * self.cell_size)
                end_pos = (grid_width, y * self.cell_size)
                pygame.draw.line(self.screen, highlight_color, start_pos, end_pos, 2)
                for glow_layer in range(3, 0, -1):
                    glow_alpha = 0.3 / glow_layer * glow_pulse
                    glow_color = tuple(int(c * glow_alpha) for c in self.COLORS['grid_highlight'])
                    offset = glow_layer
                    pygame.draw.line(self.screen, glow_color, 
                                   (0, y * self.cell_size - offset), 
                                   (grid_width, y * self.cell_size - offset), 1)
                    pygame.draw.line(self.screen, glow_color, 
                                   (0, y * self.cell_size + offset), 
                                   (grid_width, y * self.cell_size + offset), 1)
    
    def draw_snake(self, snake):
        """УЛУЧШЕННЫЙ СТРИМ-ДИЗАЙН: Продвинутая неоновая змейка с 3D эффектами и анимацией."""
        # Обновляем анимацию
        current_time = pygame.time.get_ticks()
        self.snake_animation_time = current_time
        self.snake_wave_offset = (self.snake_wave_offset + 0.15) % (2 * np.pi)
        
        # Определяем цвет на основе поколения (яркие неоновые цвета)
        gen = self.evolution.generation if hasattr(self.evolution, 'generation') else 0
        if gen < 100:
            snake_color = self.COLORS['snake_gen1']  # Яркий неоновый зеленый
            glow_color = (0, 255, 200)
            accent_color = (100, 255, 150)
        elif gen < 500:
            snake_color = self.COLORS['snake_gen2']  # Яркий циан
            glow_color = (100, 255, 255)
            accent_color = (150, 255, 255)
        elif gen < 1000:
            snake_color = self.COLORS['snake_gen3']  # Яркий пурпурный
            glow_color = (255, 100, 255)
            accent_color = (255, 150, 255)
        else:
            snake_color = self.COLORS['snake_gen4']  # Яркий желтый (элита)
            glow_color = (255, 255, 150)
            accent_color = (255, 255, 200)
        
        # Мощная пульсация энергии с несколькими частотами
        pulse1 = abs(np.sin(current_time / 150.0))  # Быстрая пульсация
        pulse2 = abs(np.sin(current_time / 300.0))  # Медленная пульсация
        pulse3 = abs(np.sin(current_time / 100.0))  # Очень быстрая для эффектов
        combined_pulse = (pulse1 + pulse2) / 2.0
        pulse_offset = int(combined_pulse * 8)
        
        # Рисуем тело с эффектом волны
        for i, (x, y) in enumerate(snake.body):
            px = x * self.cell_size
            py = y * self.cell_size
            margin = 1
            
            # Волна энергии по телу (движется от головы к хвосту)
            wave_phase = self.snake_wave_offset - (i * 0.5)
            wave_effect = abs(np.sin(wave_phase)) * 0.3 + 0.7
            
            # Градиент яркости по длине тела с волной
            body_progress = i / max(1, len(snake.body) - 1)
            if i == 0:
                body_progress = 1.0
            
            # Комбинированная яркость с волной
            body_alpha = (0.6 + body_progress * 0.4) * wave_effect
            
            if i == 0:  # Голова - УЛУЧШЕННОЕ мощное свечение
                # Расширенное многослойное пульсирующее свечение (12 слоев)
                for glow_layer in range(12, 0, -1):
                    glow_size = self.cell_size + pulse_offset + glow_layer * 5
                    glow_rect = pygame.Rect(
                        px - (glow_size - self.cell_size) // 2,
                        py - (glow_size - self.cell_size) // 2,
                        glow_size, glow_size
                    )
                    alpha = 1.0 / (glow_layer + 1) * 0.7 * (0.7 + combined_pulse * 0.3)
                    glow_col = tuple(int(c * alpha) for c in glow_color)
                    # Рисуем с градиентом свечения
                    pygame.draw.rect(self.screen, glow_col, glow_rect, width=2, border_radius=10)
                
                # Внешний ореол (самый большой)
                halo_size = self.cell_size + pulse_offset + 20
                halo_rect = pygame.Rect(
                    px - (halo_size - self.cell_size) // 2,
                    py - (halo_size - self.cell_size) // 2,
                    halo_size, halo_size
                )
                halo_alpha = 0.3 * combined_pulse
                halo_col = tuple(int(c * halo_alpha) for c in accent_color)
                pygame.draw.ellipse(self.screen, halo_col, halo_rect)
                
                # 3D эффект с тенью
                shadow_rect = pygame.Rect(px + 2, py + 2, self.cell_size - 2, self.cell_size - 2)
                shadow_color = (0, 0, 0, 100)
                pygame.draw.rect(self.screen, (0, 0, 0), shadow_rect, border_radius=8)
                
                # Голова - многослойная с градиентом
                head_rect = pygame.Rect(px + margin, py + margin,
                                      self.cell_size - margin * 2, self.cell_size - margin * 2)
                
                # Внешний слой свечения
                outer_glow = tuple(int(c * 0.9) for c in snake_color)
                pygame.draw.rect(self.screen, outer_glow, head_rect, width=3, border_radius=10)
                
                # Основной цвет (максимальная яркость с пульсацией)
                main_brightness = 0.9 + combined_pulse * 0.1
                main_color = tuple(int(c * main_brightness) for c in snake_color)
                pygame.draw.rect(self.screen, main_color, head_rect, border_radius=10)
                
                # Внутреннее ядро с пульсацией
                inner_size = int(6 + pulse3 * 3)
                inner_rect = pygame.Rect(
                    px + (self.cell_size - inner_size) // 2,
                    py + (self.cell_size - inner_size) // 2,
                    inner_size, inner_size
                )
                inner_brightness = 0.8 + pulse3 * 0.2
                inner_color = tuple(int(c * inner_brightness) for c in self.COLORS['snake_head_glow'])
                pygame.draw.ellipse(self.screen, inner_color, inner_rect)
                
                # Улучшенные глаза-сенсоры с анимацией
                eye_pulse = abs(np.sin(current_time / 180.0))
                eye_brightness = int(255 * (0.85 + eye_pulse * 0.15))
                eye_color = (eye_brightness, eye_brightness, eye_brightness)
                
                # Левый глаз - многослойный
                left_eye_pos = (px + 6, py + 6)
                # Внешнее свечение глаза
                pygame.draw.circle(self.screen, tuple(int(c * 0.5) for c in glow_color), 
                                 left_eye_pos, 6)
                # Основной глаз
                pygame.draw.circle(self.screen, eye_color, left_eye_pos, 5)
                # Внутреннее ядро
                pygame.draw.circle(self.screen, glow_color, left_eye_pos, 3)
                # Блик
                pygame.draw.circle(self.screen, (255, 255, 255), 
                                 (left_eye_pos[0] - 1, left_eye_pos[1] - 1), 1)
                
                # Правый глаз - многослойный
                right_eye_pos = (px + self.cell_size - 6, py + 6)
                pygame.draw.circle(self.screen, tuple(int(c * 0.5) for c in glow_color), 
                                 right_eye_pos, 6)
                pygame.draw.circle(self.screen, eye_color, right_eye_pos, 5)
                pygame.draw.circle(self.screen, glow_color, right_eye_pos, 3)
                pygame.draw.circle(self.screen, (255, 255, 255), 
                                 (right_eye_pos[0] - 1, right_eye_pos[1] - 1), 1)
                
                # Энергетические частицы вокруг головы
                if np.random.random() < 0.3:  # 30% шанс добавить частицу
                    particle_x = px + np.random.randint(0, self.cell_size)
                    particle_y = py + np.random.randint(0, self.cell_size)
                    particle_size = np.random.randint(2, 4)
                    particle_alpha = np.random.random() * 0.8
                    particle_col = tuple(int(c * particle_alpha) for c in accent_color)
                    pygame.draw.circle(self.screen, particle_col, (int(particle_x), int(particle_y)), particle_size)
                
            else:
                # Тело - УЛУЧШЕННОЕ с волновым эффектом
                body_color = tuple(int(c * body_alpha) for c in snake_color)
                
                # 3D эффект с тенью для тела
                shadow_offset = 1
                shadow_rect = pygame.Rect(
                    px + margin + shadow_offset, 
                    py + margin + shadow_offset,
                    self.cell_size - margin * 2, 
                    self.cell_size - margin * 2
                )
                pygame.draw.rect(self.screen, (0, 0, 0), shadow_rect, border_radius=6)
                
                body_rect = pygame.Rect(px + margin, py + margin,
                                       self.cell_size - margin * 2, self.cell_size - margin * 2)
                
                # Многослойное свечение тела
                for glow_layer in range(3, 0, -1):
                    glow_alpha = (0.3 / glow_layer) * body_alpha
                    glow_size = self.cell_size - margin * 2 + glow_layer * 2
                    glow_rect = pygame.Rect(
                        px + margin - glow_layer,
                        py + margin - glow_layer,
                        glow_size, glow_size
                    )
                    glow_col = tuple(int(c * glow_alpha) for c in snake_color)
                    pygame.draw.rect(self.screen, glow_col, glow_rect, width=2, border_radius=6 + glow_layer)
                
                # Основной цвет тела
                pygame.draw.rect(self.screen, body_color, body_rect, border_radius=6)
                
                # Внутренний градиент
                inner_margin = 2
                inner_rect = pygame.Rect(
                    px + margin + inner_margin, 
                    py + margin + inner_margin,
                    self.cell_size - margin * 2 - inner_margin * 2, 
                    self.cell_size - margin * 2 - inner_margin * 2
                )
                inner_alpha = body_alpha * 0.6
                inner_color = tuple(int(c * inner_alpha) for c in accent_color)
                pygame.draw.rect(self.screen, inner_color, inner_rect, border_radius=4)
                
                # Центральная точка энергии с пульсацией
                center = (px + self.cell_size // 2, py + self.cell_size // 2)
                center_pulse = abs(np.sin(current_time / 200.0 - i * 0.3))
                center_brightness = int(180 + body_progress * 75 + center_pulse * 30)
                center_size = int(2 + center_pulse * 2)
                center_color = tuple(min(255, int(c * (center_brightness / 255.0))) for c in snake_color)
                pygame.draw.circle(self.screen, center_color, center, center_size)
                
                # Энергетическая линия связи с градиентом
                if i > 0:
                    prev_pos = snake.body[i-1]
                    prev_px = prev_pos[0] * self.cell_size + self.cell_size // 2
                    prev_py = prev_pos[1] * self.cell_size + self.cell_size // 2
                    curr_px = x * self.cell_size + self.cell_size // 2
                    curr_py = y * self.cell_size + self.cell_size // 2
                    
                    # Толстая линия с градиентом
                    line_width = int(4 + wave_effect * 2)
                    line_alpha = 0.8 * body_alpha * wave_effect
                    line_color = tuple(int(c * line_alpha) for c in snake_color)
                    
                    # Рисуем линию с несколькими слоями для эффекта свечения
                    for layer in range(3, 0, -1):
                        layer_alpha = line_alpha / (layer + 1)
                        layer_color = tuple(int(c * layer_alpha) for c in glow_color)
                        layer_width = line_width + layer * 2
                        pygame.draw.line(self.screen, layer_color, 
                                       (prev_px, prev_py), (curr_px, curr_py), layer_width)
                    
                    # Основная линия
                    pygame.draw.line(self.screen, line_color, 
                                   (prev_px, prev_py), (curr_px, curr_py), line_width)
                    
                    # Энергетические частицы вдоль линии
                    if np.random.random() < 0.1:  # 10% шанс
                        particle_pos = (
                            int((prev_px + curr_px) / 2 + np.random.randint(-3, 4)),
                            int((prev_py + curr_py) / 2 + np.random.randint(-3, 4))
                        )
                        particle_col = tuple(int(c * 0.7) for c in accent_color)
                        pygame.draw.circle(self.screen, particle_col, particle_pos, 2)
    
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
        """СТРИМ-ДИЗАЙН: Яркая неоновая еда с мощными эффектами."""
        x, y = food_pos
        px = x * self.cell_size
        py = y * self.cell_size
        center = (px + self.cell_size // 2, py + self.cell_size // 2)
        
        current_time = pygame.time.get_ticks()
        import math
        
        # Мощная пульсация (быстрая и заметная)
        pulse1 = abs(np.sin(current_time / 200.0))
        pulse2 = abs(np.sin(current_time / 350.0))
        pulse_size = int((pulse1 * 0.7 + pulse2 * 0.3) * 8)
        
        # Многослойное магнитное свечение (10 слоев для максимального эффекта)
        for layer in range(10, 0, -1):
            radius = self.cell_size // 2 + pulse_size + layer * 3
            alpha = 1.0 / (layer + 1) * 0.5 * (0.9 + pulse1 * 0.1)
            glow_col = tuple(int(c * alpha) for c in self.COLORS['food_glow'])
            pygame.draw.circle(self.screen, glow_col, center, radius, width=1)
        
        # Вращающиеся частицы (больше частиц для эффекта)
        particle_count = 8
        rotation = current_time / 600.0
        for i in range(particle_count):
            angle = (i / particle_count) * 2 * math.pi + rotation
            particle_dist = self.cell_size // 2 + pulse_size + 8
            particle_x = center[0] + int(math.cos(angle) * particle_dist)
            particle_y = center[1] + int(math.sin(angle) * particle_dist)
            particle_alpha = 0.8 + pulse1 * 0.2
            particle_color = tuple(int(c * particle_alpha) for c in self.COLORS['food_particles'])
            pygame.draw.circle(self.screen, particle_color, (particle_x, particle_y), 3)
        
        # Основной круг - яркий неон
        outer_radius = self.cell_size // 2 + pulse_size
        pygame.draw.circle(self.screen, self.COLORS['food'], center, outer_radius, width=3)
        
        # Средний слой
        mid_radius = self.cell_size // 2 + pulse_size // 2
        mid_color = tuple(int(c * 0.9) for c in self.COLORS['food'])
        pygame.draw.circle(self.screen, mid_color, center, mid_radius, width=2)
        
        # Ядро - максимальная яркость
        core_radius = self.cell_size // 2 - 1
        pygame.draw.circle(self.screen, self.COLORS['food'], center, core_radius)
        
        # Внутреннее белое ядро
        inner_radius = core_radius - 3
        pygame.draw.circle(self.screen, self.COLORS['food_core'], center, inner_radius)
        
        # Вращающийся световой крест (быстрее)
        cross_rotation = current_time / 800.0
        cross_size = int(pulse_size + 6)
        for i in range(4):
            angle = (i * math.pi / 2) + cross_rotation
            start_x = center[0] + int(math.cos(angle) * (inner_radius - 1))
            start_y = center[1] + int(math.sin(angle) * (inner_radius - 1))
            end_x = center[0] + int(math.cos(angle) * cross_size)
            end_y = center[1] + int(math.sin(angle) * cross_size)
            flash_alpha = 0.9 + pulse1 * 0.1
            flash_color = tuple(int(c * flash_alpha) for c in self.COLORS['food_flash'])
            pygame.draw.line(self.screen, flash_color, (start_x, start_y), (end_x, end_y), 3)
        
        # Яркая центральная точка
        core_brightness = int(255 * (0.9 + pulse1 * 0.1))
        core_color = (core_brightness, core_brightness, core_brightness)
        pygame.draw.circle(self.screen, core_color, center, 4)
        pygame.draw.circle(self.screen, self.COLORS['food_flash'], center, 3)
        
        # Эффект вспышки
        if self.food_flash_alpha > 0:
            flash_color = tuple(int(c * (self.food_flash_alpha / 255.0)) for c in self.COLORS['food_flash'])
            pygame.draw.circle(self.screen, flash_color, center, self.food_flash_radius, width=3)
            self.food_flash_alpha = max(0, self.food_flash_alpha - 10)
            self.food_flash_radius += 4
    
    def draw_game_status_bar(self, snake):
        """Отрисовка статус-бара внизу игрового поля (счёт и голод)."""
        current_time = pygame.time.get_ticks()
        
        grid_size_px = self.grid_size * self.cell_size
        bar_y = grid_size_px
        bar_height = self.height - grid_size_px
        bar_width = grid_size_px
        
        # Фон статус-бара - темный с неоновой границей
        pygame.draw.rect(self.screen, self.COLORS['ui_bg_solid'], 
                        (0, bar_y, bar_width, bar_height))
        
        # Яркая неоновая разделительная линия
        line_pulse = abs(np.sin(current_time / 1000.0)) * 0.4 + 0.6
        line_color = tuple(int(c * line_pulse) for c in self.COLORS['ui_border'])
        pygame.draw.line(self.screen, line_color, 
                        (0, bar_y), (bar_width, bar_y), 4)
        # Свечение линии
        glow_color = tuple(int(c * 0.5) for c in self.COLORS['ui_border'])
        pygame.draw.line(self.screen, glow_color, 
                        (0, bar_y - 1), (bar_width, bar_y - 1), 2)
        pygame.draw.line(self.screen, glow_color, 
                        (0, bar_y + 1), (bar_width, bar_y + 1), 2)
        
        padding = 20
        y_offset = bar_y + padding
        
        # Счёт - яркий белый текст
        score_text = self.small_font.render('SCORE:', True, self.COLORS['text'])
        self.screen.blit(score_text, (padding, y_offset))
        
        score_value = int(snake.get_fitness())
        score_pulse = abs(np.sin(current_time / 600.0)) * 0.3 + 0.7
        score_color = tuple(int(c * score_pulse) for c in self.COLORS['text_accent'])
        score_display = self.font_large.render(f'{score_value}', True, score_color)
        # Свечение текста
        score_glow = self.font_large.render(f'{score_value}', True, 
                                           tuple(int(c * 0.3) for c in score_color))
        self.screen.blit(score_glow, (padding + 2, y_offset + 27))
        self.screen.blit(score_display, (padding, y_offset + 25))
        
        x_mid = bar_width // 2
        
        # Голод - яркий текст
        hunger_text = self.small_font.render('HUNGER:', True, self.COLORS['text'])
        self.screen.blit(hunger_text, (x_mid, y_offset))
        
        # Прогресс-бар голода
        hunger_bar_x = x_mid
        hunger_bar_y = y_offset + 25
        hunger_bar_width = bar_width // 2 - padding
        hunger_bar_height = 30
        
        # Макс голод = 8 секунд (по времени, не по шагам)
        max_hunger_seconds = 8.0
        hunger_percent = 1.0 - snake.get_hunger_percent(max_hunger_seconds)
        hunger_percent = max(0.0, min(1.0, hunger_percent))  # Ограничиваем 0-1
        
        # Фон прогресс-бара
        pygame.draw.rect(self.screen, self.COLORS['progress_bar_bg'], 
                        (hunger_bar_x, hunger_bar_y, hunger_bar_width, hunger_bar_height), 
                        border_radius=5)
        
        # Заполнение прогресс-бара (яркие неоновые цвета)
        fill_width = int(hunger_bar_width * hunger_percent)
        if hunger_percent > 0.5:
            hunger_color = self.COLORS['progress_bar']  # Яркий зеленый
        elif hunger_percent > 0.3:
            hunger_color = self.COLORS['progress_bar_warning']  # Яркий желтый
        else:
            hunger_color = self.COLORS['progress_bar_danger']  # Яркий красный
        
        if fill_width > 0:
            # Градиент заполнения
            pulse = abs(np.sin(current_time / 300.0)) * 0.2 + 0.8
            fill_color = tuple(int(c * pulse) for c in hunger_color)
            
            # Свечение заполнения
            pygame.draw.rect(self.screen, tuple(int(c * 0.4) for c in fill_color), 
                           (hunger_bar_x, hunger_bar_y, fill_width, hunger_bar_height), 
                           border_radius=4)
            # Основное заполнение
            pygame.draw.rect(self.screen, fill_color, 
                           (hunger_bar_x, hunger_bar_y, fill_width, hunger_bar_height), 
                           border_radius=4)
            
            # Анимация пульсации при критическом уровне
            if hunger_percent < 0.3:
                pulse2 = abs(np.sin(current_time / 200.0))
                pulse_alpha = int(100 + pulse2 * 155)
                pulse_overlay = pygame.Surface((fill_width, hunger_bar_height))
                pulse_overlay.fill(hunger_color)
                pulse_overlay.set_alpha(pulse_alpha)
                self.screen.blit(pulse_overlay, (hunger_bar_x, hunger_bar_y))
        
        # Яркая неоновая граница прогресс-бара
        border_pulse = abs(np.sin(current_time / 1500.0)) * 0.4 + 0.6
        border_color = tuple(int(c * border_pulse) for c in self.COLORS['ui_border'])
        pygame.draw.rect(self.screen, border_color, 
                        (hunger_bar_x, hunger_bar_y, hunger_bar_width, hunger_bar_height), 
                        width=3, border_radius=5)
        # Свечение границы
        glow_border = tuple(int(c * 0.4) for c in border_color)
        pygame.draw.rect(self.screen, glow_border, 
                        (hunger_bar_x - 1, hunger_bar_y - 1, 
                         hunger_bar_width + 2, hunger_bar_height + 2), 
                        width=1, border_radius=6)
        
        # Текст уровня голода
        hunger_level_text = self.tiny_font.render(f'{int(hunger_percent * 100)}%', True, 
                                                 self.COLORS['text'])
        hunger_level_rect = hunger_level_text.get_rect(
            center=(hunger_bar_x + hunger_bar_width // 2, 
                   hunger_bar_y + hunger_bar_height // 2))
        self.screen.blit(hunger_level_text, hunger_level_rect)
    
    def draw_stats(self, generation: int, best_fitness: float, avg_fitness: float):
        """Отрисовка улучшенной статистики с современным дизайном."""
        x_offset = self.grid_size * self.cell_size
        y_offset = 0
        panel_width = self.width - x_offset
        
        current_time = pygame.time.get_ticks()
        
        # Фон панели - темный с неоновой границей
        pygame.draw.rect(self.screen, self.COLORS['ui_bg_solid'], 
                        (x_offset, 0, panel_width, self.height))
        
        # Яркая неоновая разделительная линия
        border_pulse = abs(np.sin(current_time / 1500.0)) * 0.4 + 0.6
        border_color = tuple(int(c * border_pulse) for c in self.COLORS['ui_border'])
        pygame.draw.line(self.screen, border_color, 
                        (x_offset, 0), (x_offset, self.height), 4)
        # Многослойное свечение границы
        for glow_layer in range(3, 0, -1):
            glow_alpha = 0.3 / glow_layer
            glow_border = tuple(int(c * glow_alpha) for c in self.COLORS['ui_border'])
            offset = glow_layer
            pygame.draw.line(self.screen, glow_border, 
                            (x_offset - offset, 0), (x_offset - offset, self.height), 1)
            pygame.draw.line(self.screen, glow_border, 
                            (x_offset + offset, 0), (x_offset + offset, self.height), 1)
        
        # Сканирующая линия - яркая зеленая
        scan_y = int(current_time / 40) % self.height
        scan_alpha = abs(np.sin(current_time / 150.0)) * 0.6 + 0.4
        scan_color = tuple(int(c * scan_alpha) for c in self.COLORS['text_scan'])
        pygame.draw.line(self.screen, scan_color, 
                        (x_offset + 10, scan_y), (x_offset + panel_width - 10, scan_y), 3)
        # Свечение сканирующей линии
        pygame.draw.line(self.screen, tuple(int(c * 0.4) for c in scan_color), 
                        (x_offset + 10, scan_y - 1), (x_offset + panel_width - 10, scan_y - 1), 1)
        pygame.draw.line(self.screen, tuple(int(c * 0.4) for c in scan_color), 
                        (x_offset + 10, scan_y + 1), (x_offset + panel_width - 10, scan_y + 1), 1)
        
        # Заголовок
        x_offset += 20
        y_offset += 30
        
        # Яркий заголовок с неоновым свечением
        title_text = f'GEN {generation}'
        title_glow = self.font_large.render(title_text, True, 
                                          tuple(int(c * 0.4) for c in self.COLORS['text_highlight']))
        self.screen.blit(title_glow, (x_offset + 3, y_offset + 3))
        title = self.font_large.render(title_text, True, self.COLORS['text'])
        self.screen.blit(title, (x_offset, y_offset))
        
        # Мигающая курсорная линия с пульсацией
        cursor_blink = (current_time // 500) % 2
        if cursor_blink:
            cursor_x = x_offset + title.get_width() + 5
            cursor_pulse = abs(np.sin(current_time / 300.0)) * 0.5 + 0.5
            cursor_color = tuple(int(c * cursor_pulse) for c in self.COLORS['text_scan'])
            pygame.draw.line(self.screen, cursor_color,
                           (cursor_x, y_offset),
                           (cursor_x, y_offset + title.get_height()), 3)
        
        y_offset += 50
        
        # Данные в стиле терминала
        stats_items = [
            ('Gen:', f'{generation}'),
            ('Best IQ:', f'{best_fitness:.1f}'),
            ('Avg IQ:', f'{avg_fitness:.1f}'),
        ]
        
        for idx, (label, value) in enumerate(stats_items):
            # Подсветка строки при сканировании
            scan_distance = abs(scan_y - y_offset)
            if scan_distance < 35:
                highlight_alpha = max(0, 1.0 - scan_distance / 35.0) * 0.4
                highlight_rect = pygame.Rect(x_offset - 10, y_offset - 2, panel_width - 20, 32)
                highlight_color = tuple(int(c * highlight_alpha) for c in self.COLORS['text_scan'])
                pygame.draw.rect(self.screen, highlight_color, highlight_rect, border_radius=4)
            
            # Метка - яркий белый текст
            label_text = self.small_font.render(label, True, self.COLORS['text'])
            self.screen.blit(label_text, (x_offset, y_offset))
            
            # Значение - яркий золотой с пульсацией
            value_pulse = abs(np.sin(current_time / 800.0 + idx * 0.5)) * 0.3 + 0.7
            value_color = tuple(int(c * value_pulse) for c in self.COLORS['text_accent'])
            # Свечение значения
            value_glow = self.font.render(value, True, 
                                        tuple(int(c * 0.4 * value_pulse) for c in value_color))
            self.screen.blit(value_glow, (x_offset + 122, y_offset + 2))
            value_text = self.font.render(value, True, value_color)
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
            text = self.tiny_font.render(instr, True, self.COLORS['text_dim'])
            self.screen.blit(text, (x_offset, y_offset))
            y_offset += 22
        
        # График прогресса
        if len(self.evolution.best_fitness_history) > 1:
            y_offset += 20
            chart_title = self.small_font.render('EVOLUTION:', True, self.COLORS['text'])
            self.screen.blit(chart_title, (x_offset, y_offset))
            y_offset += 25
            
            self.draw_mini_chart(x_offset, y_offset, 300, 80)
    
    def draw_mini_chart(self, x, y, width, height):
        """СТРИМ-ДИЗАЙН: Яркий неоновый график."""
        if len(self.evolution.best_fitness_history) < 2:
            return
        
        current_time = pygame.time.get_ticks()
        
        # Темный фон графика
        pygame.draw.rect(self.screen, self.COLORS['chart_bg'], (x, y, width, height))
        # Яркая неоновая граница
        border_pulse = abs(np.sin(current_time / 1500.0)) * 0.4 + 0.6
        border_color = tuple(int(c * border_pulse) for c in self.COLORS['ui_border'])
        pygame.draw.rect(self.screen, border_color, (x, y, width, height), 3)
        # Свечение границы
        glow_border = tuple(int(c * 0.3) for c in border_color)
        pygame.draw.rect(self.screen, glow_border, (x - 1, y - 1, width + 2, height + 2), 1)
        
        # Сетка осциллографа - приглушенный неон
        for grid_y in range(y + 10, y + height - 10, 20):
            grid_alpha = 0.2
            grid_color = tuple(int(c * grid_alpha) for c in self.COLORS['grid_dim'])
            pygame.draw.line(self.screen, grid_color, (x + 5, grid_y), (x + width - 5, grid_y), 1)
        
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
                # Многослойная тень линии для глубины
                for shadow_offset in [3, 2, 1]:
                    shadow_alpha = 0.1 / shadow_offset
                    shadow_points = [(px, py + shadow_offset) for px, py in points]
                    shadow_color = tuple(int(c * shadow_alpha) for c in (0, 0, 0))
                    pygame.draw.lines(self.screen, shadow_color, False, shadow_points, 2)
                
                # Яркая неоновая линия графика
                for i in range(len(points) - 1):
                    p1 = points[i]
                    p2 = points[i + 1]
                    # Градиент яркости
                    line_progress = i / (len(points) - 1)
                    line_alpha = 0.7 + line_progress * 0.3
                    line_color = tuple(int(c * line_alpha) for c in self.COLORS['chart_line'])
                    pygame.draw.line(self.screen, line_color, p1, p2, 4)
                
                # Эффект "развёртки" - яркое свечение
                pulse = abs(np.sin(current_time / 300.0))
                if points:
                    last_px, last_py = points[-1]
                    # Многослойное свечение
                    for glow_layer in range(5, 0, -1):
                        end_glow = int(4 + pulse * 4 + glow_layer * 3)
                        glow_alpha = 1.0 / (glow_layer + 1) * 0.5
                        glow_color = tuple(int(c * glow_alpha) for c in self.COLORS['chart_glow'])
                        pygame.draw.circle(self.screen, glow_color, (last_px, last_py), end_glow)
                    # Основная точка - яркая
                    pygame.draw.circle(self.screen, self.COLORS['chart_line'], (last_px, last_py), 5)
                    pygame.draw.circle(self.screen, self.COLORS['chart_glow'], (last_px, last_py), 3)
                    pygame.draw.circle(self.screen, (255, 255, 255), (last_px, last_py), 2)
    
    def animate_best_snake(self):
        """Анимация лучшей змейки, показывающая как она играет."""
        if self.demo_snake is None:
            return
        
        # Проверка победы: змейка заполнила всё поле
        max_grid_size = self.grid_size * self.grid_size
        if self.demo_snake.alive and len(self.demo_snake.body) >= max_grid_size:
            # Победа!
            self.demo_snake.fitness += 10000.0
            self.demo_snake.alive = False
            print("🎉 ПОБЕДА! Змейка заполнила всё поле!")
        
        # Проверка смерти от голода (по времени, не по шагам)
        if self.demo_snake.alive:
            time_without_food = self.demo_snake.get_time_without_food()
            if time_without_food > 8.0:  # 8 секунд без еды = смерть
                self.demo_snake.alive = False
        
        # Один шаг игры
        if self.demo_step < self.demo_max_steps and self.demo_snake.alive:
            # Получение входных данных для мозга (для совместимости берём первую еду)
            food_pos = self.demo_food_positions[0] if self.demo_food_positions else (5, 5)
            # Препятствия удалены - пустой список стен
            inputs = self.demo_snake.get_view(food_pos, walls=[])
            
            # Мозг принимает решение
            action = self.demo_snake.brain.think(inputs)
            
            # Движение (без препятствий)
            move_success = self.demo_snake.move(action, walls=[])
            
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
                
                # Яды и бонусы удалены
                
                if not food_eaten:
                    self.demo_snake.remove_tail()
                
                self.demo_snake.update_fitness()
            else:
                # Движение неудачно (столкновение) - змейка уже мертва
                pass
            
            self.demo_step += 1
    
    def visualize_generation(self, auto_mode: bool = False):
        """Визуализация текущего поколения с анимацией."""
        running = True
        paused = False
        self.auto_timer = pygame.time.get_ticks()  # Сброс таймера
        
        # Подготовка демо-змейки для анимации
        if self.demo_snake is None:
            # Сброс таймера смерти
            self.death_timer = 0
            
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
            
            # Проверка победы или смерти змейки
            if self.demo_snake and not self.demo_snake.alive and not paused:
                # Проверяем, была ли это победа (fitness >= 10000)
                is_victory = self.demo_snake.fitness >= 10000.0
                
                # Запускаем таймер (если еще не запущен)
                if self.death_timer == 0:
                    if is_victory:
                        print("🎉 ПОБЕДА! Змейка заполнила всё поле!")
                        # Можно добавить звук победы
                    else:
                        self.play_sound_death()  # Звук смерти
                    self.death_timer = pygame.time.get_ticks()
                
                # Задержка перед переходом (2 секунды для победы, 1 секунда для смерти)
                delay = 2000 if is_victory else 1000
                if pygame.time.get_ticks() - self.death_timer > delay:
                    self.demo_snake = None
                    self.demo_step = 0
                    self.demo_last_food_step = 0
                    self.death_timer = 0
                    # Сброс флагов звуков
                    self.last_sound_eat = False
                    self.last_sound_death = False
                    self.last_sound_stuck = False
                    
                    # Если победа, возвращаем специальный код
                    if is_victory:
                        return "VICTORY"
                    return True
            
            # Авторежим - дополнительная проверка застревания
            if auto_mode and not paused:
                # Если змейка застряла (не ест >10 секунд по времени)
                if self.demo_snake and self.demo_snake.alive:
                    time_without_food = self.demo_snake.get_time_without_food()
                    if time_without_food > 10.0:  # 10 секунд без еды = застревание
                        self.play_sound_stuck()  # Звук застревания
                        pygame.time.wait(300)  # Небольшая задержка
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
            
            # Препятствия удалены - стены, яды и бонусы не отрисовываются
            
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
            
            # Индикатор паузы - яркий неоновый
            if paused:
                pause_text = self.font_large.render('[PAUSED]', True, self.COLORS['text_accent'])
                pause_rect = pause_text.get_rect(center=(self.width // 2, 30))
                # Фон для паузы с свечением
                pause_bg = pygame.Surface((pause_rect.width + 30, pause_rect.height + 15))
                pause_bg.set_alpha(220)
                pause_bg.fill((0, 0, 0))
                self.screen.blit(pause_bg, (pause_rect.x - 15, pause_rect.y - 7))
                # Свечение текста
                pause_glow = self.font_large.render('[PAUSED]', True, 
                                                  tuple(int(c * 0.4) for c in self.COLORS['text_accent']))
                self.screen.blit(pause_glow, (pause_rect.x + 2, pause_rect.y + 2))
                self.screen.blit(pause_text, pause_rect)
            
            # Эффект вспышки поколения - яркий неоновый
            if self.generation_flash > 0:
                self.play_sound_generation()  # Звук смены поколения
                gen_text = f'GENERATION {self.generation_text}'
                flash_alpha = self.generation_flash / 255.0
                flash_color = tuple(int(c * flash_alpha) for c in self.COLORS['generation_flash'])
                flash_text = self.font_large.render(gen_text, True, flash_color)
                flash_rect = flash_text.get_rect(center=(self.width // 2, self.height // 2))
                
                # Вспышка фона - неоновая
                alpha = int(self.generation_flash * 0.3)
                overlay = pygame.Surface((self.width, self.height))
                overlay.fill(self.COLORS['text_highlight'])
                overlay.set_alpha(alpha)
                self.screen.blit(overlay, (0, 0))
                
                # Тень текста
                shadow = self.font_large.render(gen_text, True, (0, 0, 0))
                self.screen.blit(shadow, (flash_rect.x + 3, flash_rect.y + 3))
                # Свечение текста
                glow = self.font_large.render(gen_text, True, 
                                            tuple(int(c * 0.5) for c in flash_color))
                self.screen.blit(glow, (flash_rect.x + 1, flash_rect.y + 1))
                # Основной текст
                self.screen.blit(flash_text, flash_rect)
                
                self.generation_flash = max(0, self.generation_flash - 12)
            
            pygame.display.flip()
            self.clock.tick(10 if auto_mode else 15)  # Скорость анимации
        
        return False
    
    def quit(self):
        """Закрытие pygame."""
        pygame.quit()

