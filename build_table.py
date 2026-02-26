"""
Скрипт для парсинга HTML файлов и создания таблицы с данными о кафе
Работает максимально быстро с многопоточностью
НЕ удаляет дубликаты - сохраняет все данные как есть
"""

import os
import re
import json
import glob
import concurrent.futures
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# Настройки
HTML_DIR = "html_files"
METADATA_FILE = os.path.join(HTML_DIR, "metadata.json")
OUTPUT_XLSX = "cafes_astana_table.xlsx"
OUTPUT_CSV = "cafes_astana_table.csv"
MAX_WORKERS = 16


def extract_from_title(title_text):
    """Извлечь название и адрес из title страницы"""
    # Формат может быть разным:
    # "Название, категория, улица, номер дома, Астана — 2ГИС"
    # "Название, улица, номер дома, Астана — 2ГИС"
    # Пример: "KaRima, центр плова, проспект Мангилик Ел, 54, Астана — 2ГИС"
    # Пример: "SF, улица Кайым Мухамедханов, 19а, Астана — 2ГИС"
    if not title_text:
        return None, None

    # Убираем " — 2ГИС" в конце
    title_text = re.sub(r'\s*[—–-]\s*2ГИС$', '', title_text, flags=re.I)

    # Пробуем разбить по запятым
    parts = [p.strip() for p in title_text.split(',')]

    if len(parts) < 2:
        return title_text, None

    name = parts[0]

    # Ключевые слова для определения начала адреса
    address_keywords = [
        'улица', 'проспект', 'переулок', 'бульвар', 'шоссе', 'тупик',
        'микрорайон', 'мкр', 'район', 'квартал', 'площадь', 'набережная',
        'аллея', 'проезд', 'жилой комплекс', 'жк', 'ул.', 'пр.', 'пр-т',
        # Казахские слова
        'көшесі', 'даңғылы', 'шағын ауданы'
    ]

    # Ищем индекс части, где начинается адрес
    address_start_idx = None
    for i, part in enumerate(parts[1:], start=1):
        part_lower = part.lower()
        for kw in address_keywords:
            if kw in part_lower:
                address_start_idx = i
                break
        if address_start_idx is not None:
            break

    if address_start_idx is not None:
        # Адрес - всё начиная с найденного индекса
        address = ', '.join(parts[address_start_idx:])
        return name, address
    elif len(parts) >= 3:
        # Если ключевые слова не найдены, берём последние части как адрес
        # Предполагаем: Название, категория, номер дома, Город
        # или: Название, номер дома, Город
        address = ', '.join(parts[-2:])
        return name, address
    else:
        return name, parts[-1]


def extract_from_description(desc):
    """Извлечь данные из meta description"""
    if not desc:
        return {}

    result = {}

    # Чек (средний чек)
    check_match = re.search(r'[Чч]ек\s*(\d+(?:\s*\d+)*)\s*(?:тнг|тг|₸)', desc)
    if check_match:
        result['check'] = check_match.group(1).replace(' ', '') + ' тнг'

    # Рейтинг
    rating_match = re.search(r'[Оо]ценка\s*(\d+[.,]\d+)', desc)
    if rating_match:
        result['rating'] = rating_match.group(1).replace(',', '.')

    # Количество отзывов
    reviews_match = re.search(r'(\d+(?:\s*\d+)*)\s*отзыв', desc)
    if reviews_match:
        result['reviews'] = reviews_match.group(1).replace(' ', '')

    # Количество фото
    photos_match = re.search(r'(\d+)\s*фото', desc)
    if photos_match:
        result['photos'] = photos_match.group(1)

    return result


