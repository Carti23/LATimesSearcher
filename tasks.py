import os
from typing import List
from libraries.sites import LATimesSearch
from libraries.sites import Logger, ImageDownloader, SearchPhraseCounter, MoneyChecker

def run_latimes_search(
    query: str, phrases: List[str], sort_by: str = "Newest", max_pages: int = 5
):
    logger = Logger()
    image_downloader = ImageDownloader()
    phrase_counter = SearchPhraseCounter()
    money_checker = MoneyChecker()
    searcher = LATimesSearch(logger, image_downloader,
                             phrase_counter, money_checker)
    results = searcher.search(
        query, phrases, sort_by=sort_by, max_pages=max_pages)
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "search_results.xlsx")
    searcher.save_to_excel(results, filename=output_path)

if __name__ == "__main__":
    phrases = ["space", "rocket", "NASA"]
    sort_by = "Newest"
    max_pages = 2
    run_latimes_search("space", phrases, sort_by=sort_by, max_pages=max_pages)
