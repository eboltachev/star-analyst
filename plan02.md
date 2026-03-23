# plan02.md — Реализация (execution plan) по итогам review02

Цель: перевести текущий прототип в приемочный MVP по ТЗ.  
Подход: incremental delivery с чёткими milestone, критериями готовности и командой запуска проверок.

---

## 0) Scope и принципы

- Без overengineering: монолит FastAPI + один worker + PostgreSQL/pgvector + local volume.
- Все внешние интеграции (источники/LLM/VLM/embeddings) через конфиг и provider abstraction.
- Тесты полностью оффлайн в CI (fixtures/mocks), без реальных сайтов/моделей.
- Каждое значимое утверждение отчёта и чат-ответ должно быть evidence-backed.

---

## 1) Milestone A — Оркестрация и pipeline execution model (P0)

## A1. Job queue и worker-only исполнение

### Изменения
1. Ввод таблицы `jobs`:
   - `id`, `request_id`, `status` (`queued|running|done|failed`),
   - `attempt`, `priority`, `locked_at`, `locked_by`, `error`, timestamps.
2. Endpoint `POST /requests`:
   - создаёт request,
   - создаёт job (`queued`),
   - пишет `pipeline_event(created)`.
   - **не** запускает `process_request`.
3. Worker loop:
   - claim через `FOR UPDATE SKIP LOCKED`;
   - status transitions queued→running→done/failed;
   - retry policy по `attempt`.

### Acceptance
- Submit endpoint p95 < 500ms.
- Первый event в monitor < 2s после submit (при живом worker).

### Тесты
- integration: submit does not block.
- integration: worker picks queued job and completes pipeline.
- integration: job failure writes failed status + error message.

---

## 2) Milestone B — Runtime adapters (P0)

## B1. Единый transport слой адаптера

### Изменения
1. `BaseSourceAdapter` получает:
   - httpx client config (timeout/retries/backoff),
   - rate limiting,
   - safe logging (mask PII in logs).
2. Для `FnsRegistryAdapter|SudrfAdapter|MvdWantedAdapter`:
   - dual-mode `fixture|http`;
   - нормализация в единый `EvidenceRecord`.
3. Pipeline обрабатывает частичные ошибки источников:
   - `source_runs.status`: `ok|error|unavailable|manual_required`;
   - report включает ограничения по источникам.

### Acceptance
- При падении 1 источника pipeline не падает целиком.
- В отчёте есть секция ограничений и явно указан недоступный источник.

### Тесты
- unit: retry/backoff/rate-limit behavior.
- integration: partial source failure scenario.

---

## 3) Milestone C — Explainable report (P0)

## C1. Структурированный report contract

### Изменения
1. Генератор отчёта формирует обязательные секции:
   - summary, input data, per-source matches,
   - key facts, relations, risks,
   - rationale, limitations, sources list, timeline.
2. Ввести contract:
   - `claims[]` с `claim_id`, `text`, `evidence_ids[]`, `confidence`.
3. UI отчёта:
   - claim карточки с evidence links.

### Acceptance
- >=95% ключевых claims имеют `>=1 evidence_id`.
- Нет выводов без provenance.

### Тесты
- unit: claim-evidence validator.
- integration: report sections completeness.

---

## 4) Milestone D — Chat RAG + citations + rerun (P0/P1)

## D1. Retrieval layer

### Изменения
1. Индексируем локальный контекст:
   - report claims/sections,
   - evidence items,
   - entities/relations,
   - extracted artifacts.
2. Retrieval/ranking:
   - lexical baseline + optional embedding similarity.
3. Chat response schema:
   - `answer`, `citations[]`, `insufficient_data`, `suggested_reruns[]`.
4. Из чата и отчёта добавить кнопку rerun выбранных источников.

### Acceptance
- 100% ответов чата: citations либо insufficient_data=true.
- rerun создаёт новый source run и обновляет отчёт.

### Тесты
- unit: retrieval ranking + insufficiency path.
- integration: rerun from chat end-to-end.

---

## 5) Milestone E — Graph UX (P1)

## E1. Интерактивная детализация

### Изменения
1. Graph payload расширить:
   - node/edge type, description, evidence_ids, claim_ids.
2. По клику на node/edge:
   - detail panel с evidence snippets,
   - ссылки на связанные claim/report fragment.

### Acceptance
- Любой элемент графа раскрывает доказательную базу.

### Тесты
- unit: graph payload mapping.
- e2e: click graph element shows linked evidence.

---

## 6) Milestone F — Security & hardening (P1)

## F1. Web security minimum

### Изменения
1. Cookie hardening (`HttpOnly`, `SameSite`, `Secure` via env).
2. CSRF token для form POST.
3. Upload policy:
   - allowlist MIME,
   - size limit,
   - filename sanitization.
4. PII masking in technical logs.

### Acceptance
- Невалидные upload/CSRF корректно отклоняются.

### Тесты
- unit/integration: csrf and upload validation.

---

## 7) Milestone G — Полный E2E (P0)

## G1. Реальный Playwright сценарий

### Сценарий
1. login
2. fill new request form
3. select sources
4. upload attachment
5. start check
6. see monitor updates
7. open report
8. interact with graph
9. ask chat question and validate citations
10. open history and find created request

### Acceptance
- Стабильно проходит в CI на mock mode.

---

## 8) Milestone H — Docs/ops completeness (P1)

## H1. Runtime docs

### Изменения
1. README:
   - app/worker/db run commands,
   - migration workflow,
   - mock/runtime modes,
   - legal constraints for adapters,
   - troubleshooting.
2. `.env.example`:
   - provider vars, timeout/retries,
   - security/upload limits,
   - worker polling/retry settings.

### Acceptance
- Новый инженер поднимает проект по README без ручных допущений.

---

## 9) Dependency graph (порядок реализации)

1. A (queue) → 2. B (adapters) → 3. C (report contract) → 4. D (chat/rerun) → 5. G (e2e)
6. E (graph UX), F (security), H (docs) — можно параллелить после A/B.

---

## 10) Команды валидации на каждом этапе

```bash
# базово
alembic upgrade head
pytest tests/unit
pytest tests/integration
pytest tests/e2e -m e2e
scripts/run_tests.sh

# локально с сервисами
docker compose up --build
```

---

## 11) Definition of Done (финальный)

- [ ] API create-request enqueue-only (без синхронного pipeline).
- [ ] Worker стабильно обрабатывает jobs, включая failure + retry.
- [ ] Runtime adapters поддерживают http mode + safe logging + graceful degradation.
- [ ] Report полностью соответствует структуре ТЗ и evidence-backed.
- [ ] Chat возвращает citations либо insufficiency flag, rerun работает.
- [ ] Graph интерактивно связан с claims/evidence.
- [ ] Полный Playwright e2e проходит в CI.
- [ ] README/.env полностью актуальны.

