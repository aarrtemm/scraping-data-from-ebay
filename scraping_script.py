import json
import os

import aiohttp
import aiofiles
import ssl
from bs4 import BeautifulSoup


class ScrapingScript:
    def __init__(self, url=None):
        self.url = url
        self.__ssl_context = ssl.create_default_context()
        self.__ssl_context.check_hostname = False
        self.__ssl_context.verify_mode = ssl.CERT_NONE

    async def __get_data(self) -> str | None:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.url, ssl=self.__ssl_context) as resp:
                    resp.raise_for_status()  # Raise exception for non-200 responses
                    return await resp.text(encoding="utf-8")
            except aiohttp.ClientError as e:
                print(f"Error fetching data: {e}")
                return None

    @staticmethod
    async def __write_to_file(data):
        if data:
            filename = "page.html"
            try:
                async with aiofiles.open(filename, "w", encoding="utf-8") as file:
                    await file.write(data)
                return filename
            except IOError as e:
                print(f"Error writing to file: {e}")
        return None

    async def collect_info_from_page(self):
        data = await self.__get_data()
        if data:
            filename = await self.__write_to_file(data)
            if filename:
                try:
                    async with aiofiles.open(filename, "r", encoding="utf-8") as file:
                        data = await file.read()
                    soup = BeautifulSoup(data, "html.parser")

                    title_elem = soup.find("h1", class_="x-item-title__mainTitle")
                    price_elem = soup.find("div", class_="x-price-primary").find("span")
                    condition_elem = soup.find("div", class_="x-item-condition-text").find("span", class_="ux-textspans")
                    description_elem = soup.find("div", class_="d-item-description").find("iframe")

                    title = title_elem.text.strip() if title_elem else ""
                    price = float(price_elem.text.split("$")[1]) if price_elem else 0.0
                    condition = condition_elem.text.strip() if condition_elem else ""
                    description_url = description_elem.get("src") if description_elem else ""

                    users_elem = soup.find("div", class_="x-sellercard-atf__info")
                    users = {
                        "username": users_elem.find("a").get_text(strip=True) if users_elem else "",
                        "link_to_user": users_elem.find("a").get("href") if users_elem else ""
                    }
                    links_to_images = []
                    for button in soup.find_all("button", class_="ux-image-grid-item"):
                        img_tag = button.find("img")
                        if img_tag and img_tag.get("src"):
                            links_to_images.append(img_tag.get("src"))
                    link_to_product = self.url

                    os.remove(filename)

                    return {
                        "title": title,
                        "price": price,
                        "link_to_product": link_to_product,
                        "users": users,
                        "condition": condition,
                        "description": await self.__get_description(description_url),
                        "links_to_images": links_to_images
                    }
                except Exception as e:
                    print(f"Error processing page data: {e}")

        return None

    async def __get_description(self, url):
        if not url:
            return []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=self.__ssl_context) as resp:
                    resp.raise_for_status()
                    soup = BeautifulSoup(await resp.text(), "html.parser")
                    return [p.get_text(strip=True) for p in soup.find_all("p")]
        except aiohttp.ClientError as e:
            print(f"Error fetching description: {e}")
            return []

    async def get_info_for_product(self):
        data = await self.collect_info_from_page()
        if data:
            await self.__format_data_to_json(data)

    @staticmethod
    async def __format_data_to_json(data):
        try:
            with open("data.json", "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Error writing JSON data: {e}")
