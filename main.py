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
        # Сохраняем лучшую змейку перед выходом
        if hasattr(evolution, 'current_best_snake') and evolution.current_best_snake:
            db.save_best_snake(
                session_id,
                evolution.generation,
                evolution.best_fitness_in_history,
                evolution.current_best_snake.brain.weights
            )
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
    parser.add_argument('--max-steps', type=int, default=100000, help='Макс. шагов в игре (для победы нужно ~400-5000)')
    parser.add_argument('--visualize', action='store_true', help='Включить визуализацию')
    parser.add_argument('--auto', action='store_true', help='Автоматический режим')
    parser.add_argument('--db', default='evolution.db', help='Путь к базе данных')
    parser.add_argument('--no-db', action='store_true', help='Отключить сохранение в БД')
    parser.add_argument('--continue', type=int, metavar='SESSION_ID', dest='continue_session',
                       help='Продолжить с лучшей змейкой из сессии SESSION_ID')
    parser.add_argument('--auto-continue', action='store_true',
                       help='Автоматически продолжить с последней сессии')
    parser.add_argument('--fast', action='store_true',
                       help='Быстрый режим: увеличенная популяция, элита и мутации')
    
    args = parser.parse_args()
    
    # Автоматическая оптимизация для быстрого режима
    if args.fast:
        if args.pop == 100:  # Только если не указано вручную
            args.pop = 200  # Увеличиваем популяцию
        if args.elite == 10:  # Только если не указано вручную
            args.elite = 30  # Увеличиваем элиту
        if args.mutation_rate == 0.1:  # Только если не указано вручную
            args.mutation_rate = 0.15  # Увеличиваем частоту мутаций
        if args.mutation_strength == 0.2:  # Только если не указано вручную
            args.mutation_strength = 0.25  # Увеличиваем силу мутаций
        print("⚡ Быстрый режим активирован: pop=200, elite=30, mutation_rate=0.15")
    
    # Инициализация базы данных (создается автоматически если не существует)
    db = None
    session_id = None
    if not args.no_db:
        try:
            # Создаем БД если её нет
            import os
            if not os.path.exists(args.db):
                print(f"💾 Создание базы данных: {args.db}")
            
            db = EvolutionDB(args.db)
        except Exception as e:
            print(f"⚠️  Ошибка БД: {e}. Продолжаем без сохранения.")
            db = None
    
    # Загрузка лучшей змейки из прошлой сессии (если нужно)
    initial_brain = None
    continue_session_id = None
    
    # Автоматическая загрузка лучшей змейки из всех сессий (ВСЕГДА, если не указано иначе)
    if not args.continue_session and db:
        try:
            # Ищем ЛУЧШУЮ змейку из всех сессий (не последнюю, а самую умную!)
            all_best_snakes = db.get_best_snakes(limit=1)  # Получаем лучшую змейку из всех сессий
            if all_best_snakes:
                best_session_id, best_gen, best_fitness, _ = all_best_snakes[0]
                continue_session_id = best_session_id
                print(f"🏆 Найдена ЛУЧШАЯ змейка: сессия #{best_session_id}, поколение {best_gen}, fitness {best_fitness:.1f}")
                args.continue_session = continue_session_id
            else:
                # Если нет сохраненных змеек, ищем последнюю сессию
                sessions = db.get_sessions(limit=1)
                if sessions:
                    continue_session_id = sessions[0][0]
                    print(f"ℹ️  Используем последнюю сессию #{continue_session_id} (без сохраненных змеек)")
                    args.continue_session = continue_session_id
        except Exception as e:
            print(f"⚠️  Ошибка поиска лучшей сессии: {e}")
            import traceback
            traceback.print_exc()
    
    # Создание новой сессии только если не продолжаем старую
    if db and not args.continue_session:
        try:
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
            print(f"⚠️  Ошибка создания сессии: {e}")
            session_id = None
    
    if args.continue_session and db:
        try:
            # Используем существующую сессию для продолжения
            session_id = args.continue_session
            best_snakes = db.get_best_snakes(session_id=args.continue_session, limit=1)
            if best_snakes:
                from brain import Brain
                s_id, gen, fitness, weights_bytes = best_snakes[0]
                weights, hidden_weights = db.load_snake_weights(weights_bytes, has_hidden=True)
                if hidden_weights is not None:
                    initial_brain = Brain(weights=weights, hidden_weights=hidden_weights)
                else:
                    # Старый формат - создаем новый мозг
                    initial_brain = None
                print(f"✓ Загружена лучшая змейка из сессии #{s_id}, поколение {gen}, fitness {fitness:.1f}")
                print(f"✓ Продолжаем сессию #{session_id}")
            else:
                # Проверяем, есть ли история поколений в этой сессии
                history = db.get_generation_history(args.continue_session)
                if history:
                    print(f"✓ Продолжаем сессию #{session_id} (найдено {len(history)} поколений в истории)")
                    print(f"ℹ️  В сессии нет сохраненных змеек, начинаем с новой популяции")
                else:
                    print(f"⚠️  Сессия #{args.continue_session} пустая, но продолжаем её")
        except Exception as e:
            print(f"⚠️  Ошибка загрузки прошлой сессии: {e}")
            import traceback
            traceback.print_exc()
    
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
    if session_id:
        if args.continue_session:
            print(f"📂 Продолжение сессии #{session_id}")
        else:
            print(f"📂 Новая сессия #{session_id}")
    if initial_brain:
        print(f"🧠 Загружена змейка из базы данных")
    print("=" * 60)
    print()
    
    # Основной цикл эволюции (бесконечный до победы)
    victory_achieved = False
    gen = 0
    
    while not victory_achieved:
        best_fit, avg_fit = evolution.evolve()
        gen += 1
        
        # Сохранение в БД
        if db and session_id:
            db.save_generation(session_id, evolution.generation, best_fit, avg_fit)
            # Оптимизация: сохраняем лучшую змейку каждое поколение, но только если улучшилась
            # или раз в 5 поколений (для ускорения)
            should_save = (gen % 5 == 0) or (best_fit > getattr(evolution, '_last_saved_fitness', 0))
            if should_save and hasattr(evolution, 'current_best_snake') and evolution.current_best_snake:
                brain = evolution.current_best_snake.brain
                db.save_best_snake(
                    session_id, 
                    evolution.generation, 
                    best_fit,
                    brain.weights,
                    brain.hidden_weights
                )
                evolution._last_saved_fitness = best_fit
        
        # Вывод статистики
        best_length = evolution.current_best_length if hasattr(evolution, 'current_best_length') else 0
        print(f"Поколение {evolution.generation:4d} | "
              f"Лучший: {best_fit:6.1f} | "
              f"Средний: {avg_fit:6.1f} | "
              f"Длина: {best_length}/{evolution.win_condition_length}")
        
        # Проверка победы: если змейка заполнила поле (проверяется в evolution.py)
        if evolution.victory_achieved:
            victory_achieved = True
            print("\n" + "=" * 60)
            print("🎉 ПОБЕДА! ЗМЕЙКА ЗАПОЛНИЛА ВСЁ ПОЛЕ! 🎉")
            print("=" * 60)
            print(f"Поколение победы: {evolution.generation}")
            print(f"Fitness победителя: {best_fit:.1f}")
            print(f"Длина змейки: {best_length} клеток (цель: {evolution.win_condition_length})")
        
        # Визуализация (если нужна)
        if args.visualize:
            result = visualizer.visualize_generation(auto_mode=args.auto)
            if result == "VICTORY":
                victory_achieved = True
                print("\n" + "=" * 60)
                print("🎉 ПОБЕДА! ЗМЕЙКА ЗАПОЛНИЛА ВСЁ ПОЛЕ! 🎉")
                print("=" * 60)
                print(f"Поколение победы: {evolution.generation}")
                print(f"Fitness победителя: {best_fit:.1f}")
            elif not result:
                print("\nВизуализация остановлена пользователем.")
                break
        
        # Сохранение лучшей змейки периодически
        if gen % 50 == 0:
            print(f"✓ Поколение {gen} завершено (эволюция продолжается до победы...)")
        
        # Эволюция продолжается бесконечно до победы
        # Лимит поколений игнорируется - эволюция не останавливается!
    
    # Финальная статистика
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ ЭВОЛЮЦИИ")
    print("=" * 60)
    
    # Финальное сохранение в БД
    if db and session_id:
        # Сохраняем лучшую змейку перед завершением
        if hasattr(evolution, 'current_best_snake') and evolution.current_best_snake:
            db.save_best_snake(
                session_id,
                evolution.generation,
                evolution.best_fitness_in_history,
                evolution.current_best_snake.brain.weights
            )
        # Обновляем статистику сессии
        db.update_session(
            session_id,
            evolution.generation,
            evolution.best_fitness_in_history
        )
        print(f"✓ Финальное сохранение: сессия #{session_id}, поколение {evolution.generation}")
    
    # Получаем лучшую змейку
    best_snake = evolution.get_best_snake()
    
    print(f"Лучший fitness в истории: {evolution.best_fitness_in_history:.1f}")
    
    # Демонстрационная игра для статистики
    if best_snake and evolution.best_fitness_in_history > 0:
        demo_snake = best_snake.clone()
        demo_fitness, demo_length = evolution.environment.play_game(demo_snake, evolution.max_steps)
        print(f"Демо игра fitness: {demo_fitness:.1f}")
        print(f"Длина змейки: {demo_length}")
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

