# Дракончик Тоору

Первый работающий локальный этап проекта по [полной спецификации](docs/DRAGON_TOORU_MASTER_SPEC.json). Одно ядро на Python, локальный web-интерфейс и SQLite.

## Запуск

На Windows основной запуск: `ДракончикТоору.bat`.

Если `runtime/python/python.exe` уже существует и способен импортировать `core.server`, launcher использует его. Если portable Python отсутствует, запустите `SETUP.bat`.

Новый `SETUP.bat` подготавливает portable runtime без PowerShell: определяет AMD64/ARM64/x86, скачивает официальный Python 3.14.7 embeddable package с python.org, проверяет зафиксированный SHA-256, распаковывает во временную папку, настраивает штатный `python*._pth` для доступа к корню проекта, проверяет импорт ядра и только затем активирует `runtime/python`. До успешной финальной проверки предыдущий runtime сохраняется для rollback.

Фактическая Windows/SSD-проверка нового installer ещё не выполнена, поэтому эта часть проекта имеет статус IN_PROGRESS.

Ядро защищено от второго экземпляра OS-level файловой блокировкой `runtime_state/core.lock`. Launcher проверяет работающую Тоору через `/api/v1/system/identity`.

Локальный AI по умолчанию использует Ollama на `http://127.0.0.1:11435` и модель `tooru-local:4b`.

Данные находятся в `database/tooru.db`. Схема управляется `database/migrations/NNN_*.sql`. В настройках можно создать online backup SQLite с SHA-256; backend восстановления проверяет копию и создаёт safety-backup.

## Текущие возможности

- локальный личный помощник с Ollama;
- изолированная personal/home/work память и память проектов;
- SQLite migrations;
- backup/restore SQLite;
- защита одного экземпляра;
- проверяемая подготовка portable Python — IN_PROGRESS до Windows-проверки;
- адаптивный web-интерфейс.

Internet Gateway, почта, мобильные приложения, публичный сервер, полный Backup Manager, Crash Recovery/Safe Mode, updater и подписанные релизы пока не реализованы.

## Проверка

`python -m unittest discover -s tests -v`

Фактическое состояние и результаты проверок ведутся в `ИСТОРИЯ/`.
