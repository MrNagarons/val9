from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--disable-images')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options)
try:
    SEARCH_QUERY = "Поесть"
    url = f"https://2gis.kz/astana/search/{SEARCH_QUERY}"
    driver.get(url)
    time.sleep(1)

    wait = WebDriverWait(driver, 5)
    all_nav = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '._n5hmn94')))
    print(f"Найдено кнопок с классом _n5hmn94: {len(all_nav)}")
    for i, b in enumerate(all_nav):
        try:
            disp = b.is_displayed()
        except:
            disp = None
        try:
            dis_attr = b.get_attribute('disabled')
        except:
            dis_attr = None
        try:
            outer = b.get_attribute('outerHTML')[:200]
        except:
            outer = None
        try:
            has_svg = driver.execute_script("return arguments[0].querySelector('svg') !== null;", b)
        except:
            has_svg = None
        print(f"btn[{i}] displayed={disp} disabled={dis_attr} has_svg={has_svg} html_snippet={outer}")

    # collect first hrefs
    elems = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/firm/"]')
    print(f"Первый href до клика: {elems[0].get_attribute('href') if elems else None}")
    print(f"Количество элементов до клика: {len(elems)}")
    old_url = driver.current_url
    print(f"URL before: {old_url}")

    # choose second button if exists
    if len(all_nav) >= 2:
        btn = all_nav[1]
        # try click svg inside
        try:
            has_svg = driver.execute_script("return arguments[0].querySelector('svg') !== null;", btn)
            if has_svg:
                driver.execute_script("arguments[0].querySelector('svg').click();", btn)
            else:
                driver.execute_script("arguments[0].click();", btn)
            print("Клик выполнен по второй кнопке (или её svg)")
        except Exception as e:
            print("Ошибка при клике:", e)
    else:
        print("Второй кнопки нет")

    # wait a bit and print changes
    time.sleep(2)
    new_url = driver.current_url
    elems_after = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/firm/"]')
    print(f"URL after: {new_url}")
    print(f"Первый href после клика: {elems_after[0].get_attribute('href') if elems_after else None}")
    print(f"Количество элементов после клика: {len(elems_after)}")

finally:
    driver.quit()
    print('Тест завершён')

