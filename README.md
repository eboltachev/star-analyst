# Star Analyst MVP

Монолитный MVP сервиса OSINT-проверок: FastAPI веб-приложение + worker + PostgreSQL/pgvector + адаптеры источников + explainable report/chat.

## Что реализовано
- **Web/API:** логин, создание запроса (enqueue-only), мониторинг событий (SSE), отчёт, граф, чат, rerun источников.
- **Worker:** фоновая обработка job-очереди, безопасный claim (`SKIP LOCKED` для PostgreSQL), lifecycle rerun.
- **Adapters:** fixture/http-режимы, retry/rate-limit, error taxonomy, базовые parser contracts и drift detection.
- **Quality/Security:** claim coverage gate, chat policy gate, CSRF, upload content sniffing (проверка declared/detected MIME).
- **Observability:** source-метрики в Prometheus-формате на `/metrics`.

## Архитектура
- `app` — FastAPI + шаблоны + pipeline/services.
- `app/worker` — worker loop и обработка job.
- `app/models` + `alembic` — ORM-модели и миграции.
- `config/sources.yml` — конфигурация источников.
- `docs/runbook_sources.md` — runbook деградации источников.

## Быстрый старт (локально)
```bash
cp .env.example .env
docker compose up -d db
pip install -e .[dev]
alembic upgrade head
python scripts/create_admin.py
uvicorn app.main:app --reload
# в отдельном терминале
python -m app.worker.run
```

## Docker compose
```bash
docker compose up --build
```

## Пользовательский сценарий
1. Выполнить `POST /seed-admin` (или `python scripts/create_admin.py`).
2. Войти: `admin@example.com` / `admin123`.
3. Создать проверку, выбрать источники, загрузить файлы.
4. Отслеживать прогресс на monitor-странице, затем открыть отчёт/чат.
5. При необходимости выполнить rerun источников из отчёта.

## Миграции
```bash
alembic upgrade head
```

## Тестирование
### Базовый запуск
```bash
scripts/run_tests.sh
```

### Отдельные test lanes
```bash
scripts/test_adapter_runtime_mocks.sh
scripts/test_integration_postgres.sh
scripts/test_e2e_full.sh
```

> Примечание: в локальной среде без optional-зависимостей (например, Playwright/PostgreSQL) некоторые lane-скрипты могут завершаться soft-skip сообщением.

## CI release gates
Blocking jobs описаны в `.github/workflows/ci.yml`:
- baseline (`pytest tests/unit tests/integration tests/e2e`)
- adapter-runtime-mocks
- integration-postgres
- e2e-full

## Observability
- Метрики: `GET /metrics` (Prometheus text format).
- Runbook: `docs/runbook_sources.md`.

## Настройка AI провайдеров
Провайдеры инкапсулированы в `app/services/ai.py`. Для подключения OpenAI-compatible endpoints задайте:
- `LLM_BASE_URL`, `LLM_MODEL`
- `VISION_BASE_URL`, `VISION_MODEL`
- `EMBEDDING_BASE_URL`, `EMBEDDING_MODEL`
- `API_KEY`
