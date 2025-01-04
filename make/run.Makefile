.PHONY: run
run: ## Run application
	gunicorn \
	    --bind $(APP_HOST):$(APP_PORT_INTERNAL) \
		--worker-class uvicorn.workers.UvicornWorker \
		--workers $(APP_WORKERS) \
		--log-level $(APP_LOG_LEVEL) \
		--chdir cmd/app \
		main:app

.PHONY: run-dev
run-dev: ## Run application in development mode
	uvicorn --app-dir cmd/app main:app --reload --host 0.0.0.0