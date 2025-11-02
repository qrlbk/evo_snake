"""
Скрипт для просмотра истории эволюции из базы данных.
"""

import argparse
from database import EvolutionDB
import sqlite3


def view_sessions(db_path):
    """Показать все сессии."""
    db = EvolutionDB(db_path)
    sessions = db.get_sessions(limit=100)
    
    if not sessions:
        print("Нет сохраненных сессий.")
        return
    
    print("\n" + "=" * 80)
    print("СЕССИИ ЭВОЛЮЦИИ")
    print("=" * 80)
    print(f"{'ID':<5} {'Дата':<20} {'Pop':<5} {'Grid':<6} {'Gens':<6} {'Лучший':<10}")
    print("-" * 80)
    
    for s in sessions:
        session_id, created_at, pop, grid, elite, mut_rate, mut_strength, max_steps, total_gens, best_fit = s
        print(f"{session_id:<5} {created_at[:16]:<20} {pop:<5} {grid}x{grid:<4} {total_gens or 0:<6} {best_fit or 0:<10.1f}")
    
    print("=" * 80)


def view_session_details(db_path, session_id):
    """Показать детали сессии."""
    db = EvolutionDB(db_path)
    
    # Информация о сессии
    conn = db.conn
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM sessions WHERE id = ?
    ''', (session_id,))
    session = cursor.fetchone()
    
    if not session:
        print(f"Сессия #{session_id} не найдена.")
        return
    
    print("\n" + "=" * 80)
    print(f"СЕССИЯ #{session_id}")
    print("=" * 80)
    
    # session = (id, created_at, pop, grid, elite, mut_rate, mut_strength, max_steps, total_gens, best_fit, notes)
    print(f"Дата создания: {session[1]}")
    print(f"Параметры:")
    print(f"  - Популяция: {session[2]}")
    print(f"  - Размер поля: {session[3]}x{session[3]}")
    print(f"  - Элита: {session[4]}")
    print(f"  - Вероятность мутации: {session[5]}")
    print(f"  - Сила мутации: {session[6]}")
    print(f"  - Макс. шагов: {session[7]}")
    print(f"Прогресс: {session[8] or 0} поколений")
    print(f"Лучший fitness: {session[9] or 0:.1f}")
    print("=" * 80)
    
    # История поколений
    history = db.get_generation_history(session_id)
    
    if history:
        print("\nИстория поколений (последние 20):")
        print(f"{'Gen':<6} {'Лучший':<10} {'Средний':<10}")
        print("-" * 30)
        
        for gen, best, avg in history[-20:]:
            print(f"{gen:<6} {best:<10.1f} {avg:<10.1f}")


def view_best_snakes(db_path, session_id=None):
    """Показать лучшие змейки."""
    db = EvolutionDB(db_path)
    best_snakes = db.get_best_snakes(session_id=session_id, limit=20)
    
    if not best_snakes:
        print("Нет сохраненных змеек.")
        return
    
    print("\n" + "=" * 80)
    print("ЛУЧШИЕ ЗМЕЙКИ")
    print("=" * 80)
    
    if session_id:
        print(f"Сессия #{session_id}")
    else:
        print("Все сессии")
    
    print(f"{'Сессия':<8} {'Gen':<6} {'Fitness':<12} {'Размер весов'}")
    print("-" * 80)
    
    for s_id, gen, fitness, weights in best_snakes:
        weight_size = len(weights) if weights else 0
        print(f"{s_id:<8} {gen:<6} {fitness:<12.1f} {weight_size} байт")
    
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Просмотр истории эволюции')
    parser.add_argument('--db', default='evolution.db', help='Путь к базе данных')
    parser.add_argument('--session', type=int, help='ID сессии для детального просмотра')
    parser.add_argument('--best', action='store_true', help='Показать лучшие змейки')
    parser.add_argument('--session-best', type=int, help='ID сессии для лучших змеек')
    
    args = parser.parse_args()
    
    if args.session:
        view_session_details(args.db, args.session)
    elif args.best:
        view_best_snakes(args.db, session_id=args.session_best)
    else:
        view_sessions(args.db)


if __name__ == '__main__':
    main()

