import os
from typing import List
from libraries.sites import LATimesSearch
from libraries.sites import Logger, ImageDownloader, SearchPhraseCounter, MoneyChecker
from RPA.Robocorp.WorkItems import WorkItems


def run_latimes_search(
    query: str, phrases: List[str], sort_by: str = "Newest", max_pages: int = 5
):
    logger = Logger()
    output_directory = "output"
    image_downloader = ImageDownloader(output_directory)
    phrase_counter = SearchPhraseCounter()
    money_checker = MoneyChecker()
    searcher = LATimesSearch(logger, image_downloader, phrase_counter, money_checker)
    results = searcher.search(query, phrases, sort_by=sort_by, max_pages=max_pages)
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "search_results.xlsx")
    searcher.save_to_excel(results, filename=output_path)


if __name__ == "__main__":
    work_items = WorkItems()
    work_items.get_input_work_item()

    phrases = work_items.get_work_item_variable("phrases", ["space", "rocket", "NASA"])
    sort_by = work_items.get_work_item_variable("sort_by", "Newest")
    max_pages = work_items.get_work_item_variable("max_pages", 1)

    run_latimes_search("space", phrases, sort_by=sort_by, max_pages=max_pages)
    work_items.clear_work_item()
