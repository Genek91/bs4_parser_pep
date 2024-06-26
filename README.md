# Парсер документации Python

### Технологии
Python, BS4

## Описание

Парсер документации Python.

Основной функционал, это сбор таких данных как:

- ссылки на статьи о нововведениях в Python
- информация об авторах и редакторах статей
- информация о статусах версий Python

Возможность скачивать архив с актуальной документацией.

Ссылка на документацию Python: <https://docs.python.org/>

Получение данных обо всех документах PEP, cравнение их статусов на странице PEP со статусом в общем списке.

- вывод результата сравнения и общего количества PEP

Ссылка на страницу с PEP: <https://peps.python.org/>

Все данные можно сохранить в csv-файл или вывести результат в консоли в виде таблицы.

## Запуск проекта

- Установите и активируйте виртуальное окружение

- Установите зависимости из файла requirements.txt

```bash
pip install -r requirements.txt
```

- Перейдите в директорию с файлом main.py

- Справочная информация по функционалу

```bash
python main.py -h
```

- Основные ежимы работы парсера

```bash
positional arguments:
  {whats-new,latest-versions,download,pep}
```

### Автор

[Genek91](https://github.com/Genek91)
