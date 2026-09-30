# Проверки

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

Команда: `python -m unittest discover -s tests -v`.

Результат: 3 теста прошли в Linux (2026-09-30). Проверены SQLite и исходные проекты, изоляция контекста памяти при API/AI-запросе, запрет записи из чужого Origin. Модули Python также прошли `compileall`. Windows launcher, реальный Ollama, браузер и SSD в этой среде не проверялись.
