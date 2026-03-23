# review18.md — Устранение недостатков по review17 и фокус на реальные источники

Дата: 2026-03-23

## Что реализовано в коде

1. **Productionization runtime-адаптеров (реальные источники)**
   - Добавлен базовый каркас runtime HTTP-профиля с поддержкой:
     - source-specific `search_path`,
     - `query_param_map` для маппинга полей запроса,
     - JSON shape handling (`items/results/data`) и HTML fallback parsing,
     - required-field validation для каждой записи.
   - Адаптеры `FnsRegistryAdapter`, `SudrfAdapter`, `MvdWantedAdapter` переведены на typed normalization + валидацию обязательных полей.

2. **Error taxonomy и наблюдаемость по источникам**
   - Введён `AdapterError(code, retryable, details)` с кодами:
     - `timeout`, `unavailable`, `parse_error`, `rate_limited`, `manual_required`.
   - В pipeline добавлены source-level события и сообщения с latency/record-count/error taxonomy.
   - Статус шага `search sources` теперь деградирует в `degraded`, если хотя бы один источник завершился ошибкой.

3. **Runtime regression слой для HTTP-интеграций**
   - Добавлены integration-тесты с mock HTTP server:
     - JSON-профиль,
     - HTML-профиль,
     - error taxonomy (`rate_limited`).

4. **Rerun lifecycle и прозрачность UX**
   - Worker теперь переводит `rerun_runs` по lifecycle: `queued -> running -> done/error`.
   - В отчёте отображаются:
     - история запусков источников со статусами/сообщениями,
     - история rerun,
     - предупреждение о частичной недоступности источников.

## Что ещё нужно довести (предложения)

1. **Жёсткие CI gates (обязательно)**
   - Выделить отдельные джобы `integration-postgres`, `adapter-runtime-mocks`, `e2e-full` как blocking.

2. **Источник-специфичные парсеры для production**
   - Расширить HTML parsing c DOM-ориентированными селекторами и версиями parser contracts per source.
   - Добавить детект изменения шаблонов страниц (contract drift alerts).

3. **SLO/метрики**
   - Вывести source метрики в Prometheus: `success_rate`, `timeout_rate`, `parse_error_rate`, `p95_latency`.
   - Ввести алерты и runbook на деградации источников.

4. **Security hardening**
   - Добавить негативные тесты на upload/content-sniffing/csrf для production-mode.

5. **Explainability и chat policy**
   - Зафиксировать отдельный CI gate: chat только `citations` или `insufficient_data`.

## Итог

Ключевые блокеры из review17 по реальным источникам существенно закрыты: runtime HTTP-path стал структурированным, появились error taxonomy, деградация и regression-тесты на mock runtime. Для полного production уровня остаются обязательные CI gates, расширенный parser hardening и операционные метрики/алерты.
