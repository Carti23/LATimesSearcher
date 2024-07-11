from datetime import datetime
from typing import List, Tuple
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from RPA.Browser.Selenium import Selenium
import pandas as pd
from urllib.parse import urlparse
import os
import logging
from libraries.utils import count_search_phrases, contains_money, download_image
import re
import requests

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Logger:
    def log(self, message: str) -> None:
        logging.info(message)


class ImageDownloader:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def download_image(self, url: str, filename: str) -> None:
        download_image(url, filename, self.output_dir)


class SearchPhraseCounter:
    def count_search_phrases(self, text: str, phrases: List[str]) -> int:
        return count_search_phrases(text, phrases)


class MoneyChecker:
    def contains_money(self, text: str) -> bool:
        return contains_money(text)


class LATimesSearch:
    def __init__(
        self,
        logger: Logger,
        image_downloader: ImageDownloader,
        phrase_counter: SearchPhraseCounter,
        money_checker: MoneyChecker,
    ):
        self.logger = logger
        self.image_downloader = image_downloader
        self.phrase_counter = phrase_counter
        self.money_checker = money_checker
        self.browser = Selenium()
        self.browser.set_download_directory(os.getcwd())
        self.logger.log("Initialized LATimesSearch")

    def search(
        self,
        query: str,
        phrases: List[str],
        sort_by: str = "Relevance",
        max_pages: int = 5,
    ) -> List[Tuple[str, datetime, str, str, int, bool, str]]:
        self.logger.log(
            f"Starting search for query: {query} with sort order: {sort_by}"
        )
        search_url = "https://www.latimes.com/"
        try:
            self._open_browser(search_url)
            self._input_search_query(query)
            self._sort_results(sort_by)
            results = self._scrape_results(phrases, max_pages)
            return results
        except (WebDriverException, TimeoutException) as e:
            self.logger.log(f"Error during search: {e}")
            return []

    def _open_browser(self, url: str):
        self.browser.open_available_browser(url)
        self.browser.maximize_browser_window()
        self.browser.wait_until_page_contains_element(
            '//input[@data-element="search-form-input"]', timeout=30
        )

    def _input_search_query(self, query: str):
        self.browser.wait_until_element_is_visible(
            '//input[@data-element="search-form-input"]', timeout=30
        )
        self.browser.input_text(
            '//input[@data-element="search-form-input"]', query)
        self.browser.wait_until_element_is_visible(
            '//element_after_search_input', timeout=30)
        self.browser.press_keys(
            '//input[@data-element="search-form-input"]', "ENTER")
        self.browser.wait_until_element_is_visible(
            '//element_after_search_submit', timeout=30)

    def _sort_results(self, sort_by: str):
        sort_order_map = {"Relevance": "0", "Newest": "1", "Oldest": "2"}
        sort_value = sort_order_map.get(sort_by, "1")
        self.browser.wait_until_element_is_visible(
            '//select[@name="s"]', timeout=30)
        self.browser.select_from_list_by_value(
            '//select[@name="s"]', sort_value)
        self.browser.wait_until_element_is_visible(
            '//element_after_sort', timeout=30)

    def _scrape_results(
        self, phrases: List[str], max_pages: int
    ) -> List[Tuple[str, datetime, str, str, int, bool, str]]:
        data = []
        for current_page in range(1, max_pages + 1):
            self.browser.wait_until_element_is_visible(
                '//ul[@class="search-results-module-results-menu"]/li', timeout=30
            )
            results = self.browser.find_elements(
                '//ul[@class="search-results-module-results-menu"]/li'
            )
            for result in results:
                data.append(self._process_result(result, phrases))
            if not self._go_to_next_page():
                break
            self.browser.wait_until_element_is_visible(
                '//element_after_page_load', timeout=30)
        return data

    def _process_result(
        self, result, phrases: List[str]
    ) -> Tuple[str, datetime, str, str, int, bool, str]:
        try:
            title_element = result.find_element(By.XPATH, './/h2/a')
            title = title_element.text.strip()
            link = title_element.get_attribute('href')
            description = result.find_element(By.XPATH, './/p').text.strip()
            date_text = result.find_element(
                By.XPATH, './/time').get_attribute('datetime')
            date = datetime.strptime(date_text, "%Y-%m-%dT%H:%M:%S%z")
            count_phrases = self.phrase_counter.count_search_phrases(
                description, phrases)
            money_present = self.money_checker.contains_money(description)
            image_filename = self._download_image(result, title)
            return title, date, description, image_filename, count_phrases, money_present, link
        except (NoSuchElementException, TimeoutException) as e:
            self.logger.log(f"Error processing result: {e}")
            return "", datetime.now(), "", "", 0, False, ""

    def _download_image(self, result, title: str) -> str:
        try:
            image_element = result.find_element(
                By.XPATH, './/figure/picture/source')
            image_url = image_element.get_attribute("srcset").split()[0]
            alt_text = image_element.get_attribute("alt")
            image_filename = self._get_image_filename(
                title, alt_text, image_url)
            self.image_downloader.download_image(image_url, image_filename)
            return image_filename
        except (NoSuchElementException, TimeoutException, requests.RequestException) as e:
            self.logger.log(f"Error processing image: {e}")
            return ""

    def _go_to_next_page(self) -> bool:
        try:
            next_button = self.browser.find_element(
                '//div[@class="search-results-module-next-page"]/a'
            )
            if next_button:
                next_button.click()
                return True
            else:
                return False
        except (NoSuchElementException, TimeoutException) as e:
            self.logger.log(f"Failed to find next page button: {e}")
            return False

    @staticmethod
    def _get_image_filename(title: str, alt_text: str, url: str) -> str:
        if alt_text:
            filename = re.sub(r"[^a-zA-Z0-9_\-]", "_", alt_text[:50])
        else:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = re.sub(r"[^a-zA-Z0-9_\-]", "_", title[:50])
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"{filename}_{timestamp}.jpg"

    @staticmethod
    def save_to_excel(
        data: List[Tuple[str, datetime, str, str, int, bool, str]],
        filename: str = "search_results.xlsx",
    ):
        df = pd.DataFrame(
            data,
            columns=[
                "Title",
                "Date",
                "Description",
                "Picture Filename",
                "Count of Search Phrases",
                "Money Present",
                "Link",
            ],
        )
        df.to_excel(filename, index=False)
        logging.info(f"Results saved to Excel: {filename}")
