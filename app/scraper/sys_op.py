import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

drivers = []

def setup_driver(download_dir=None):
    """
    Crea un nuovo driver configurato per gestire i download.
    """

    if download_dir is None:
        download_dir = os.path.join(os.getcwd(), "download")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")

    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    new_driver = webdriver.Chrome(options=chrome_options)
    drivers.append(new_driver)
    return new_driver

def close_driver():
    """
    Chiude tutti i driver aperti e svuota la lista.
    """
    global drivers
    for driver in drivers:
        driver.quit()
    drivers = []
