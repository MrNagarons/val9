"""Тест парсинга og:description"""
from bs4 import BeautifulSoup
import re

output = []

html = open('C:/Users/rcsthcs/PycharmProjects/gisparser/html_files/cafe_0001.html', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')

# Найдём все meta теги
metas = soup.find_all('meta')
output.append(f"Всего meta тегов: {len(metas)}")

for m in metas:
    prop = m.get('property', '')
    name = m.get('name', '')
    content = m.get('content', '')[:100] if m.get('content') else ''
    if prop or name:
        output.append(f"  {prop or name}: {content}...")

# Ищем og:description
og = soup.find('meta', attrs={'property': 'og:description'})
if og:
    content = og.get('content', '')
    output.append(f"\n=== og:description ===\n{content}\n")

    # Тестируем regex
    rating_match = re.search(r'Оценка\s*(\d+[.,]\d+)', content)
    output.append(f"Rating match: {rating_match.group(1) if rating_match else 'None'}")
else:
    output.append("\nog:description не найден!")

    # Попробуем найти через регулярку в HTML
    og_match = re.search(r'property="og:description"\s+content="([^"]+)"', html)
    if og_match:
        output.append(f"\nНайден через regex: {og_match.group(1)}")

# Сохраняем в файл
with open('C:/Users/rcsthcs/PycharmProjects/gisparser/test_output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("Результаты сохранены в test_output.txt")


