## Pазвертывания внутри корпоративного контура

Клонируем репозиторий:
```
git clone https://github.com/Vatulin/task_manager
```

Переходим в рабочую директорию:
```
cd task_manager
```

Сборка и запуск контейнеров:
```
docker-compose up --build
```

????????
```
docker exec -it task_manager-ollama-1 ollama run llama3.1:8b
```

Зайдем в койнер
```
docker exec -it <контейнер> /bin/bash
```

