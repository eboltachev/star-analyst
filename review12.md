# review12.md — Предложения по дальнейшему устранению недостатков после закрытия приоритетов review11

Дата: 2026-03-23

## Что закрыто в текущем цикле
1. Добавлена отдельная миграция `0002_add_claims_json_to_reports` для безопасного обновления существующих БД.
2. Добавлен конкурентный integration test на отсутствие двойного claim (`test_worker_concurrency.py`).
3. E2E слой расширен до полноценного browser-flow теста (под флагом `RUN_FULL_E2E=1`).
4. Усилен контракт report claims: `ReportClaim` теперь валидирует непустой `evidence_ids`.

## Оставшиеся недостатки

### P0
1. Full E2E сейчас опционален через env-флаг; для строгого CI нужна отдельная job с браузерной средой.
2. Не реализован KPI-чек покрытия claims (`>=95%`) как автоматический quality gate.
3. Worker concurrency test выполняется на sqlite в тестовой среде; для строгой проверки lock semantics нужен PostgreSQL integration run.

### P1
1. Chat rerun всё ещё рекомендация, а не полноценный workflow.
2. Security hardening остаётся частичным (CSRF, upload hard limits, cookie policy).
3. Graph detail panel с evidence snippets и ссылками на claims не завершён.

## Предложения на следующий итерационный PR

## PR-1 (P0): CI quality gates
- Добавить job `e2e-full` (RUN_FULL_E2E=1) в CI.
- Добавить job `integration-postgres` для проверки `skip_locked` на PostgreSQL.
- Добавить тест-гейт на claim coverage >=95%.

## PR-2 (P1): Chat rerun workflow
- Endpoint rerun выбранных источников + UI кнопка с подтверждением.
- Переход monitor->report после rerun completion.

## PR-3 (P1): Security completion
- CSRF middleware/token,
- upload MIME/size allowlist,
- secure cookie flags by env default.

## PR-4 (P1): Graph explainability UX
- Click panel для node/edge,
- snippets evidence,
- deep links на report claims.

## Критерии готовности следующего релиза
1. `scripts/run_tests.sh` green + e2e-full green.
2. claim coverage gate >=95% enforced.
3. postgres concurrency integration green.
4. security negative tests green.
