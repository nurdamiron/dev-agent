#!/bin/bash
# run.sh - универсальный скрипт запуска проекта DevAgent

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для проверки зависимостей
check_dependencies() {
  echo -e "${BLUE}Проверка зависимостей...${NC}"
  
  # Проверка Python
  if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 не установлен. Установите Python 3.8 или выше.${NC}"
    exit 1
  fi
  
  # Проверка Node.js
  if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js не установлен. Установите Node.js 16 или выше.${NC}"
    exit 1
  fi
  
  # Проверка Docker (для режима docker)
  if [[ "$1" == "docker" && ! $(command -v docker) ]]; then
    echo -e "${RED}Docker не установлен. Установите Docker для запуска в контейнерах.${NC}"
    exit 1
  fi
  
  # Проверка Docker Compose (для режима docker)
  if [[ "$1" == "docker" && ! $(command -v docker-compose) ]]; then
    echo -e "${RED}Docker Compose не установлен. Установите Docker Compose для запуска в контейнерах.${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}Зависимости проверены.${NC}"
}

# Функция для установки зависимостей Python
install_python_dependencies() {
  echo -e "${BLUE}Установка Python зависимостей...${NC}"
  
  # Используем --break-system-packages для macOS или других систем с внешним управлением пакетами
  if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}Обнаружена macOS. Используем --break-system-packages.${NC}"
    pip_cmd="pip3 install --break-system-packages"
  else
    pip_cmd="pip3 install"
  fi
  
  # Устанавливаем зависимости
  $pip_cmd -r requirements.txt
  
  if [ $? -ne 0 ]; then
    echo -e "${RED}Ошибка при установке зависимостей Python.${NC}"
    echo -e "${YELLOW}Попробуйте использовать виртуальное окружение:${NC}"
    echo "python3 -m venv venv"
    echo "source venv/bin/activate"
    echo "pip install -r requirements.txt"
    exit 1
  fi
  
  echo -e "${GREEN}Python зависимости установлены.${NC}"
}

# Функция для установки зависимостей Node.js
install_node_dependencies() {
  echo -e "${BLUE}Установка Node.js зависимостей...${NC}"
  
  cd frontend
  npm install
  
  if [ $? -ne 0 ]; then
    echo -e "${RED}Ошибка при установке зависимостей Node.js.${NC}"
    exit 1
  fi
  
  cd ..
  echo -e "${GREEN}Node.js зависимости установлены.${NC}"
}

# Функция для настройки .env файлов
setup_env_files() {
  echo -e "${BLUE}Настройка .env файлов...${NC}"
  
  # Проверяем и копируем основной .env файл
  if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
      cp .env.example .env
      echo -e "${YELLOW}Файл .env создан из .env.example. Отредактируйте его с вашими настройками.${NC}"
    else
      echo -e "${RED}Файл .env.example не найден. Создайте .env файл вручную.${NC}"
    fi
  fi
  
  # Копируем .env файл в директории сервисов
  services=("api-service" "agent-service" "git-service" "frontend")
  for service in "${services[@]}"; do
    if [ ! -f "$service/.env" ]; then
      cp .env "$service/.env"
      echo -e "${GREEN}Файл .env скопирован в $service/.${NC}"
    fi
  done
  
  echo -e "${GREEN}Настройка .env файлов завершена.${NC}"
}

# Функция для инициализации базы данных
init_database() {
  echo -e "${BLUE}Инициализация базы данных...${NC}"
  
  cd api-service
  python3 scripts/init_db.py
  
  if [ $? -ne 0 ]; then
    echo -e "${RED}Ошибка при инициализации базы данных.${NC}"
    echo -e "${YELLOW}Убедитесь, что MySQL сервер запущен и настройки в .env корректны.${NC}"
    exit 1
  fi
  
  cd ..
  echo -e "${GREEN}База данных инициализирована.${NC}"
}

