import re
import requests
import logging
from typing import List


def count_search_phrases(text: str, phrases: List[str]) -> int:
    count = 0
    for phrase in phrases:
        count += len(re.findall(re.escape(phrase), text, re.IGNORECASE))
    return count


def contains_money(text: str) -> bool:
    # Improved money patterns
    money_patterns = [
        r"\$\d+(,\d{3})*(\.\d{2})?",  # $12,345.67 or $12345.67
        r"\b\d+(,\d{3})*\.\d{2}\b",  # 12,345.67 or 12345.67
        r"\b\d+ dollars\b",  # 12 dollars
        r"\b\d+ USD\b",  # 12 USD
    ]
    # Adding word boundaries to avoid matching parts of words
    for pattern in money_patterns:
        if re.search(pattern, text):
            return True
    return False


def download_image(url: str, filename: str) -> None:
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(filename, "wb") as file:
            file.write(response.content)
        logging.info(f"Image downloaded: {filename}")
    except Exception as e:
        logging.error(f"Failed to download image from {url}: {e}")
