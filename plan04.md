# plan04.md — Implementation plan #4 + testing protocol (from planning to delivery)

Дата: 2026-03-22

## Цель
Закрыть разрыв между планированием (`plan01..03`) и фактической поставкой приемочного MVP: выполнить P0-блоки, подтвердить критерии приемки тестами и зафиксировать release-gates.

---

## 1. Delivery фокус (что считаем done)

MVP считается готовым только если одновременно выполнены:
1. API create request работает в enqueue-only режиме (без синхронного pipeline).
2. Worker обрабатывает jobs с retry/dead-letter и наблюдаемыми статусами.
3. Runtime adapters работают в `http` режиме (с fallback на fixtures в test mode), есть timeout/retry/rate-limit и safe logging.
4. Отчёт explainable: claims привязаны к evidence.
5. Чат возвращает citations либо `insufficient_data=true`; есть rerun источников.
6. Полный E2E сценарий Playwright проходит стабильно.
7. Security baseline: CSRF, cookie hardening, upload allowlist/limits.

---

## 2. Реализация по PR-волнам

## Wave A (P0) — Orchestration + Runtime adapters

### A1. Queue/Job model
- Добавить `jobs` (migration + ORM):
  - `id`, `request_id`, `status`, `attempt`, `max_attempts`, `locked_at`, `locked_by`, `error`, timestamps.
- Убрать запуск `process_request()` из HTTP handler.
- Worker: claim через `FOR UPDATE SKIP LOCKED`, retry, dead-letter.

### A2. Runtime adapters
- `BaseSourceAdapter`:
  - transport wrapper (httpx)
  - retry/backoff
  - per-source rate-limit
  - safe structured logs (маскирование PII)
- Адаптеры FNS/SUDRF/MVD: dual-mode (`fixture`/`http`).
- Частичные ошибки источников не ломают весь pipeline.

### A Acceptance
- submit p95 < 500ms;
- first event < 2s;
- partial source failure handled.

---

## Wave B (P0) — Explainability + Chat contract

### B1. Report contract
- Ввести `report_claims_v1`:
  - `claim_id`, `text`, `evidence_ids`, `confidence`, `source_refs`.
- Гарантировать обязательные секции отчёта по ТЗ.

### B2. Chat contract + rerun
- Ввести `chat_answer_v1`:
  - `answer`, `citations`, `insufficient_data`, `suggested_reruns`.
- Добавить retrieval слой по локальному контексту.
- Добавить rerun endpoint + кнопку в UI.

### B Acceptance
- >=95% claims имеют evidence;
- 100% ответов чата: citations или insufficiency.

---

## Wave C (P0/P1) — Full E2E + Security baseline

### C1. E2E
- Полный сценарий:
  login → new request → sources → file upload → monitor → report → graph click → chat citation → history.
- Добавить `data-testid` по ключевым элементам.

### C2. Security
- CSRF token в POST формах.
- Cookie flags (`HttpOnly`, `Secure`, `SameSite`).
- Upload policy (MIME allowlist, max size, filename sanitization).

### C Acceptance
- e2e green в CI;
- негативные security тесты green.

---

## 3. Тестовый протокол (обязательный)

Порядок запуска:
```bash
alembic upgrade head
pytest tests/unit
pytest tests/integration
pytest tests/e2e -m e2e
scripts/run_tests.sh
```

Критерий успешности:
- все команды завершаются без ошибок;
- отсутствуют flaky-e2e (минимум 3 последовательных зеленых прогона e2e в CI);
- для каждого P0 acceptance есть соответствующий тест(ы).

---

## 4. Матрица тестов по требованиям

1. Unit:
- adapter normalization/retry/rate-limit
- OCR/entities extraction
- evidence construction
- graph payload mapping
- retrieval ranking + insufficiency policy

2. Integration:
- enqueue-only request creation
- worker pipeline execution
- partial source failure
- report generation with claim-evidence mappings
- rerun source from chat

3. E2E:
- полный пользовательский сценарий из ТЗ
- валидация citations в чате
- переходы monitor/report/history

---

## 5. Риски и mitigation

1. Риск: race conditions в worker claim.
- Mitigation: DB транзакции + row-level locking + tests с конкурентными воркерами.

2. Риск: нестабильный e2e.
- Mitigation: deterministic fixtures, явные wait conditions, data-testid.

3. Риск: ложные выводы в чате.
- Mitigation: строгий contract `citations or insufficiency` + unit/integration enforcement.

4. Риск: безопасность upload/form.
- Mitigation: CSRF + allowlist + limits + negative tests.

---

## 6. Release checklist

- [ ] Wave A complete + accepted
- [ ] Wave B complete + accepted
- [ ] Wave C complete + accepted
- [ ] Full tests green
- [ ] README/.env актуализированы
- [ ] Миграции backwards-safe
- [ ] Известные ограничения зафиксированы

