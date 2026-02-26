"""
Тестовый скрипт для отладки пагинации 2ГИС
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option("excludeSwitches", ["enable-automation"])

driver = webdriver.Chrome(options=options)

try:
    SEARCH_QUERY = "Поесть"
    base_url = f"https://2gis.kz/astana/search/{SEARCH_QUERY}"

    print(f"Загрузка: {base_url}")
    driver.get(base_url)

    # Ждем загрузки
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/firm/"]'))
    )
    time.sleep(2)

    for page in range(1, 6):  # Попробуем 5 страниц
        print(f"\n{'='*50}")
        print(f"СТРАНИЦА {page}")
        print(f"{'='*50}")

        # Скроллим к пагинации
        scroll_containers = driver.find_elements(By.CSS_SELECTOR, '._8hh56jx')
        if scroll_containers:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scroll_containers[0])
            time.sleep(0.5)

        # Получаем первое кафе
        first_cafe = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/firm/"]')
        if first_cafe:
            first_href = first_cafe[0].get_attribute('href')
            print(f"Первое кафе: {first_href[:80]}...")

        # Проверяем пагинацию
        pagination = driver.find_elements(By.CSS_SELECTOR, '._1x4k6z7')
        print(f"Контейнер пагинации найден: {len(pagination) > 0}")

        # Ищем активную страницу
        active_page = driver.find_elements(By.CSS_SELECTOR, '._l934xo5')
        if active_page:
            print(f"Активная страница (UI): {active_page[0].text}")

        # Ищем все ссылки страниц
        page_links = driver.find_elements(By.CSS_SELECTOR, 'a._12164l30')
        print(f"Ссылки на страницы: {[l.text for l in page_links]}")

        # Ищем кнопки навигации
        nav_buttons_active = driver.find_elements(By.CSS_SELECTOR, '._n5hmn94')
        nav_buttons_inactive = driver.find_elements(By.CSS_SELECTOR, '._7q94tr')
        print(f"Активных кнопок навигации (_n5hmn94): {len(nav_buttons_active)}")
        print(f"Неактивных кнопок навигации (_7q94tr): {len(nav_buttons_inactive)}")

        # Определяем кнопку "Вперёд"
        # Она должна быть активной (_n5hmn94), но НЕ серой (_7q94tr)
        # Это вторая кнопка _n5hmn94 или первая активная после кнопки "Назад"

        next_button = None
        all_pagination_buttons = driver.find_elements(By.CSS_SELECTOR, '._1x4k6z7 button, ._1x4k6z7 ._n5hmn94, ._1x4k6z7 ._7q94tr')
        print(f"Все кнопки в пагинации: {len(all_pagination_buttons)}")

        # Попробуем найти кнопку "Вперёд" более точно
        # Внутри контейнера _1x4k6z7 есть div _5ocwns (страницы) и кнопки справа
        pagination_container = driver.find_elements(By.CSS_SELECTOR, '._1x4k6z7')
        if pagination_container:
            # Ищем все элементы с классами кнопок внутри контейнера
            buttons_in_pagination = pagination_container[0].find_elements(By.CSS_SELECTOR, '._n5hmn94, ._7q94tr')
            print(f"Кнопки внутри пагинации: {len(buttons_in_pagination)}")

            for i, btn in enumerate(buttons_in_pagination):
                cls = btn.get_attribute('class')
                is_active = '_n5hmn94' in cls and '_7q94tr' not in cls
                print(f"  Кнопка {i}: classes={cls[:50]}... active={is_active}")

            # Кнопка "Вперёд" - это последняя активная кнопка (вторая, если обе активны)
            if len(buttons_in_pagination) >= 2:
                # Вторая кнопка - "Вперёд"
                forward_btn = buttons_in_pagination[1]
                forward_class = forward_btn.get_attribute('class')

                if '_7q94tr' in forward_class:
                    print("Кнопка 'Вперёд' НЕАКТИВНА - это последняя страница!")
                    break
                else:
                    print("Кнопка 'Вперёд' АКТИВНА - кликаем...")
                    next_button = forward_btn

        if next_button is None:
            print("Кнопка 'Вперёд' не найдена!")
            break

        # Кликаем
        first_href_before = first_cafe[0].get_attribute('href') if first_cafe else None

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", next_button)

        # Ждём изменения
        print("Ожидание изменения контента...")
        for attempt in range(30):
            time.sleep(0.2)
            new_cafe = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/firm/"]')
            if new_cafe:
                new_href = new_cafe[0].get_attribute('href')
                if new_href != first_href_before:
                    print(f"✓ Контент изменился! Новое первое кафе: {new_href[:80]}...")
                    break
        else:
            print("⚠ Контент НЕ изменился после клика!")

        time.sleep(0.5)

    print("\n\nТест завершён!")
    input("Нажмите Enter для закрытия браузера...")

finally:
    driver.quit()

