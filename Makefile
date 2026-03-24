PYTHON ?= python
PIP ?= pip
API_HOST ?= 127.0.0.1
API_PORT ?= 8000

.PHONY: install dev test lint clean

install:
	$(PIP) install -e ".[api,dev]"
	cd frontend && npm install

dev:
	@echo "Start API in one terminal:"
	@echo "  uvicorn api.app:app --reload --host $(API_HOST) --port $(API_PORT)"
	@echo "Start frontend in another terminal:"
	@echo "  cd frontend && npm run dev"

test:
	pytest tests/ -v

lint:
	ruff check .
	cd frontend && npm run lint

clean:
	$(PYTHON) -c "from pathlib import Path; [p.unlink() for p in Path('projecao_bus/projecoes').glob('*.csv')] if Path('projecao_bus/projecoes').exists() else None; [p.unlink() for p in Path('projecao_bus/dcf_output').glob('*.csv')] if Path('projecao_bus/dcf_output').exists() else None"
