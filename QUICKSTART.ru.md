# 🚀 Быстрый старт (5 минут)

## Установка одной командой

```bash
chmod +x install.sh && ./install.sh
```

Вот и всё! Скрипт сделает всё автоматически. ✨

---

## Пошаговая инструкция

### 1️⃣ Установите Docker Desktop

**Скачайте и установите:**
https://www.docker.com/products/docker-desktop

**Или через Homebrew:**
```bash
brew install --cask docker
```

Запустите Docker Desktop из Applications и дождитесь запуска.

---

### 2️⃣ Клонируйте репозиторий

```bash
cd ~/Documents
git clone <URL_РЕПОЗИТОРИЯ> amalfinews
cd amalfinews
```

---

### 3️⃣ Настройте API ключи

```bash
# Создайте .env файл
cp .env.example .env

# Откройте для редактирования
nano .env
```

**Заполните 3 обязательных параметра:**

#### 🤖 Telegram Bot Token
```bash
1. Откройте Telegram
2. Найдите @BotFather
3. Отправьте: /newbot
4. Следуйте инструкциям
5. Скопируйте токен в .env
```

#### 👤 Ваш Telegram ID
```bash
1. Найдите @userinfobot
2. Отправьте: /start
3. Скопируйте ваш ID в .env
```

#### 🌐 WordPress
```bash
1. Войдите в админку WordPress
2. Пользователи → Ваш профиль
3. Прокрутите до "Application Passwords"
4. Создайте новый пароль
5. Скопируйте в .env
```

**Сохраните файл:** `Ctrl+X`, затем `Y`, затем `Enter`

---

### 4️⃣ Запустите контейнер

```bash
chmod +x install.sh
./install.sh
```

Скрипт автоматически:
- ✅ Проверит Docker
- ✅ Создаст директории
- ✅ Соберёт образ
- ✅ Запустит контейнер
- ✅ Откроет веб-интерфейс

---

## 🎉 Готово!

Система запущена на случайном порту, например: **http://localhost:32768**

### Веб-интерфейс

Откройте в браузере URL, который показал скрипт установки.

**Доступные страницы:**
- 📊 **/** - Главная панель управления
- 📈 **/status** - Статус системы в реальном времени
- 📋 **/stats** - Статистика за день
- 🌐 **/sources/health** - Проверка 11 источников
- 📝 **/events/pending** - События на модерации
- 📚 **/docs** - API документация

---

## 📱 Управление

### Посмотреть логи
```bash
./docker-logs.sh
```

### Остановить
```bash
./docker-stop.sh
```

### Перезапустить
```bash
docker-compose restart
```

### Зайти в контейнер
```bash
docker-compose exec amalfi-events bash
```

### Запустить вручную
```bash
docker-compose exec amalfi-events python scripts/daily_run.py
```

---

## 🔍 Проверка работы

### Через веб-интерфейс
```bash
# Откройте в браузере
open http://localhost:$(docker-compose port amalfi-events 8000 | cut -d: -f2)
```

### Через API
```bash
# Получите порт
PORT=$(docker-compose port amalfi-events 8000 | cut -d: -f2)

# Проверьте статус
curl http://localhost:$PORT/status | jq

# Проверьте источники
curl http://localhost:$PORT/sources/health | jq

# Посмотрите статистику
curl http://localhost:$PORT/stats | jq
```

---

## ⏰ Автоматический запуск

Система автоматически запускается каждый день в **04:05** и:
1. Проверяет 11 итальянских сайтов
2. Собирает события
3. Фильтрует через DeepSeek AI
4. Переводит на английский
5. Отправляет вам в Telegram для модерации

---

## 🆘 Проблемы?

### Docker не запускается
```bash
# Перезапустите Docker Desktop
killall Docker
open /Applications/Docker.app
```

### Контейнер падает
```bash
# Посмотрите логи
docker-compose logs

# Пересоберите образ
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Не могу найти порт
```bash
# Узнайте порт
docker-compose port amalfi-events 8000

# Или посмотрите все контейнеры
docker-compose ps
```

### База данных не создается
```bash
# Создайте вручную
docker-compose exec amalfi-events python scripts/setup_database.py
```

---

## 📖 Полная документация

- **[README.md](README.md)** - Полное описание системы
- **[docs/DOCKER.md](docs/DOCKER.md)** - Docker документация
- **[docs/API.md](docs/API.md)** - DeepSeek API
- **[docs/SOURCES.md](docs/SOURCES.md)** - Настройка источников

---

## 💡 Полезные команды

```bash
# Узнать порт и открыть браузер
open http://localhost:$(docker-compose port amalfi-events 8000 | cut -d: -f2)

# Посмотреть логи в реальном времени
docker-compose logs -f --tail=100

# Проверить статус контейнера
docker-compose ps

# Перезапустить
docker-compose restart

# Остановить и удалить всё
docker-compose down

# Очистить всё включая volumes
docker-compose down -v

# Зайти в shell контейнера
docker-compose exec amalfi-events bash

# Посмотреть базу данных
docker-compose exec amalfi-events sqlite3 /app/data/events.db "SELECT COUNT(*) FROM raw_events;"

# Запустить тесты
docker-compose exec amalfi-events python scripts/test_sources.py
docker-compose exec amalfi-events python scripts/test_deepseek.py
```

---

## ✅ Что дальше?

1. **Откройте веб-интерфейс** - там всё понятно
2. **Подождите первого запуска** - в 04:05 утра
3. **Проверьте Telegram** - бот пришлёт события
4. **Одобрите события** - через кнопки в Telegram
5. **Готово!** - события опубликуются на WordPress

---

**Вопросы?** Проверьте [полную документацию](docs/DOCKER.md) или логи: `./docker-logs.sh`

🎉 **Приятного использования!**
