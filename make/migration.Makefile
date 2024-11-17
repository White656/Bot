.PHONY: migrate-create
migrate-create: ## Create new migration
	poetry run alembic revision --autogenerate -m $(name)

.PHONY: migrate-history
migrate-history: ## Migration history
	poetry run alembic history

.PHONY: migrate-up
migrate-up: ## Migration up
	poetry run alembic upgrade head

.PHONY: migrate-down
migrate-down: ## Migration down
	poetry run alembic downgrade -1
