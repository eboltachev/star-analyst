# review03.md — Техническое ревью #3 (с учётом `review02.md`, `plan02.md` и требований заказчика)

Дата: 2026-03-22  
Контекст: третий цикл ревью для подготовки к фактической реализации MVP до приемочного уровня.

---

## 1) Executive summary

`review02.md` и `plan02.md` хорошо фиксируют приоритеты и путь внедрения.  
На текущем этапе проблема не в отсутствии плана, а в том, что **основные P0-изменения ещё не имплементированы в коде**.

### Ключевой вывод
Для приемки по ТЗ необходимо перейти от документации к исполнению и закрыть 5 блоков:
1. queue/worker-only execution model;
2. runtime adapters с отказоустойчивостью;
3. explainable report contract;
4. chat RAG + citations + rerun;
5. полноценный e2e сценарий (а не smoke).

До выполнения этих блоков решение остаётся «MVP blueprint», но не «MVP accepted».

---

## 2) Валидация `review02.md`

## Что сделано правильно
- Есть чёткая P0/P1/P2 рамка и явные блокеры приемки.
- Введены измеримые критерии (latency/event/citation coverage).
- Есть execution-порядок, снижающий риск регрессий.

## Что добавить для engineering governance
1. **Owner/ETA matrix**: кто реализует каждый milestone и в какие сроки.
2. **Definition of Ready** для каждого блока (входные предпосылки перед стартом разработки).
3. **Risk burn-down tracker**: weekly status по P0 блокерам.

Вывод: `review02.md` качественный, но для управления реализацией нужен слой ownership/ETA.

---

## 3) Валидация `plan02.md`

## Плюсы
- Хорошая структуризация по milestone A–H.
- У каждого этапа есть acceptance и тесты.
- Правильная dependency sequence (A→B→C→D→G).

## Уточнения перед code execution
1. Для Milestone A нужно зафиксировать:
   - стратегию идемпотентности submit (idempotency-key);
   - max retry attempts и retry delay;
   - правила dead-letter (когда job окончательно failed).
2. Для Milestone B:
   - унифицировать error taxonomy (`timeout`, `unavailable`, `validation_error`, `manual_required`).
3. Для Milestone C/D:
   - JSON schema для `claims` и `chat_response` (версионируемая).
4. Для Milestone G:
   - обязательные `data-testid` по всем критическим элементам UI.

Вывод: `plan02.md` готов к реализации после формализации контрактов (schemas/taxonomy/idempotency).

---

## 4) Текущее соответствие требованиям заказчика (третья проверка)

### 4.1 Сильные стороны текущего состояния
- Архитектурный baseline соответствует ограничениям (монолит + worker + Postgres/pgvector + SSR).
- Есть полноценный скелет доменной модели и экранов.
- Есть миграции, compose, env, базовый тестовый каркас.

### 4.2 Системные разрывы, которые всё ещё критичны
1. **Оркестрация**: pipeline запускается не как чистая фоновая очередь (P0).  
2. **Runtime adapters**: нет полноценных HTTP/retry/rate-limit сценариев в боевом контуре (P0).  
3. **Explainability**: отчёт и чат не гарантируют строгую привязку каждого claim/answer к evidence (P0).  
4. **E2E**: отсутствует полный пользовательский сценарий (P0).  
5. **Security baseline**: CSRF/upload hardening/cookie policy не закреплены end-to-end (P1).

---

## 5) Предложения по реализации (обновлённый action set)

## Action 1 (немедленно, Sprint-1)
**Выполнить Milestone A + B из `plan02.md` как единый delivery пакет.**

### Почему вместе
- Без A мониторинг и UX некорректны.
- Без B «проверка по источникам» не соответствует бизнес-смыслу.

### Проверка готовности
- API enqueue-only;
- worker claims jobs;
- source partial failure не валит весь pipeline;
- в отчёте отображаются source limitations.

## Action 2 (Sprint-2)
**Выполнить Milestone C + D (report contract + chat contract).**

### Что обязательно
- JSON schema versioning:
  - `report_claims_v1`
  - `chat_answer_v1`
- Policy: no citation => insufficient_data.

## Action 3 (Sprint-3)
**Выполнить Milestone G + частично E/F.**

### Что обязательно
- Полный Playwright e2e;
- graph click-to-evidence;
- CSRF + upload allowlist/size limit.

---

## 6) Предлагаемые acceptance gates (обновлённо)

Gate считается пройденным только при одновременном выполнении всех условий:

1. **Performance gate**
   - submit p95 < 500ms,
   - first monitor event < 2s.
2. **Reliability gate**
   - partial source failure handled,
   - retry policy works,
   - failed jobs observable.
3. **Explainability gate**
   - >=95% report claims mapped to evidence,
   - chat: 100% citations or insufficient_data.
4. **E2E gate**
   - full playwright scenario green in CI.
5. **Security gate**
   - CSRF enforced,
   - upload policy enforced,
   - secure cookie config validated.

---

## 7) Рекомендации по структуре следующих PR

Чтобы ускорить ревью и снизить риск:

1. Делать PR строго по milestone (не смешивать A+B+C в одном гигантском PR).  
2. В каждом PR добавлять:
   - migration notes,
   - backward compatibility notes,
   - rollout plan,
   - rollback plan.
3. В описании PR использовать шаблон:
   - changed contracts,
   - acceptance criteria,
   - executed tests (команды + результаты).

---

## 8) Итог

- `review02.md` и `plan02.md` уже дают достаточную аналитическую и плановую базу.
- Главный приоритет теперь — **исполнение P0 в коде**, а не выпуск новых планов.
- После закрытия Action 1→2→3 и прохождения acceptance gates решение можно считать соответствующим требованиям заказчика для MVP.
