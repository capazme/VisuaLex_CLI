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
def estrai_da_html(atto, num_articolo=None, comma=None):
    """
    Estrae il testo di un articolo specifico da un documento HTML.
    
    Arguments:
    atto -- The HTML content of the document
    num_articolo -- The article number to extract (optional)
    comma -- The comma number to extract (optional)
    
    Returns:
    str -- The extracted text or an error message
    """
    logging.info(f"Extracting article from HTML. Article number: {num_articolo}, Comma: {comma}")
    try:
        soup = BeautifulSoup(atto, 'html.parser')
        corpo = soup.find('div', class_='bodyTesto')

        if not corpo:
            logging.warning("Body of the document not found.")
            return "Corpo dell'atto non trovato."

        if num_articolo:
            # Log the id of the found articles
            articoli = corpo.find_all('div', class_='articolo')
            articoli_ids = [art['id'] for art in articoli]
            logging.info(f"Found articles with IDs: {articoli_ids}")

            articolo = next((art for art in articoli if art.get('id') == num_articolo), None)
            if not articolo:
                logging.warning(f"Article number {num_articolo} not found.")
                return "Nessun articolo trovato."

            if comma:
                commi = articolo.find_all('div', class_='art-comma-div-akn')
                for c in commi:
                    comma_text = c.find('span', class_='comma-num-akn').text
                    logging.info(f"Found comma with text: {comma_text}")
                    if f'{comma}.' in comma_text:
                        extracted_text = c.get_text(separator="\n", strip=True)
                        logging.info(f"Extracted comma text: {extracted_text}")
                        return extracted_text
                logging.warning(f"Comma number {comma} not found.")
                return "Comma non trovato."
            
            extracted_text = articolo.get_text(separator="\n", strip=True)
            logging.info(f"Extracted article text: {extracted_text}")
            return extracted_text
        else:
            extracted_text = corpo.get_text(separator="\n", strip=True)
            logging.info(f"Extracted document body text: {extracted_text}")
            return extracted_text

    except Exception as e:
        logging.error(f"Error extracting article: {e}", exc_info=True)
        return f"Errore durante l'estrazione: {e}"

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
            return estrai_da_html(atto=html_content, num_articolo=norma_visitata.numero_articolo, comma=None)
        else:
            logging.warning(f"Failed to fetch HTML content. Status code: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error fetching HTML content: {e}", exc_info=True)
        return None
