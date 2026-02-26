from bs4 import BeautifulSoup
import pandas as pd
import os
import json
import re

# Загрузка метаданных
with open("html_files/metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

print(f"🔄 Повторный парсинг с новыми полями...\n")

cafes_data = []

for item in metadata:
    try:
        filename = item['filename']
        filepath = os.path.join("html_files", filename)

        with open(filepath, "r", encoding="utf-8") as f:
            html = f.read()

        soup = BeautifulSoup(html, 'html.parser')

        # ========================================
        # ЗДЕСЬ ДОБАВЛЯЙТЕ ИЛИ УБИРАЙТЕ ПОЛЯ
        # ========================================

        name = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Не указано"

        # Новое поле: Email
        email = "Не указано"
        email_elem = soup.find('a', href=re.compile(r'mailto:'))
        if email_elem:
            email = email_elem.get('href', '').replace('mailto:', '')

        # Новое поле: Instagram
        instagram = "Не указано"
        ig_elem = soup.find('a', href=re.compile(r'instagram\.com'))
        if ig_elem:
            instagram = ig_elem.get('href', '')

        # Новое поле: Описание
        description = "Не указано"
        desc_elem = soup.find('div', class_=re.compile(r'description|about', re.I))
        if desc_elem:
            description = desc_elem.get_text(strip=True)[:200]  # Первые 200 символов

        cafes_data.append({
            "№": item['id'],
            "Название": name,
            "Email": email,
            "Instagram": instagram,
            "Описание": description,
            "HTML файл": filename
        })

        print(f"✓ {item['id']:3d}. {name[:40]}")

    except Exception as e:
        print(f"✗ {item['id']}: {str(e)[:50]}")
        continue

# Создание новой таблицы
if cafes_data:
    df = pd.DataFrame(cafes_data)
    df.to_excel("cafes_astana_NEW_FIELDS.xlsx", index=False)
    df.to_csv("cafes_astana_NEW_FIELDS.csv", index=False, encoding="utf-8-sig")

    print(f"\n✓ Новая таблица создана: cafes_astana_NEW_FIELDS.xlsx")
    print(df.head())
