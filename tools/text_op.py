import re
import datetime
from functools import lru_cache
from .config import MAX_CACHE_SIZE
from .map import NORMATTIVA, NORMATTIVA_SEARCH, BROCARDI_SEARCH
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.FileHandler("norma.log"),
                              logging.StreamHandler()])

def nospazi(text):
    """
    Rimuove spazi multipli da una stringa.
    
    Arguments:
    text -- The input text string
    
    Returns:
    str -- The text with single spaces between words
    """
    logging.info(f"Removing extra spaces from text: {text}")
    textlist = text.split()
    for t in textlist:
        t.strip()
    textout = ' '.join(textlist)
    logging.info(f"Text after removing spaces: {textout}")
    return textout

@lru_cache(maxsize=MAX_CACHE_SIZE)
def parse_date(input_date):
    """
    Converte una stringa di data in formato esteso o YYYY-MM-DD al formato YYYY-MM-DD.
    Supporta mesi in italiano.
    
    Arguments:
    input_date -- The input date string
    
    Returns:
    str -- The formatted date string
    """
    logging.info(f"Parsing date: {input_date}")
    
    month_map = {
        "gennaio": "01", "febbraio": "02", "marzo": "03", "aprile": "04",
        "maggio": "05", "giugno": "06", "luglio": "07", "agosto": "08",
        "settembre": "09", "ottobre": "10", "novembre": "11", "dicembre": "12"
    }

    pattern = r"(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})"
    match = re.search(pattern, input_date)
    if match:
        day, month, year = match.groups()
        month = month_map.get(month.lower())
        if not month:
            logging.error("Invalid month found in date string")
            raise ValueError("Mese non valido")
        formatted_date = f"{year}-{month}-{day.zfill(2)}"
        logging.info(f"Formatted date: {formatted_date}")
        return formatted_date
    
    try:
        datetime.datetime.strptime(input_date, "%Y-%m-%d")
        return input_date
    except ValueError:
        logging.error("Invalid date format")
        raise ValueError("Formato data non valido")

@lru_cache(maxsize=MAX_CACHE_SIZE)
def normalize_act_type(input_type, search=False, source='normattiva'):
    """
    Normalizes the type of legislative act based on a variable input.
    
    Arguments:
    input_type -- The input act type string
    search -- Boolean flag to indicate if the input is for search purposes
    source -- Source dictionary to use for normalization (default: 'normattiva')
    
    Returns:
    str -- The normalized act type
    """
    logging.info(f"Normalizing act type: {input_type}, search: {search}, source: {source}")
    
    act_types = {}
    if source == 'normattiva':
        act_types = NORMATTIVA_SEARCH if search else NORMATTIVA
    elif source == 'brocardi':
        act_types = BROCARDI_SEARCH if search else {}

    input_type = input_type.lower().strip()

    for key, value in act_types.items():
        if input_type == key or input_type == key.replace(" ", ""):
            normalized_type = value
            logging.info(f"Normalized act type found: {normalized_type}")
            return normalized_type

    logging.info(f"Returning input act type as normalized type: {input_type}")
    return input_type

@lru_cache(maxsize=MAX_CACHE_SIZE)
def estrai_data_da_denominazione(denominazione):
    """
    Estrae una data da una denominazione.
    
    Arguments:
    denominazione -- The input string containing a date
    
    Returns:
    str -- The extracted date or the original denominazione if no date is found
    """
    logging.info(f"Extracting date from denomination: {denominazione}")
    
    pattern = r"\b(\d{1,2})\s([Gg]ennaio|[Ff]ebbraio|[Mm]arzo|[Aa]prile|[Mm]aggio|[Gg]iugno|[Ll]uglio|[Aa]gosto|[Ss]ettembre|[Oo]ttobre|[Nn]ovembre|[Dd]icembre)\s(\d{4})\b"
    match = re.search(pattern, denominazione)
    
    if match:
        extracted_date = match.group(0)
        logging.info(f"Extracted date: {extracted_date}")
        return extracted_date
    else:
        logging.info("No date found in denomination")
        return denominazione

@lru_cache(maxsize=MAX_CACHE_SIZE)
def estrai_numero_da_estensione(estensione):
    """
    Estrae il numero corrispondente da una estensione (es. 'bis', 'tris').
    
    Arguments:
    estensione -- The input extension string
    
    Returns:
    int -- The extracted number or 0 if the extension is not found
    """
    logging.info(f"Extracting number from extension: {estensione}")
    
    estensioni_numeriche = {
        None: 0, 'bis': 2, 'tris': 3, 'ter': 3, 'quater': 4, 'quinquies': 5,
        'quinques': 5, 'sexies': 6, 'septies': 7, 'octies': 8, 'novies': 9, 'decies': 10, 'undecies': 11, 'duodecies': 12, 'terdecies': 13, 'quaterdecies': 14,
        'quindecies': 15, 'sexdecies': 16, 'septiesdecies': 17, 'duodevicies': 18, 'undevicies': 19,
        'vices': 20, 'vicessemel': 21, 'vicesbis': 22, 'vicester': 23, 'vicesquater': 24,
        'vicesquinquies': 25, 'vicessexies': 26, 'vicessepties': 27, 'duodetricies': 28, 'undetricies': 29,
        'tricies': 30, 'triciessemel': 31, 'triciesbis': 32, 'triciester': 33, 'triciesquater': 34,
        'triciesquinquies': 35, 'triciessexies': 36, 'triciessepties': 37, 'duodequadragies': 38, 'undequadragies': 39,
        'quadragies': 40, 'quadragiessemel': 41, 'quadragiesbis': 42, 'quadragiester': 43, 'quadragiesquater': 44,
        'quadragiesquinquies': 45, 'quadragiessexies': 46, 'quadragiessepties': 47, 'duodequinquagies': 48, 'undequinquagies': 49,
    }
    
    number = estensioni_numeriche.get(estensione, 0)
    logging.info(f"Extracted number: {number}")
    return number

def get_annex_from_urn(urn):
    """
    Estrae l'annesso da una URN.
    
    Arguments:
    urn -- The input URN string
    
    Returns:
    str -- The annex number if found, otherwise None
    """
    logging.info(f"Extracting annex from URN: {urn}")
    
    ann_num = re.search(r":(\d+)(!vig=|@originale)$", urn)
    if ann_num:
        annex = ann_num.group(1)
        logging.info(f"Extracted annex: {annex}")
        return annex
    logging.info("No annex found in URN")
    return None
