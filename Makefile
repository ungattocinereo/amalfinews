.PHONY: help install start stop restart logs status shell clean test

# Цвета для вывода
GREEN  := \033[0;32m
YELLOW := \033[1;33m
BLUE   := \033[0;34m
NC     := \033[0m

help: ## Показать эту помощь
	@echo "$(BLUE)Amalfi Events Intelligence - Команды управления$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## Установить и запустить (первый раз)
	@chmod +x install.sh
	@./install.sh

start: ## Запустить контейнер
	@echo "$(BLUE)▶ Запуск контейнера...$(NC)"
	@docker-compose up -d
	@sleep 5
	@$(MAKE) status

stop: ## Остановить контейнер
	@echo "$(YELLOW)■ Остановка контейнера...$(NC)"
	@docker-compose stop

restart: ## Перезапустить контейнер
	@echo "$(BLUE)↻ Перезапуск контейнера...$(NC)"
	@docker-compose restart
	@sleep 5
	@$(MAKE) status

logs: ## Показать логи
	@docker-compose logs -f --tail=100

status: ## Показать статус и URL
	@echo "$(GREEN)✓ Статус контейнера:$(NC)"
	@docker-compose ps
	@echo ""
	@PORT=$$(docker-compose port amalfi-events 8000 2>/dev/null | cut -d: -f2); \
	if [ -n "$$PORT" ]; then \
		echo "$(GREEN)🌐 Веб-интерфейс: $(BLUE)http://localhost:$$PORT$(NC)"; \
		echo "$(GREEN)📚 API Docs:      $(BLUE)http://localhost:$$PORT/docs$(NC)"; \
		echo "$(GREEN)📊 Статус:        $(BLUE)http://localhost:$$PORT/status$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Контейнер не запущен$(NC)"; \
	fi

open: ## Открыть веб-интерфейс в браузере
	@PORT=$$(docker-compose port amalfi-events 8000 2>/dev/null | cut -d: -f2); \
	if [ -n "$$PORT" ]; then \
		open "http://localhost:$$PORT" 2>/dev/null || xdg-open "http://localhost:$$PORT" 2>/dev/null; \
	else \
		echo "$(YELLOW)⚠ Контейнер не запущен$(NC)"; \
	fi

shell: ## Зайти в shell контейнера
	@docker-compose exec amalfi-events bash

run: ## Запустить workflow вручную
	@docker-compose exec amalfi-events python scripts/daily_run.py

test-sources: ## Протестировать источники
	@docker-compose exec amalfi-events python scripts/test_sources.py

test-api: ## Протестировать DeepSeek API
	@docker-compose exec amalfi-events python scripts/test_deepseek.py

db-init: ## Инициализировать базу данных
	@docker-compose exec amalfi-events python scripts/setup_database.py

db-backup: ## Создать бэкап базы данных
	@docker-compose exec amalfi-events cp /app/data/events.db /app/data/backups/events_$$(date +%Y%m%d_%H%M%S).db
	@echo "$(GREEN)✓ Бэкап создан$(NC)"

clean: ## Остановить и удалить контейнер
	@echo "$(YELLOW)⚠ Остановка и удаление контейнера...$(NC)"
	@docker-compose down

clean-all: ## Удалить контейнер и данные
	@echo "$(YELLOW)⚠ ВНИМАНИЕ: Будут удалены ВСЕ данные!$(NC)"
	@read -p "Вы уверены? (y/n) " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		rm -rf data/*.db logs/*.log; \
		echo "$(GREEN)✓ Всё удалено$(NC)"; \
	else \
		echo "$(YELLOW)Отменено$(NC)"; \
	fi

build: ## Пересобрать образ
	@echo "$(BLUE)🔨 Сборка образа...$(NC)"
	@docker-compose build --no-cache

rebuild: build start ## Пересобрать и запустить

update: ## Обновить код и перезапустить
	@echo "$(BLUE)↻ Обновление...$(NC)"
	@git pull
	@docker-compose down
	@docker-compose build
	@docker-compose up -d
	@sleep 5
	@$(MAKE) status
