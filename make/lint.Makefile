.PHONY: lint
lint: ## Run linters
	make lint-isort
	make lint-flake


.PHONY: lint-isort
lint-isort: ## Run isort linter
	poetry run isort .

.PHONY: lint-flake8
lint-flake:  ## Run flake8 linter
	poetry run flake8
