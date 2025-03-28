# AI-Agent Developer Documentation

## Обзор системы

AI-Agent Developer - это платформа для автоматизации задач разработки с использованием Claude 3.7 Sonnet. Система обеспечивает интеллектуальную помощь разработчикам через чат-интерфейс, анализ кода, генерацию кода и интеграцию с Git-репозиториями.

### Архитектура системы

Система построена на основе микросервисной архитектуры и состоит из следующих компонентов:

1. **Frontend** - React-приложение с чат-интерфейсом для взаимодействия с пользователем
2. **API Service** - FastAPI сервис для обработки запросов и управления состоянием
3. **Agent Service** - AI-агент с интеграцией Claude API для выполнения задач разработки
4. **Git Service** - Сервис для работы с Git-репозиториями

![Архитектура системы](https://mermaid.ink/img/pako:eNqNkk9PhDAQxb_KZGMizAZdYPHgxURjYmK8rAcP0HbYNoG2pH-M6-53d4CNoF68tOn0vd_MvJTRWuaIErrV5p4JXllvWvGOHFbWgYY9M1dWX4kIGBYo4Hn5LLy1olAajUUQkDPSa-2wQKXE2bixwAhapwX3Fhsv8m_I0pTXjjvxwYI3yEA0-QlZMDnA0Qp7K1Z_KE0SgtcLlhVYH3qOTtcbVppcNH6kzHKu33gwX4TLllkZPD6G2UvZjmkwzgb1YNdoKzgdpS3GdUYUKvyNTIk5MBsxpMmkNwOKFWBuqYZKjzO6Y_KKexb0OXRoM2FDtDuqpQFOWexrEefU0UayrUE0iG4d4xC92TgixWc2V7yQqxrZz-pJe7CJNL5TsWBNdEpiJzqI3hWNr0iyjdx0-Ob_wT-zz8hfwdnxF0g7Gj8?type=png)

### Основные функциональности

- **Анализ кода и архитектуры** - анализ кода, выявление проблем и предложение улучшений
- **Генерация кода** - создание нового кода на основе текстового описания
- **Исправление ошибок** - отладка и исправление проблем в коде
- **Операции с Git** - управление репозиториями, коммитами, ветками и PR
- **Контекстуальная помощь** - ответы на вопросы с учетом контекста проекта

## Руководство по установке

### Требования

- Docker и Docker Compose
- GitHub/GitLab аккаунт для интеграции с репозиториями
- API ключ Claude (через Anthropic)

### Локальная установка

1. Клонировать репозиторий:
   ```bash
   git clone https://github.com/your-username/dev-agent.git
   cd dev-agent
   ```

2. Создать файл `.env` в корневой директории:
   ```
   CLAUDE_API_KEY=your_claude_api_key
   GITHUB_TOKEN=your_github_token
   GITLAB_TOKEN=your_gitlab_token
   ```

3. Запустить с использованием Docker Compose:
   ```bash
   cd infrastructure
   docker-compose up -d
   ```

4. Открыть веб-интерфейс в браузере:
   ```
   http://localhost:3000
   ```

### Деплой на Restack

1. Форкнуть репозиторий на GitHub
2. Зарегистрироваться на [Restack](https://restack.io)
3. Создать новый проект, подключив репозиторий GitHub
4. Настроить следующие секреты в GitHub Actions:
   - `RESTACK_USERNAME`
   - `RESTACK_PASSWORD`
   - `RESTACK_TOKEN`
   - `RESTACK_ORG`
   - `CLAUDE_API_KEY`
   - `GITHUB_TOKEN`
   - `GITLAB_TOKEN`
   - `JWT_SECRET`
   - `DATABASE_URL`
5. Запустить GitHub Actions workflow для деплоя

## Руководство пользователя

### Начало работы

1. Войдите в систему используя свои учетные данные
2. Создайте новый проект или выберите существующий
3. Подключите Git-репозиторий к проекту для контекста кода

### Чат с AI-агентом

- Взаимодействуйте с AI-агентом через чат-интерфейс
- Задавайте вопросы о коде, архитектуре и проблемах
- Запрашивайте генерацию новых компонентов
- Поручайте исправление ошибок и рефакторинг кода

### Примеры запросов

#### Анализ кода
```
Проанализируй модуль authentication.py и предложи улучшения безопасности
```

#### Генерация кода
```
Создай REST API endpoint для обработки задачи регистрации пользователя с валидацией полей
```

#### Исправление ошибок
```
Мой код выдаёт ошибку TypeError: cannot convert 'NoneType' object to str implicitly. Вот функция где это происходит...
```

#### Работа с Git
```
Создай новую ветку feature/user-settings, внеси изменения для добавления страницы настроек пользователя и создай pull request
```

## API Документация

### API Service

- **FastAPI** - основной фреймворк для API
- **Модули**:
  - auth.py - аутентификация и авторизация
  - projects.py - управление проектами
  - messages.py - обработка сообщений
  - tasks.py - управление задачами
- **База данных**: PostgreSQL для хранения пользователей, проектов, задач и сообщений

### Agent Service

- **Claude API** - интеграция с Claude 3.7 Sonnet
- **Модули**:
  - agent.py - основная логика AI-агента
  - code_analyzer.py - анализ кода
  - code_generator.py - генерация кода
  - task_executor.py - асинхронное выполнение задач
- **Redis**: для очередей задач и кэширования

### Git Service

- **GitPython** - взаимодействие с Git-репозиториями
- **Модули**:
  - github.py - интеграция с GitHub API
  - gitlab.py - интеграция с GitLab API
  - repo_manager.py - управление локальными репозиториями

## Модель данных

### Пользователи (users)

| Поле        | Тип      | Описание                     |
|-------------|----------|-----------------------------|
| id          | UUID     | Уникальный идентификатор     |
| email       | String   | Email пользователя           |
| username    | String   | Имя пользователя             |
| hashed_password | String | Хешированный пароль         |
| is_active   | Boolean  | Активен ли пользователь      |
| is_superuser| Boolean  | Является ли администратором  |
| created_at  | DateTime | Дата создания                |
| updated_at  | DateTime | Дата обновления              |

### Проекты (projects)

| Поле          | Тип      | Описание                     |
|---------------|----------|-----------------------------|
| id            | UUID     | Уникальный идентификатор     |
| name          | String   | Название проекта             |
| description   | Text     | Описание проекта             |
| repository_url| String   | URL Git-репозитория          |
| user_id       | UUID     | ID владельца проекта         |
| created_at    | DateTime | Дата создания                |
| updated_at    | DateTime | Дата обновления              |

### Задачи (tasks)

| Поле          | Тип      | Описание                        |
|---------------|----------|--------------------------------|
| id            | UUID     | Уникальный идентификатор        |
| description   | Text     | Описание задачи                 |
| status        | String   | Статус задачи                   |
| progress      | Integer  | Прогресс выполнения (0-100%)    |
| result        | JSON     | Результат выполнения            |
| error         | Text     | Ошибка (если есть)              |
| project_id    | UUID     | ID проекта                      |
| user_id       | UUID     | ID пользователя                 |
| created_at    | DateTime | Дата создания                   |
| started_at    | DateTime | Дата начала выполнения          |
| completed_at  | DateTime | Дата завершения                 |

### Сообщения (messages)

| Поле          | Тип      | Описание                     |
|---------------|----------|-----------------------------|
| id            | UUID     | Уникальный идентификатор     |
| content       | Text     | Содержимое сообщения         |
| role          | String   | Роль (user, assistant, system) |
| meta          | JSON     | Метаданные сообщения         |
| task_id       | UUID     | ID связанной задачи          |
| user_id       | UUID     | ID пользователя              |
| created_at    | DateTime | Дата создания                |

## Технический стек

### Frontend
- React.js
- Tailwind CSS
- Axios для HTTP-запросов
- React Router для маршрутизации
- React Markdown для отображения Markdown
- React Syntax Highlighter для подсветки кода

### Backend
- Python 3.10+
- FastAPI для REST API
- SQLAlchemy для ORM
- Pydantic для валидации данных
- Anthropic SDK для Claude API
- Redis для очередей и кэширования
- PostgreSQL для хранения данных

### DevOps
- Docker и Docker Compose для контейнеризации
- GitHub Actions для CI/CD
- Restack для хостинга

## Расширения и интеграции

### Интеграции с IDE
- VS Code Extension (планируется)
- JetBrains Plugin (планируется)

### Интеграции с инструментами разработки
- Jira
- GitHub Issues
- GitLab Issues
- Slack

## Дорожная карта разработки

### Версия 1.0 (MVP)
- [x] Базовый чат-интерфейс с Claude API
- [x] Аутентификация и управление пользователями
- [x] Управление проектами и контекстом
- [x] Интеграция с GitHub/GitLab
- [x] Анализ и генерация кода

### Версия 1.1
- [ ] Улучшенный анализ зависимостей
- [ ] Генерация тестов для кода
- [ ] Интеграция с CI/CD
- [ ] Управление несколькими репозиториями

### Версия 1.2
- [ ] VS Code Extension
- [ ] Анализ производительности кода
- [ ] Рефакторинг существующего кода
- [ ] Интеграция с Jira/Trello

### Версия 2.0
- [ ] Командные функции и совместная работа
- [ ] Обучение на корпоративных данных
- [ ] Автоматизированные сценарии разработки
- [ ] Генерация документации

## Часто задаваемые вопросы

### Общие вопросы

**Вопрос**: Какая модель AI используется в системе?  
**Ответ**: Система использует Claude 3.7 Sonnet от Anthropic для анализа и генерации кода.

**Вопрос**: Сохраняет ли система мой код?  
**Ответ**: Система временно кэширует код для анализа и генерации, но не хранит его постоянно, если это не требуется для выполнения конкретной задачи.

**Вопрос**: Могу ли я использовать систему с приватными репозиториями?  
**Ответ**: Да, система поддерживает работу с приватными репозиториями через токены доступа GitHub/GitLab.

### Технические вопросы

**Вопрос**: Какие языки программирования поддерживаются?  
**Ответ**: Система поддерживает большинство популярных языков программирования, включая Python, JavaScript, TypeScript, Java, C#, Go, Ruby, PHP и другие.

**Вопрос**: Как система обрабатывает большие репозитории?  
**Ответ**: Система использует интеллектуальное индексирование и извлечение релевантных файлов для анализа, чтобы эффективно работать с большими репозиториями.

**Вопрос**: Могу ли я использовать систему без подключения Git-репозитория?  
**Ответ**: Да, вы можете использовать систему для генерации и анализа отдельных фрагментов кода без привязки к репозиторию.

## Контакты и поддержка

- Техническая поддержка: support@devagent.io
- Документация: docs.devagent.io
- GitHub: github.com/devagent-ai/dev-agent

## Лицензия

AI-Agent Developer распространяется под лицензией MIT. См. файл LICENSE для получения подробной информации. Service

#### Аутентификация

```
POST /auth/login
POST /auth/register
GET /auth/me
```

#### Управление проектами

```
GET /projects
POST /projects
GET /projects/{id}
PUT /projects/{id}
DELETE /projects/{id}
```

#### Управление сообщениями

```
POST /messages
GET /messages/{id}
```

#### Управление задачами

```
GET /tasks
GET /tasks/{id}
PATCH /tasks/{id}/status
```

### Agent Service

```
POST /process
GET /tasks/{id}
GET /tasks
```

### Git Service

```
POST /repos/clone
GET /repos/{id}
GET /repos/{id}/files
POST /repos/{id}/commit
```

## Архитектура компонентов

### Frontend

- **React** - основной UI фреймворк
- **Компоненты**:
  - ChatInterface - интерфейс чата с агентом
  - CodeEditor - редактор кода с подсветкой синтаксиса
  - ProjectSelector - выбор активного проекта
  - TaskHistory - история задач

### API