from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import json
import re
import requests
import concurrent.futures

os.makedirs("html_files", exist_ok=True)

options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-extensions')
options.add_argument('--disable-plugins')
# options.add_argument('--disable-images')  # Закомментировано - иногда мешает загрузке
options.add_argument('--disable-blink-features')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options)
driver.implicitly_wait(2)
metadata = []


def get_first_cafe_href():
    """Получить href первого кафе на текущей странице для определения смены страницы."""
    try:
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/firm/"]')
        for link in links:
            href = link.get_attribute('href')
            if href and '/firm/' in href:
                return href
    except:
        pass
    return None


def get_all_cafe_hrefs():
    """Получить все hrefs кафе на странице."""
    hrefs = []
    try:
        # Сначала прокручиваем список результатов несколько раз для загрузки всех элементов
        scroll_container = driver.find_elements(By.CSS_SELECTOR, '._8hh56jx')
        if scroll_container:
            container = scroll_container[0]
            # Прокручиваем вниз несколько раз
            for _ in range(5):
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", container)
                time.sleep(0.2)
            # Возвращаем в начало
            driver.execute_script("arguments[0].scrollTop = 0;", container)
            time.sleep(0.2)

        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/firm/"]')
        for link in links:
            href = link.get_attribute('href')
            if href and '/firm/' in href:
                hrefs.append(href)
    except:
        pass
    return hrefs


def get_current_page_number():
    """Получить текущий номер страницы из пагинации."""
    try:
        # Ищем активную страницу (класс _l934xo5 - активная страница с серым фоном)
        active = driver.find_elements(By.CSS_SELECTOR, '._l934xo5')
        if active:
            text = active[0].text.strip()
            if text.isdigit():
                return int(text)
    except:
        pass
    return 1


def scroll_to_pagination():
    """Прокрутка к пагинации внизу списка."""
    try:
        # Ищем контейнер со списком
        scroll_container = driver.find_elements(By.CSS_SELECTOR, '._8hh56jx')
        if scroll_container:
            # Скроллим несколько раз для загрузки всего контента
            for _ in range(3):
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scroll_container[0])
                time.sleep(0.3)
            return True
    except:
        pass

    # Fallback - просто скроллим окно несколько раз
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.3)
    return False


