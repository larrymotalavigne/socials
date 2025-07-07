.DEFAULT_GOAL := install

.PHONY: install
install:
	pip install -U pip uv
	uv sync --active --all-extras --compile-bytecode --frozen --no-install-project

.PHONY: update
update:
	pip install -U pip uv
	uv lock --upgrade
	uv sync --active --all-extras --compile-bytecode --frozen --no-install-project

.PHONY: run
run:
	docker-compose up

.PHONY: lint
lint:
	ruff back

.PHONY: clean
clean:
	find . -type d -name "__pycache__" -depth -exec rm -rf '{}' \;

.PHONY: security
security:
	bandit -v -r . -c pyproject.toml --exit-zero

.PHONY: test
test:
	uv run --active --all-extras --frozen pytest -c pyproject.toml $(PYTEST_EXTRA_ARGS)
