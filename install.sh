#!/bin/bash
# Простая установка Amalfi Events в один клик

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║   🎯 Amalfi Events Intelligence - Установка           ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода
print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Проверка Docker
print_step "Проверка Docker..."
if ! command -v docker &> /dev/null; then
    print_error "Docker не установлен!"
    echo ""
    echo "Установите Docker Desktop для Mac:"
    echo "https://www.docker.com/products/docker-desktop"
    echo ""
    echo "Или через Homebrew:"
    echo "  brew install --cask docker"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker не запущен!"
    echo ""
    echo "Запустите Docker Desktop из Applications"
    exit 1
fi

print_success "Docker работает"

# Проверка docker-compose
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose не установлен!"
    echo "Установите: brew install docker-compose"
    exit 1
fi

print_success "docker-compose установлен"

# Проверка .env файла
print_step "Проверка конфигурации..."
if [ ! -f ".env" ]; then
    print_warning ".env файл не найден, создаю из шаблона..."
    cp .env.example .env

    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║   📝 НАСТРОЙКА ОБЯЗАТЕЛЬНА!                            ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    echo "Отредактируйте файл .env перед запуском:"
    echo ""
    echo "  nano .env"
    echo ""
    echo "Обязательные параметры:"
    echo "  - TELEGRAM_BOT_TOKEN     (получите у @BotFather)"
    echo "  - TELEGRAM_ADMIN_ID      (получите у @userinfobot)"
    echo "  - WORDPRESS_URL          (адрес вашего сайта)"
    echo "  - WORDPRESS_USERNAME     (логин WordPress)"
    echo "  - WORDPRESS_APP_PASSWORD (пароль приложения WP)"
    echo ""
    read -p "Нажмите Enter после настройки .env..."
fi

# Проверка обязательных параметров
print_step "Проверка обязательных параметров..."
source .env 2>/dev/null || true

missing_vars=()
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_bot_token_here" ]; then
    missing_vars+=("TELEGRAM_BOT_TOKEN")
fi
if [ -z "$TELEGRAM_ADMIN_ID" ] || [ "$TELEGRAM_ADMIN_ID" = "your_telegram_id" ]; then
    missing_vars+=("TELEGRAM_ADMIN_ID")
fi
if [ -z "$WORDPRESS_URL" ] || [ "$WORDPRESS_URL" = "https://your-site.com" ]; then
    missing_vars+=("WORDPRESS_URL")
fi

if [ ${#missing_vars[@]} -gt 0 ]; then
    print_error "Не настроены обязательные параметры:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Отредактируйте .env:"
    echo "  nano .env"
    exit 1
fi

print_success "Конфигурация в порядке"

# Создание директорий
print_step "Создание директорий..."
mkdir -p data logs data/backups
print_success "Директории созданы"

# Остановка старого контейнера (если есть)
print_step "Очистка старых контейнеров..."
docker-compose down 2>/dev/null || true
print_success "Готово"

# Сборка образа
echo ""
print_step "Сборка Docker образа (это может занять 3-5 минут)..."
echo ""
docker-compose build

print_success "Образ собран"

# Запуск контейнера
echo ""
print_step "Запуск контейнера..."
docker-compose up -d

# Ожидание готовности
print_step "Ожидание запуска (10 секунд)..."
sleep 10

# Проверка здоровья
print_step "Проверка работоспособности..."
if docker-compose ps | grep -q "Up"; then
    print_success "Контейнер запущен"
else
    print_error "Контейнер не запустился"
    echo ""
    echo "Логи:"
    docker-compose logs --tail=50
    exit 1
fi

# Получение порта
PORT=$(docker-compose port amalfi-events 8000 2>/dev/null | cut -d: -f2)

if [ -z "$PORT" ]; then
    print_error "Не удалось получить порт"
    exit 1
fi

# Проверка health endpoint
sleep 3
if curl -s -f http://localhost:$PORT/health > /dev/null 2>&1; then
    print_success "Сервис работает"
else
    print_warning "Сервис запускается, подождите..."
    sleep 5
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║   ✅ УСТАНОВКА ЗАВЕРШЕНА!                              ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Веб-интерфейс:  ${GREEN}http://localhost:$PORT${NC}"
echo "📚 API Документация: ${GREEN}http://localhost:$PORT/docs${NC}"
echo "📊 Статус системы: ${GREEN}http://localhost:$PORT/status${NC}"
echo ""
echo "Открыть в браузере:"
echo "  ${BLUE}open http://localhost:$PORT${NC}"
echo ""
echo "Полезные команды:"
echo "  ${BLUE}./docker-logs.sh${NC}         - Просмотр логов"
echo "  ${BLUE}./docker-stop.sh${NC}         - Остановка"
echo "  ${BLUE}docker-compose restart${NC}   - Перезапуск"
echo ""
echo "Система будет автоматически запускать ежедневный сбор в 04:05"
echo ""

# Открыть браузер (опционально)
read -p "Открыть веб-интерфейс в браузере? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[YyДд]$ ]]; then
    open "http://localhost:$PORT" 2>/dev/null || xdg-open "http://localhost:$PORT" 2>/dev/null || echo "Откройте вручную: http://localhost:$PORT"
fi

echo ""
print_success "Готово! 🎉"
