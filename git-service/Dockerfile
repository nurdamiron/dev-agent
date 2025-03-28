# Базовый образ Python
FROM python:3.10-slim

# Установка рабочей директории
WORKDIR /app

# Копирование файла с зависимостями
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Установка Git
RUN apt-get update && apt-get install -y git && apt-get clean

# Копирование исходного кода
COPY . .

# Создание директории для репозиториев
RUN mkdir -p /tmp/repos

# Переменные среды
ENV PORT=8004
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Открытие порта
EXPOSE 8004

# Команда запуска приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]