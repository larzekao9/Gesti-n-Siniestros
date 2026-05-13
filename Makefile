.PHONY: up down logs ps backend-shell frontend-shell migrate test-backend seed build build-no-cache

## Levantar todos los servicios en background
up:
	docker compose up -d

## Levantar con logs en foreground
up-logs:
	docker compose up

## Bajar todos los servicios (preserva volúmenes)
down:
	docker compose down

## Bajar servicios y eliminar volúmenes (reset completo de BD)
down-volumes:
	docker compose down -v

## Seguir logs de todos los servicios
logs:
	docker compose logs -f

## Seguir logs solo del backend
logs-backend:
	docker compose logs -f backend

## Estado de los contenedores
ps:
	docker compose ps

## Shell interactiva en el contenedor backend
backend-shell:
	docker compose exec backend bash

## Shell interactiva en el contenedor frontend
frontend-shell:
	docker compose exec frontend sh

## Ejecutar migraciones Alembic
migrate:
	docker compose exec backend alembic upgrade head

## Crear una nueva migración (uso: make migration MSG="add users table")
migration:
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

## Correr tests del backend dentro del contenedor
test-backend:
	docker compose exec backend pytest tests/ -v --cov=app --cov-report=term-missing

## Setup local con Python 3.12 (sin Docker) — requiere: /opt/homebrew/bin/python3.12
venv:
	/opt/homebrew/bin/python3.12 -m venv backend/.venv
	backend/.venv/bin/pip install -r backend/requirements.txt -q
	@echo "Venv listo. Activar con: source backend/.venv/bin/activate"

## Correr tests localmente (sin Docker)
test-local:
	cd backend && ../.venv/bin/pytest tests/ -v --cov=app --cov-report=term-missing 2>/dev/null || \
	backend/.venv/bin/pytest backend/tests/ -v --cov=backend/app --cov-report=term-missing

## Cargar datos semilla
seed:
	docker compose exec backend python scripts/seed.py

## Construir imágenes (con cache)
build:
	docker compose build

## Construir imágenes sin cache (rebuild completo)
build-no-cache:
	docker compose build --no-cache

## Setup inicial: copiar .env.example a .env
setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env creado desde .env.example. Editalo con tus valores antes de correr 'make up'."; \
	else \
		echo ".env ya existe, no se sobreescribio."; \
	fi
