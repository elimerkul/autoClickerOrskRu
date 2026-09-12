init:
	python -m pip install poetry
	poetry install --no-root

test:
	poetry run pytest -sv tests

run:
	poetry run python cmd/app/main.py

docker-build:
	docker compose build

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f
