.PHONY: docker-clean
docker-clean: ## Remove unused data
	docker system prune -a
