import requests
from bs4 import BeautifulSoup
from functools import lru_cache
import logging
from .config import MAX_CACHE_SIZE

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.FileHandler("norma.log"),
                              logging.StreamHandler()])

@lru_cache(maxsize=MAX_CACHE_SIZE)
def save_html(html_data, save_html_path):
    """
    Salva i dati HTML in un file specificato.
    
    Arguments:
    html_data -- The HTML data to save
    save_html_path -- The path to save the HTML file
    
    Returns:
    str -- Path where the HTML is saved
    """
    logging.info(f"Saving HTML to: {save_html_path}")
    try:
        with open(save_html_path, 'w', encoding='utf-8') as file:
            file.write(html_data)
        logging.info(f"HTML saved successfully: {save_html_path}")
        return f"HTML salvato in: {save_html_path}"
    except Exception as e:
        logging.error(f"Error saving HTML: {e}", exc_info=True)
        return f"Errore durante il salvataggio dell'HTML: {e}"

@lru_cache(maxsize=MAX_CACHE_SIZE)
def estrai_da_html(atto, comma=None):
    """
    Estrae il testo di un articolo specifico da un documento HTML.
    
    Arguments:
    atto -- The HTML content of the document
    comma -- The comma number to extract (optional)
    
    Returns:
    str -- The extracted text or an error message
    """
    logging.info(f"Extracting article from HTML. Comma: {comma}")
    try:
        soup = BeautifulSoup(atto, 'html.parser')
        logging.info("Parsed HTML with BeautifulSoup")

        corpo = soup.find('div', class_='bodyTesto')
        logging.info("Found body of the document")

        if not comma:
            logging.info("No comma specified, returning full body text")
            return corpo.text
        else:
            parsedcorpo = corpo.find('div', class_='art-commi-div-akn')
            logging.info("Found parsed body for comma extraction")

            commi = parsedcorpo.find_all('div', class_='art-comma-div-akn')
            logging.info(f"Found {len(commi)} commi elements")

            for c in commi:
                comma_text = c.find('span', class_='comma-num-akn').text
                logging.info(f"Checking comma: {comma_text}")
                if f'{comma}.' in comma_text:
                    extracted_text = c.text.strip()
                    logging.info(f"Extracted comma text: {extracted_text}")
                    return extracted_text
    except Exception as e:
        logging.error(f"Errore generico: {e}", exc_info=True)
        return f"Errore generico: {e}"



@lru_cache(maxsize=MAX_CACHE_SIZE)
def extract_html_article(norma_visitata):
    """
    Estrae un articolo HTML da un oggetto NormaVisitata.
    
    Arguments:
    norma_visitata -- The NormaVisitata object containing the URN
    
    Returns:
    str -- The extracted article text or None if not found
    """
    urn = norma_visitata.get_urn()
    logging.info(f"Fetching HTML content from URN: {urn}")
    try:
        response = requests.get(urn)
        if response.status_code == 200:
            html_content = response.text
            logging.info("HTML content fetched successfully")
            return estrai_da_html(atto=html_content, comma=None)
        else:
            logging.warning(f"Failed to fetch HTML content. Status code: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error fetching HTML content: {e}", exc_info=True)
        return None
