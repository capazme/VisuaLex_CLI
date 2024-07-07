from tools.urngenerator import generate_urn
from tools.text_op import normalize_act_type
from datetime import datetime
from tools.treextractor import get_tree
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.FileHandler("norma.log"),
                              logging.StreamHandler()])

class Norma:
    def __init__(self, tipo_atto, data=None, numero_atto=None, url=None, tree=None):
        """
        Initializes a Norma object.
        
        Arguments:
        tipo_atto -- Type of the legal act
        data -- Date of the act
        numero_atto -- Number of the act
        url -- URL of the act
        tree -- Tree structure of the act
        """
        logging.info(f"Initializing Norma with tipo_atto: {tipo_atto}, data: {data}, numero_atto: {numero_atto}, url: {url}")
        
        self.tipo_atto_str = normalize_act_type(tipo_atto, search=True)
        self.tipo_atto_urn = normalize_act_type(tipo_atto)
        self.data = data if data else ""
        self.numero_atto = numero_atto if numero_atto else ""
        self.url = url or generate_urn(act_type=self.tipo_atto_urn, date=data, act_number=numero_atto, urn_flag=False)
        self.tree = tree if tree else get_tree(self.url)
        
        logging.info(f"Norma initialized: {self}")

    def __str__(self):
        """
        Returns a string representation of the Norma object.
        """
        parts = [self.tipo_atto_str]

        if self.data:
            parts.append(f"{self.data},".strip())

        if self.numero_atto:
            num_prefix = "n."
            parts.append(f"{num_prefix} {self.numero_atto}".strip())

        return " ".join(parts)
    
    def to_dict(self):
        """
        Converts the Norma object to a dictionary.
        
        Returns:
        dict -- Dictionary representation of the Norma object
        """
        return {
            'tipo_atto': self.tipo_atto_str,
            'data': self.data,
            'numero_atto': self.numero_atto,
            'url': self.url,
            'tree': self.tree,
        }

class NormaVisitata(Norma):
    def __init__(self, norma, numero_articolo=None, versione=None, data_versione=None, urn=None, timestamp=None):
        """
        Initializes a NormaVisitata object.
        
        Arguments:
        norma -- An instance of Norma
        numero_articolo -- Article number
        versione -- Version of the act
        data_versione -- Date of the version
        urn -- URN of the act
        timestamp -- Timestamp of the visit
        """
        # Initialize additional attributes first
        self.numero_articolo = numero_articolo
        self.versione = versione
        self.data_versione = data_versione
        self.urn = urn or generate_urn(norma.tipo_atto_urn, date=norma.data, act_number=norma.numero_atto, article=numero_articolo, version=versione, version_date=data_versione)
        self.timestamp = timestamp if timestamp else datetime.now().isoformat()

        # Call the base class initializer
        super().__init__(tipo_atto=norma.tipo_atto_str, data=norma.data, numero_atto=norma.numero_atto, url=norma.url, tree=norma.tree)

        logging.info(f"NormaVisitata initialized: {self}")

    def __str__(self):
        """
        Returns a string representation of the NormaVisitata object.
        """
        base_str = super().__str__()
        if self.numero_articolo:
            base_str += f" art. {self.numero_articolo}"
        return base_str
    
    def to_dict(self):
        """
        Converts the NormaVisitata object to a dictionary.
        
        Returns:
        dict -- Dictionary representation of the NormaVisitata object
        """
        base_dict = super().to_dict()
        base_dict.update({
            'numero_articolo': self.numero_articolo,
            'versione': self.versione,
            'data_versione': self.data_versione,
            'timestamp': self.timestamp
        })
        return base_dict
    
    def get_urn(self):
        """
        Returns the URN of the NormaVisitata object.
        
        Returns:
        str -- URN of the NormaVisitata object
        """
        logging.info(f"Getting URN: {self.urn}")
        return self.urn
    
    def get_url(self):
        """
        Returns the URL of the NormaVisitata object.
        
        Returns:
        str -- URL of the NormaVisitata object
        """
        return self.url

    @staticmethod
    def from_dict(data):
        """
        Creates a NormaVisitata object from a dictionary.
        
        Arguments:
        data -- Dictionary containing the NormaVisitata data
        
        Returns:
        NormaVisitata -- The created NormaVisitata object
        """
        logging.info(f"Creating NormaVisitata from dict: {data}")
        
        norma = Norma(
            tipo_atto=data['tipo_atto'],
            data=data.get('data'),
            numero_atto=data.get('numero_atto'),
            url=data.get('url'),
            tree=data.get('tree')
        )
        norma_visitata = NormaVisitata(
            norma=norma,
            numero_articolo=data.get('numero_articolo'),
            versione=data.get('versione'),
            data_versione=data.get('data_versione'),
            timestamp=data.get('timestamp')
        )
        
        logging.info(f"NormaVisitata created: {norma_visitata}")
        return norma_visitata
