from flask import Blueprint, request, jsonify
from .scraper.norma import Norma, NormaVisitata
from .scraper.xlm_htmlextractor import extract_html_article

bp = Blueprint('api', __name__)

@bp.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    tipo_atto = data['tipo_atto']
    norma = Norma(tipo_atto, data.get('data'), data.get('numero_atto'))
    norma_visitata = NormaVisitata(norma, data['numero_articolo'], data.get('versione', 'vigente'), data.get('data_versione'))
    html_content = extract_html_article(norma_visitata)
    response_data = norma_visitata.to_dict()
    response_data['html'] = html_content
    response_data['tree'] = norma_visitata.tree
    return jsonify(response_data)