def click_next_page():
    """
    Кликнуть для перехода на следующую страницу.
    Возвращает True если успешно, False если достигнут конец.
    """
    try:
        # Скроллим к пагинации
        scroll_to_pagination()
        time.sleep(0.3)

        # Получаем текущие данные для сравнения
        first_href_before = get_first_cafe_href()
        current_page = get_current_page_number()

        # Ищем контейнер пагинации
        pagination_container = driver.find_elements(By.CSS_SELECTOR, '._1x4k6z7')
        if not pagination_container:
            print("  [!] Контейнер пагинации не найден")
            return False

        # Метод 1: Кликнуть по номеру следующей страницы (самый надёжный)
        next_page_num = current_page + 1
        page_links = pagination_container[0].find_elements(By.CSS_SELECTOR, 'a._12164l30')

        for link in page_links:
            try:
                link_text = link.text.strip()
                if link_text.isdigit() and int(link_text) == next_page_num:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                    time.sleep(0.2)
                    driver.execute_script("arguments[0].click();", link)

                    # Ждем изменения
                    for _ in range(40):
                        time.sleep(0.15)
                        new_page = get_current_page_number()
                        if new_page == next_page_num:
                            time.sleep(0.3)
                            return True
                        first_href_after = get_first_cafe_href()
                        if first_href_after and first_href_after != first_href_before:
                            time.sleep(0.3)
                            return True
                    break
            except:
                continue

        # Метод 2: Кликнуть по кнопке "Вперёд"
        # В пагинации есть 2 кнопки: "Назад" и "Вперёд"
        # _7q94tr = серая/неактивная кнопка
        # _n5hmn94 = синяя/активная кнопка

        # Ищем все кнопки навигации внутри контейнера пагинации
        all_nav_elements = pagination_container[0].find_elements(By.CSS_SELECTOR, '._n5hmn94, ._7q94tr')

        if len(all_nav_elements) >= 2:
            # Вторая кнопка - это кнопка "Вперёд"
            forward_btn = all_nav_elements[1]
            forward_class = forward_btn.get_attribute('class') or ''

            # Проверяем, активна ли кнопка "Вперёд"
            if '_7q94tr' in forward_class:
                print("  [+] Кнопка 'Вперед' неактивна (серая) - достигнут конец")
                return False

            # Кнопка активна - кликаем
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", forward_btn)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", forward_btn)

            # Ждем изменения
            for _ in range(40):
                time.sleep(0.15)
                first_href_after = get_first_cafe_href()
                if first_href_after and first_href_after != first_href_before:
                    time.sleep(0.3)
                    return True
                new_page = get_current_page_number()
                if new_page > current_page:
                    time.sleep(0.3)
                    return True

            print("  [!] Контент не изменился после клика на кнопку 'Вперед'")
            return False
        elif len(all_nav_elements) == 1:
            # Только одна кнопка - проверяем, это "Назад" или "Вперёд"
            single_class = all_nav_elements[0].get_attribute('class') or ''
            if '_7q94tr' in single_class:
                # Неактивная кнопка "Вперед" - конец
                print("  [+] Единственная кнопка неактивна - достигнут конец")
                return False
            else:
                # Активная кнопка "Вперед" - кликаем
                driver.execute_script("arguments[0].click();", all_nav_elements[0])
                for _ in range(40):
                    time.sleep(0.15)
                    first_href_after = get_first_cafe_href()
                    if first_href_after and first_href_after != first_href_before:
                        time.sleep(0.3)
                        return True

        print("  [!] Кнопки навигации не найдены в контейнере пагинации")
        return False

    except Exception as e:
        print(f"  [!] Ошибка при клике: {str(e)[:80]}")
        return False


