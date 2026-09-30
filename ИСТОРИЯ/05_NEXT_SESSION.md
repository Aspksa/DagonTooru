# Следующее действие

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

Версия: 0.1.0.

Сделано: добавлен проверяемый portable Python installer в `SETUP.bat`. Закреплён официальный Python 3.14.7 embeddable package для AMD64/ARM64/x86 и SHA-256 из официального Windows release manifest. Реализованы HTTPS download, SHA-256 verification, staging `runtime/python.new`, настройка `python*._pth`, проверка `import core.server`, безопасная активация и rollback предыдущего runtime.

Дополнительно усилен single-instance startup: после OS-lock ядро сначала занимает рабочий localhost-порт и только затем инициализирует `Storage`/миграции и Ollama. Это исключает касание SQLite новым процессом, если порт уже занят старой версией Тоору или другой программой. Launcher использует тот же `TOORU_PORT`.

Проверено в Linux: ранее прошли 10 тестов ядра; 4/4 теста single-instance/identity; отдельный smoke-тест подтвердил освобождение OS-lock после аварийного завершения владельца; 4/4 контрактных теста portable installer. Новые Python-модули успешно проходят `compileall`.

Не закончено: функциональная проверка нового `SETUP.bat`, `msvcrt.locking`, повторного launcher и конфликта рабочего порта на Windows/внешнем SSD. Нельзя переводить portable installer в полностью IMPLEMENTED до реального запуска.

Следующая практическая проверка на Windows:
1. закрыть Tooru Core;
2. временно переименовать существующий `runtime/python`, если нужно проверить чистую установку;
3. запустить `SETUP.bat`;
4. убедиться, что показывается Python 3.14.7 и создаётся `runtime/python/TOORU_RUNTIME.txt`;
5. запустить `ДракончикТоору.bat` и проверить сайт/AI;
6. повторно запустить launcher и проверить один экземпляр;
7. проверить прямой второй запуск `python -m core.server`, аварийное завершение и последующий перезапуск.

Следующая задача разработки после этого: Crash Recovery и `runtime_state/state.json` с clean-shutdown marker, затем Safe Mode / Maintenance Mode.

Следующий ChatGPT обязан сначала прочитать `AGENTS.md`, всю `ИСТОРИЯ/`, затем `SETUP.bat`, `core/instance.py`, `core/server.py` и тесты.
