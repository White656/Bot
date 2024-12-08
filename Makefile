ifneq ($(wildcard .env.example),)
	ENV_FILE = .env.example
endif
ifneq ($(wildcard .env.example),)
	ifeq ($(COMPOSE_PROJECT_NAME),)
		include .env.example
	endif
endif
ifneq ($(wildcard .env),)
	ENV_FILE = .env
endif
ifneq ($(wildcard .env),)
	ifeq ($(COMPOSE_PROJECT_NAME),)
		include .env
	endif
endif

export


.SILENT:
.PHONY: help
help: ## Display this help screen
	awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)


include make/run.Makefile
include make/lint.Makefile
include make/test.Makefile
include make/migration.Makefile
include make/compose.Makefile
include make/docker.Makefile
