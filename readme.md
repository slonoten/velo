# Proof of concept сервиса для распределенного исполнения моделей с интерфейсом HTTP

## Запуск

### Веса модели
Загужаем из https://huggingface.co/cointegrated/rubert-tiny2/tree/main файлы 
```config.json  pytorch_model.bin  tokenizer_config.json  tokenizer.json```.

И экспоритрум путь к папке с загруженными файлами в переменную VELO_MODEL_PATH

```
export VELO_MODEL_PATH=/my/model/path
```

### Контейнеры
```
git clone https://github.com/slonoten/velo.git
cd velo
docker-compose up
```

### Swagger

http://localhost:8877/docs


## Запуск с несколькими воркерами

Можно указать число воркеров на старте:

```
docker-compose up --scale worker=3
```

Можно изменить число воркеров на лету:

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

## Замена модели on the fly

Останавливаем worker со старой моделью, запускаем с новой (код, веса).

Сейчас модель имитируется через time.sleep(0.01)

## Статистика

http://localhost:8877/stat возвращает json со статистикой по приложению и worker'ам

```
{
  "workers": {
    "3efa3b00-129e-11ed-93dd-00e01c680b13": {
      "last_seen": "2022-08-02T20:09:02.844896",
      "model_version": "1.0.0",
      "node_name": "dl-box",
      "model_time": 0.010133134899660945
    },
    "13f625f8-129f-11ed-9f0a-00e01c680b13": {
      "last_seen": "2022-08-02T20:11:07.293424",
      "model_version": "1.0.0",
      "node_name": "dl-box",
      "model_time": 0.010282244998961687
    }
  },
  "queue_lenght": 1,
  "response_time": 0.5234761741012335
}
```

В ключи в словаре workers - id worker'ов по которым их можно "убить" в исследовательских целях.

## Тестирование отказоустойчивости

Для того чтобы сымитировать падение worker'a из-за внутренней ошибки необходимо отправить ему его идентификатор в качестве входных данных для модели. 

Запускаем нагрузочный тест, смотрим в статистике id worker'a, через swagger отправляем запрос с этим id (несколько раз, т.к. мы не знаем к какому worker'у попадет наш запрос). В конце концов, запрос попадет к нужному worker'y и worker "упадет". Запрос по истечении таймаута будет направлен к другому worker'у и обработан без ошибки.


## TODO 

Прикрутить настоящую модель, например BERT, тогда получим BERT as service

Добавить сервис для формирования батчей, посмотреть выигрыш в пропускной способности vs задержка