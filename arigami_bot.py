import os
import sys
import subprocess

# Принудительная установка Python 3.11 и зависимостей
def setup_environment():
    # Проверяем версию Python
    if sys.version_info >= (3, 13):
        print("⛔ Несовместимая версия Python! Требуется 3.11")
        print("🔄 Переключение на Python 3.11...")
        
        # Установка Python 3.11
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "python==3.11.8", "virtualenv"
        ])
        
        # Создание нового окружения
        subprocess.check_call([sys.executable, "-m", "virtualenv", ".venv311"])
        
        # Перезапуск в новом окружении
        if os.name == 'nt':
            os.execv(".venv311/Scripts/python.exe", [".venv311/Scripts/python.exe"] + sys.argv)
        else:
            os.execv(".venv311/bin/python", [".venv311/bin/python"] + sys.argv)
    
    # Проверка и установка setuptools
    try:
        import setuptools
        if setuptools.__version__ < "68.0.0":
            raise ImportError
    except ImportError:
        print("🛠 Установка setuptools...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "setuptools==68.0.0"
        ])

if __name__ == "__main__":
    setup_environment()
    
    # Оригинальный код бота
    from aiogram import Bot, Dispatcher, types, F
    # ... остальной код ...
import os
import sys
import subprocess

# Принудительная установка зависимостей перед запуском
def install_dependencies():
    required = {
        "aiogram": "aiogram==3.0.0b7",
        "matplotlib": "matplotlib==3.7.1",
        "numpy": "numpy==1.24.3",
        "Pillow": "Pillow==9.5.0"
    }
    
    try:
        from importlib.metadata import version, PackageNotFoundError
        for pkg, spec in required.items():
            try:
                version(pkg)
            except PackageNotFoundError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", spec])
    except:
        pass  # Если не получилось, продолжим дальше

if __name__ == "__main__":
    install_dependencies()
    
    # Остальной код бота без изменений
    from aiogram import Bot, Dispatcher, types, F
    # ... весь остальной код ...
