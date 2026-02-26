from selenium import webdriver
from selenium.webdriver.common.by import By
import time

options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')

driver = webdriver.Chrome(options=options)

try:
    print("🔍 Проверка количества страниц с кафе...\n")

    page = 1

    while page <= 20:  # Проверяем первые 20 страниц
        url = f"https://2gis.kz/astana/search/кафе/page/{page}"
        driver.get(url)
        time.sleep(8)

        cafe_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/firm/"]')

        print(f"Страница {page:2d}: {len(cafe_links)} элементов", end='')

        if len(cafe_links) == 0:
            print(" ← КОНЕЦ")
            break
        else:
            print(" ✓")

        page += 1
        time.sleep(2)

    print(f"\n{'=' * 60}")
    print(f"✓ Всего доступно страниц: {page - 1}")
    print(f"✓ Примерное количество кафе: ~{(page - 1) * 10}-{(page - 1) * 15}")
    print(f"{'=' * 60}")

finally:
    driver.quit()
