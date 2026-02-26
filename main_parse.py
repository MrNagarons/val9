from bs4 import BeautifulSoup
import pandas as pd
import os
import json
import re

# Проверка наличия метаданных
if not os.path.exists("html_files/metadata.json"):
    print("❌ Файл metadata.json не найден!")
    print("Сначала запустите main_collect_final.py")
    exit()

# Загрузка метаданных
with open("html_files/metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

print(f"📊 Парсинг {len(metadata)} HTML файлов...\n")

cafes_data = []

for item in metadata:
    try:
        filepath = os.path.join("html_files", item['filename'])

        # Чтение HTML
        with open(filepath, "r", encoding="utf-8") as f:
            html = f.read()

        soup = BeautifulSoup(html, 'html.parser')

        # === ПАРСИНГ ДАННЫХ ===

        # Название
        name = "Не указано"
        h1 = soup.find('h1')
        if h1:
            name = h1.get_text(strip=True)

        # Адрес
        address = "Не указано"
        # Ищем по разным вариантам
        address_patterns = [
            soup.find('a', href=re.compile(r'directions')),
            soup.find('div', class_=re.compile(r'address', re.I)),
            soup.find(string=re.compile(r'Астана,.*улица|Астана,.*проспект|Астана,.*микрорайон', re.I))
        ]
        for pattern in address_patterns:
            if pattern:
                if hasattr(pattern, 'get_text'):
                    address = pattern.get_text(strip=True)
                else:
                    address = str(pattern).strip()
                break

        # Телефон
        phone = "Не указано"
        phone_elem = soup.find('a', href=re.compile(r'tel:'))
        if phone_elem:
            phone_raw = phone_elem.get('href', '')
            phone = phone_raw.replace('tel:', '').replace('+', '').replace(' ', '').replace('-', '').replace('(',
                                                                                                             '').replace(
                ')', '')
            if not phone:
                phone = phone_elem.get_text(strip=True)

        # Рейтинг
        rating = "Нет рейтинга"
        rating_elem = soup.find('div', class_=re.compile(r'rating', re.I))
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            # Извлекаем числовой рейтинг
            rating_match = re.search(r'(\d+[.,]\d+|\d+)', rating_text)
            if rating_match:
                rating = rating_match.group(1)

        # Количество отзывов
        reviews = "0"
        reviews_elem = soup.find(string=re.compile(r'\d+\s*отзыв', re.I))
        if reviews_elem:
            reviews_match = re.search(r'(\d+)', reviews_elem)
            if reviews_match:
                reviews = reviews_match.group(1)

        # Режим работы
        schedule = "Не указано"
        schedule_patterns = [
            soup.find(string=re.compile(r'круглосуточно', re.I)),
            soup.find(string=re.compile(r'пн|вт|ср|чт|пт|сб|вс', re.I)),
            soup.find('div', class_=re.compile(r'schedule|hours', re.I))
        ]
        for pattern in schedule_patterns:
            if pattern:
                if hasattr(pattern, 'get_text'):
                    schedule = pattern.get_text(strip=True)
                else:
                    schedule = str(pattern).strip()
                break

        # Веб-сайт
        website = "Не указано"
        website_elem = soup.find('a', href=re.compile(r'^https?://(?!.*2gis)'))
        if website_elem:
            website = website_elem.get('href', '')

        # Средний чек
        price = "Не указано"
        price_elem = soup.find(string=re.compile(r'средний чек|₸', re.I))
        if price_elem:
            price = str(price_elem).strip()[:50]

        # Категория
        category = "Кафе"
        category_elem = soup.find('div', class_=re.compile(r'rubric|category', re.I))
        if category_elem:
            category = category_elem.get_text(strip=True)

        # Сохранение
        cafes_data.append({
            "№": item['id'],
            "Название": name,
            "Адрес": address,
            "Телефон": phone,
            "Рейтинг": rating,
            "Отзывов": reviews,
            "Режим работы": schedule,
            "Категория": category,
            "Средний чек": price,
            "Веб-сайт": website,
            "URL 2GIS": item['url'],
            "HTML файл": item['filename'],
            "Дата сбора": item['collected_at']
        })

        print(f"✓ {item['id']:3d}. {name[:50]}")

    except Exception as e:
        print(f"✗ {item['id']:3d}. Ошибка: {str(e)[:50]}")
        continue

# Создание таблицы
if cafes_data:
    df = pd.DataFrame(cafes_data)

    # Сохранение
    df.to_excel("cafes_astana_table.xlsx", index=False)
    df.to_csv("cafes_astana_table.csv", index=False, encoding="utf-8-sig")

    print(f"\n{'=' * 60}")
    print(f"✓ ПАРСИНГ ЗАВЕРШЕН!")
    print(f"✓ Обработано: {len(df)} кафе")
    print(f"✓ Excel: cafes_astana_table.xlsx")
    print(f"✓ CSV: cafes_astana_table.csv")
    print(f"{'=' * 60}\n")

    # Статистика
    print("📊 Статистика:")
    print(f"  - С телефонами: {df[df['Телефон'] != 'Не указано'].shape[0]}")
    print(f"  - С рейтингом: {df[df['Рейтинг'] != 'Нет рейтинга'].shape[0]}")
    print(f"  - С веб-сайтом: {df[df['Веб-сайт'] != 'Не указано'].shape[0]}")

    print("\n📋 Первые 5 кафе:")
    print(df[['№', 'Название', 'Адрес', 'Телефон', 'Рейтинг']].head())
else:
    print("\n❌ Данные не собраны")
