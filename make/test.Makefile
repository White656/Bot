.PHONY: test
test: ## Run pytest
	poetry run pytest -rs --junitxml=reports/test-report.xml

.PHONY: test-coverage
test-coverage: ## Run pytest coverage
	poetry run coverage run -m pytest -rs --junitxml=reports/test-report.xml
	poetry run coverage report
	poetry run coverage xml -o reports/coverage.xml
	poetry run coverage html -d reports/coverage/
