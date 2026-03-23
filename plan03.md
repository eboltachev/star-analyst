# plan03.md — Delivery plan #3 (execution-first, from blueprint to accepted MVP)

Дата: 2026-03-22  
Основание: `review03.md`, `plan02.md`, требования заказчика.

## Цель
Перевести проект из состояния «документированного прототипа» в состояние «приемочный MVP» с доказуемым соответствием ТЗ и проверяемыми метриками.

---

## 1) Стратегия исполнения

- Работать короткими milestone-PR (не смешивать несколько P0-блоков в один PR).
- Каждый milestone закрывается только при прохождении конкретного acceptance gate.
- Сначала P0 (архитектура исполнения + достоверность результатов), затем P1/P2 (UX/security/ops hardening).

---

## 2) Milestone M1 — Queue/Worker-first orchestration (P0)

### Scope
1. Добавить `jobs` таблицу и модель (`queued|running|done|failed`, attempt/retry metadata).
2. `POST /requests` делает только enqueue + initial event.
3. Worker забирает jobs атомарно (`FOR UPDATE SKIP LOCKED`) и исполняет pipeline.
4. Добавить dead-letter semantics (max attempts, final failure reason).

### Deliverables
- migration + ORM model + worker claim logic
- status transition диаграмма в README

### Acceptance gate
- submit p95 < 500ms
- first pipeline event < 2s
- failed jobs наблюдаемы в БД и UI

### Tests
- integration: enqueue-only behavior
- integration: worker claim and run
- integration: retry then dead-letter

---

## 3) Milestone M2 — Runtime source adapters (P0)

### Scope
1. Вынести transport в base adapter:
   - httpx timeout/retry/backoff
   - rate limiting
   - structured safe logs (PII redaction)
2. Реализовать dual-mode adapters (`fixture`/`http`) через конфиг.
3. Унифицировать error taxonomy:
   - `timeout`, `unavailable`, `manual_required`, `validation_error`.
4. partial-failure режим: pipeline продолжает работу, отчёт содержит ограничения.

### Deliverables
- adapter runtime path
- source run status mapping
- ограничения по источникам в отчёте

### Acceptance gate
- pipeline не падает полностью при недоступности одного источника
- source limitation section присутствует в отчёте

### Tests
- unit: retries/rate limit/error mapping
- integration: 1-of-N source failure

---

## 4) Milestone M3 — Explainable report contract (P0)

### Scope
1. Ввести версионированный контракт `report_claims_v1`:
   - `claim_id`, `text`, `evidence_ids[]`, `confidence`, `source_refs[]`.
2. Доработать структуру отчёта под ТЗ:
   - summary/input/per-source/key-facts/relations/risks/rationale/limits/sources/timeline.
3. UI: блок «утверждение → доказательства».

### Deliverables
- schema + validator
- report renderer with mandatory sections

### Acceptance gate
- >=95% claims имеют >=1 evidence_id
- нет section-level пустых обоснований при наличии выводов

### Tests
- unit: claim schema validator
- integration: full report completeness

---

## 5) Milestone M4 — Chat RAG contract + rerun (P0)

### Scope
1. Ввести `chat_answer_v1`:
   - `answer`, `citations[]`, `insufficient_data`, `suggested_reruns[]`.
2. Retrieval layer по локальному контексту:
   - report claims
   - evidence
   - entities/relations
   - extracted artifacts
3. Кнопка rerun источников из чата/отчёта.

### Deliverables
- chat contract + retrieval service
- rerun endpoint + UI action

### Acceptance gate
- 100% ответов: citations или insufficient_data=true
- rerun создаёт source runs и обновляет отчёт

### Tests
- unit: retrieval ranking/empty-context behavior
- integration: chat rerun flow

---

## 6) Milestone M5 — Full e2e scenario (P0)

### Scope
Полный Playwright flow:
1. login
2. create request
3. select sources
4. upload file
5. monitor progress
6. open report
7. inspect graph details
8. ask chat + verify citations
9. open history + find request

### Deliverables
- stable selectors (`data-testid`)
- deterministic e2e fixtures

### Acceptance gate
- `pytest tests/e2e -m e2e` стабильно green в CI

---

## 7) Milestone M6 — Security baseline (P1)

### Scope
1. CSRF protection for POST forms
2. secure cookie flags
3. upload controls (MIME allowlist, max size, filename sanitization)
4. log redaction policy

### Acceptance gate
- negative security tests pass

### Tests
- integration: csrf fail/pass
- integration: invalid upload rejected

---

## 8) Milestone M7 — Graph evidence UX (P1)

### Scope
1. Graph nodes/edges enriched with evidence & claim links
2. side panel details on click
3. deep-links from graph to report claims

### Acceptance gate
- graph click always exposes evidence-backed details

### Tests
- unit: graph payload mapping
- e2e: graph detail panel assertions

---

## 9) Milestone M8 — Docs/ops finalization (P1)

### Scope
1. README runbook (dev + docker + migration + troubleshooting)
2. `.env.example` complete vars for runtime/security limits
3. rollout/rollback notes for queue and schema changes

### Acceptance gate
- clean bootstrap by new engineer from README only

---

## 10) Ownership & timeline template (заполнить перед стартом)

| Milestone | Owner | ETA | Risk | Status |
|---|---|---|---|---|
| M1 | TBD | TBD | High | Planned |
| M2 | TBD | TBD | High | Planned |
| M3 | TBD | TBD | High | Planned |
| M4 | TBD | TBD | High | Planned |
| M5 | TBD | TBD | Medium | Planned |
| M6 | TBD | TBD | Medium | Planned |
| M7 | TBD | TBD | Medium | Planned |
| M8 | TBD | TBD | Low | Planned |

---

## 11) Unified acceptance gates (final)

Релиз MVP допускается только если одновременно:

1. Performance gate:
   - submit p95 < 500ms
   - first monitor event < 2s
2. Reliability gate:
   - partial source failure handled
   - retry/dead-letter policies verified
3. Explainability gate:
   - >=95% report claims mapped to evidence
   - chat: 100% citations or insufficiency
4. E2E gate:
   - full playwright scenario green
5. Security gate:
   - CSRF + upload + cookie controls verified

---

## 12) Команды контроля качества

```bash
alembic upgrade head
pytest tests/unit
pytest tests/integration
pytest tests/e2e -m e2e
scripts/run_tests.sh
docker compose up --build
```

---

## 13) Definition of Done for MVP release

- [ ] M1..M5 выполнены и приняты (все P0 закрыты)
- [ ] Explainability и chat citation policies соблюдаются
- [ ] Полный e2e сценарий стабилен
- [ ] Security baseline реализован
- [ ] README/.env/ops-документация актуальны
