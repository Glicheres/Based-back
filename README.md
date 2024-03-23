# turlalead backend

Python 3.11

## Информация для локальной отладки
### Перед локальным запуском:
- Создать в `/deployments` файл `.env` и заполнить переменными окружения из `/deployments/.env.example`;  
- Cоздать в корне папку `pgdata` - там будет сохранено состояние БД;
- Создать виртуальное окружение в корне проекта;
- Перед каждым коммитом лучше проверять код через форматтер `black` (скрипы `make pretty` или `make pretty-win`)

### Сборка и старт
```
make dev-build
make dev-start
```
