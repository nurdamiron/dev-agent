#!/bin/bash
# start_services.sh

echo "==== Запуск AI-Agent Developer ===="

# Загружаем переменные окружения
set -a
source .env
set +a

# Создаем директории для логов
mkdir -p logs

# Инициализация базы данных (если нужно)
echo "Инициализация базы данных..."
cd api-service
python scripts/init_db.py
cd ..

# Запуск API-сервиса
echo "Запуск API-сервиса..."
cd api-service
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/api-service.log 2>&1 &
cd ..

# Запуск Agent-сервиса
echo "Запуск Agent-сервиса..."
cd agent-service
nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 > ../logs/agent-service.log 2>&1 &
cd ..

# Запуск Git-сервиса
echo "Запуск Git-сервиса..."
cd git-service
nohup uvicorn app.main:app --host 0.0.0.0 --port 8004 > ../logs/git-service.log 2>&1 &
cd ..

# Запуск Frontend (в режиме разработки)
echo "Запуск Frontend..."
cd frontend
nohup npm start > ../logs/frontend.log 2>&1 &
cd ..

echo "Все сервисы запущены. Проверьте логи в директории logs/"
echo "Frontend доступен по адресу: http://localhost:3000"
echo "API-сервис доступен по адресу: http://localhost:8000"
echo "Agent-сервис доступен по адресу: http://localhost:8001"
echo "Git-сервис доступен по адресу: http://localhost:8004"