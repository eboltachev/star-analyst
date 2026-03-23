# review13.md — Полное техническое ревью соответствия требованиям заказчика

Дата: 2026-03-23  
Объект ревью: текущее состояние репозитория после итераций `review01..review12`.

---

## 1. Executive summary

Проект достиг уровня **рабочего MVP-скелета** с корректным направлением архитектуры (монолит + worker + PostgreSQL/pgvector + SSR UI), enqueue-only submit, базовой queue-моделью, отчётом, графом и чатом.  
Однако для полного соответствия исходному ТЗ заказчика текущая реализация всё ещё имеет ряд **критичных/существенных разрывов**.

### Итого по зрелости
- Архитектура: **хорошо (B+)**
- Функциональная полнота: **частично (C+)**
- Explainability/доказуемость: **частично (C+)**
- Тестовая полнота по ТЗ: **частично (C)**
- Production readiness: **низкая/средняя (C-)**

---

## 2. Соответствие требованиям заказчика (детальная матрица)

Обозначения: ✅ выполнено, ⚠️ частично, ❌ не выполнено.

## 2.1 Архитектура и инфраструктура

1. Один Python-репозиторий, backend-монолит, worker, PostgreSQL + pgvector, local volume, docker compose  
**Статус:** ✅

2. Нет overengineering (Kafka/Celery/Neo4j/OpenSearch/отдельный SPA-build pipeline)  
**Статус:** ✅

3. Наличие Dockerfile / compose / env / README / migrations / tests  
**Статус:** ✅

4. Готовность к замене mock-провайдеров на реальные endpoint'ы  
**Статус:** ⚠️ (абстракции есть, но runtime-интеграции и контроль качества ответа пока упрощены)

## 2.2 Функциональные требования

1. Форма нового запроса (ФИО, дата рождения, ИНН, комментарий, источники, файлы)  
**Статус:** ✅

2. Конфигурируемые источники + дефолтные ФНС / sudrf / МВД  
**Статус:** ✅

3. Обработка вложений (OCR + выделение сущностей + показ пользователю)  
**Статус:** ⚠️  
Комментарий: extraction есть, но multimodal runtime и богатый UI показа промежуточных extraction-результатов неполные.

4. Мониторинг near real-time (SSE/WebSocket)  
**Статус:** ✅ (SSE + enqueue/worker path реализованы)

5. Адаптеры: единый интерфейс, timeouts/retries/rate-limit, законное поведение при недоступности  
**Статус:** ⚠️  
Комментарий: технический baseline есть, но необходима более строгая error taxonomy + устойчивые runtime сценарии и интеграционные тесты на реальные transport-failure классы.

6. Нормализованная модель данных по сущностям ТЗ  
**Статус:** ✅

7. Аналитическая справка в полной структуре ТЗ и доказуемость каждого ключевого вывода  
**Статус:** ⚠️  
Комментарий: claims введены, но coverage gate и формальная проверка на уровне CI/DB-инвариантов ещё не доведены до целевого уровня.

8. Интерактивный граф связей с доказательствами по клику  
**Статус:** ⚠️  
Комментарий: базовая визуализация есть, UX-детализация с панелью доказательств и deep-links ещё неполная.

9. Чат по отчёту с RAG, citations и честным insufficiency  
**Статус:** ⚠️  
Комментарий: контракт ответа добавлен, но полноценный retrieval-ranking и строгие CI-гейты качества ответов ещё не завершены.

10. Дозапуск источников из чата/отчёта  
**Статус:** ❌ (пока suggestion-only / не end-to-end flow)

11. История запросов + поиск/фильтрация  
**Статус:** ✅

12. Простая аутентификация (login/logout, cookie session)  
**Статус:** ✅

## 2.3 Тестирование

1. Unit coverage ключевых блоков  
**Статус:** ⚠️ (есть база, но coverage policy для explainability и runtime adapters нужна строже)

2. Integration coverage pipeline + worker + partial failure + concurrency  
**Статус:** ⚠️ (есть прогресс, но требуется PostgreSQL-ориентированный integration run)

3. E2E Playwright полный пользовательский сценарий  
**Статус:** ⚠️  
Комментарий: сценарий добавлен, но gated через env-флаг и не является обязательным CI gate по умолчанию.

---

## 3. Ключевые недостатки (приоритеты)

## P0 (блокеры приемки)
1. Нет обязательного CI-гейта на full e2e flow (RUN_FULL_E2E=1 пока опционален).
2. Нет строгого quality gate на claim coverage (`>=95%`) на уровне тестов/CI.
3. Нет PostgreSQL-focused integration suite для проверки `skip_locked` под реальной lock-семантикой.

## P1 (высокий приоритет)
1. Chat rerun workflow не завершён (API+UI end-to-end).
2. Security baseline не завершён полностью (CSRF/upload limits/cookie hardening defaults).
3. Graph explainability UX (click details + snippets + deep-links) неполный.

## P2 (желательно)
1. Формализовать метрики качества pipeline/chat/report и алертинг.
2. Улучшить эксплуатационную документацию (runbook failure modes, incident playbook).

---

## 4. Предложения по устранению недостатков

## Этап A (P0 hard gates)
1. Ввести обязательную CI-job `e2e-full` с `RUN_FULL_E2E=1`.
2. Добавить CI-job `integration-postgres` с dockerized PostgreSQL и тестами конкурентного claim.
3. Добавить тест-гейт `claim_coverage_test` (assert >=95% claims with evidence).

## Этап B (P1 функциональная полнота)
1. Реализовать полноценный rerun workflow (chat/report -> выбрать источники -> enqueue rerun -> monitor -> обновлённый report).
2. Закрыть security baseline:
   - CSRF токены,
   - upload MIME/size limits,
   - secure cookie defaults.
3. Доработать graph detail panel с доказательствами и report-anchors.

## Этап C (качество эксплуатации)
1. Метрики (latency, retries, source error rates, chat citation ratio).
2. Документация rollback/incident playbook.
3. Контроль миграционной совместимости на long-lived окружениях.

---

## 5. Рекомендуемые критерии приемки (release gates)

Релиз принимается только если все пункты зелёные:

1. `scripts/run_tests.sh` green.
2. `e2e-full` green (не опционально).
3. `integration-postgres` green с concurrency assertions.
4. claim coverage gate >=95%.
5. chat policy gate: 100% ответов соответствуют контракту (`citations` или `insufficient_data=true`).
6. security negative tests green.

---

## 6. Заключение

Текущее решение — хороший и уже функциональный MVP baseline, но для **формальной приемки по исходному ТЗ** требуется довести обязательные P0-гейты (full E2E, postgres integration, claim coverage) и закрыть P1-блоки (rerun workflow, security, graph explainability UX).
