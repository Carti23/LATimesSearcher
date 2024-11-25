# LATimesSearcher

## Overview

This project is an RPA (Robotic Process Automation) bot designed to automate the extraction of news articles from a selected news website. The bot processes search parameters, retrieves news articles, and outputs structured data into an Excel file, along with downloaded images.

## Features

- **Automated Data Extraction**: Fetches article titles, publication dates, descriptions, and associated images.
- **Excel Output**: Saves news data into an Excel file, including:
  - Title
  - Date
  - Description
  - Picture filename
  - Search phrase count in title and description
  - Presence of monetary amounts in the content
- **Dynamic Parameters**: Accepts the following input parameters via Robocloud work items:
  - Search phrase
  - News category/section/topic
  - Time period (current month, or up to the specified number of months)
- **Image Handling**: Downloads associated images and links them in the Excel file.

## Workflow

1. Open a selected news website (e.g., [AP News](https://apnews.com), [Reuters](https://www.reuters.com)).
2. Perform a search using the provided search phrase.
3. Filter results by category/topic (if applicable).
4. Extract and save data for articles published within the specified time frame.
5. Download article images and include their filenames in the output.

## Prerequisites

- Python 3.8+
- [Robocorp](https://robocorp.com/) installed and configured
- Necessary Python packages (see `requirements.txt`):
  - `rpaframework`
  - `openpyxl`
  - Other dependencies

## Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-repo/news-automation-bot.git
   cd news-automation-bot
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration**
   - Define input parameters via Robocloud work items.
   - Set up Robocloud for deployment and process execution.

4. **Run the Bot**
   ```bash
   python main.py
   ```

## Output

The bot generates:
- An Excel file in the `/output` directory containing the extracted news data.
- Images downloaded to the `/output` directory, with filenames linked in the Excel file.

## Development Guidelines

- **Code Quality**: Ensure PEP8 compliance and use an object-oriented design.
- **Resiliency**: Implement fault-tolerant architecture (e.g., explicit waits for website interactions).
- **Logging**: Use structured logging to track bot actions and errors.

## Bonus Features

- Incorporate creative logging messages to showcase personality and engagement.
- Make the bot intuitive and extensible for future improvements.

## Repository Structure

```
news-automation-bot/
├── main.py              # Entry point for the bot
├── config/
│   ├── settings.json    # Configuration file for parameters
├── output/              # Directory for output files
├── logs/                # Directory for logs
├── requirements.txt     # Python dependencies
├── README.md            # Project documentation
```

## Contributing

Contributions are welcome! Feel free to open issues or submit PRs to improve this bot.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
