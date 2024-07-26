import re
import os
import logging
from bs4 import BeautifulSoup
from .map import BROCARDI_CODICI, BROCARDI_MAP
from .norma import NormaVisitata
from .text_op import normalize_act_type
import requests

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.FileHandler("brocardi_scraper.log"),
                              logging.StreamHandler()])

CURRENT_APP_PATH = os.path.dirname(os.path.abspath(__file__))

class BrocardiScraper:
    """
    Scraper for Brocardi.it to search for legal terms and provide links.
    """
    def __init__(self):
        """
        Initialize the scraper by loading the brocardi links from a JSON file.
        """
        logging.info("Initializing BrocardiScraper")
        self.knowledge = [BROCARDI_CODICI, BROCARDI_MAP]

    def do_know(self, norma):
        if isinstance(norma, NormaVisitata):
            atts = norma.to_dict()
            data_atto = atts['data']
            numero_atto = atts['numero_atto'] 
            tipo_atto = atts['tipo_atto']
            if not tipo_atto:
                raise Exception("TIPO ATTO NON INSERITO")
            
            tipo_norm = normalize_act_type(tipo_atto, True, 'brocardi')
            components = [tipo_norm]
            if data_atto:
                components.append(data_atto)
            if numero_atto:
                components.append(f"n. {numero_atto}")
            strcmp = " ".join(components)
            logging.info(f"Searching for: {strcmp}")
            
        elif isinstance(norma, str):
            strcmp = norma
        else:
            raise Exception("Formato norma non valido")
        
        for txt, link in self.knowledge[0].items():
            if strcmp.lower() in txt.lower():
                logging.info(f"Found match: {txt} -> {link}")
                return txt, link
        logging.warning(f"No match found for: {strcmp}")
        return False
        
    def look_up(self, norma):
        if isinstance(norma, NormaVisitata):
            norma_info = self.do_know(norma)
            if norma_info:
                link = norma_info[1]
                numero_articolo = norma.to_dict()['numero_articolo']
                if '-' in numero_articolo:
                    numero_articolo = numero_articolo.replace('-', '')
                logging.info(f"Looking up article number: {numero_articolo}")
                
                components = [link, f"art{numero_articolo}.html" if numero_articolo else None]
                start, end = components[0], components[1]
                pattern = re.compile(re.escape(start) + r".*" + re.escape(end))

                for key, value in self.knowledge[1].items():
                    if re.search(pattern, value.lower()):
                        logging.info(f"Match found: {value}")
                        return value

                logging.warning("No match found.")
            else:
                logging.warning("No knowledge available.")
        else:
            logging.error("Invalid input type.")
            
    def get_info(self, norma):
        if isinstance(norma, NormaVisitata):
            norma_link = self.look_up(norma)
            if norma_link:
                response = requests.get(norma_link)
                if response.status_code == 200:
                    logging.info(f"Fetching information from: {norma_link}")
                    html_content = response.text
                    soup = BeautifulSoup(html_content, 'html.parser')
                    info = {}
                    position = soup.find('div', id='breadcrumb', recursive=True).text
                    if position:
                        position = position.strip().replace('\n', '').replace('  ', '')[17:]
                    
                    corpo = soup.find('div', class_='panes-condensed panes-w-ads content-ext-guide content-mark', recursive=True)
                    if corpo:
                        brocardi_sections = soup.find_all('div', class_='brocardi-content')
                        if brocardi_sections:
                            brocardi_texts = [broc.text.strip() for broc in brocardi_sections]
                            info['Brocardi'] = brocardi_texts

                        ratio_section = soup.find('div', class_='container-ratio')
                        if ratio_section:
                            ratio_text = ratio_section.find('div', class_='corpoDelTesto')
                            if ratio_text:
                                info['Ratio'] = ratio_text.text.strip()
                        
                        spiegazione_header = soup.find('h3', string=lambda text: 'Spiegazione dell\'art' in text)
                        if spiegazione_header:
                            spiegazione_content = spiegazione_header.find_next_sibling('div', class_='text')
                            if spiegazione_content:
                                info['Spiegazione'] = spiegazione_content.text.strip()
                        
                        massime_header = soup.find('h3', string=lambda text: 'Massime relative all\'art' in text)
                        if massime_header:
                            massime_content = massime_header.find_next_sibling('div', class_='text')
                            if massime_content:
                                info['Massime'] = massime_content.text.strip()
                            
                    return position, info, norma_link
            else:
                logging.warning("No link found for the norma")
        return None, {}, None

    def search_brocardi(self, search_term):
        """
        Search for a given term in the brocardi links and return the URL if available.
        """
        url = self.links.get(search_term)
        if url:
            logging.info(f"Link found for term '{search_term}': {url}")
        else:
            logging.warning(f"No link found for term '{search_term}'")
        return url if url else "No brocardi link available for this term."
