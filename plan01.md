# plan01.md — Готовый к кодингу patch-list (commit-by-commit)

Цель: довести текущий прототип до MVP, который проходит требования заказчика из ТЗ и замечания из `review01.md`.

Ниже — последовательность коммитов в формате «что меняем / где меняем / критерии готовности / тесты».

---

## Commit 1 — `refactor(queue): move pipeline execution to worker-only job orchestration`

### Что делаем
1. Убираем синхронный запуск `process_request(...)` из HTTP `POST /requests`.
2. Добавляем явную модель job-очереди (минимально: новая таблица `jobs`), либо безопасный claim через `requests` + lock-поля.
3. Реализуем атомарный claim в worker (PostgreSQL-совместимо): `FOR UPDATE SKIP LOCKED`.
4. API при создании заявки только:
   - создаёт `request`;
   - создаёт `job` со статусом `queued`;
   - пишет `PipelineEvent(created)`;
   - делает быстрый redirect на monitor.
5. Worker:
   - берёт queued job;
   - переводит в `running`;
   - запускает `process_request`;
   - выставляет `done/failed`, пишет финальные события.

### Файлы
- `app/main.py`
- `app/worker/run.py`
- `app/services/pipeline.py`
- `app/models/models.py` (новая сущность `Job`)
- `alembic/versions/*` (миграция под job-таблицу/индексы)

### DoD
- Создание заявки всегда отвечает быстро (без долгого блокирующего запроса).
- Мониторинг реально показывает прогресс, пока worker обрабатывает.
- При падении pipeline request/job корректно переходят в failed.

### Тесты
- integration: verify async behavior (status remains `created/processing` сразу после submit).
- integration: worker picks queued job and finishes report.

---

## Commit 2 — `feat(adapters): add runtime httpx path with retries, rate-limit and safe technical logging`

### Что делаем
1. В `BaseSourceAdapter` добавляем:
   - `httpx.Client`/`AsyncClient` с timeout;
   - retry/backoff policy (без внешней тяжёлой инфраструктуры);
   - простой rate limiter per adapter/source;
   - structured технический лог request/response meta (без утечки PII).
2. Для `FnsRegistryAdapter`, `SudrfAdapter`, `MvdWantedAdapter`:
   - оставляем fixture mode для тестов;
   - добавляем runtime http-path (через `base_url` из `sources.yml`);
   - нормализуем в единый `EvidenceRecord`.
3. Ошибки источников маппим в статусы `source_runs` (`ok/error/unavailable/manual_required`).

### Файлы
- `app/services/adapters/base.py`
- `app/services/adapters/fns.py`
- `app/services/adapters/sudrf.py`
- `app/services/adapters/mvd.py`
- `app/services/pipeline.py`
- `app/core/logging.py`
- `config/sources.yml` (добавить optional поля для transport mode)

### DoD
- В runtime адаптеры могут ходить в HTTP (без обхода капчи/защит).
- В test mode всё полностью оффлайн на фикстурах.
- При недоступном источнике отчёт/мониторинг показывают корректный статус и ограничение.

### Тесты
- unit: retries/rate-limit/normalization.
- integration: partial failure (1 источник упал, pipeline завершился с warnings).

---

## Commit 3 — `feat(ai-providers): wire OpenAI-compatible clients for llm/vision/embeddings with configurable fallback`

### Что делаем
1. Заменяем чистые stubs на provider abstraction с двумя режимами:
   - `mock` (tests/dev offline);
   - `openai_compatible` (runtime).
2. Используем env:
   - `LLM_BASE_URL`, `LLM_MODEL`
   - `VISION_BASE_URL`, `VISION_MODEL`
   - `EMBEDDING_BASE_URL`, `EMBEDDING_MODEL`
   - `API_KEY=sk-111`
   - timeout/retries.
3. Для vision extraction добавляем единый контракт результата: `raw_text`, `entities`, `confidence`, `provider_meta`.

### Файлы
- `app/services/ai.py`
- `app/core/config.py`
- `.env.example`
- `README.md`
- `tests/mocks/*` (новые mock providers)

### DoD
- Переключение mock/runtime — только конфигом.
- Никакой внешний вызов в тестах.

### Тесты
- unit: provider selection by config.
- integration: pipeline with mock providers end-to-end.

---

## Commit 4 — `feat(report): implement explainable report schema with claim->evidence mapping`

### Что делаем
1. Перестраиваем генерацию отчёта по обязательной структуре ТЗ:
   - краткое резюме;
   - входные данные;
   - совпадения по источникам;
   - ключевые факты;
   - связи;
   - риски/красные флаги;
   - обоснование выводов;
   - ограничения/неопределённости;
   - перечень источников;
   - таймлайн выполнения.
2. Формализуем explainability:
   - отдельная структура `claims` с обязательными `evidence_ids[]`;
   - отображение в UI «каждое утверждение -> доказательства».
3. Добавляем provenance стандартизированно (`source_id`, `url_or_record_id`, `acquired_at`, `raw_fragment`, `normalized_fragment`, `confidence`).

### Файлы
- `app/services/pipeline.py`
- `app/models/models.py` (при необходимости json-поля report sections/claims)
- `app/templates/report.html`
- `app/services/chat.py` (использование claims в retrieval)

