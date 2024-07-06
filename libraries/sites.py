import logging
import os
import time
from datetime import datetime
from typing import List, Tuple
from selenium.webdriver.common.by import By
from RPA.Browser.Selenium import Selenium
import pandas as pd
from urllib.parse import urlparse, unquote
from libraries.utils import count_search_phrases, contains_money, download_image

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Logger:
    def log(self, message: str) -> None:
        logging.info(message)


class ImageDownloader:
    def download_image(self, url: str, filename: str) -> None:
        download_image(url, filename)


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
        self.logger.log("Initialized LATimesSearcher")

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

        try:
            self.browser.open_available_browser(
                "https://www.latimes.com/", headless=False
            )
            self.browser.wait_until_element_is_visible(
                '//button[@data-element="search-button"]', timeout=30
            )
            self.browser.click_element(
                '//button[@data-element="search-button"]')
            self.browser.wait_until_element_is_visible(
                '//input[@data-element="search-form-input"]', timeout=30
            )
            self.browser.input_text(
                '//input[@data-element="search-form-input"]', query)
            time.sleep(2)
            self.browser.press_keys(
                '//input[@data-element="search-form-input"]', "ENTER"
            )
            time.sleep(5)

            sort_order_map = {"Relevance": "0", "Newest": "1", "Oldest": "2"}
            sort_value = sort_order_map.get(sort_by, "1")
            self.browser.wait_until_element_is_visible(
                '//select[@name="s"]', timeout=30
            )
            self.browser.select_from_list_by_value(
                '//select[@name="s"]', sort_value)
            time.sleep(5)

            data = []
            current_page = 1

            while current_page <= max_pages:
                self.browser.wait_until_element_is_visible(
                    '//ul[@class="search-results-module-results-menu"]/li', timeout=30
                )
                results = self.browser.find_elements(
                    '//ul[@class="search-results-module-results-menu"]/li'
                )

                for result in results:
                    try:
                        title_element = result.find_element(
                            By.XPATH, './/h3[@class="promo-title"]/a'
                        )
                        title = title_element.text
                        link = title_element.get_attribute("href")
                    except Exception as e:
                        logging.error(f"Error processing title and link: {e}")
                        continue

                    description = ""
                    date = None
                    image_filename = ""

                    try:
                        description_element = result.find_element(
                            By.XPATH, './/p[@class="promo-description"]'
                        )
                        description = description_element.text
                    except Exception as e:
                        logging.error(f"Error processing description: {e}")

                    try:
                        date_element = result.find_element(
                            By.XPATH, './/p[@class="promo-timestamp"]'
                        )
                        date = datetime.fromtimestamp(
                            int(date_element.get_attribute(
                                "data-timestamp")) / 1000
                        )
                    except Exception as e:
                        logging.error(f"Error processing date: {e}")

                    try:
                        image_element = result.find_element(
                            By.XPATH, ".//picture/source"
                        )
                        image_url = image_element.get_attribute(
                            "srcset").split()[0]
                        image_filename = self.get_image_filename(image_url)
                        self.image_downloader.download_image(
                            image_url, image_filename)
                    except Exception as e:
                        logging.error(f"Error processing image: {e}")
                        image_filename = ""

                    combined_text = f"{title} {description}"
                    count_phrases = self.phrase_counter.count_search_phrases(
                        combined_text, phrases
                    )
                    money_present = self.money_checker.contains_money(
                        combined_text)

                    data.append(
                        (
                            title,
                            date,
                            description,
                            image_filename,
                            count_phrases,
                            money_present,
                            link,
                        )
                    )

                try:
                    next_button = self.browser.find_element(
                        '//div[@class="search-results-module-next-page"]/a'
                    )
                    if next_button:
                        next_button.click()
                        current_page += 1
                        time.sleep(5)
                    else:
                        break
                except Exception as e:
                    logging.error(f"Failed to find next page button: {e}")
                    break

        except Exception as e:
            logging.error(f"Error during search: {e}")
        finally:
            self.browser.close_all_browsers()

        self.logger.log("Search completed")
        return data

    @staticmethod
    def get_image_filename(url: str) -> str:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        return unquote(filename)

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
