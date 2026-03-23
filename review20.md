# review20.md — Предложения по дальнейшему закрытию рисков после review19

Дата: 2026-03-23

## Что закрыто в этой итерации

1. Добавлен CI workflow с blocking jobs (`adapter-runtime-mocks`, `integration-postgres`, `e2e-full`).
2. Усилены parser contracts и drift-detection для HTML runtime источников.
3. Добавлен экспорт source-метрик в Prometheus-формате через `/metrics`.
4. Добавлены production-profile integration tests для CSRF и upload spoofing.
5. Добавлен операционный runbook для деградаций источников.

## Критические риски, которые ещё остаются

1. **Parser drift покрывает базовые маркеры, но не DOM-семантику целевых страниц**.
2. **Observability не включает distributed tracing (request_id/source_run correlation в APM)**.
3. **Нет автоматического auto-disable источника при длительной деградации**.

## Предложения (следующие шаги)

1. Ввести source-specific DOM parser adapters с versioned селекторами и контрактными снапшотами HTML.
2. Добавить OpenTelemetry tracing для pipeline/job/source-run и связать с `/metrics`.
3. Реализовать circuit-breaker per source (auto-degrade + cooldown + manual override).
4. Добавить chaos-тесты на сетевые ошибки/таймауты/429 в CI lane.
5. Расширить security matrix: вредоносные PDF, zip-bomb-like payloads, oversized multipart fuzzing.

## Вывод

Критические замечания из review19 закрыты в инженерном смысле (CI gating, parser drift checks, observability export, security integration coverage). Для production enterprise-уровня остаются задачи на глубину парсеров, трассировку и автоматическое управление деградацией источников.
