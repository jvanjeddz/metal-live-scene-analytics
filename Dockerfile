FROM python:3.13-slim

RUN groupadd -g 1000 app && useradd -u 1000 -g app -m app

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev && chown -R app:app /app

COPY --chown=app:app . .

USER app