# Функция для создания админа (опционально)
create_admin() {
  echo -e "${BLUE}Создание административного пользователя...${NC}"
  
  read -p "Создать административного пользователя? (y/n): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Введите имя пользователя: " admin_username
    read -p "Введите email: " admin_email
    read -s -p "Введите пароль: " admin_password
    echo
    
    cd api-service
    python3 scripts/create_admin.py "$admin_username" "$admin_email" "$admin_password"
    
    if [ $? -ne 0 ]; then
      echo -e "${RED}Ошибка при создании администратора.${NC}"
    else
      echo -e "${GREEN}Администратор создан успешно.${NC}"
    fi
    
    cd ..
  else
    echo -e "${YELLOW}Создание администратора пропущено.${NC}"
  fi
}

# Функция для запуска сервисов в режиме разработки
run_dev_services() {
  echo -e "${BLUE}Запуск сервисов в режиме разработки...${NC}"
  
  # Создаем директорию для логов
  mkdir -p logs
  
  # Запуск API-сервиса
  echo -e "${GREEN}Запуск API-сервиса...${NC}"
  cd api-service
  nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/api-service.log 2>&1 &
  API_PID=$!
  echo $API_PID > ../logs/api-service.pid
  cd ..
  
  # Запуск Agent-сервиса
  echo -e "${GREEN}Запуск Agent-сервиса...${NC}"
  cd agent-service
  nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > ../logs/agent-service.log 2>&1 &
  AGENT_PID=$!
  echo $AGENT_PID > ../logs/agent-service.pid
  cd ..
  
  # Запуск Git-сервиса
  echo -e "${GREEN}Запуск Git-сервиса...${NC}"
  cd git-service
  nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload > ../logs/git-service.log 2>&1 &
  GIT_PID=$!
  echo $GIT_PID > ../logs/git-service.pid
  cd ..
  
  # Запуск Frontend
  echo -e "${GREEN}Запуск Frontend...${NC}"
  cd frontend
  nohup npm start > ../logs/frontend.log 2>&1 &
  FRONTEND_PID=$!
  echo $FRONTEND_PID > ../logs/frontend.pid
  cd ..
  
  echo -e "${GREEN}Все сервисы запущены в режиме разработки.${NC}"
  echo -e "${BLUE}API: ${NC}http://localhost:8000"
  echo -e "${BLUE}Agent: ${NC}http://localhost:8001"
  echo -e "${BLUE}Git: ${NC}http://localhost:8004"
  echo -e "${BLUE}Frontend: ${NC}http://localhost:3000"
  echo -e "${YELLOW}Логи доступны в директории logs/${NC}"
  echo -e "${YELLOW}Для остановки сервисов выполните: ./run.sh stop${NC}"
}

# Функция для запуска сервисов через Docker
run_docker_services() {
  echo -e "${BLUE}Запуск сервисов через Docker...${NC}"
  
  cd infrastructure
  docker-compose up -d
  
  if [ $? -ne 0 ]; then
    echo -e "${RED}Ошибка при запуске контейнеров Docker.${NC}"
    exit 1
  fi
  
  cd ..
  echo -e "${GREEN}Сервисы запущены в Docker контейнерах.${NC}"
  echo -e "${BLUE}API: ${NC}http://localhost:8000"
  echo -e "${BLUE}Agent: ${NC}http://localhost:8001"
  echo -e "${BLUE}Git: ${NC}http://localhost:8004"
  echo -e "${BLUE}Frontend: ${NC}http://localhost:3000"
  echo -e "${YELLOW}Для просмотра логов: docker-compose logs -f${NC}"
  echo -e "${YELLOW}Для остановки сервисов: ./run.sh docker-stop${NC}"
}

# Функция для остановки сервисов в режиме разработки
stop_dev_services() {
  echo -e "${BLUE}Остановка сервисов...${NC}"
  
  # Функция для остановки процесса по PID-файлу
  stop_process() {
    if [ -f "logs/$1.pid" ]; then
      PID=$(cat "logs/$1.pid")
      if ps -p $PID > /dev/null; then
        echo -e "${YELLOW}Остановка $1 (PID: $PID)...${NC}"
        kill $PID
        rm "logs/$1.pid"
      else
        echo -e "${YELLOW}Процесс $1 (PID: $PID) не найден.${NC}"
        rm "logs/$1.pid"
      fi
    else
      echo -e "${YELLOW}PID-файл для $1 не найден.${NC}"
    fi
  }
  
  # Останавливаем все сервисы
  stop_process "api-service"
  stop_process "agent-service"
  stop_process "git-service"
  stop_process "frontend"
  
  echo -e "${GREEN}Все сервисы остановлены.${NC}"
}

