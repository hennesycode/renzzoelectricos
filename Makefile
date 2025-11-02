# ============================================================================
# Makefile para Renzzo Eléctricos - Comandos útiles de Docker
# ============================================================================

.PHONY: help build up down restart logs shell migrate collectstatic createsuperuser clean backup restore

# Variables
COMPOSE_FILE = docker-compose.yml
SERVICE_WEB = web
SERVICE_DB = db

# Colores para output
BLUE = \033[0;34m
GREEN = \033[0;32m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Mostrar esta ayuda
	@echo ""
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║     🔌 RENZZO ELÉCTRICOS - Comandos Docker                ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

build: ## Construir las imágenes Docker
	@echo "$(BLUE)🔨 Construyendo imágenes...$(NC)"
	docker-compose -f $(COMPOSE_FILE) build --no-cache

up: ## Iniciar todos los servicios
	@echo "$(BLUE)🚀 Iniciando servicios...$(NC)"
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ Servicios iniciados$(NC)"
	@echo "$(BLUE)📱 Aplicación disponible en: http://localhost$(NC)"

down: ## Detener todos los servicios
	@echo "$(BLUE)🛑 Deteniendo servicios...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down
	@echo "$(GREEN)✅ Servicios detenidos$(NC)"

restart: ## Reiniciar todos los servicios
	@echo "$(BLUE)🔄 Reiniciando servicios...$(NC)"
	docker-compose -f $(COMPOSE_FILE) restart
	@echo "$(GREEN)✅ Servicios reiniciados$(NC)"

logs: ## Ver logs de todos los servicios
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-web: ## Ver logs solo de la aplicación web
	docker-compose -f $(COMPOSE_FILE) logs -f $(SERVICE_WEB)

logs-db: ## Ver logs solo de la base de datos
	docker-compose -f $(COMPOSE_FILE) logs -f $(SERVICE_DB)

shell: ## Abrir shell en el contenedor web
	@echo "$(BLUE)🐚 Abriendo shell en contenedor web...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec $(SERVICE_WEB) /bin/bash

shell-db: ## Abrir shell MySQL en el contenedor de base de datos
	@echo "$(BLUE)🐚 Abriendo shell MySQL...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec $(SERVICE_DB) mysql -u root -p

django-shell: ## Abrir Django shell
	@echo "$(BLUE)🐍 Abriendo Django shell...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec $(SERVICE_WEB) python manage.py shell

migrate: ## Ejecutar migraciones de Django
	@echo "$(BLUE)🔄 Ejecutando migraciones...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec $(SERVICE_WEB) python manage.py migrate
	@echo "$(GREEN)✅ Migraciones completadas$(NC)"

makemigrations: ## Crear nuevas migraciones
	@echo "$(BLUE)📝 Creando migraciones...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec $(SERVICE_WEB) python manage.py makemigrations
	@echo "$(GREEN)✅ Migraciones creadas$(NC)"

collectstatic: ## Recolectar archivos estáticos
	@echo "$(BLUE)📦 Recolectando archivos estáticos...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec $(SERVICE_WEB) python manage.py collectstatic --noinput
	@echo "$(GREEN)✅ Archivos estáticos recolectados$(NC)"

createsuperuser: ## Crear un superusuario
	@echo "$(BLUE)👤 Creando superusuario...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec $(SERVICE_WEB) python manage.py createsuperuser

clean: ## Limpiar contenedores, volúmenes e imágenes
	@echo "$(RED)⚠️  ADVERTENCIA: Esto eliminará todos los contenedores, volúmenes e imágenes$(NC)"
	@read -p "¿Estás seguro? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)🧹 Limpiando...$(NC)"; \
		docker-compose -f $(COMPOSE_FILE) down -v; \
		docker system prune -af; \
		echo "$(GREEN)✅ Limpieza completada$(NC)"; \
	fi

backup-db: ## Hacer backup de la base de datos
	@echo "$(BLUE)💾 Creando backup de la base de datos...$(NC)"
	@mkdir -p backups/mysql
	@docker-compose -f $(COMPOSE_FILE) exec -T $(SERVICE_DB) mysqldump -u root -p$$(grep DATABASE_ROOT_PASSWORD .env | cut -d '=' -f2) $$(grep DATABASE_NAME .env | cut -d '=' -f2) > backups/mysql/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Backup creado en backups/mysql/$(NC)"

restore-db: ## Restaurar base de datos desde backup (usage: make restore-db FILE=backup.sql)
	@echo "$(BLUE)📥 Restaurando base de datos desde $(FILE)...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) exec -T $(SERVICE_DB) mysql -u root -p$$(grep DATABASE_ROOT_PASSWORD .env | cut -d '=' -f2) $$(grep DATABASE_NAME .env | cut -d '=' -f2) < $(FILE)
	@echo "$(GREEN)✅ Base de datos restaurada$(NC)"

ps: ## Ver estado de los contenedores
	@echo "$(BLUE)📊 Estado de los contenedores:$(NC)"
	@docker-compose -f $(COMPOSE_FILE) ps

stats: ## Ver estadísticas de recursos de los contenedores
	docker stats

init: ## Inicializar proyecto completo (build + up + migrate + collectstatic)
	@echo "$(BLUE)🎯 Inicializando proyecto completo...$(NC)"
	@make build
	@make up
	@sleep 10
	@make migrate
	@make collectstatic
	@echo "$(GREEN)✅ Proyecto inicializado correctamente$(NC)"
	@echo "$(BLUE)📱 Aplicación disponible en: http://localhost$(NC)"
	@echo "$(BLUE)🔐 Admin disponible en: http://localhost/admin$(NC)"

deploy: ## Desplegar cambios (build + up)
	@echo "$(BLUE)🚀 Desplegando cambios...$(NC)"
	@make build
	@make down
	@make up
	@sleep 5
	@make collectstatic
	@echo "$(GREEN)✅ Despliegue completado$(NC)"
