import re
import requests
import logging
from typing import List
import os


def count_search_phrases(text: str, phrases: List[str]) -> int:
    count = 0
    for phrase in phrases:
        count += len(re.findall(re.escape(phrase), text, re.IGNORECASE))
    return count


def contains_money(text: str) -> bool:
    # Define patterns to match dollar amounts
    money_patterns = [
        r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # e.g., $1000.00, $1,000, $1000
        r'\d+\s*USD'                         # e.g., 1000 USD
    ]

    # Combine all patterns into a single regular expression
    combined_pattern = re.compile('|'.join(money_patterns), re.IGNORECASE)

    # Search for any of the money patterns in the text
    return bool(combined_pattern.search(text))


def download_image(url: str, filename: str, output_dir: str) -> None:
    try:
        response = requests.get(url)
        response.raise_for_status()
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "wb") as file:
            file.write(response.content)
        logging.info(f"Image downloaded: {filepath}")
    except Exception as e:
        logging.error(f"Failed to download image from {url}: {e}")
