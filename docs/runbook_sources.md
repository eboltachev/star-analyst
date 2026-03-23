# Runbook: деградация внешних источников

## 1. Симптомы
- рост `star_source_failures_total` / `star_source_parse_errors_total`
- падение `star_source_success_rate`
- скачок `star_source_p95_latency_ms`

## 2. Быстрая диагностика
1. Открыть `/metrics` и определить деградировавший source.
2. Проверить последние `source:<id>` события в `pipeline_events`.
3. Проверить `source_runs.message` (error taxonomy / retryable).

## 3. Тактика восстановления
1. Если `rate_limited` — снизить RPS в `config/sources.yml` и повторить rerun.
2. Если `parse_error` — запустить parser drift тесты и обновить source parser contract.
3. Если `unavailable/timeout` — временно пометить источник degraded в UI и сообщить SLA-impact.

## 4. Rollback
- Если правки адаптера ухудшили успешность, откатить последний adapter commit.
- Оставить источник в ограниченном режиме (manual verification only), пока не восстановлен парсер.

## 5. Пост-инцидентные действия
- Обновить тест-фикстуры drift-кейсами.
- Добавить regression test и alert threshold для данного источника.
