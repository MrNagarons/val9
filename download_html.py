"""
Скрипт для загрузки HTML-страниц кафе по списку URL из all_urls.txt
Использует многопоточность для максимальной скорости
"""

import os
import re
import json
import concurrent.futures
import requests
from pathlib import Path

# Настройки
HTML_DIR = "html_files"
URLS_FILE = os.path.join(HTML_DIR, "all_urls.txt")
METADATA_FILE = os.path.join(HTML_DIR, "metadata.json")
MAX_WORKERS = 16  # Количество параллельных потоков (можно увеличить для большей скорости)
TIMEOUT = 15  # Таймаут запроса в секундах

# Заголовки для запросов
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
}


def parse_urls_file(filepath):
    """Парсим файл с URL в формате 'N. URL'"""
    urls = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Формат: "1. https://..."
            match = re.match(r'^(\d+)\.\s+(.+)$', line)
            if match:
                idx = int(match.group(1))
                url = match.group(2).strip()
                urls.append((idx, url))
    return urls


def download_and_save(args):
    """Скачать HTML и сохранить в файл"""
    idx, url = args
    filename = f"cafe_{idx:04d}.html"
    filepath = os.path.join(HTML_DIR, filename)

    try:
        # Создаём сессию для переиспользования соединений
        response = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        response.raise_for_status()

        html_content = response.text

        # Сохраняем HTML
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Пытаемся извлечь название из <h1>
        quick_name = "Неизвестно"
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.I | re.S)
        if h1_match:
            quick_name = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()

        return {
            "id": idx,
            "filename": filename,
            "url": url,
            "quick_name": quick_name,
            "status": "success"
        }

    except requests.exceptions.Timeout:
        return {"id": idx, "url": url, "status": "error", "error": "timeout"}
    except requests.exceptions.RequestException as e:
        return {"id": idx, "url": url, "status": "error", "error": str(e)[:100]}
    except Exception as e:
        return {"id": idx, "url": url, "status": "error", "error": str(e)[:100]}


def main():
    # Проверяем наличие файла с URL
    if not os.path.exists(URLS_FILE):
        print(f"❌ Файл {URLS_FILE} не найден!")
        print("Сначала запустите main_collect.py для сбора URL")
        return

    # Создаём папку если не существует
    os.makedirs(HTML_DIR, exist_ok=True)

    # Парсим URL
    print(f"📂 Читаю URL из {URLS_FILE}...")
    urls = parse_urls_file(URLS_FILE)
    print(f"✓ Найдено URL: {len(urls)}")

    if not urls:
        print("❌ URL не найдены в файле!")
        return

    print(f"\n{'=' * 60}")
    print(f"ЗАГРУЗКА HTML ({MAX_WORKERS} потоков)")
    print(f"{'=' * 60}\n")

    metadata = []
    success_count = 0
    error_count = 0

    # Параллельная загрузка
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Создаём все задачи
        future_to_idx = {executor.submit(download_and_save, item): item[0] for item in urls}

        # Обрабатываем результаты по мере завершения
        for future in concurrent.futures.as_completed(future_to_idx):
            result = future.result()

            if result["status"] == "success":
                success_count += 1
                metadata.append({
                    "id": result["id"],
                    "filename": result["filename"],
                    "url": result["url"],
                    "quick_name": result["quick_name"]
                })

                # Прогресс каждые 50 файлов
                if success_count % 50 == 0:
                    print(f"✓ Скачано: {success_count} / {len(urls)}")
            else:
                error_count += 1
                if error_count <= 10:  # Показываем только первые 10 ошибок
                    print(f"✗ Ошибка #{result['id']}: {result.get('error', 'unknown')[:50]}")

    # Сортируем метаданные по id
    metadata.sort(key=lambda x: x["id"])

    # Сохраняем метаданные
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print("ЗАВЕРШЕНО!")
    print(f"{'=' * 60}")
    print(f"✓ Успешно скачано: {success_count}")
    print(f"✗ Ошибок: {error_count}")
    print(f"📁 HTML файлы: {HTML_DIR}/")
    print(f"📋 Метаданные: {METADATA_FILE}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

