"""
Главный файл для запуска эволюционной змейки.
"""

import argparse
import signal
import sys
from evolution import Evolution
from database import EvolutionDB
import numpy as np

# Глобальные переменные для обработчика сигналов
db = None
session_id = None
evolution = None
finalized = False


def signal_handler(sig, frame):
    """Обработчик сигнала для корректного завершения."""
    global db, session_id, evolution, finalized
    if finalized:
        sys.exit(0)
    finalized = True
    
    if db and session_id and evolution:
        print("\n⚠️  Получен сигнал прерывания. Сохранение прогресса...")
        db.update_session(
            session_id,
            evolution.generation,
            evolution.best_fitness_in_history
        )
        print(f"✓ Сессия #{session_id} сохранена: поколение {evolution.generation}, fitness {evolution.best_fitness_in_history:.1f}")
    
    sys.exit(0)


def main():
    """Основная функция."""
    global db, session_id, evolution
    
    # Регистрируем обработчик сигнала для корректного завершения
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    parser = argparse.ArgumentParser(description='Эволюционная змейка')
    parser.add_argument('--pop', type=int, default=100, help='Размер популяции')
    parser.add_argument('--gens', type=int, default=500, help='Количество поколений')
    parser.add_argument('--elite', type=int, default=10, help='Размер элиты')
    parser.add_argument('--grid', type=int, default=20, help='Размер поля')
    parser.add_argument('--mutation-rate', type=float, default=0.1, help='Вероятность мутации')
    parser.add_argument('--mutation-strength', type=float, default=0.2, help='Сила мутации')
    parser.add_argument('--max-steps', type=int, default=400, help='Макс. шагов в игре')
    parser.add_argument('--visualize', action='store_true', help='Включить визуализацию')
    parser.add_argument('--auto', action='store_true', help='Автоматический режим')
    parser.add_argument('--db', default='evolution.db', help='Путь к базе данных')
    parser.add_argument('--no-db', action='store_true', help='Отключить сохранение в БД')
    parser.add_argument('--continue', type=int, metavar='SESSION_ID', dest='continue_session',
                       help='Продолжить с лучшей змейкой из сессии SESSION_ID')
    
    args = parser.parse_args()
    
    # Инициализация базы данных
    if not args.no_db:
        try:
            db = EvolutionDB(args.db)
            session_id = db.create_session(
                population_size=args.pop,
                grid_size=args.grid,
                elite_size=args.elite,
                mutation_rate=args.mutation_rate,
                mutation_strength=args.mutation_strength,
                max_steps=args.max_steps,
                notes=''
            )
            print(f"✓ База данных: {args.db} (Session #{session_id})")
        except Exception as e:
            print(f"⚠️  Ошибка БД: {e}. Продолжаем без сохранения.")
            db = None
    
    # Загрузка лучшей змейки из прошлой сессии (если нужно)
    initial_brain = None
    if args.continue_session and db:
        try:
            best_snakes = db.get_best_snakes(session_id=args.continue_session, limit=1)
            if best_snakes:
                from brain import Brain
                s_id, gen, fitness, weights_bytes = best_snakes[0]
                weights = db.load_snake_weights(weights_bytes)
                initial_brain = Brain(weights=weights)
                print(f"✓ Загружена лучшая змейка из сессии #{s_id}, поколение {gen}, fitness {fitness:.1f}")
        except Exception as e:
            print(f"⚠️  Ошибка загрузки прошлой сессии: {e}")
    
    # Создание эволюционной системы
    evolution = Evolution(
        population_size=args.pop,
        grid_size=args.grid,
        elite_size=args.elite,
        mutation_rate=args.mutation_rate,
        mutation_strength=args.mutation_strength,
        max_steps=args.max_steps
    )
    
    # Если есть загруженный мозг, добавляем его в популяцию
    if initial_brain:
        from snake import Snake
        loaded_snake = Snake(brain=initial_brain, grid_size=args.grid)
        # Заменяем случайную змейку на загруженную
        evolution.population[0] = loaded_snake
        print(f"✓ Восстановленная змейка добавлена в популяцию")
    
    # Визуализатор (если нужен)
    visualizer = None
    if args.visualize:
        from visualizer import Visualizer
        visualizer = Visualizer(evolution)
    
    print("=" * 60)
    print("ЭВОЛЮЦИОННАЯ ЗМЕЙКА")
    print("=" * 60)
    print(f"Популяция: {args.pop}")
    print(f"Поколений: {args.gens}")
    print(f"Размер поля: {args.grid}x{args.grid}")
    if args.continue_session:
        print(f"Продолжение с сессии #{args.continue_session}")
    print("=" * 60)
    print()
    
    # Основной цикл эволюции
    for gen in range(args.gens):
        best_fit, avg_fit = evolution.evolve()
        
        # Сохранение в БД
        if db and session_id:
            db.save_generation(session_id, evolution.generation, best_fit, avg_fit)
            # Сохраняем лучшую змейку раз в 10 поколений (не каждое)
            if hasattr(evolution, 'current_best_snake') and evolution.generation % 10 == 0:
                db.save_best_snake(
                    session_id, 
                    evolution.generation, 
                    best_fit,
                    evolution.current_best_snake.brain.weights
                )
        
        # Вывод статистики
        print(f"Поколение {evolution.generation:4d} | "
              f"Лучший: {best_fit:6.1f} | "
              f"Средний: {avg_fit:6.1f}")
        
        # Визуализация (если нужна)
        if args.visualize:
            result = visualizer.visualize_generation(auto_mode=args.auto)
            if not result:
                print("\nВизуализация остановлена пользователем.")
                break
        
        # Сохранение лучшей змейки периодически
        if (gen + 1) % 50 == 0:
            print(f"✓ Поколение {gen + 1} завершено")
    
    # Финальная статистика
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ ЭВОЛЮЦИИ")
    print("=" * 60)
    
    # Обновление финальной статистики в БД
    if db and session_id:
        db.update_session(
            session_id,
            evolution.generation,
            evolution.best_fitness_in_history
        )
    
    # Получаем лучшую змейку
    best_snake = evolution.get_best_snake()
    
    print(f"Лучший fitness в истории: {evolution.best_fitness_in_history:.1f}")
    
    # Демонстрационная игра для статистики
    if best_snake and evolution.best_fitness_in_history > 0:
        demo_snake = best_snake.clone()
        demo_fitness = evolution.environment.play_game(demo_snake, evolution.max_steps)
        print(f"Демо игра fitness: {demo_fitness:.1f}")
        print(f"Длина змейки: {len(demo_snake.body)}")
        print(f"Шагов: {demo_snake.steps}")
    else:
        print("Демо игра не выполнена (нет сохраненной змейки)")
    
    # Визуализация финальной змейки
    if args.visualize:
        print("\nДемонстрация лучшей змейки. Закройте окно для выхода.")
        
        # Показать демо лучшей змейки
        demo_evolution = Evolution(population_size=1, grid_size=args.grid)
        demo_evolution.population = [best_snake.clone()]
        
        demo_visualizer = Visualizer(demo_evolution)
        demo_visualizer.visualize_generation()
        demo_visualizer.quit()
    
    # Закрытие БД
    if db:
        db.close()
        print(f"✓ Данные сохранены в {args.db}")
    
    print("=" * 60)


if __name__ == '__main__':
    main()

