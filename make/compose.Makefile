.PHONY: compose-build
compose-build: ## Build or rebuild services
	docker compose -f docker/docker-compose.yml --env-file $(ENV_FILE) build

.PHONY: compose-up
compose-up: ## Create and start containers
	docker compose -f docker/docker-compose.yml --env-file $(ENV_FILE) up -d --build

.PHONY: compose-migration
compose-migration: ## Create and start containers
	docker compose -f docker/docker-compose.yml --env-file $(ENV_FILE) up migration --exit-code-from migration

.PHONY: compose-logs
compose-logs: ## View output from containers
	docker compose -f docker/docker-compose.yml logs

.PHONY: compose-ps
compose-ps: ## List containers
	docker compose -f docker/docker-compose.yml ps

.PHONY: compose-ls
compose-ls: ## List running compose projects
	docker compose -f docker/docker-compose.yml ls

.PHONY: compose-start
compose-start: ## Start services
	docker compose -f docker/docker-compose.yml --env-file $(ENV_FILE) start

.PHONY: compose-restart
compose-restart: ## Restart services
	docker cp ./ tarvos-api:/code/
	docker compose -f docker/docker-compose.yml restart

.PHONY: compose-stop
compose-stop: ## Stop services
	docker compose -f docker/docker-compose.yml stop

.PHONY: compose-down
compose-down: ## Stop and remove containers, networks
	docker compose -f docker/docker-compose.yml down --remove-orphans
