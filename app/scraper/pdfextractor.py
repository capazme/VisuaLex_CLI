import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from functools import lru_cache
from .config import MAX_CACHE_SIZE

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.FileHandler("norma.log"),
                              logging.StreamHandler()])

@lru_cache(maxsize=MAX_CACHE_SIZE)
def extract_pdf(driver, urn, timeout=30):
    """
    Extracts a PDF from a given URN using Selenium WebDriver.
    
    Arguments:
    driver -- Selenium WebDriver instance
    urn -- URN of the legal document
    timeout -- Maximum time to wait for operations (default: 30 seconds)
    
    Returns:
    str -- Path to the downloaded PDF file
    """
    logging.info(f"Extracting PDF for URN: {urn} with timeout: {timeout}")
    
    download_dir = os.path.join(os.getcwd(), "download")
    
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        logging.info(f"Created download directory: {download_dir}")
    
    try:
        driver.get(urn)
        logging.info(f"Accessed URN: {urn}")
        
        # Selectors for the export button and the PDF download button
        export_button_selector = "#mySidebarRight > div > div:nth-child(2) > div > div > ul > li:nth-child(2) > a"
        export_pdf_selector = "downloadPdf"
        
        # Click the export button
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, export_button_selector))).click()
        logging.info("Clicked on export button")
        
        # Switch to the new window that opens
        driver.switch_to.window(driver.window_handles[-1])
        logging.info("Switched to the export window")
        
        # Click the download PDF button
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.NAME, export_pdf_selector))).click()
        logging.info("Clicked on download PDF button")
        
        # Wait for the download to complete
        start_time = time.time()
        downloaded_files = os.listdir(download_dir)
        
        while True:
            current_files = os.listdir(download_dir)
            new_files = set(current_files) - set(downloaded_files)
            if new_files:
                pdf_file_path = os.path.join(download_dir, new_files.pop())
                if pdf_file_path.endswith(".pdf"):
                    logging.info(f"PDF downloaded successfully: {pdf_file_path}")
                    return pdf_file_path
            if time.time() - start_time > timeout:
                raise TimeoutError("Download PDF timed out")
            time.sleep(1)
    except Exception as e:
        logging.error(f"Error extracting PDF: {e}", exc_info=True)
        raise
    finally:
        logging.info("Closing the driver")
        driver.quit()
