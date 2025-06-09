.PHONY: .uv
.uv: ## Check that uv is installed
	@uv --version || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'

.PHONY: install
install: .uv ## Install the package, dependencies, and pre-commit for local development
	uv pip install -r pyproject.toml --all-extras
	uvx pre-commit install --install-hooks

.PHONY: .uv lint
lint: ## Run linters
	uvx pre-commit run --all-files

.PHONY: .uv test
test: ## Run tests
	uvx pytest

.PHONY: .uv install preview
preview:  ## Preview the application
	uvicorn src.web.main:app --reload

.PHONY: .uv build
build: ## Build while packaging
	uv build

.PHONY: help
help: ## Show this help (usage: make help)
	@echo "Usage: make [recipe]"
	@echo "Recipes:"
	@awk '/^[a-zA-Z0-9_-]+:.*?##/ { \
		helpMessage = match($$0, /## (.*)/); \
		if (helpMessage) { \
			recipe = $$1; \
			sub(/:/, "", recipe); \
			printf "  \033[36m%-20s\033[0m %s\n", recipe, substr($$0, RSTART + 3, RLENGTH); \
		} \
	}' $(MAKEFILE_LIST)
