# review07.md — Предложения по дальнейшему устранению недостатков после текущих исправлений

Дата: 2026-03-22

## Что устранено в этом цикле
1. Переведён запуск pipeline в enqueue-only модель на стороне API (добавлен `Job`, убран синхронный `process_request` из HTTP path).
2. Worker теперь забирает queued jobs и обрабатывает их отдельным тиком (`process_once`) с retry/fail логикой.
3. Интеграционный тест обновлён под новую оркестрацию (request enqueue -> worker tick -> report/chat).

## Оставшиеся ключевые недостатки

### P0
1. Runtime adapters всё ещё не доведены до полного HTTP/retry/rate-limit production path.
2. Explainability contract отчёта (claim->evidence schema) не формализован как отдельный валидируемый контракт.
3. Chat contract с обязательными citations/insufficiency и rerun UI/API — частично/неполно.
4. Полный Playwright e2e пользовательский сценарий пока отсутствует (есть smoke/stub).

### P1
1. Security baseline (CSRF/upload policy/cookie hardening) требует завершения.
2. Graph UX нужно связать с evidence details и report claims через click panel.

## Предложения по следующему итерационному PR-пакету

## PR-1 (P0): runtime adapters
- Реализовать dual-mode (`fixture/http`) через env/config.
- Добавить transport wrapper (timeout/retry/backoff/rate-limit).
- Добавить error taxonomy + partial failure handling в отчёт.

## PR-2 (P0): explainable report + chat contract
- Ввести `report_claims_v1` и `chat_answer_v1` JSON schemas.
- Проверять в рантайме: нет claim без evidence.
- Для чата: либо citations, либо `insufficient_data=true`.

## PR-3 (P0): full e2e
- Реализовать полный Playwright flow с `data-testid`.
- Включить проверки мониторинга, графа, чата и истории.

## PR-4 (P1): security/UX hardening
- CSRF, upload allowlist/limits, cookie flags.
- Graph detail panel с evidence snippets и deep-link на claims.

## Метрики приемки
1. submit p95 < 500ms.
2. first event < 2s.
3. >=95% report claims имеют evidence.
4. 100% ответов чата имеют citations или insufficiency.
5. full e2e green в CI.

