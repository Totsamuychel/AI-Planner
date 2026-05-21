COMPOSE := docker compose -f infra/docker/docker-compose.yml --env-file .env

.PHONY: up down build logs ps restart api-sh web-sh worker-sh migrate revision test lint fmt clean

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

restart:
	$(COMPOSE) restart

api-sh:
	$(COMPOSE) exec api bash

web-sh:
	$(COMPOSE) exec web sh

worker-sh:
	$(COMPOSE) exec worker bash

migrate:
	$(COMPOSE) exec api alembic upgrade head

revision:
	$(COMPOSE) exec api alembic revision --autogenerate -m "$(m)"

test:
	$(COMPOSE) exec api pytest -q

lint:
	$(COMPOSE) exec api ruff check . && $(COMPOSE) exec api mypy app
	$(COMPOSE) exec web pnpm lint

fmt:
	$(COMPOSE) exec api ruff format .
	$(COMPOSE) exec web pnpm format

clean:
	$(COMPOSE) down -v --remove-orphans
