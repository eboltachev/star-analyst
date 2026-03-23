# review19.md — Предложения по закрытию оставшихся недостатков после review18

Дата: 2026-03-23

## Что закрыто в текущей итерации

1. Усилены runtime-адаптеры для реальных источников и error taxonomy.
2. Добавлены source-level метрики (success/failure/error-code/p95) в runtime-регистре.
3. Усилен upload security baseline: content sniffing + защита от spoofing MIME.
4. Добавлен chat policy gate (ответ с citations или `insufficient_data`).
5. Разложены CI lane entrypoints под blocking-гейты.

## Критические замечания, которые остаются

1. **CI пока не enforcing на уровне платформы**
   - Есть скрипты lane entrypoints, но нужно закрепить в GitHub/GitLab pipeline как обязательные blocking jobs.

2. **Source-specific parser contracts требуют углубления**
   - Нужны отдельные контракты и тест-кейсы на drift верстки для каждого боевого источника.

3. **Observability пока in-process**
   - Метрики собираются в памяти процесса; для production нужен экспорт в Prometheus/OpenTelemetry и централизованные алерты.

4. **Security negative-tests неполные**
   - Добавить интеграционные кейсы на CSRF в production profile и проверки upload policy на уровне HTTP endpoint matrix.

## Предложения (next commits)

1. `ci(gates): enforce blocking lanes in pipeline config`
2. `feat(adapters): add per-source parser contracts + drift fixtures`
3. `feat(observability): export source SLO metrics to prometheus`
4. `test(security): add production-mode csrf/upload negative integration suite`
5. `docs(ops): runbook for source degradation and incident response`

## Финальный вывод

Сервис стал существенно устойчивее к работе с реальными источниками и безопаснее на уровне загрузок/политик ответа чата. Для production acceptance осталось формально закрепить blocking CI и вынести observability/алерты в внешнюю операционную инфраструктуру.