### DoD
- В отчёте нет «висящих» ключевых утверждений без evidence.
- Пользователь может увидеть обоснование каждого вывода.

### Тесты
- unit: report claim-evidence mapper.
- integration: generated report contains required sections + non-empty mappings.

---

## Commit 5 — `feat(graph): enrich graph interactions with evidence panel and report linkage`

### Что делаем
1. Расширяем payload узлов/ребер:
   - `type`, `label`, `description`, `evidence_ids[]`, `source_refs[]`.
2. На UI отчёта:
   - click node/edge -> правая панель деталей;
   - показываем связанные фрагменты отчёта и доказательства.
3. Добавляем связь «элемент графа -> claim IDs».

### Файлы
- `app/services/graph.py`
- `app/templates/report.html`
- `app/static/style.css`

### DoD
- Клик по графу раскрывает доказательную базу и связанный текст отчёта.

### Тесты
- unit: graph payload includes evidence/claim references.
- e2e: click graph element shows details panel.

---

## Commit 6 — `feat(chat-rag): implement deterministic retrieval layer with citations and insufficiency policy`

### Что делаем
1. Выделяем retrieval слой:
   - индексируем report sections + evidence + entities + relations;
   - добавляем ranking (простая lexical + optional embedding similarity через pgvector).
2. Чат-ответ в структурированном формате:
   - `answer`
   - `citations[]` (evidence_id/source/url)
   - `insufficient_data`
   - `suggested_reruns[]`
3. Политика anti-hallucination:
   - нет подтверждений => явный отказ + предложение дозапуска источников.
4. Кнопка из чата: «дозапустить выбранные источники».

### Файлы
- `app/services/chat.py`
- `app/main.py` (endpoint rerun)
- `app/templates/report.html`
- `app/models/models.py` (если нужен rerun event entity)

### DoD
- Каждый содержательный ответ имеет citations либо честный insufficient_data.
- Дозапуск источников работает из UI.

### Тесты
- unit: retrieval ranking + insufficient policy.
- integration: rerun from chat creates new source runs and updates report.

---

## Commit 7 — `feat(security): harden session auth and upload validation for MVP`

### Что делаем
1. Включаем безопасные cookie-параметры (`HttpOnly`, `SameSite`, `Secure` configurable).
2. Добавляем CSRF защиту для form POST (минимальный server-side token pattern).
3. Ограничиваем upload:
   - max size;
   - content-type allowlist;
   - безопасные имена файлов.
4. Маскирование чувствительных данных в логах.

### Файлы
- `app/main.py`
- `app/api/deps.py`
- `app/core/config.py`
- `app/services/pipeline.py`

### DoD
- Базовые web security требования соблюдены для MVP.

### Тесты
- unit/integration: csrf fail/pass, invalid file type/size rejected.

---

## Commit 8 — `test(e2e): replace playwright smoke with full end-to-end scenario`

### Что делаем
1. Пишем полноценный e2e Playwright сценарий:
   - login;
   - заполнение формы;
   - выбор источников;
   - загрузка файла;
   - запуск проверки;
   - мониторинг статусов;
   - переход в справку;
   - проверка графа;
   - вопрос в чат и проверка citations.
2. Добавляем стабильные test hooks/селекторы в шаблоны (`data-testid`).

### Файлы
- `tests/e2e/test_ui_playwright.py`
- `app/templates/*.html` (test hooks)
- `scripts/run_tests.sh`

### DoD
- E2E покрывает весь заявленный user flow.

### Тесты
- `pytest tests/e2e -m e2e` проходит оффлайн на mock mode.

---

## Commit 9 — `test(integration): add failure-mode coverage and deterministic fixtures`

### Что делаем
1. Добавляем интеграционные кейсы:
   - source timeout/unavailable;
   - partial source success;
   - empty OCR extraction;
   - LLM provider fallback.
2. Укрепляем deterministic fixtures/mocks.

### Файлы
- `tests/integration/*`
- `tests/fixtures/*`
- `tests/mocks/*`

### DoD
- Негативные сценарии гарантированно покрыты.

---

## Commit 10 — `docs(ops): update README/runbook/env for production-like MVP usage`

### Что делаем
1. Обновляем `README.md`:
   - точные команды запуска app/worker/db;
   - миграции;
   - создание пользователя;
   - режимы mock/runtime;
   - legal/ethical ограничения адаптеров.
2. Обновляем `.env.example` (все provider vars + security vars + limits).
3. Добавляем раздел «Known limitations / next steps to production».

### Файлы
- `README.md`
- `.env.example`
- `docker-compose.yml` (если нужно healthcheck/depends_on conditions)

### DoD
- Документация соответствует фактическому поведению системы.

---

## ФИНАЛЬНЫЙ CHECKLIST перед merge

- [ ] `docker compose up --build` поднимает app/worker/db без ручных правок.
- [ ] `alembic upgrade head` выполняется чисто.
- [ ] Полный suite: `scripts/run_tests.sh` зелёный.
- [ ] E2E проходит end-to-end сценарий из ТЗ.
- [ ] В отчёте каждый ключевой claim имеет `evidence_ids`.
- [ ] В чате каждый ответ содержит citations или `insufficient_data=true`.
- [ ] Мониторинг показывает прогресс реально во время работы worker.

