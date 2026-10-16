PYTHON ?= python

.PHONY: data api test

data:
	$(PYTHON) scripts/generate_synthetic_data.py --out data/generated --seed 42 --scale small

api:
	cd backend && uvicorn app.main:app --reload --port 8000

test:
	cd backend && pytest
