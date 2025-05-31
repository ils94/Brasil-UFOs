import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import logging
from datetime import datetime
from typing import List, Tuple
from requests.exceptions import RequestException

BASE_URL = "http://imagem.sian.an.gov.br/acervo/derivadas"
PDF_DIR = Path("pdfs")
TXT_DIR = Path("txt")
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


def get_all_links() -> List[Tuple[str, str]]:
    if not TXT_DIR.exists():
        logger.error(f"Text file directory not found: {TXT_DIR}")
        return []

    tasks = []
    txt_files = sorted(TXT_DIR.glob("*.txt"))

    for txt_file in txt_files:
        logger.info(f"Processing text file: {txt_file}")
        try:
            with txt_file.open("r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            for path in lines:
                full_url = f"{BASE_URL}{path}"
                filename = path.split("/")[-1]

                if not filename.endswith('.pdf'):
                    logger.warning(f"Skipping invalid filename: {filename}")
                    continue

                tasks.append((full_url, filename))

        except Exception as e:
            logger.error(f"Error reading {txt_file}: {str(e)}")

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
    import time

    start_time = time.time()
    main()
    logger.info(f"Total execution time: {time.time() - start_time:.2f} seconds")
