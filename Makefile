run:
	uvicorn app.main:app --reload --workers 1 --host 0.0.0.0 --port 8000

install: update

update:
	pip install --upgrade pip pip-tools
	pip-compile -U --no-header --no-annotate --strip-extras --resolver=backtracking
	pip-sync
