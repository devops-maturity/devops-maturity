
.PHONY: lint
lint:
	uvx pre-commit run --all-files

.PHONY: test
test:
	uvx pytest

.PHONY: preview
preview:
	uvicorn src.web.main:app --reload

.PHONY: build
build:
	uv build

.PHONY: help
help:
	@echo "Available commands:"
	@echo "  lint     - Run linters"
	@echo "  test     - Run tests"
	@echo "  preview  - Start the development server"
	@echo "  build    - Build the application"
	@echo "  help     - Show this help message"