#!/usr/bin/env python3
"""
Автоматический запуск эволюционной змейки.
Проверяет зависимости, создает окружение и запускает программу.
"""

import sys
import os
import subprocess
import platform

def check_python_version():
    """Проверка версии Python."""
    if sys.version_info < (3, 7):
        print("❌ Требуется Python 3.7 или выше!")
        print(f"   Текущая версия: {sys.version}")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

def check_and_install_dependencies():
    """Проверка и установка зависимостей."""
    print("\n📦 Проверка зависимостей...")
    
    required_packages = {
        'numpy': 'numpy>=1.21.0',
        'pygame': 'pygame>=2.0.0'
    }
    
    missing_packages = []
    
    for package_name, package_spec in required_packages.items():
        try:
            __import__(package_name)
            print(f"  ✓ {package_name} установлен")
        except ImportError:
            print(f"  ⚠ {package_name} не найден")
            missing_packages.append(package_spec)
    
    if missing_packages:
        print(f"\n📥 Установка недостающих пакетов: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages)
            print("✓ Все зависимости установлены!")
        except subprocess.CalledProcessError:
            print("❌ Ошибка при установке зависимостей!")
            print("   Попробуйте установить вручную: pip install -r requirements.txt")
            sys.exit(1)
    else:
        print("✓ Все зависимости на месте!")

def ensure_database():
    """Создание базы данных если её нет."""
    db_path = 'evolution.db'
    if not os.path.exists(db_path):
        print(f"\n💾 Создание базы данных: {db_path}")
        try:
            from database import EvolutionDB
            db = EvolutionDB(db_path)
            db.close()
            print("✓ База данных создана!")
        except Exception as e:
            print(f"⚠️  Не удалось создать БД: {e}")
            print("   Продолжаем без БД...")
    else:
        print(f"✓ База данных найдена: {db_path}")

def main():
    """Главная функция запуска."""
    print("=" * 60)
    print("🐍 ЭВОЛЮЦИОННАЯ ЗМЕЙКА - АВТОЗАПУСК")
    print("=" * 60)
    
    # Проверка Python
    check_python_version()
    
    # Проверка и установка зависимостей
    check_and_install_dependencies()
    
    # Создание БД
    ensure_database()
    
    print("\n" + "=" * 60)
    print("🚀 ЗАПУСК ПРОГРАММЫ")
    print("=" * 60 + "\n")
    
    # Запуск основной программы с аргументами командной строки
    try:
        # Заменяем sys.argv[0] на 'main.py' чтобы argparse работал правильно
        # Но сохраняем все остальные аргументы
        import main
        # Вызываем main.main() который сам парсит sys.argv
        main.main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Программа остановлена пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Ошибка при запуске: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

