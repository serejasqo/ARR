FROM python:3.11-slim-bullseye

WORKDIR /app

# Установка системных зависимостей для numpy и matplotlib
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    libfreetype6-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY arigami_bot.py .

# Запуск бота
CMD ["python", "arigami_bot.py"]
