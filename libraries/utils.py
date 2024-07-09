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
    money_patterns = [
        r"\$\d+(,\d{3})*(\.\d{2})?",
        r"\b\d+(,\d{3})*\.\d{2}\b",
        r"\b\d+ dollars\b",
        r"\b\d+ USD\b",
    ]
    for pattern in money_patterns:
        if re.search(pattern, text):
            return True
    return False


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
