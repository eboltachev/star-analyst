# review09.md — Предложения по устранению оставшихся недостатков

Дата: 2026-03-23

> Примечание: файл `review08.md` в репозитории не найден. В этом ревью использованы фактически выявленные незакрытые разрывы по текущему коду и предыдущим review/plan документам.

## Что исправлено в текущем цикле
1. Тестовый слой теперь корректно работает в средах без FastAPI: интеграционные тесты автоматически `skip`, а unit-сценарии не блокируются из-за импорта FastAPI в `conftest.py`.
2. Адаптерный base layer усилен: добавлены базовые механизмы `rate_limit` и `retry/backoff`.
3. Источники FNS/SUDRF/MVD получили dual-mode (`fixture`/`http`) через конфиг `mode`.

## Оставшиеся недостатки (приоритет)

### P0
1. Worker claim должен быть атомарным для конкурентных воркеров (`FOR UPDATE SKIP LOCKED` в PostgreSQL), сейчас claim ещё упрощённый.
2. Отчёт не формализован как `report_claims_v1` с обязательным `claim -> evidence` контрактом.
3. Chat не соблюдает строгий `citations-or-insufficiency` JSON-контракт.
4. Нет полного Playwright E2E по бизнес-сценарию (сейчас smoke/skip).

### P1
1. Security baseline не закрыт полностью: CSRF, upload limits/allowlist, cookie flags.
2. Graph UX не даёт полноценной evidence-панели по клику.

## Рекомендованные PR-пакеты

## PR-A (P0): queue concurrency + reliability
- Внедрить PostgreSQL row-lock claim.
- Добавить idempotency ключ submit.
- Формализовать retry/dead-letter и метрики job processing.

## PR-B (P0): explainable contracts
- `report_claims_v1` schema + validator.
- `chat_answer_v1` schema + enforcement.
- Инварианты в тестах: no claim without evidence; no answer without citations/insufficiency.

## PR-C (P0): complete E2E
- Реализовать полный Playwright flow.
- Добавить `data-testid` и детерминированные фикстуры.

## PR-D (P1): security + graph details
- CSRF + upload policy + secure cookies.
- Graph node/edge detail panel с evidence snippets и ссылками на claims.

## Критерии приемки
1. submit p95 < 500ms.
2. first monitor event < 2s.
3. >=95% claims с evidence.
4. 100% chat answers: citations или insufficiency.
5. full e2e green.

