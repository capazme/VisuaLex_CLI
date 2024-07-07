from flask import Flask, render_template, request, jsonify, send_file
from tools.norma import NormaVisitata, Norma
from tools.xlm_htmlextractor import extract_html_article
from tools import pdfextractor, text_op, treextractor, urngenerator, sys_op
import os
from functools import lru_cache
from collections import deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.FileHandler("app.log"),
                              logging.StreamHandler()])

MAX_CACHE_SIZE = 1000  # Define maximum cache size
HISTORY_LIMIT = 50  # Define history limit for recent NormaVisitata objects

app = Flask(__name__)

history = deque(maxlen=HISTORY_LIMIT)  # Initialize history with a max length

@app.route('/')
def home():
    """
    Renders the home page.
    """
    return render_template('index.html')

@lru_cache(maxsize=MAX_CACHE_SIZE)
@app.route('/fetch_norm', methods=['POST'])
def fetch_data():
    """
    Endpoint to fetch the details of a legal norm.
    Expected JSON input:
    {
        "act_type": "type of act",
        "date": "date of the act",
        "act_number": "act number",
        "article": "article number",
        "version": "version",
        "version_date": "version date" (optional)
    }
    Returns:
    {
        "result": "text of the article",
        "urn": "URN of the act",
        "norma_data": { ... }
    }
    """
    try:
        data = request.get_json()
        logging.info(f"Received data for fetch_norm: {data}")

        act_type = data['act_type']
        date = data['date']
        act_number = data['act_number']
        article = data['article']
        version = data['version']
        version_date = data.get('version_date')  # Optional field

        # Create NormaVisitata instance
        normavisitata = NormaVisitata(
            norma=Norma(tipo_atto=act_type, data=date, numero_atto=act_number),
            numero_articolo=article,
            versione=version,
            data_versione=version_date
        )
        logging.info(f"Created NormaVisitata: {normavisitata}")

        # Extract article text
        norma_art_text = extract_html_article(normavisitata)
        logging.info(f"Extracted article text: {norma_art_text}")

        norma_data = normavisitata.to_dict()
        response = {
            'result': norma_art_text,
            'urn': normavisitata.get_urn(),
            'norma_data': norma_data
        }
        
        # Append the NormaVisitata instance to history
        history.append(normavisitata)
        logging.info(f"Appended NormaVisitata to history. Current history size: {len(history)}")

        return jsonify(response)
    except Exception as e:
        logging.error(f"Error in fetch_data: {e}", exc_info=True)
        return jsonify({'error': str(e)})

@app.route('/fetch_tree', methods=['POST'])
def fetch_tree():
    """
    Endpoint to fetch the tree structure of a legal norm.
    Expected JSON input:
    {
        "norma_data": { ... }
    }
    Returns:
    {
        "tree": { ... }
    }
    """
    try:
        data = request.get_json()
        logging.info(f"Received data for fetch_tree: {data}")

        if 'norma_data' not in data:
            logging.error("'norma_data' key not found in the request payload")
            return jsonify({'error': "'norma_data' key not found in the request payload"}), 400

        norma_data = data['norma_data']
        norma_visitata = NormaVisitata.from_dict(norma_data)
        logging.info(f"Created NormaVisitata from dict: {norma_visitata}")

        if norma_visitata.tree:
            tree = norma_visitata.tree
            logging.info("Using pre-fetched tree from NormaVisitata object")
        else:
            tree = get_tree_from_urn(norma_visitata.get_url())
            logging.info("Fetched tree from URN")

        return jsonify({'tree': tree})
    except Exception as e:
        logging.error(f"Error in fetch_tree: {e}", exc_info=True)
        return jsonify({'error': str(e)})

def get_tree_from_urn(urn):
    # Dummy implementation of get_tree_from_urn, replace with actual logic
    return {"dummy_tree": urn}


@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    """
    Endpoint to export the legal norm as a PDF.
    Expected JSON input:
    {
        "urn": "URN of the act"
    }
    Returns:
    PDF file as an attachment.
    """
    try:
        data = request.get_json()
        urn = data['urn']
        logging.info(f"Received data for export_pdf: {urn}")

        filename = urngenerator.urn_to_filename(urn)
        if not filename:
            raise ValueError("Invalid URN")

        pdf_path = os.path.join(os.getcwd(), "download", filename)
        logging.info(f"PDF path: {pdf_path}")

        if os.path.exists(pdf_path):
            logging.info(f"PDF already exists: {pdf_path}")
            return send_file(pdf_path, as_attachment=True)

        # Setup or reuse the driver
        if not sys_op.drivers:
            driver = sys_op.setup_driver()
        else:
            driver = sys_op.drivers[0]

        pdf_path = pdfextractor.extract_pdf(driver, urn, 30)
        if not pdf_path:
            raise ValueError("Error generating PDF")

        os.rename(os.path.join(os.getcwd(), "download", pdf_path), pdf_path)
        logging.info(f"PDF generated and saved: {pdf_path}")

        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        logging.error(f"Error in export_pdf: {e}", exc_info=True)
        return jsonify({'error': str(e)})
    finally:
        sys_op.close_driver()
        logging.info("Driver closed")

if __name__ == '__main__':
    logging.info("Starting Flask app in debug mode")
    app.run(debug=True)
