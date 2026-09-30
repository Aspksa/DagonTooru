# Состояние проекта

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

Версия 0.1.0. Статус проекта: IN_PROGRESS.

IMPLEMENTED: локальный Python HTTP API, SQLite, память personal/home/work и по проектам, локальный Ollama-адаптер, web-интерфейс, backup/restore SQLite, миграции, защита одного экземпляра и базовый Crash Recovery.

Crash Recovery ведёт `runtime_state/state.json`. При старте текущая сессия отмечается как незавершённая до штатного закрытия. При следующем старте ядро определяет предыдущую незавершённую сессию и выполняет проверку SQLite. Результат доступен через `/api/v1/system/status` и отображается в «Настройках».

Portable Python installer: IN_PROGRESS. Код установки Python 3.14.7 и контрактные тесты готовы; Windows/SSD-проверка ещё не выполнена.

PLANNED: Safe Mode, Maintenance Mode, полный Backup Manager, AI provider/model manager, Internet Gateway/почта, очередь, события, мобильные приложения, публичная версия, updater и подписанные релизы.
