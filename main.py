import asyncio

from scraping_script import ScrapingScript

if __name__ == '__main__':
    url = str(input("Enter url: "))
    srap = ScrapingScript(url)
    print(asyncio.run(srap.get_info_for_product()))