# Функция для остановки сервисов в Docker
stop_docker_services() {
  echo -e "${BLUE}Остановка Docker сервисов...${NC}"
  
  cd infrastructure
  docker-compose down
  
  if [ $? -ne 0 ]; then
    echo -e "${RED}Ошибка при остановке контейнеров Docker.${NC}"
    exit 1
  fi
  
  cd ..
  echo -e "${GREEN}Docker сервисы остановлены.${NC}"
}

# Функция для проверки состояния сервисов
check_services_status() {
  echo -e "${BLUE}Проверка состояния сервисов...${NC}"
  
  # Проверка сервисов запущенных в режиме разработки
  echo -e "${YELLOW}Процессы в режиме разработки:${NC}"
  for service in "api-service" "agent-service" "git-service" "frontend"; do
    if [ -f "logs/$service.pid" ]; then
      PID=$(cat "logs/$service.pid")
      if ps -p $PID > /dev/null; then
        echo -e "${GREEN}$service запущен (PID: $PID)${NC}"
      else
        echo -e "${RED}$service не запущен (PID: $PID - процесс не существует)${NC}"
      fi
    else
      echo -e "${RED}$service не запущен (PID-файл не найден)${NC}"
    fi
  done
  
  # Проверка Docker контейнеров
  echo -e "\n${YELLOW}Docker контейнеры:${NC}"
  if command -v docker &> /dev/null; then
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E 'api-service|agent-service|git-service|frontend'
  else
    echo -e "${RED}Docker не установлен${NC}"
  fi
  
  # Проверка доступности API
  echo -e "\n${YELLOW}Проверка доступности API:${NC}"
  if command -v curl &> /dev/null; then
    for port in 8000 8001 8004; do
      response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health 2>/dev/null)
      if [ "$response" == "200" ]; then
        echo -e "${GREEN}API на порту $port доступен (HTTP 200)${NC}"
      else
        echo -e "${RED}API на порту $port недоступен (HTTP $response)${NC}"
      fi
    done
  else
    echo -e "${RED}curl не установлен, невозможно проверить доступность API${NC}"
  fi
}

# Главная функция
main() {
  echo -e "${BLUE}======== DevAgent ========${NC}"
  
  # Обработка команд
  case "$1" in
    install)
      check_dependencies
      setup_env_files
      install_python_dependencies
      install_node_dependencies
      init_database
      create_admin
      echo -e "${GREEN}Установка завершена.${NC}"
      ;;
    start|run)
      check_dependencies "dev"
      run_dev_services
      ;;
    docker)
      check_dependencies "docker"
      run_docker_services
      ;;
    stop)
      stop_dev_services
      ;;
    docker-stop)
      stop_docker_services
      ;;
    status)
      check_services_status
      ;;
    init-db)
      init_database
      ;;
    help|*)
      echo -e "${YELLOW}Использование:${NC}"
      echo -e "${GREEN}./run.sh install${NC} - Установка зависимостей и инициализация проекта"
      echo -e "${GREEN}./run.sh start${NC} - Запуск всех сервисов в режиме разработки"
      echo -e "${GREEN}./run.sh docker${NC} - Запуск всех сервисов через Docker"
      echo -e "${GREEN}./run.sh stop${NC} - Остановка сервисов запущенных в режиме разработки"
      echo -e "${GREEN}./run.sh docker-stop${NC} - Остановка Docker контейнеров"
      echo -e "${GREEN}./run.sh status${NC} - Проверка статуса сервисов"
      echo -e "${GREEN}./run.sh init-db${NC} - Инициализация базы данных"
      echo -e "${GREEN}./run.sh help${NC} - Показать эту справку"
      ;;
  esac
}

# Запуск главной функции
main "$@"