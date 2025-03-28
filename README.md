# AI-Agent Developer на Restack

Платформа для автоматизации задач разработки с использованием Claude 3.7 Sonnet.

## Компоненты системы

- **Фронтенд**: React-приложение с чат-интерфейсом
- **API-сервис**: FastAPI сервис для обработки запросов
- **Agent-сервис**: Сервис AI-агента с интеграцией Claude API
- **Git-сервис**: Сервис для работы с Git-репозиториями

## Начало работы

### Локальная разработка

```bash
# Клонирование репозитория
git clone https://github.com/your-username/dev-agent.git
cd dev-agent

# Запуск с Docker Compose
cd infrastructure
docker-compose up -d
```

### Деплой на Restack

1. Создайте проект в Restack
2. Настройте переменные среды в GitHub Secrets
3. Запустите workflow деплоя

## Настройка

Смотрите документацию в каждом сервисе для подробной информации о настройке.
