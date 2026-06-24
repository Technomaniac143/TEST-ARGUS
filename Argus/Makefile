.PHONY: install install-dev compile test run

install:
	python -m pip install -r requirements.txt

install-dev:
	python -m pip install -r requirements-dev.txt

compile:
	python -m compileall backend tests

test:
	pytest

run:
	uvicorn backend.main:app --reload