try:
    SEARCH_QUERY = "Поесть"

    print(f"[*] Сбор '{SEARCH_QUERY}' из 2GIS Астана")
    print(f"[*] Загружаю страницу и переключаюсь по страницам...\n")

    # Загружаем стартовую страницу
    base_url = f"https://2gis.kz/astana/search/{SEARCH_QUERY}"
    driver.get(base_url)

    # Ждем загрузки результатов
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/firm/"]'))
        )
    except:
        print("⚠ Не удалось дождаться загрузки результатов")

    time.sleep(1.5)  # Дополнительное ожидание для полной загрузки

    all_cafe_urls = []
    page_number = 1
    max_same_content_count = 3  # Сколько раз контент может быть одинаковым до остановки
    same_content_count = 0
    previous_first_href = None

    print(f"{'=' * 60}")
    print("СБОР URL СО СТРАНИЦ")
    print(f"{'=' * 60}")

    while True:
        # Ждём загрузки контента на странице
        time.sleep(0.5)

        # Получаем текущий номер страницы из UI
        current_page = get_current_page_number()

        # Получаем первый href для проверки изменения контента
        first_href = get_first_cafe_href()

        # Проверяем, изменился ли контент
        if first_href == previous_first_href and first_href is not None:
            same_content_count += 1
            if same_content_count >= max_same_content_count:
                print(f"\n[+] Контент повторяется {max_same_content_count} раза - достигнут конец")
                break
        else:
            same_content_count = 0
        previous_first_href = first_href

        # Собираем URL со страницы
        page_urls = get_all_cafe_hrefs()
        urls_before = len(all_cafe_urls)

        # Добавляем URL (все, включая дубликаты, как просил пользователь)
        all_cafe_urls.extend(page_urls)

        new_count = len(all_cafe_urls) - urls_before
        print(f"[Стр. {page_number:3d}] UI: стр.{current_page} | Найдено: {len(page_urls):3d} | Всего: {len(all_cafe_urls):5d}")

        # Пытаемся перейти на следующую страницу
        if not click_next_page():
            print(f"\n[+] Достигнут конец пагинации на странице {page_number}")
            break

        page_number += 1

        # Безопасное ограничение (на случай бесконечного цикла)
        if page_number > 500:
            print(f"\n[!] Достигнуто ограничение в 500 страниц")
            break

    print(f"\n{'=' * 60}")
    print("СБОР ЗАВЕРШЕН!")
    print(f"{'=' * 60}")
    print(f"[+] Пройдено страниц: {page_number}")
    print(f"[+] Всего URL собрано: {len(all_cafe_urls)}")

    if len(all_cafe_urls) == 0:
        print("\n[!] Кафе не найдены!")
        driver.quit()
        exit()

    # Сохраняем список URL
    with open("html_files/all_urls.txt", "w", encoding="utf-8") as f:
        for i, url in enumerate(all_cafe_urls, 1):
            f.write(f"{i}. {url}\n")

    print(f"\n{'=' * 60}")
    print(f"[+] ЗАГРУЗКА HTML")
    print(f"{'=' * 60}")
    print(f"Количество кафе: {len(all_cafe_urls)}")

    # Параллельная загрузка HTML через requests для скорости
    def download_and_save(args):
        idx, cafe_url = args
        try:
            r = requests.get(cafe_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 200 and '/firm/' in cafe_url:
                filename = f"cafe_{idx:04d}.html"
                filepath = os.path.join("html_files", filename)
                with open(filepath, "w", encoding="utf-8") as fh:
                    fh.write(r.text)
                # Попытка получить заголовок h1 для метаданных
                quick_name = "Неизвестно"
                m = re.search(r'<h1[^>]*>(.*?)</h1>', r.text, re.I | re.S)
                if m:
                    quick_name = re.sub('<[^<]+?>', '', m.group(1)).strip()
                return {"id": idx, "filename": filename, "url": cafe_url, "quick_name": quick_name}
            else:
                return {"error": cafe_url}
        except Exception as e:
            return {"error": cafe_url, "exc": str(e)[:120]}

    print("\nЗапускаю параллельную загрузку HTML (8 потоков)...")
    downloaded_count = 0
    error_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as exe:
        futures = {exe.submit(download_and_save, (i + 1, url)): (i + 1, url) for i, url in enumerate(all_cafe_urls)}
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            if res and 'error' not in res:
                metadata.append(res)
                downloaded_count += 1
                if downloaded_count % 50 == 0:
                    print(f"✓ Скачано: {downloaded_count} файлов...")
            else:
                error_count += 1
                info = futures[fut]
                # Попытка selenium fall-back для ошибочных
                try:
                    idx_f, url_f = info
                    driver.get(url_f)
                    time.sleep(1.5)
                    filename = f"cafe_{idx_f:04d}.html"
                    filepath = os.path.join("html_files", filename)
                    with open(filepath, "w", encoding="utf-8") as fh:
                        fh.write(driver.page_source)
                    quick_name = "Неизвестно"
                    try:
                        quick_name = driver.find_element(By.TAG_NAME, 'h1').text
                    except:
                        pass
                    metadata.append({"id": idx_f, "filename": filename, "url": driver.current_url, "quick_name": quick_name})
                    downloaded_count += 1
                except Exception as e:
                    pass

    # Сохраняем metadata
    with open("html_files/metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Скачано файлов: {downloaded_count}")
    print(f"✗ Ошибок: {error_count}")

finally:
    driver.quit()

if metadata:
    print(f"\n{'=' * 60}")
    print(f"✓ ЗАВЕРШЕНО!")
    print(f"{'=' * 60}")
    print(f"✓ Собрано: {len(metadata)} кафе")
    print(f"📁 html_files/metadata.json")
    print(f"{'=' * 60}")
else:
    print("\n❌ Файлы не собраны")
