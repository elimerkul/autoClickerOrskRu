# autoClickerOrskRu

Автокликер объявлений [board.orsk.ru](https://board.orsk.ru).

Образ публикуется в GHCR: `ghcr.io/elimerkul/autoclickerorskru:latest`.

## Запуск в Docker

```bash
cp .env.example .env
```

Заполните `AUTH_LOGIN` и `AUTH_PASSWORD` в `.env`.

Если пакет в GHCR приватный, сначала залогиньтесь:

```bash
echo "$GITHUB_TOKEN" | docker login ghcr.io -u USERNAME --password-stdin
```

Затем:

```bash
docker compose up -d
docker compose logs -f
```
