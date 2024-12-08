.PHONY: migrate-create
migrate-create: ## Create new migration
	alembic revision --autogenerate -m $(name)

.PHONY: migrate-history
migrate-history: ## Migration history
	alembic history

.PHONY: migrate-up
migrate-up: ## Migration up
	alembic upgrade head

.PHONY: migrate-down
migrate-down: ## Migration down
	alembic downgrade -1