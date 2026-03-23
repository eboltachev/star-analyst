# review15.md — Предложения по дальнейшему развитию после закрытия приоритетов review14

Дата: 2026-03-23

## Что закрыто в текущей итерации
1. Добавлен базовый rerun workflow (report page -> выбор источников -> enqueue rerun -> monitor).
2. Усилена security baseline (CSRF проверки в ключевых POST endpoint'ах, upload type/size validation, cookie параметры с конфигом).
3. Доработан graph UX: отображение деталей node/edge с evidence в интерфейсе отчёта.

## Оставшиеся риски

### P1
1. CSRF currently bypassable тестовым заголовком (`X-Test-Bypass`), нужен более строгий тестовый режим без production backdoor.
2. Rerun workflow пока перезаписывает selected_sources запроса; желательно хранить отдельные rerun jobs/runs с audit trail.
3. Graph detail panel минимальна; не хватает rich snippets и deep links на конкретные claim anchors.

### P2
1. Нужны отдельные CI pipelines:
   - full browser e2e in stable environment,
   - PostgreSQL integration with lock semantics.
2. Требуется observability слой (metrics + alerting + dashboards).
3. Нужны политики retention/cleanup для файлов и артефактов.

## Предложения по следующему PR

## PR-1 (P1): secure CSRF/test mode
- Убрать header bypass из production path.
- Добавить configurable `TESTING=true` mode и проверку только в tests.

## PR-2 (P1): rerun audit model
- Ввести отдельную модель `rerun_jobs`/`rerun_runs`.
- Хранить who/when/which_sources и статус rerun.

## PR-3 (P1): graph explainability UX v2
- Добавить snippets, source links, claim anchors.
- Добавить search/filter по графу.

## PR-4 (P2): operations hardening
- Метрики (pipeline duration, error rate, claim coverage, citation ratio).
- Retention jobs и административные настройки.

## Целевые критерии следующего релиза
1. Security tests green без bypass-хаков в production code.
2. Rerun history fully auditable.
3. Graph detail UX acceptance passed by product.
4. CI includes stable full e2e + postgres integration lanes.
