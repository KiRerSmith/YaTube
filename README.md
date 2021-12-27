# YaTube
##### Социальная сеть для публикации дневников, с возможностью подписок и комментирования.  

### Действующий пример:
http://kirer.pythonanywhere.com/

### Запустить проекта:
Склонировать репозиторий, перейти в него при помощи команды:

```
git clone https://github.com/KiRerSmith/YaTube
```

```
cd yatube
```

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```

```
source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python manage.py migrate
```

Запустить проект:

```
python manage.py runserver
```
