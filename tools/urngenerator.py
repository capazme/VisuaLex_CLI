import re
from .text_op import normalize_act_type, parse_date
from .map import NORMATTIVA_URN_CODICI
from functools import lru_cache
from .config import MAX_CACHE_SIZE
from .sys_op import setup_driver, close_driver, drivers
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tools.text_op import estrai_data_da_denominazione
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.FileHandler("norma.log"),
                              logging.StreamHandler()])

@lru_cache(maxsize=MAX_CACHE_SIZE)
def complete_date(act_type, date, act_number):
    """
    Completes the date of a legal norm using the Normattiva website.
    Arguments:
    act_type -- Type of the legal act
    date -- Date of the act (year)
    act_number -- Number of the act

    Returns:
    data_completa -- Completed date
    """
    logging.info(f"Starting complete_date with act_type: {act_type}, date: {date}, act_number: {act_number}")
    try:
        setup_driver()
        drivers[0].get("https://www.normattiva.it/")
        search_box = drivers[0].find_element(By.CSS_SELECTOR, "#testoRicerca")
        search_criteria = f"{act_type} {act_number} {date}"
        logging.info(f"Search criteria: {search_criteria}")
        
        search_box.send_keys(search_criteria)
        WebDriverWait(drivers[0], 5).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"button-3\"]"))).click()
        elemento = WebDriverWait(drivers[0], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="heading_1"]/p[1]/a')))
        elemento_text = elemento.text
        logging.info(f"Element text found: {elemento_text}")
        
        data_completa = estrai_data_da_denominazione(elemento_text)
        logging.info(f"Completed date: {data_completa}")
        
        close_driver()
        return data_completa
    except Exception as e:
        logging.error(f"Error in complete_date: {e}", exc_info=True)
        close_driver()
        return f"Errore nel completamento della data, inserisci la data completa: {e}"

def generate_urn(act_type, date=None, act_number=None, article=None, extension=None, version=None, version_date=None, urn_flag=True):
    """
    Generates the URN for a legal norm.
    Arguments:
    act_type -- Type of the legal act
    date -- Date of the act
    act_number -- Number of the act
    article -- Article number (optional)
    extension -- Article extension (optional)
    version -- Version of the act (optional)
    version_date -- Date of the version (optional)
    urn_flag -- Boolean flag to include full URN or not

    Returns:
    result -- The generated URN
    """
    logging.info(f"Starting generate_urn with act_type: {act_type}, date: {date}, act_number: {act_number}, article: {article}, extension: {extension}, version: {version}, version_date: {version_date}, urn_flag: {urn_flag}")
    codici_urn = NORMATTIVA_URN_CODICI
    base_url = "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:"
    normalized_act_type = normalize_act_type(act_type)
    
    if normalized_act_type in codici_urn:
        urn = codici_urn[normalized_act_type]
        logging.info(f"Found URN in codici_urn: {urn}")
    else:
        try:
            if re.match(r"^\d{4}$", date) and act_number:
                act_type_for_search = normalize_act_type(act_type, search=True)
                full_date = complete_date(act_type=act_type_for_search, date=date, act_number=act_number)
                formatted_date = parse_date(full_date)
            else:
                formatted_date = parse_date(date)
            logging.info(f"Formatted date: {formatted_date}")
        except Exception as e:
            logging.error(f"Error generating URN: {e}", exc_info=True)
            return None, None
        urn = f"{normalized_act_type}:{formatted_date};{act_number}"
        logging.info(f"Generated URN: {urn}")
            
    if article:
        if "-" in article:
            parts = article.split("-")
            article = parts[0]
            extension = parts[1]
    
        if isinstance(article, str):
            article = re.sub(r'\b[Aa]rticoli?\b|\b[Aa]rt\.?\b', "", article).strip()
        
        urn += f"~art{str(article)}"
        
        if extension:
            urn += extension
        else:
            extension = ''
        logging.info(f"Article part of URN: {urn}")
                
    if version == "originale":
        urn += "@originale"
    elif version == "vigente":
        urn += "!vig="
        if version_date:
            formatted_version_date = parse_date(version_date)
            urn += formatted_version_date
        logging.info(f"Version part of URN: {urn}")

    full = base_url + urn

    result = full if urn_flag else full.split("~")[0]
    logging.info(f"Final URN: {result}")
    
    return result

def urn_to_filename(urn):
    """
    Converts a URN to a filename.
    Arguments:
    urn -- The URN string

    Returns:
    filename -- The generated filename
    """
    logging.info(f"Starting urn_to_filename with URN: {urn}")
    parts = urn.split(':')
    if len(parts) < 3:
        raise ValueError("Invalid URN format")
    act_type = parts[2]
    if len(parts) > 3:
        date_number = parts[3].split(';')
        if len(date_number) == 2:
            date, number = date_number
            filename = f"{number}_{date}.pdf"
            logging.info(f"Generated filename: {filename}")
            return filename
    filename = f"{act_type}.pdf"
    logging.info(f"Generated filename: {filename}")
    return filename
