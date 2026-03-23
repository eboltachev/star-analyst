# review16.md — Предложения после устранения недостатков review15

Дата: 2026-03-23

## Что устранено
1. CSRF контроль переведён на `settings.testing` вместо production backdoor header.
2. Добавлен audit trail для дозапуска источников через модель `rerun_runs` и миграцию.
3. Улучшен UX графа: детализация node/edge показывает evidence links.

## Что ещё важно довести

### P1
1. Для CSRF нужен полноценный integration/e2e сценарий с реальным токеном, а не bypass через testing mode.
2. `rerun_runs` пока без обновления статуса выполнения (queued/running/done/error) в worker pipeline.
3. В отчёте нет отдельной секции истории rerun с provenance.

### P2
1. Добавить retention/cleanup задачи для `uploaded_files` и артефактов.
2. Добавить dashboard-метрики для rerun (latency/success rate).
3. Расширить graph panel: source URLs, snippets, confidence badges.

## Рекомендуемые PR

## PR-1 (P1): rerun status lifecycle
- Обновлять `rerun_runs.status` из worker (running/done/error).
- Показывать историю rerun на странице отчёта.

## PR-2 (P1): CSRF hardening tests
- Добавить integration test на обязательность CSRF token в prod mode.
- Добавить e2e шаги с формами и csrf hidden field.

## PR-3 (P2): observability + retention
- Метрики rerun/pipeline quality.
- Cleanup cron/worker for old files and artifacts.

## Критерии следующего релиза
1. Security tests green в prod-mode (без testing bypass).
2. Rerun lifecycle полностью наблюдаем и отображается в UI.
3. Graph evidence panel проходит UX acceptance.