def extract_from_og_description(og_desc):
    """Извлечь данные из og:description (там есть оценка)"""
    if not og_desc:
        return {}

    result = {}

    # Формат: "Оценка 4.5, 180 фото, 3362 отзыва, чек 3000 тнг."
    rating_match = re.search(r'[Оо]ценка\s*(\d+[.,]\d+)', og_desc)
    if rating_match:
        result['rating'] = rating_match.group(1).replace(',', '.')

    photos_match = re.search(r'(\d+)\s*фото', og_desc)
    if photos_match:
        result['photos'] = photos_match.group(1)

    reviews_match = re.search(r'(\d+)\s*отзыв', og_desc)
    if reviews_match:
        result['reviews'] = reviews_match.group(1)

    check_match = re.search(r'[Чч]ек\s*(\d+)\s*(?:тнг|тг)', og_desc)
    if check_match:
        result['check'] = check_match.group(1) + ' тнг'

    return result


def parse_html_file(filepath):
    """Парсит один HTML файл и возвращает данные"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            html = f.read()

        soup = BeautifulSoup(html, 'html.parser')

        # === Название и адрес из title ===
        title_tag = soup.find('title')
        title_text = title_tag.get_text(strip=True) if title_tag else ''
        name, address_from_title = extract_from_title(title_text)

        # === Meta description ===
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        description = desc_tag.get('content', '') if desc_tag else ''
        desc_data = extract_from_description(description)

        # === OG Description (здесь рейтинг!) ===
        # Пробуем через BeautifulSoup
        og_desc_tag = soup.find('meta', attrs={'property': 'og:description'})
        og_description = og_desc_tag.get('content', '') if og_desc_tag else ''

        # Если не нашли, пробуем через regex (бывает на одной строке с другими тегами)
        if not og_description:
            og_match = re.search(r'property=["\']og:description["\']\s+content=["\']([^"\']+)["\']', html)
            if og_match:
                og_description = og_match.group(1)

        og_data = extract_from_og_description(og_description)

        # Объединяем данные (og_data приоритетнее для рейтинга)
        merged_data = {**desc_data, **og_data}

        # === Телефон ===
        phone = None
        phone_links = soup.find_all('a', href=lambda x: x and x.startswith('tel:'))
        if phone_links:
            phone_href = phone_links[0].get('href', '')
            phone = phone_href.replace('tel:', '').strip()

        # === URL из canonical link ===
        url_2gis = None
        canonical = soup.find('link', rel='canonical')
        if canonical:
            url_2gis = canonical.get('href', '')

        # === Категории из description ===
        categories = []
        if description:
            # Ищем текст после "как доехать." и до точки
            cat_match = re.search(r'как доехать\.\s*([^.]+)', description, re.I)
            if cat_match:
                cat_text = cat_match.group(1)
                categories = [c.strip() for c in cat_text.split(',') if c.strip()][:5]

        return {
            'name': name or 'Неизвестно',
            'address': address_from_title or 'Не указано',
            'phone': phone or 'Не указано',
            'rating': merged_data.get('rating', 'Нет рейтинга'),
            'reviews': merged_data.get('reviews', '0'),
            'photos': merged_data.get('photos', '0'),
            'avg_check': merged_data.get('check', 'Не указано'),
            'categories': ', '.join(categories) if categories else 'Кафе',
            'url_2gis': url_2gis or '',
            'status': 'success'
        }

    except Exception as e:
        return {
            'name': 'Ошибка парсинга',
            'address': '',
            'phone': '',
            'rating': '',
            'reviews': '',
            'photos': '',
            'avg_check': '',
            'categories': '',
            'url_2gis': '',
            'status': 'error',
            'error': str(e)[:100]
        }


def parse_with_id(args):
    """Обёртка для параллельного парсинга"""
    idx, filepath = args
    result = parse_html_file(filepath)
    result['id'] = idx
    result['filename'] = os.path.basename(filepath)
    return result


def main():
    print(f"{'=' * 60}")
    print("ПАРСИНГ HTML ФАЙЛОВ И СОЗДАНИЕ ТАБЛИЦЫ")
    print(f"{'=' * 60}\n")

    # Способ 1: Использовать metadata.json если есть
    if os.path.exists(METADATA_FILE):
        print(f"📂 Загружаю метаданные из {METADATA_FILE}...")
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        files_to_parse = []
        for item in metadata:
            filepath = os.path.join(HTML_DIR, item['filename'])
            if os.path.exists(filepath):
                files_to_parse.append((item['id'], filepath))

        print(f"✓ Найдено {len(files_to_parse)} файлов по метаданным")
    else:
        # Способ 2: Найти все HTML файлы
        print(f"📂 Ищу HTML файлы в {HTML_DIR}...")
        html_files = glob.glob(os.path.join(HTML_DIR, "cafe_*.html"))

        files_to_parse = []
        for filepath in html_files:
            # Извлекаем номер из имени файла
            match = re.search(r'cafe_(\d+)\.html', filepath)
            if match:
                idx = int(match.group(1))
                files_to_parse.append((idx, filepath))

        files_to_parse.sort(key=lambda x: x[0])
        print(f"✓ Найдено {len(files_to_parse)} HTML файлов")

    if not files_to_parse:
        print("❌ HTML файлы не найдены!")
        print("Сначала запустите download_html.py для загрузки страниц")
        return

    print(f"\n🔄 Парсинг {len(files_to_parse)} файлов ({MAX_WORKERS} потоков)...\n")

    # Параллельный парсинг
    results = []
    success_count = 0
    error_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(parse_with_id, item): item[0] for item in files_to_parse}

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)

            if result.get('status') == 'success':
                success_count += 1
                if success_count % 100 == 0:
                    print(f"✓ Обработано: {success_count} / {len(files_to_parse)}")
            else:
                error_count += 1
                if error_count <= 5:
                    print(f"✗ Ошибка в файле {result.get('filename', '?')}: {result.get('error', 'unknown')[:50]}")

    # Сортируем по ID (НЕ удаляем дубликаты!)
    results.sort(key=lambda x: x.get('id', 0))

    # Формируем DataFrame
    df_data = []
    for r in results:
        if r.get('status') == 'success':
            df_data.append({
                '№': r.get('id', 0),
                'Название': r.get('name', ''),
                'Адрес': r.get('address', ''),
                'Телефон': r.get('phone', ''),
                'Рейтинг': r.get('rating', ''),
                'Отзывов': r.get('reviews', ''),
                'Фото': r.get('photos', ''),
                'Средний чек': r.get('avg_check', ''),
                'Категории': r.get('categories', ''),
                'URL 2GIS': r.get('url_2gis', ''),
                'HTML файл': r.get('filename', '')
            })

    if not df_data:
        print("\n❌ Нет данных для сохранения!")
        return

    df = pd.DataFrame(df_data)

    # Сохраняем в Excel и CSV
    df.to_excel(OUTPUT_XLSX, index=False, engine='openpyxl')
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')

    print(f"\n{'=' * 60}")
    print("✅ ПАРСИНГ ЗАВЕРШЕН!")
    print(f"{'=' * 60}")
    print(f"✓ Успешно обработано: {success_count}")
    print(f"✗ Ошибок: {error_count}")
    print(f"📊 Всего записей в таблице: {len(df)}")
    print(f"📁 Excel: {OUTPUT_XLSX}")
    print(f"📁 CSV: {OUTPUT_CSV}")
    print(f"{'=' * 60}\n")

    # Статистика
    print("📊 Статистика:")
    print(f"  - С телефонами: {len(df[df['Телефон'] != 'Не указано'])}")
    print(f"  - С рейтингом: {len(df[df['Рейтинг'] != 'Нет рейтинга'])}")
    print(f"  - Со средним чеком: {len(df[df['Средний чек'] != 'Не указано'])}")

    # Показываем первые записи
    print("\n📋 Первые 5 записей:")
    print(df[['№', 'Название', 'Адрес', 'Телефон', 'Рейтинг']].head().to_string(index=False))


if __name__ == "__main__":
    main()






