# Проверки

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

Основная команда проекта: `python -m unittest discover -s tests -v`.

Ранее подтверждены 10 тестов ядра и 4 теста single-instance.

В текущей сессии добавлены 4 контрактных теста portable installer. Все 4 прошли в Linux harness. Проверены закреплённые источники Python 3.14.7, контрольные суммы, переносимые пути и наличие staging/rollback.

Функциональная Windows-проверка `SETUP.bat` ещё не выполнена.
