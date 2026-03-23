# review14.md — Предложения по дальнейшему устранению недостатков после закрытия P0-гейтов review13

Дата: 2026-03-23

## Что закрыто в текущей итерации
1. Введён quality gate claims coverage (>=95%) через `app/services/quality.py` и использование в pipeline.
2. Добавлен PostgreSQL-specific integration test на lock semantics (`test_worker_postgres_lock.py`).
3. E2E browser flow переведён в always-on тест в рамках `scripts/run_tests.sh` (через `RUN_FULL_E2E=1`, при наличии зависимостей).
4. Добавлена migration strategy для `claims_json` (initial + additive migration).

## Что остаётся незакрытым

### P1
1. Chat rerun всё ещё не end-to-end workflow (нет полного UX/API цикла).
2. Security baseline остаётся частично неполным:
   - CSRF middleware/token,
   - upload MIME/size enforcement,
   - secure cookie defaults-by-env.
3. Graph explainability UX неполный (детальная панель и deep links).

### P2
1. Нужны эксплуатационные метрики/алертинг по pipeline и chat quality.
2. Нужно уменьшить долю skip-тестов в default test run (поднять стабильный CI env с нужными зависимостями).

## Предложения по следующему PR-пакету

## PR-1 (P1): Chat rerun complete flow
- API rerun с выбором источников.
- UI кнопка в report/chat + отображение статусов rerun.
- integration/e2e проверки rerun -> updated report.

## PR-2 (P1): Security hardening
- CSRF защита.
- upload policy (allowlist + size limits + filename sanitization).
- cookie policy hardening (`HttpOnly`, `Secure`, `SameSite`).

## PR-3 (P1): Graph UX completion
- click node/edge detail panel.
- evidence snippets + deep links на claims.

## PR-4 (P2): Observability
- метрики: enqueue latency, worker throughput, source error rate, claim coverage ratio.
- structured alerts по деградациям.

## Целевые критерии следующего релиза
1. `scripts/run_tests.sh` green с минимальными skip.
2. Security negative tests green.
3. End-to-end rerun flow green.
4. Graph explainability UX acceptance passed.
