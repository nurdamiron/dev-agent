# Этап сборки
FROM node:18-alpine as build

# Установка рабочей директории
WORKDIR /app

# Копирование файлов package.json и package-lock.json
COPY package*.json ./

# Установка зависимостей
RUN npm ci

# Копирование исходного кода
COPY . .

# Установка переменных окружения для сборки
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Сборка приложения
RUN npm run build

# Этап релиза - используем nginx для раздачи статических файлов
FROM nginx:alpine

# Копирование собранных файлов из этапа сборки
COPY --from=build /app/build /usr/share/nginx/html

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открытие порта
EXPOSE 80

# Команда запуска
CMD ["nginx", "-g", "daemon off;"]