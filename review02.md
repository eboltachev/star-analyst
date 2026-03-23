# review02.md — Техническое ревью #2 (с учётом `review01.md`, `plan01.md` и требований заказчика)

Дата: 2026-03-22  
Контекст: повторное ревью текущего состояния репозитория и ранее предложенных планов исправления.

---

## 1) Executive summary

`review01.md` корректно выявил основные разрывы, а `plan01.md` дал рабочий commit-by-commit маршрут.  
Текущее состояние всё ещё соответствует **прототипу/каркасу**, а не полностью приемочному MVP по ТЗ.

### Главный вывод
Для прохождения приемки требуется реализовать минимум:
1. **Worker-only orchestration** (убрать синхронный pipeline из web request).  
2. **Runtime-контур адаптеров** (httpx + retries + rate-limit + safe technical logs).  
3. **Explainable-report + chat citations** (claim->evidence и честная политика insufficiency).  
4. **Полноценный Playwright e2e** (вместо smoke-check).

Без этих четырёх блоков продукт не соответствует обязательным требованиям заказчика.

---

## 2) Оценка качества `review01.md`

## Сильные стороны
- Правильно выделены P0-риски: синхронная оркестрация, недореализованные адаптеры, неполный e2e, слабая explainability/anti-hallucination дисциплина.
- Есть приоритизация (P0/P1/P2), что полезно для triage и планирования спринта.
- Даны предметные рекомендации (claim/evidence mapping, rerun из чата, улучшение graph UX).

## Что можно улучшить в `review01.md`
1. Добавить **измеримые acceptance metrics** (SLO/SLI):
   - latency submit endpoint (p95),
   - время до первого event в мониторинге,
   - доля ответов чата с citations,
   - доля report-claims с evidence.
2. Разделить риски на **product risk vs technical risk vs legal/compliance risk**.
3. Добавить минимальный **rollback strategy** для изменений очереди/job-оркестрации.

Вывод: `review01.md` пригоден как база, но для execution tracking лучше добавить measurable KPI и risk register.

---

## 3) Оценка качества `plan01.md`

## Сильные стороны
- План практически ready-to-implement: по каждому коммиту есть scope, файлы, DoD, тесты.
- Правильно выбран порядок: сначала архитектурный P0 (job orchestration), затем adapters/providers/report/chat/e2e.
- В конце есть финальный checklist для merge gate.

## Что стоит уточнить до старта кодинга
1. **Schema strategy**: явно зафиксировать, где используется новая таблица `jobs`, а где переиспользуются статусы `requests`.
2. **Concurrency model**: ограничение числа воркеров, дедупликация одинаковых jobs, idempotency key.
3. **Migration safety**:
   - backward-compatible этап для existing rows,
   - индексы под frequent queries (`jobs(status, created_at)`, `pipeline_events(request_id, id)`).
4. **Observability baseline**:
   - единый correlation id (`request_id`, `job_id`) в логах и событиях.
5. **E2E stability**:
   - test ids в шаблонах,
   - deterministic fixtures и clock/timer controls.

Вывод: `plan01.md` хороший практический план; перед реализацией добавить 1-page ADR по очереди/jobs и observability conventions.

---

## 4) Повторная матрица соответствия ТЗ (текущее состояние)

Обозначения: ✅ выполнено, ⚠️ частично, ❌ не выполнено.

### 4.1 Функциональный слой
1. Форма нового запроса с нужными полями и файлами — ✅  
2. Источники из конфигурации (`sources.yml`) — ✅  
3. OCR/интеллектуальный парсинг вложений + отображение результатов пользователю — ⚠️  
4. Мониторинг в near real-time — ⚠️ (SSE есть, но оркестрация синхронная)  
5. Адаптерный слой с runtime HTTP + retries/rate-limit/logging — ❌  
6. Нормализованная модель данных — ✅  
7. Explainable аналитическая справка (полная структура + evidence-backed claims) — ⚠️  
8. Интерактивный граф с доказательной детализацией — ⚠️  
9. Чат по локальному контексту с RAG и citations — ⚠️  
10. Реран источников из чата — ❌  
11. История запросов с фильтрацией/поиском — ✅

### 4.2 Нефункциональный слой
1. Минимальная архитектура без overengineering — ✅  
2. Docker compose + миграции + env пример + README — ✅  
3. Structured logging — ⚠️ (нужно унифицировать schema и redaction policy)  
4. Ошибки/UX сообщения — ⚠️  
5. Безопасность (cookie flags, CSRF, upload constraints) — ⚠️  
6. Тесты unit/integration/e2e по полному сценарию — ⚠️ (e2e пока smoke)

---

## 5) Приоритетные предложения (обновлённо)

## P0 (блокеры приёмки)
1. **Развязать API и pipeline**: только enqueue в API, исполнение исключительно в worker.
2. **Довести adapters до runtime-ready**: httpx path + retries + timeout + rate-limit + status mapping.
3. **Ввести explainability contract**:
   - report claims обязаны иметь `evidence_ids`,
   - chat response обязан иметь citations или `insufficient_data=true`.
4. **Заменить e2e smoke на реальный flow** по ТЗ.

## P1 (высокая ценность)
1. Graph detail panel с evidence snippets и связью на claims.
2. UI секция extracted artifacts до/после поиска.
3. Rerun конкретных источников из отчёта/чата.
4. Security baseline (CSRF + upload policy + cookie hardening).

## P2 (укрепление эксплуатации)
1. Метрики и алерты (pipeline durations, source error rates, chat citation ratio).
2. Pagination/FTS улучшения истории.
3. Data retention + cleanup jobs для storage/artifacts.

---

## 6) Рекомендуемый execution-порядок (на базе `plan01.md`)

1. Commit 1 + Commit 2 из `plan01.md` (очередь/воркер + runtime adapters).  
2. Commit 4 + Commit 6 (explainable report + chat retrieval/citations).  
3. Commit 8 (полный Playwright e2e).  
4. Остальные security/graph/docs commits как hardening.

Это самый короткий путь к прохождению приемки по ТЗ с минимальным риском регрессий.

---

## 7) Конкретные критерии приёмки (предлагаемые)

Считать MVP принятым, если одновременно выполнены условия:

1. Submit API отвечает < 500ms p95 при enqueue-only модели.  
2. Мониторинг показывает первый pipeline event < 2s после submit при работающем worker.  
3. Минимум 95% ключевых claim в отчёте имеют `>=1 evidence_id`.  
4. 100% ответов чата содержат либо citations, либо явный insufficiency flag.  
5. Полный e2e Playwright сценарий стабильно проходит в CI на mock mode.  
6. При падении одного источника pipeline завершает запрос с частичным результатом и явным ограничением в отчёте.

---

## 8) Итог

- `review01.md` — корректная диагностика.
- `plan01.md` — практически готовый roadmap к реализации.
- Для выхода на «приемочный MVP» нужно сфокусироваться на 4 блокерах: worker-orchestration, runtime adapters, explainable report/chat, полноценный e2e.

После закрытия этих блоков и прохождения критериев раздела 7 решение можно считать соответствующим ТЗ MVP.
