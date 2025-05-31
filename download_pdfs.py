import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import logging
from datetime import datetime
from typing import List, Tuple
from requests.exceptions import RequestException
import json
import re
import time

BASE_URL = "http://imagem.sian.an.gov.br/acervo/derivadas"
PDF_DIR = Path("pdfs")
JSON_DIR = Path("jsons")
LOG_DIR = Path("logs")
MAX_THREADS = min(10, os.cpu_count() * 2)
TIMEOUT_SECONDS = 15
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2

LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def download_pdf(url: str, filename: str, max_retries: int = RETRY_ATTEMPTS) -> bool:
    filepath = PDF_DIR / filename

    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()

            if not response.content.startswith(b'%PDF'):
                raise ValueError("Downloaded file is not a valid PDF")

            filepath.write_bytes(response.content)
            logger.info(f"Successfully downloaded: {filepath}")
            return True

        except (RequestException, ValueError) as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to download {url} after {max_retries} attempts: {str(e)}")
                return False
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}. Retrying...")
            time.sleep(RETRY_DELAY)

    return False


def sanitize_filename(title: str) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', title).strip()
    return sanitized[:255]


def get_all_links() -> List[Tuple[str, str]]:
    json_files = list(JSON_DIR.glob("*.json"))

    if not json_files:
        logger.error("No JSON files found in jsons directory.")
        return []

    tasks = []
    for json_file in json_files:
        try:
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list) and all("title" in item and "link" in item for item in data):
                logger.info(f"Processing JSON file: {json_file}")
                for item in data:
                    path = item["link"]
                    title = item["title"]
                    sanitized_title = sanitize_filename(title) + ".pdf"
                    full_url = f"{BASE_URL}{path}"
                    tasks.append((full_url, sanitized_title))
            else:
                logger.warning(f"File {json_file} does not contain expected data format.")

        except Exception as e:
            logger.warning(f"Failed to parse {json_file}: {str(e)}")

    if not tasks:
        logger.error("No valid JSON file with 'title' and 'link' fields found.")
    return tasks


def main():
    PDF_DIR.mkdir(exist_ok=True)

    tasks = get_all_links()
    if not tasks:
        logger.error("No download tasks found")
        return

    logger.info(f"Starting download of {len(tasks)} files with {MAX_THREADS} threads")

    success_count = 0
    failed_count = 0

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_url = {
            executor.submit(download_pdf, url, filename): url
            for url, filename in tasks
        }

        for future in as_completed(future_to_url):
            if future.result():
                success_count += 1
            else:
                failed_count += 1

    logger.info(f"Download complete. Success: {success_count}, Failed: {failed_count}")


if __name__ == "__main__":
    start_time = time.time()
    main()
    logger.info(f"Total execution time: {time.time() - start_time:.2f} seconds")
