# Следующее действие

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

Версия: 0.1.0.

Сделано: добавлен проверяемый portable Python installer в `SETUP.bat`. Закреплён официальный Python 3.14.7 embeddable package для AMD64/ARM64/x86 и SHA-256 из официального Windows release manifest. Реализованы HTTPS download, SHA-256 verification, staging `runtime/python.new`, настройка `python*._pth`, проверка `import core.server`, безопасная активация и rollback предыдущего runtime.

Добавлен `tests/test_setup_contract.py`; 4 контрактных теста прошли в Linux harness. Подтверждено отсутствие жёстких букв диска и PowerShell-команды.

Не закончено: функциональная проверка нового `SETUP.bat` на Windows/внешнем SSD. Нельзя переводить installer в полностью IMPLEMENTED до реального запуска.

Следующая практическая проверка на Windows:
1. закрыть Tooru Core;
2. временно переименовать существующий `runtime/python`, если нужно проверить чистую установку;
3. запустить `SETUP.bat`;
4. убедиться, что показывается Python 3.14.7 и создаётся `runtime/python/TOORU_RUNTIME.txt`;
5. запустить `ДракончикТоору.bat` и проверить сайт/AI;
6. повторно запустить launcher и проверить один экземпляр.

Следующая задача разработки после этого: Crash Recovery и `runtime_state/state.json` с clean-shutdown marker, затем Safe Mode / Maintenance Mode.

Следующий ChatGPT обязан сначала прочитать `AGENTS.md`, всю `ИСТОРИЯ/`, затем `SETUP.bat`, `core/instance.py`, `core/server.py` и тесты.
