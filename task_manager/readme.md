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
docker compose up --build -d
```

Зайдем в контейнер:
```
docker exec -it task_manager-app-1 /bin/bash
```

Применем миграции:
```
python manage.py migrate
```

Создадим суперпользователя(email вводить необязательно):
```
python manage.py createsuperuser
```

Чтобы выйти из контейнера:
```
exit
```
