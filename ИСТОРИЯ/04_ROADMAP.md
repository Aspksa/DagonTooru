# Дорожная карта

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

1. Portable Python — IN_PROGRESS:
   - официальный Python 3.14.7 embeddable package и SHA-256 закреплены — IMPLEMENTED;
   - AMD64/ARM64/x86 выбор архитектуры — IMPLEMENTED;
   - HTTPS download + SHA-256 verification + staging + rollback — IMPLEMENTED;
   - настройка `python*._pth` для корня проекта — IMPLEMENTED;
   - контрактные тесты — IMPLEMENTED;
   - фактическая проверка `SETUP.bat` на Windows и внешнем SSD — PLANNED.
2. Надёжность локальных данных и процесса — IN_PROGRESS:
   - миграции SQLite — IMPLEMENTED;
   - online backup SQLite + SHA-256 — IMPLEMENTED;
   - проверенное восстановление SQLite с safety-backup — IMPLEMENTED;
   - защита одного экземпляра ядра — IMPLEMENTED;
   - полный Backup Manager для защищаемых каталогов — PLANNED;
   - Crash Recovery / Safe Mode / Maintenance Mode — PLANNED.
3. Менеджер моделей AI, диалоги, настройки и контроль потребления памяти — PLANNED.
4. Internet Gateway, разрешения, чтение веба и почты с защитой от недоверенного содержимого — PLANNED.
5. Проверяемые и подписанные обновления из GitHub с откатом — PLANNED.
6. Аккаунты, мобильный API и приложения Android/iOS — PLANNED.
