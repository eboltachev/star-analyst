# review11.md — Предложения по закрытию оставшихся недостатков после итерации review10

Дата: 2026-03-23

## Что закрыто в текущем цикле
1. Добавлен structured chat contract на уровне схемы (`chat_answer_v1`) и response_model API.
2. Добавлен structured report claims payload (`report_claims_v1`) и сохранение claims в `Report.claims_json`.
3. Worker claim усилен PostgreSQL `skip_locked` веткой.
4. Добавлены unit checks для новых контрактов.

## Что ещё остаётся (приоритет)

### P0
1. Нужна отдельная миграция для существующих БД (если `claims_json` добавляется post-deploy).
2. Нужен конкурентный integration test для `skip_locked` (2+ воркера).
3. Нужен полноценный Playwright E2E сценарий вместо smoke/skip.
4. Нужна строгая проверка claim coverage в CI (`>=95%` claim с evidence).

### P1
1. Chat rerun пока suggestion-only, нужен полноценный UI/API flow на дозапуск источников.
2. Security baseline всё ещё неполный: CSRF/upload limits/cookie policy.
3. Graph detail panel с deep links на claims/evidence не завершён.

## Рекомендуемые следующие PR

## PR-1 (P0): migration & compatibility
- Добавить alembic migration `add_claims_json_to_reports` (если база уже развёрнута).
- Добавить backward-compatible чтение report без claims_json.

## PR-2 (P0): concurrent worker correctness
- Реализовать integration тест с двумя worker-сессиями и assert no double-claim.
- Добавить метрики: claim latency, retry count, dead-letter count.

## PR-3 (P0): full e2e
- Полный Playwright flow по ТЗ.
- `data-testid` по критическим узлам UI.

## PR-4 (P1): security + graph UX
- CSRF tokens + upload policy + secure cookies.
- Graph click panel + snippets + report claim anchors.

## Критерии приемки следующей версии
1. Полный `scripts/run_tests.sh` green без skip критичных кейсов.
2. Full e2e flow green в CI.
3. Report claims coverage >=95%.
4. Chat policy соблюдается на 100% (citations или insufficiency).
