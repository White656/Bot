.PHONY: run
run: ## Run application
	poetry run gunicorn \
	    --bind $(APP_HOST):$(APP_PORT_INTERNAL) \
		--worker-class uvicorn.workers.UvicornWorker \
		--workers $(APP_WORKERS) \
		--log-level $(APP_LOG_LEVEL) \
		--chdir cmd/app \
		main:app


.PHONY: run-dev
run-dev: ## Run application
	poetry run uvicorn --app-dir cmd/app main:app --reload