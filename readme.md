# Proof of concept сервиса для распределенного исполнения моделей с интерфейсом HTTP

## Запуск

```
git clone https://github.com/slonoten/velo.git
cd velo
docker-compose up
```

Swagger: http://localhost:8877/docs


## Запуск с несколькими воркерами

Можно указать число воркеров на старте:

```
docker-compose up --scale worker=3
```

Можно изменить число воркеров налету:

```
docker-compose scale worker=5
```

## Нагрузочное тестирование

Установим пакет locust:

```
pip install locust
```

Запустим тест: 

```
locust -f perfomance_test.py
```

В веб-интерфейсе http://localhost:8989 задаём количество пользователей, их скорость их добавления и URL API: http://localhost:8877. Нажимаем Start. 
