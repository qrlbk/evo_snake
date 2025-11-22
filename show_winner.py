"""
Скрипт для демонстрации победившей змейки.
"""

import sys
from database import EvolutionDB
from evolution import Evolution
from snake import Snake
from brain import Brain
from visualizer import Visualizer

def main():
    print("=" * 70)
    print("🏆 ЗАГРУЗКА ПОБЕДИТЕЛЯ")
    print("=" * 70)
    print()
    
    # Подключение к базе данных
    db = EvolutionDB('evolution.db')
    
    # Получаем лучшую змейку (победителя)
    best_snakes = db.get_best_snakes(limit=1)
    
    if not best_snakes:
        print("❌ Не найдено сохраненных змеек в базе данных")
        return
    
    sess_id, gen, fitness, weights_bytes = best_snakes[0]
    
    print(f"✅ Найдена лучшая змейка:")
    print(f"   Сессия: #{sess_id}")
    print(f"   Поколение: {gen}")
    print(f"   Fitness: {fitness:,.1f}")
    print()
    
    # Загружаем веса мозга
    try:
        loaded_weights = db.load_snake_weights(weights_bytes, has_hidden=True)
        
        if len(loaded_weights) == 3:
            # Новый формат: (weights1, weights2, weights3)
            weights1, weights2, weights3 = loaded_weights
            brain = Brain(hidden1_weights=weights1, weights2=weights2, weights3=weights3)
            print("🧠 Загружен улучшенный мозг (три слоя: 16->32->16->4)")
        elif len(loaded_weights) == 2:
            weights1, weights2_3 = loaded_weights
            if weights2_3 is not None:
                brain = Brain(hidden1_weights=weights1, hidden2_weights=weights2_3)
                print("🧠 Загружен мозг (старый формат, конвертирован)")
            else:
                brain = Brain(weights=weights1, hidden_weights=None)
                print("🧠 Загружен мозг (старый формат, конвертирован)")
        else:
            print("⚠️  Неизвестный формат весов, создаем новый мозг")
            brain = Brain()
    except Exception as e:
        print(f"⚠️  Ошибка загрузки весов: {e}")
        import traceback
        traceback.print_exc()
        brain = Brain()
    
    print()
    print("=" * 70)
    print("🎮 ЗАПУСК ВИЗУАЛИЗАЦИИ ПОБЕДИТЕЛЯ")
    print("=" * 70)
    print()
    print("💡 Управление:")
    print("   ПРОБЕЛ - пауза/продолжить")
    print("   ESC - выход")
    print()
    print("🎬 Демонстрация начинается...")
    print()
    
    # Создаем эволюционную систему для демо
    grid_size = 20
    demo_evolution = Evolution(population_size=1, grid_size=grid_size, max_steps=100000)
    
    # Создаем змейку с загруженным мозгом
    winner_snake = Snake(brain=brain, grid_size=grid_size)
    demo_evolution.population = [winner_snake]
    demo_evolution.generation = gen
    demo_evolution.best_fitness_in_history = fitness
    
    # Создаем визуализатор
    visualizer = Visualizer(demo_evolution)
    
    # Запускаем визуализацию
    try:
        visualizer.visualize_generation(auto_mode=False)
    except KeyboardInterrupt:
        print("\n⚠️  Визуализация прервана пользователем")
    finally:
        visualizer.quit()
        db.close()
        print("✅ Визуализация завершена")

if __name__ == '__main__':
    main()

