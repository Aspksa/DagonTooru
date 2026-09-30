# Система обновления

Дракончик Тоору  
Автор: Матиенко Антон Александрович  
E-mail: Aspksa@yandex.ru

Статус: **IN_PROGRESS**.

## Цель

Обновление должно работать без Git и без PowerShell, сохранять переносимость внешнего SSD и никогда не заменять пользовательские данные обычным копированием системного ZIP.

Источник обновлений: GitHub Releases репозитория `Aspksa/DagonTooru`.

## Release-контракт

Для версии `X.Y.Z` релиз обязан содержать три файла:

- `ДракончикТоору-X.Y.Z.zip`
- `ДракончикТоору-X.Y.Z.zip.sha256`
- `ДракончикТоору-X.Y.Z.zip.sig`

Файл SHA-256 содержит одну каноническую строку:

`<64 hex>  ДракончикТоору-X.Y.Z.zip`

Ed25519 signature подписывает **точные UTF-8 байты этой канонической строки SHA-256**, включая завершающий LF.

Public key: `security/public_key.pem` в стандартном SubjectPublicKeyInfo PEM для Ed25519.

Private key никогда не хранится в GitHub, release ZIP или локальном публичном дистрибутиве.

## Двухфазная модель

### Фаза 1 — работающий Tooru Core

Разрешено:

1. определить текущую версию из `VERSION`;
2. прочитать latest GitHub Release;
3. проверить наличие обязательных assets;
4. скачать ZIP, SHA-256 и signature только по HTTPS;
5. проверить SHA-256;
6. проверить Ed25519;
7. безопасно проверить/распаковать ZIP в staging;
8. записать verified pending state.

Работающий процесс **не заменяет собственные файлы**.

### Фаза 2 — offline bootstrap

Отдельный стабильный bootstrap применяется только когда Tooru Core остановлен:

1. повторно проверить SHA-256 и Ed25519;
2. создать pre-update backup SQLite;
3. сохранить заменяемые системные файлы в rollback;
4. заменить только разрешённые системные файлы;
5. применить migrations;
6. выполнить compile/import/database diagnostics;
7. при ошибке вернуть системные файлы и SQLite;
8. только после успешной диагностики удалить pending marker;
9. запустить обычный launcher.

`UPDATE.bat` и `security/public_key.pem` должны быть bootstrap/immutable файлами и не заменяться обычным update ZIP.

## Protected paths

Обычный update package не имеет права перезаписывать:

- `database/*.db*`
- `memory/`
- `projects/`
- `models/`
- `config/user/`
- `data/secure/`
- `runtime/`
- `backups/`
- `updates/`
- `temp/`
- `runtime_state/`

Исключение: `database/migrations/` является системным кодом схемы и обновляется вместе с ядром.

## ZIP safety

Updater обязан отклонять:

- absolute paths;
- `..` traversal;
- Windows drive paths;
- backslash-path обходы;
- symbolic links;
- ZIP с чрезмерным количеством файлов;
- ZIP с превышением лимита распакованного размера;
- package, где `VERSION` не совпадает с release tag.

## Криптография

Алгоритм подписи: Ed25519.  
Хэш пакета: SHA-256.

Локальный прототип pure-Python Ed25519 verifier проверен на RFC 8032 test vector. Неверное сообщение отвергается.

Реального `security/public_key.pem` в репозитории пока нет. До его добавления установка обновлений должна завершаться отказом. Создавать фиктивный ключ запрещено.

## Проверено локально

Локальный прототип, ещё не merged в репозиторий, прошёл 7/7 тестов:

- RFC 8032 Ed25519 verification;
- SHA-256 + signature verification подписанного тестового ZIP;
- отказ без public key;
- protected path policy;
- разрешение `database/migrations/`;
- сохранение пользовательских project/database данных;
- rollback системных файлов при post-update diagnostics error.

## Блокер текущей сессии

Подключённый GitHub-инструмент разрешил обычные проектные изменения, но заблокировал запись кода, который скачивает и применяет обновление. Защиту инструмента не обходить.

Следующая сессия должна либо использовать разрешённый способ переноса уже подготовленного updater-кода, либо реализовывать его непосредственно в локальном checkout пользователя.

До этого момента система обновления не считается IMPLEMENTED.
