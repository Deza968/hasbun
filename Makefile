# Makefile - Inversiones Hasbun
# Uso: make up | make down | make logs | make shell-api | make shell-db | make migrate | make test | make seed

COMPOSE := docker compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.override.yml

.PHONY: up down logs build ps shell-api shell-db shell-web migrate makemigration seed test test-api lint api-install web-install

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

build:
	$(COMPOSE) build

ps:
	$(COMPOSE) ps

shell-api:
	$(COMPOSE) exec api bash

shell-db:
	$(COMPOSE) exec postgres psql -U hasbun -d hasbun

shell-web:
	$(COMPOSE) exec web sh

migrate:
	$(COMPOSE) exec api alembic upgrade head

makemigration:
	$(COMPOSE) exec api alembic revision --autogenerate -m "$(msg)"

seed:
	$(COMPOSE) exec api python -m app.database.seeds

test:
	$(COMPOSE) exec api pytest

test-api:
	cd apps/api && pytest

lint:
	cd apps/api && ruff check apps/api/ 2>/dev/null || ruff check app/

api-install:
	cd apps/api && pip install -e ".[dev]"

web-install:
	cd apps/web && npm install