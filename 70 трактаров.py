import requests
from bs4 import BeautifulSoup
import pandas as pd
import re


URL = "https://www.rialcom.ru/internet_tariffs/"


HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/114.0.5735.199 Safari/537.36')
}


def get_html(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()  # Если код ответа не 200, вызовет исключение
        return response.text
    except Exception as e:
        print("Ошибка при получении страницы:", e)
        return None


def clean_price(text):
    digits = re.sub(r"[^\d]", "", text)  # Убираем все, кроме цифр
    return int(digits) if digits.isdigit() else 0


def clean_speed(text):
    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1)) // 1000
    return 0


def extract_channels(text):
    match = re.search(r"(\d+)\s*канал", text)
    if match:
        return int(match.group(1))
    return None


def parse_internet_tariffs(soup, section_id, suffix):
    tariffs = []  # Здесь будем сохранять данные
    section = soup.find("div", id=section_id)
    if section is None:
        print("Раздел не найден:", section_id)
        return tariffs


    tables = section.find_all("table")
    if not tables:
        print("Таблица с тарифами не найдена в", section_id)
        return tariffs


    table = tables[0]
    rows = table.find_all("tr")[1:]
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 4:
            continue


        name = cols[0].text.strip() + suffix
        price = clean_price(cols[1].text)
        speed = clean_speed(cols[3].text)
        tariffs.append([name, None, speed, price])
        print("Добавлен тариф (Интернет):", name, "Скорость:", speed, "Цена:", price)
    return tariffs


def parse_tv_tariffs(soup, section_id, suffix):
    tariffs = []
    section = soup.find("div", id=section_id)
    if section is None:
        print("Раздел не найден:", section_id)
        return tariffs


    tables = section.find_all("table")
    if len(tables) < 2:
        print("Таблица с ТВ тарифами не найдена в", section_id)
        return tariffs


    table = tables[1]


    header_row = table.find("tr")
    headers = [th.text.strip() for th in header_row.find_all("th")[1:]]
    print("Заголовки тарифов ТВ:", headers)


    rows = table.find_all("tr")[1:]
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < len(headers) + 1:
            continue

        base_name = cols[0].text.strip()
        channels = extract_channels(base_name)
        for i, col in enumerate(cols[1:]):
            name = f"{base_name} + {headers[i]}" + suffix
            price = clean_price(col.text)
            speed_match = re.search(r"(\d+)", headers[i])
            speed = int(speed_match.group(1)) if speed_match else 0
            tariffs.append([name, channels, speed, price])
            print("Добавлен тариф (ТВ):", name, "Каналы:", channels, "Скорость:", speed, "Цена:", price)
    return tariffs


def main():

    html = get_html(URL)
    if html is None:
        return


    soup = BeautifulSoup(html, "html.parser")


    all_tariffs = []


    tariffs_internet_m = parse_internet_tariffs(soup, "collapse1", "_м")
    all_tariffs.extend(tariffs_internet_m)


    tariffs_internet_c = parse_internet_tariffs(soup, "collapse2", "_ч")
    all_tariffs.extend(tariffs_internet_c)


    tariffs_tv_m = parse_tv_tariffs(soup, "collapse1", "_м")
    all_tariffs.extend(tariffs_tv_m)


    tariffs_tv_c = parse_tv_tariffs(soup, "collapse2", "_ч")
    all_tariffs.extend(tariffs_tv_c)

    print("\nОбщее количество тарифов найдено:", len(all_tariffs))

    # Сохраняем данные в Excel-файл с помощью pandas
    df = pd.DataFrame(all_tariffs, columns=["Название тарифа", "Количество каналов", "Скорость (Мбит/с)", "Цена"])
    df.to_excel("tariffs.xlsx", index=False)
    print("Данные сохранены в файл tariffs.xlsx")


if __name__ == "__main__":
    main()
