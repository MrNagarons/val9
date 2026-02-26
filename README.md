# 2GIS Parser - Кафе Астаны

Парсер для сбора данных о кафе и ресторанах Астаны с сайта 2GIS.

## Структура проекта

```
gisparser/
├── main_collect.py      # Сбор URL кафе со всех страниц 2GIS
├── download_html.py     # Скачивание HTML страниц по URL
├── build_table.py       # Парсинг HTML и создание таблицы
├── main_parse.py        # Альтернативный парсер
├── html_files/          # Сохранённые HTML страницы
│   ├── all_urls.txt     # Список всех URL
│   ├── metadata.json    # Метаданные о скачанных файлах
│   └── cafe_*.html      # HTML страницы кафе
├── cafes_astana_table.csv   # Итоговая таблица (CSV)
└── cafes_astana_table.xlsx  # Итоговая таблица (Excel)
```

## Использование

### 1. Сбор URL
```bash
python main_collect.py
```
Собирает URL всех кафе со всех страниц поиска 2GIS.

### 2. Скачивание HTML
```bash
python download_html.py
```
Скачивает HTML страницы по списку URL из `html_files/all_urls.txt`.
Работает в многопоточном режиме (16 потоков).

### 3. Создание таблицы
```bash
python build_table.py
```
Парсит все HTML файлы и создаёт таблицу с данными:
- Название
- Адрес (полный, с улицей)
- Телефон
- Рейтинг
- Количество отзывов
- Количество фото
- Средний чек
- Категории
- URL 2GIS

## Результаты

- **3088** кафе и ресторанов
- **2934** с телефонами
- **2611** с рейтингом
- **2193** со средним чеком

## Требования

```
beautifulsoup4
pandas
selenium
requests
openpyxl
```

## Установка

```bash
pip install beautifulsoup4 pandas selenium requests openpyxl
```

