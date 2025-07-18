import requests
import bs4
import tinydb
import csv

sites = [
    "https://www.swerk-wue.de/bamberg/essen-trinken/mensen-speiseplaene/mensa-austrasse-bamberg/menu",
    "https://www.swerk-wue.de/bamberg/essen-trinken/mensen-speiseplaene/mensa-feldkirchenstrasse-bamberg/menu",
]

import logging
from logfmter import Logfmter

handler = logging.StreamHandler()
handler.setFormatter(Logfmter())
logging.basicConfig(handlers=[handler], level=logging.DEBUG)

logger = logging.getLogger("mensa_scraper")

database = tinydb.TinyDB("day_menu_entries.json")

def get_site_content(url):
    logger.debug("Fetching site content...", extra={"url": url})
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses
    logger.debug("Fetched site content.", extra={"url": url, "status_code": response.status_code, "length": len(response.text)})
    return response.text

def get_day_menus_html(content):
    logger.debug("Getting day menus HTML...")
    soup = bs4.BeautifulSoup(content, "html.parser")
    day_menus = [str(div) for div in soup.find_all("div", class_="day-menu")]
    logger.debug(f"Got day menus HTML.", extra={"count": len(day_menus)})
    return day_menus

class DayMenuEntry:
    def __init__(self, date_text, data_day, data_dispo, data_type_title, data_price_student, is_climate_plate, co2_per_serving_text, date, co2_per_serving_int, title, scrape_datetime):
        self.date_text = date_text
        self.date = date
        self.day_in_year = data_day
        self.data_dispo = data_dispo
        self.diet = data_type_title
        self.price_student = data_price_student
        self.is_climate_plate = is_climate_plate
        self.co2_per_serving = co2_per_serving_text
        self.co2_per_serving_int = co2_per_serving_int
        self.title = title
        self.scrape_datetime = scrape_datetime

    def __repr__(self):
        return (f"DayMenuEntry("
                f"date_text={self.date_text}, "
                f"date={self.date}, "
                f"day_in_year={self.day_in_year}, "
                f"data_dispo={self.data_dispo}, "
                f"diet={self.diet}, "
                f"price_student={self.price_student}, "
                f"is_climate_plate={self.is_climate_plate}, "
                f"co2_per_serving={self.co2_per_serving}, "
                f"co2_per_serving_int={self.co2_per_serving_int}, "
                f"title={self.title}, "
                f"scrape_datetime={self.scrape_datetime}, "
                f")")

def parse_day_menu(html):
    logger.debug("Parsing day menu HTML...")
    soup = bs4.BeautifulSoup(html, "html.parser")
    day_menu_entries = []

    logger.debug("Finding day menu div...")
    day_menu_div = soup.find("div", class_="day-menu")

    logger.debug("Extracting date_text...")
    date = day_menu_div.find("h3").text.strip()
    logger.debug("Extracted date_text.", extra={"date_text": date})

    # data-day is the day of the year, 0-based.
    logger.debug("Extracting data-day...")
    data_day = day_menu_div.get("data-day")
    logger.debug("Extracted data-day.", extra={"data_day": data_day})

    logger.debug("Converting data-day to date...")
    from datetime import datetime, timedelta
    base_date = datetime(datetime.now().year, 1, 1)
    date = base_date + timedelta(days=int(data_day))
    date = date.strftime("%Y-%m-%d")
    logger.debug("Converted data-day to date.", extra={"date": date})

    logger.debug("Extracting individual menu entries...")
    articles = day_menu_div.find_all("article")
    logger.debug(f"Extracted individual menu entries.", extra={"count": len(articles)})

    for article in articles:
        logger.debug("Processing article...")

        logger.debug("Extracting title...")
        title = article.find("h5").text.strip()
        logger.debug("Extracted title.", extra={"title": title})

        logger.debug("Extracting data-dispo...")
        data_dispo = article.get("data-dispo")
        logger.debug("Extracted data-dispo.", extra={"data_dispo": data_dispo})

        logger.debug("Extracting data-type-title...")
        data_type_title = article.find("span", class_="food-icon").get("data-type-title")
        logger.debug("Extracted data-type-title.", extra={"data_type_title": data_type_title})

        logger.debug("Extracting data-price-student...")
        data_price_student = article.find("div", class_="price").get("data-price-student")
        logger.debug("Extracted data-price-student.", extra={"data_price_student": data_price_student})

        logger.debug("Checking for climate plate...")
        is_climate_plate = article.find("span", class_="climate-plate") is not None
        logger.debug("Checked for climate plate.", extra={"is_climate_plate": is_climate_plate})

        logger.debug("Extracting CO2 per serving...")
        co2_element = article.find("div", class_="co2-per-serving")
        co2_per_serving_text = None
        if co2_element:
            co2_per_serving_text = co2_element.find("span").text.strip()
            logger.debug("Extracted CO2 per serving.", extra={"co2_per_serving_text": co2_per_serving_text})

            logger.debug("Converting CO2 text to int...", extra={"co2_per_serving_text": co2_per_serving_text})
            co2_per_serving_int = int(co2_per_serving_text.replace(" g", ""))
            logger.debug("Converted CO2 text to int.", extra={"co2_per_serving_text": co2_per_serving_text, "co2_per_serving_int": co2_per_serving_int})

        entry = DayMenuEntry(
            date_text=date,
            data_day=data_day,
            data_dispo=data_dispo,
            data_type_title=data_type_title,
            data_price_student=data_price_student,
            is_climate_plate=is_climate_plate,
            co2_per_serving_text=co2_per_serving_text,
            date=date,
            co2_per_serving_int=co2_per_serving_int if co2_element else None,
            title=title,
            scrape_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        day_menu_entries.append(entry)

        logger.debug("Processed article.", extra={"entry": entry})

    logger.debug("Finished parsing day menu HTML.", extra={"count": len(day_menu_entries)})
    return day_menu_entries

def convert_database_to_csv():
    logger.debug("Converting database to CSV...")
    all_entries = database.all()
    csv_file = "day_menu_entries.csv"

    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=all_entries[0].keys(), delimiter=';')
        writer.writeheader()
        writer.writerows(all_entries)

    logger.debug("Converted database to CSV.", extra={"csv_file": csv_file})

def main():
    all_entries = []

    for site in sites:
        content = get_site_content(site)
        day_menus_html = get_day_menus_html(content)
        for day_menu_html in day_menus_html:
            entries = parse_day_menu(day_menu_html)
            all_entries.extend(entries)

    for entry in all_entries:
        logger.debug("Dumping Day Menu Entry...", extra={
            "Title": entry.title,
            "Diet": entry.diet,
            "CO2": entry.co2_per_serving_int,
        })

        database.insert({
            "date_text": entry.date_text,
            "date": entry.date,
            "day_in_year": entry.day_in_year,
            "data_dispo": entry.data_dispo,
            "diet": entry.diet,
            "price_student": entry.price_student,
            "is_climate_plate": entry.is_climate_plate,
            "co2_per_serving_text": entry.co2_per_serving,
            "co2_per_serving_int": entry.co2_per_serving_int,
            "title": entry.title,
            "scrape_datetime": entry.scrape_datetime,
        })

    convert_database_to_csv()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
