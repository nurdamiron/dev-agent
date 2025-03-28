# AI-Agent Developer на MySQL RDS

Платформа для автоматизации задач разработки с использованием Claude 3.7 Sonnet и MySQL RDS.

## Компоненты системы

- **Фронтенд**: React-приложение с чат-интерфейсом
- **API-сервис**: FastAPI сервис для обработки запросов
- **Agent-сервис**: Сервис AI-агента с интеграцией Claude API
- **Git-сервис**: Сервис для работы с Git-репозиториями
- **База данных**: MySQL RDS
- **Кэш**: Redis для очередей и кэширования

## Начало работы

### Предварительные требования

- Python 3.10+
- Node.js 16+
- MySQL RDS (или локальный MySQL сервер)
- Redis (опционально, для продакшн)
- API-ключ Claude от Anthropic
- Токены GitHub/GitLab (для интеграции с репозиториями)

### Локальная разработка

1. Клонировать репозиторий:
```bash
git clone https://github.com/your-username/dev-agent.git
cd dev-agent