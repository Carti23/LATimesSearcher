from datetime import datetime
from typing import List, Tuple
from selenium.webdriver.common.by import By
from RPA.Browser.Selenium import Selenium
import pandas as pd
from urllib.parse import urlparse
import os
import logging
from libraries.utils import count_search_phrases, contains_money, download_image
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

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
            data = self._scrape_results(phrases, max_pages)
        except Exception as e:
            logging.error(f"Error during search: {e}")
            data = []
        finally:
            self.browser.close_all_browsers()
            self.logger.log("Search completed")
        return data

    def _open_browser(self, url: str):
        self.browser.open_available_browser(url, headless=False)
        self.browser.wait_until_element_is_visible(
            '//button[@data-element="search-button"]', timeout=30
        )
        self.browser.click_element('//button[@data-element="search-button"]')

    def _input_search_query(self, query: str):
        self.browser.wait_until_element_is_visible(
            '//input[@data-element="search-form-input"]', timeout=40
        )
        self.browser.input_text(
            '//input[@data-element="search-form-input"]', query)
        self.browser.press_keys(
            '//input[@data-element="search-form-input"]', "ENTER")
        WebDriverWait(self.browser.driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, '//ul[@class="search-results-module-results-menu"]/li'))
        )

    def _sort_results(self, sort_by: str):
        sort_order_map = {"Relevance": "0", "Newest": "1", "Oldest": "2"}
        sort_value = sort_order_map.get(sort_by, "1")
        self.browser.wait_until_element_is_visible(
            '//select[@name="s"]', timeout=30)
        self.browser.select_from_list_by_value(
            '//select[@name="s"]', sort_value)
        WebDriverWait(self.browser.driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, '//ul[@class="search-results-module-results-menu"]/li'))
        )

    def _scrape_results(
        self, phrases: List[str], max_pages: int
    ) -> List[Tuple[str, datetime, str, str, int, bool, str]]:
        data = []
        for _ in range(max_pages):
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
        return data

    def _process_result(
        self, result, phrases: List[str]
    ) -> Tuple[str, datetime, str, str, int, bool, str]:
        title, link = self._extract_title_and_link(result)
        description = self._extract_description(result)
        date = self._extract_date(result)
        image_filename = self._download_image(result, title)
        combined_text = f"{title} {description}"
        count_phrases = self.phrase_counter.count_search_phrases(
            combined_text, phrases)
        money_present = self.money_checker.contains_money(combined_text)
        return (
            title,
            date,
            description,
            image_filename,
            count_phrases,
            money_present,
            link,
        )

    def _extract_title_and_link(self, result) -> Tuple[str, str]:
        try:
            title_element = result.find_element(
                By.XPATH, './/h3[@class="promo-title"]/a', timeout=10
            )
            title = title_element.text
            link = title_element.get_attribute("href")
            return title, link
        except NoSuchElementException as e:
            logging.error(f"Error processing title and link: {e}")
            return "", ""

    def _extract_description(self, result) -> str:
        try:
            description_element = result.find_element(
                By.XPATH, './/p[@class="promo-description"]', timeout=10
            )
            return description_element.text
        except NoSuchElementException as e:
            logging.error(f"Error processing description: {e}")
            return ""

    def _extract_date(self, result) -> datetime:
        try:
            date_element = result.find_element(
                By.XPATH, './/p[@class="promo-timestamp"]', timeout=10
            )
            return datetime.fromtimestamp(
                int(date_element.get_attribute("data-timestamp")) / 1000
            )
        except (NoSuchElementException, ValueError) as e:
            logging.error(f"Error processing date: {e}")
            return None

    def _download_image(self, result, title: str) -> str:
        try:
            image_element = result.find_element(By.XPATH, ".//picture/source", timeout=15)
            image_url = image_element.get_attribute("srcset").split()[0]
            alt_text = image_element.get_attribute("alt")
            image_filename = self._get_image_filename(
                title, alt_text, image_url)
            self.image_downloader.download_image(image_url, image_filename)
            return image_filename
        except NoSuchElementException as e:
            logging.error(f"Error processing image: {e}")
            return ""

    def _go_to_next_page(self) -> bool:
        try:
            next_button = self.browser.find_element(
                '//div[@class="search-results-module-next-page"]/a'
            )
            if next_button:
                next_button.click()
                WebDriverWait(self.browser.driver, 30).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//ul[@class="search-results-module-results-menu"]/li'))
                )
                return True
            else:
                return False
        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f"Failed to find next page button: {e}")
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
