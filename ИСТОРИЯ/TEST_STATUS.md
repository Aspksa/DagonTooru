# Проверки

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

Основная команда проекта: `python -m unittest discover -s tests -v`.

Linux 2026-09-30: 28/28 тестов прошли.

Состав:
- 10 существующих тестов core/storage/Ollama;
- 4 теста single-instance/identity;
- 10 тестов Crash Recovery;
- 4 контрактных теста portable installer.

Crash Recovery тестами проверены:
- первый запуск, running и clean shutdown;
- распознавание предыдущего штатного и аварийного завершения;
- повреждённый `state.json`;
- атомарная lifecycle-запись без оставшегося `state.json.tmp`;
- `recovery_count` и сохранение незавершённого recovery-сигнала;
- SQLite recovery `ok` и `error`;
- `/api/v1/system/status` с recovery warning;
- необработанный startup error не записывает `clean_shutdown=true`;
- конфликт рабочего порта происходит до изменения recovery-state и до вызова Storage/SQLite.

`python -m compileall -q core tests` — успешно.

`node --check web/static/app.js` — успешно.

Финальные GitHub blob SHA изменённых файлов:
- `core/recovery.py` — `de24932bb8c24a6c1ac3f5fe6df7efcc0c667d52`;
- `core/server.py` — `27f82bb1ad761a307fea4470255d08b216a13d17`;
- `tests/test_recovery.py` — `f68238d19e6f0375828d618ca27e5f03935315be`;
- `web/static/app.js` — `613a8a37b80628f13c8ab05295b3c368b0f10c31`.

Во время существующих backup/restore тестов Python 3.13 выдаёт `ResourceWarning` о незакрытых SQLite connection. Результат тестов остаётся OK; предупреждение зафиксировано как технический долг.

Функциональная проверка Crash Recovery, portable installer, `msvcrt.locking` и конфликтов запуска на Windows/внешнем SSD ещё не выполнена.
