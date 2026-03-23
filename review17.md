# review17.md — Полноценное техническое ревью соответствия требованиям заказчика

Дата: 2026-03-23

## Краткий ответ на ключевой вопрос

**Будет ли сервис работать с реальными источниками прямо сейчас?**  
**Коротко: частично, но в текущем виде — скорее нет для production-эксплуатации.**

Почему:
1. Адаптеры имеют dual-mode (`fixture/http`), но фактическая реализация `http` пути слишком упрощена (ожидается прямой JSON-ответ от `base_url`, без устойчивого парсинга реальных HTML/сложных ответов и без per-source бизнес-логики).  
2. Нет завершённой стратегии обработки реальных ограничений источников (нестабильность, rate limits, ручные подтверждения, изменения верстки, антибот-механизмы — без обхода защит).  
3. Недостаточно production-grade observability и SLO-гейтов для адаптеров (нет зрелых метрик success/failure per source, деградаций, ретраев с классификацией причин).  
4. E2E и integration в основном fixture/test-mode; отсутствует гарантированный regression-suite именно для runtime HTTP интеграций с контролируемыми мок-серверами, близкими к реальным профилям ответов.

Итого: архитектурно путь к реальным источникам есть, но до «надежно работает с реальными источниками» не доведено.

---

## 1) Оценка соответствия требованиям заказчика

Обозначения: ✅ выполнено, ⚠️ частично, ❌ не выполнено.

## 1.1 Архитектура
- Монолит FastAPI + worker + PostgreSQL/pgvector + local storage + docker compose: ✅
- Отсутствие overengineering (Kafka/Celery/Neo4j/...): ✅
- Миграции/конфиги/README/скрипты: ✅

## 1.2 Бизнес-функции
- Форма запроса + загрузка файлов + выбор источников: ✅
- Мониторинг статусов near real-time (SSE): ✅
- История запросов + фильтрация: ✅
- Граф + чат поверх отчета: ⚠️ (базово есть, но explainability UX и retrieval глубина ограничены)
- Реран источников из отчета/чата: ⚠️ (есть базовый enqueue rerun, но lifecycle и аудит недостаточно зрелые)

## 1.3 Explainability и качество выводов
- Claim/evidence контракт введен: ✅
- Coverage quality gate в pipeline: ✅
- Строгий CI gate по coverage и chat policy: ⚠️ (нужен явный enforce в CI lane)

## 1.4 Безопасность
- Базовый CSRF/checks/upload limits/cookie settings: ⚠️
- Security baseline production-grade (без тестовых упрощений, полноценные negative-tests): ⚠️

## 1.5 Тестирование
- Unit/Integration/E2E контуры присутствуют: ✅
- Полноценный non-optional browser E2E в стабильной CI среде: ⚠️
- PostgreSQL-specific integration lock tests как обязательный gate: ⚠️

---

## 2) Почему сейчас сервис не готов к надежной работе с реальными источниками

## 2.1 Технические причины
1. **Adapter HTTP path слишком общий**  
   Реальные источники часто требуют:
   - многошаговые запросы,
   - HTML-парсинг с нестабильной версткой,
   - различные форматы ответов/кодировки,
   - нюансы pagination/filtering.

2. **Нет source-specific robustness-профиля**  
   Для каждого источника нужны свои:
   - retry/pacing policy,
   - parser contracts,
   - fallback path,
   - degradation messaging.

3. **Недостаточная наблюдаемость**  
   Нужны метрики и события: success-rate, timeout-rate, parse-failure-rate, latency percentiles, error taxonomy.

4. **Недостаточный runtime regression layer**  
   Нужен тестовый слой с HTTP mock servers, имитирующих реальные ответы источников (включая edge cases).

## 2.2 Операционные причины
1. Нет полноценного CI lane `integration-postgres + runtime-adapter mocks` как обязательного release gate.
2. Нет runbook для отказов источников и изменений их форматов.

## 2.3 Продуктовые причины
1. Недостаточно прозрачная UX-коммуникация «источник недоступен/нужна ручная проверка/данных недостаточно» по каждому источнику.
2. Не завершен UX rerun lifecycle (queued/running/done/error + история rerun).

---

## 3) Что нужно сделать, чтобы сервис стал работать с реальными источниками

## Этап A — Runtime adapters productionization (критично)
1. Для каждого источника реализовать **отдельный runtime adapter profile**:
   - request flow,
   - parser strategy,
   - schema mapping в `EvidenceRecord`,
   - edge-case handling.
2. Ввести строгую error taxonomy:
   - timeout,
   - unavailable,
   - parse_error,
   - rate_limited,
   - manual_required.
3. Добавить source-level SLO:
   - p95 latency,
   - success-rate,
   - parse validity.

## Этап B — Testing & CI hard gates (критично)
1. Обязательный CI lane: `integration-postgres` (lock semantics, job claim concurrency).
2. Обязательный CI lane: `adapter-runtime-mocks` (mock HTTP servers with realistic payloads).
3. Обязательный CI lane: `e2e-full` (browser flow, non-optional).
4. Явный quality gate:
   - claim coverage >=95%,
   - chat policy 100% (`citations` or `insufficient_data`).

## Этап C — Rerun lifecycle & UX transparency
1. Вести полный lifecycle `rerun_runs` (queued/running/done/error).
2. Показывать историю rerun в UI отчета с provenance.
3. Явно показывать ограничения по источникам в отчете/чате (что подтверждено, что не подтверждено).

## Этап D — Security & operations hardening
1. Production CSRF mode без тестовых shortcut в runtime.
2. upload security policy + content validation + retention policy.
3. Метрики/алерты и runbook для деградаций источников.

---

## 4) Детальный план устранения недостатков (commit-by-commit)

## Commit 1 — `feat(adapters): source-specific runtime profiles`
- Реализовать per-source parsing/request strategy.
- Добавить typed normalizers + parse validators.

## Commit 2 — `feat(observability): source metrics and error taxonomy`
- Добавить structured fields в events/logs.
- Добавить метрики per source run.

## Commit 3 — `test(integration): postgres lock + runtime adapter mocks`
- Обязательные integration кейсы для concurrency + parse failures.

## Commit 4 — `test(e2e): enforce full browser flow`
- Включить non-optional e2e lane.

## Commit 5 — `feat(rerun): lifecycle + report visibility`
- Обновление статусов rerun в worker.
- UI блок истории rerun.

## Commit 6 — `sec(hardening): strict csrf/upload/cookie policies`
- Закрыть security baseline и negative tests.

## Commit 7 — `docs(runbook): runtime ops & incident handling`
- Runbook/rollback/playbook для источников.

---

## 5) Рекомендованные release gates

Релиз принимается только если:
1. Unit + integration + e2e-full green.
2. `integration-postgres` green.
3. `adapter-runtime-mocks` green.
4. claim coverage >=95% enforced.
5. chat policy gate enforced.
6. security negative-tests green.

---

## 6) Финальный вывод

Проект уже близок к функциональному MVP и имеет правильную архитектурную основу.  
Но для реальной работы с внешними источниками в production нужно завершить productionization адаптеров, усилить тестовые и операционные гейты, а также довести прозрачность rerun/explainability/security до уровня обязательных требований заказчика.
