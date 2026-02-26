from selenium import webdriver
from selenium.webdriver.common.by import By
import time

options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-images')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options)
driver.implicitly_wait(1)

try:
    SEARCH_QUERY = "Поесть"

    for page in range(0, 5):  # Проверим первые 5 страниц
        url = f"https://2gis.kz/astana/search/{SEARCH_QUERY}?p={page}"
        print(f"\n[Страница {page + 1}] Загружаю: {url}")

        driver.get(url)
        time.sleep(0.5)

        # Прокрутка
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.3)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.3)

        # Находим элементы
        cafe_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/firm/"]')
        print(f"Найдено кафе: {len(cafe_links)}")

        # Печатаем первые 3 URL
        for i, link in enumerate(cafe_links[:3]):
            href = link.get_attribute('href')
            print(f"  - {href}")

        if len(cafe_links) == 0:
            print("⚠ Пустая страница!")

finally:
    driver.quit()
    print("\n✓ Тест завершён")

