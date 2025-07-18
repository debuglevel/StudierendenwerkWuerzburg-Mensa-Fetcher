import requests
import bs4

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

def main():
    for site in sites:
        content = get_site_content(site)
        day_menus_html = get_day_menus_html(content)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
