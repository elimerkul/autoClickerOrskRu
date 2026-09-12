FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.5 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    TZ=Asia/Yekaterinburg

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        wget \
        gnupg \
        unzip \
        ca-certificates \
        tzdata \
        fonts-liberation \
        libnss3 \
        libatk-bridge2.0-0 \
        libgtk-3-0 \
        libgbm1 \
        libasound2 \
        libdrm2 \
        libxkbcommon0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
    && wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y --no-install-recommends /tmp/chrome.deb \
    && CHROME_MAJOR="$(google-chrome --version | awk '{print $3}' | cut -d. -f1)" \
    && DRIVER_VERSION="$(wget -qO- "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_MAJOR}")" \
    && wget -q "https://storage.googleapis.com/chrome-for-testing-public/${DRIVER_VERSION}/linux64/chromedriver-linux64.zip" -O /tmp/chromedriver.zip \
    && unzip /tmp/chromedriver.zip -d /tmp \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && ln -sf /usr/bin/google-chrome-stable /usr/bin/google-chrome \
    && rm -rf /tmp/chrome.deb /tmp/chromedriver.zip /tmp/chromedriver-linux64 /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock ./
RUN touch README.md \
    && pip install --no-cache-dir "poetry==${POETRY_VERSION}" \
    && poetry install --no-root --only main --no-interaction --no-ansi

COPY cmd ./cmd
COPY internal ./internal
COPY config ./config

RUN mkdir -p /app/data/log

CMD ["python", "cmd/app/main.py"]
