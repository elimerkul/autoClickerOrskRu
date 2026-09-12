# autoClickerOrskRu

Автокликер объявлений [board.orsk.ru](https://board.orsk.ru).

## Запуск в Docker

```bash
cp .env.example .env
```

Заполните `AUTH_LOGIN` и `AUTH_PASSWORD` в `.env`, затем:

```bash
docker compose up -d --build
docker compose logs -f
```
