.PHONY: install test lint format clean build docker-build docker-test

install:
	python -m pip install -e ".[dev,test]"
	pre-commit install

test:
	pytest

coverage:
	pytest --cov=eleven_audiobooks --cov-report=xml --cov-report=term-missing

lint:
	black --check .
	isort --check-only --diff .
	ruff check .
	mypy .

format:
	black .
	isort .
	ruff check --fix .

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +

build:
	python -m build

docker-build:
	docker-compose build

docker-test:
	docker-compose run --rm app

setup-dev: install
	mkdir -p data/processed
	mkdir -p tests/data

help:
	@echo "Available commands:"
	@echo "  install      Install package and development dependencies"
	@echo "  test         Run tests"
	@echo "  coverage     Run tests with coverage report"
	@echo "  lint         Run all linters"
	@echo "  format       Format code"
	@echo "  clean        Clean build artifacts"
	@echo "  build        Build package"
	@echo "  docker-build Build Docker image"
	@echo "  docker-test  Run tests in Docker"
	@echo "  setup-dev    Setup development environment" 