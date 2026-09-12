init:
	python -m pip install poetry
	poetry install --no-root

test:
	poetry run pytest -sv tests

run:
	poetry run python cmd/app/main.py

docker-pull:
	docker compose pull

docker-up:
	docker compose pull
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f
