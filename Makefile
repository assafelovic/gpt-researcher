PYTHON ?= python3

.PHONY: test test-cov test-watch e2e e2e-nextjs lint typecheck

test:
	$(PYTHON) -m pytest tests/ -v --tb=short

test-cov:
	$(PYTHON) -m pytest tests/ --cov --cov-report=term-missing

test-watch:
	find tests/ gpt_researcher/ -name '*.py' | entr $(PYTHON) -m pytest tests/ -v --tb=short

e2e:
	bash tests/e2e/run-e2e.sh

e2e-nextjs:
	bash tests/e2e/run-e2e.sh --nextjs

e2e-ci:
	bash tests/e2e/run-e2e.sh --ci

lint:
	ruff check gpt_researcher/ backend/ tests/

typecheck:
	pyright gpt_researcher/ backend/
