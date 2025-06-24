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
