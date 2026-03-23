# review10.md — Предложения по дальнейшему закрытию недостатков после итерации review09

Дата: 2026-03-23

## Что исправлено в этой итерации
1. Добавлена база для атомарного claim в worker: при PostgreSQL используется `with_for_update(skip_locked=True)`.
2. Усилен report contract: в итоговый markdown добавляется секция `Claims (report_claims_v1)` с привязкой `claim_id -> evidence_ids`.
3. Усилен chat contract: endpoint возвращает структурированный ответ (`answer`, `citations`, `insufficient_data`, `suggested_reruns`).
4. Интеграционный тест адаптирован под новый chat contract.

## Что всё ещё не закрыто полностью

### P0
1. Claim атомарность пока без полноценного конкурентного integration test (несколько worker-сессий).
2. `report_claims_v1` существует как markdown section, но нужен отдельный формальный JSON schema/validator и хранение в структурированном поле.
3. `chat_answer_v1` не валидируется строгой схемой на уровне API (Pydantic response model).
4. Полный Playwright E2E бизнес-сценарий отсутствует.

### P1
1. Rerun из чата возвращается как suggestion, но ещё нет полноценного UI flow с выбором источников и подтверждением.
2. Security baseline (CSRF, upload hardening, cookie flags) остаётся для отдельной итерации.
3. Graph detail panel по клику с evidence snippets не завершён.

## Рекомендуемые следующие PR

## PR-1 (P0) — strict contracts
- Ввести `ReportClaimsPayload` и `ChatAnswerPayload` как Pydantic v2 модели.
- Хранить report claims в отдельном JSON поле (`reports.claims_json`) или отдельной таблице.
- Добавить unit tests на schema validation.

## PR-2 (P0) — worker concurrency correctness
- Написать integration test с 2+ конкурентными воркерами для проверки `skip_locked`.
- Добавить idempotency-key для submit endpoint.

## PR-3 (P0) — full e2e user flow
- Реализовать Playwright сценарий: login -> submit -> monitor -> report -> graph -> chat -> history.
- Добавить `data-testid` hooks.

## PR-4 (P1) — security + UX hardening
- CSRF tokens, upload allowlist/size limits, secure cookie settings.
- Graph detail panel + deep links на claims/evidence.

## Критерии приемки следующего релиза
1. `scripts/run_tests.sh` green без пропусков критичных сценариев.
2. Full Playwright E2E green.
3. >=95% report claims имеют evidence ids.
4. 100% chat responses соответствуют схеме и policy (citations или insufficiency).

