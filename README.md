## Запуск локально
1. pip install -r requirements.txt
2. python app.py

## Запуск готового образа с Docker Hub
docker run -d -p 8000:80 -v todo_data:/app/data alyonaloz/todo-flask:latest
  
### Остановка и удаление контейнера:
docker stop shorturl
docker rm shorturl


## Документация:
- Swagger UI: `http://localhost:8000/docs`
