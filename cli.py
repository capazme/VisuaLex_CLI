import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.tree import Tree
from rich.panel import Panel
from app import create_app
from app.scraper.map import NORMATTIVA_SEARCH, TIPI_ATTI_CON_DATA_E_NUMERO
from app.scraper.norma import Norma, NormaVisitata
import requests

console = Console()

@click.group()
def cli():
    pass

@cli.command()
def menu():
    console.print("[bold green]Benvenuto nell'app CLI![/bold green]")
    norma_visitata = None
    while True:
        console.print("\n[bold blue]Menu Principale[/bold blue]")
        console.print("1. Cerca una norma")
        console.print("2. Esci")

        scelta = Prompt.ask("Seleziona un'opzione", choices=["1", "2"])

        if scelta == "1":
            norma_visitata, html_content, tree = cerca_norma()
            if norma_visitata:
                visualizza_dettagli_norma(norma_visitata, html_content, tree)
        elif scelta == "2":
            console.print("[bold red]Arrivederci![/bold red]")
            break

def cerca_norma():
    tipo_atto = Prompt.ask("Inserisci il tipo di atto (es. c.c., c.p., costituzione)")
    tipo_atto = NORMATTIVA_SEARCH.get(tipo_atto.lower(), tipo_atto)
    
    if tipo_atto in TIPI_ATTI_CON_DATA_E_NUMERO:
        data = Prompt.ask("Inserisci la data della norma (es. 2023-01-01)")
        numero_atto = Prompt.ask("Inserisci il numero dell'atto")
    else:
        data = None
        numero_atto = None

    numero_articolo = Prompt.ask("Inserisci il numero dell'articolo")
    versione = Prompt.ask("Inserisci la versione (default: vigente)", default="vigente")

    if versione != "originale":
        data_versione = Prompt.ask("Inserisci la data della versione (opzionale)", default="")
    else:
        data_versione = None

    app = create_app()
    with app.app_context():
        url = 'http://127.0.0.1:5000/scrape'  # URL dell'API
        payload = {
            'tipo_atto': tipo_atto,
            'data': data,
            'numero_atto': numero_atto,
            'numero_articolo': numero_articolo,
            'versione': versione,
            'data_versione': data_versione if data_versione else None
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                response_data = response.json()
                html_content = response_data.get('html', 'No content found')
                norma = Norma(tipo_atto, data, numero_atto, payload.get('url'))
                norma_visitata = NormaVisitata(
                    norma=norma,
                    numero_articolo=numero_articolo,
                    versione=versione,
                    data_versione=data_versione,
                    tree=response_data.get('tree'),
                    urn=response_data.get('urn'),
                    timestamp=response_data.get('timestamp')
                )
                return norma_visitata, html_content, norma_visitata.tree
            else:
                console.print(f"Error: {response.status_code}")
        except requests.exceptions.RequestException as e:
            console.print(f"Request failed: {e}")
    return None, None, None

def visualizza_dettagli_norma(norma_visitata, html_content, tree):
    def add_to_tree(tree_view, items, selected_article):
        for item in items:
            if isinstance(item, dict):
                for key, value in item.items():
                    branch = tree_view.add(f"[bold red]{key}[/bold red]" if key == selected_article else key)
                    add_to_tree(branch, value, selected_article)
            else:
                tree_view.add(f"[bold red]{item}[/bold red]" if item == selected_article else item)

    def get_tree_slice(tree, target_article, window=10):
        articles_list = tree[0]
        if target_article not in articles_list:
            return articles_list[:window]
        target_index = articles_list.index(target_article)
        start = max(0, target_index - window // 2)
        end = min(len(articles_list), target_index + window // 2 + 1)
        return articles_list[start:end]

    def fetch_article_text(norma_visitata, article_number):
        app = create_app()
        with app.app_context():
            url = 'http://127.0.0.1:5000/scrape'  # URL dell'API
            payload = {
                'tipo_atto': norma_visitata.tipo_atto_str,
                'data': norma_visitata.data,
                'numero_atto': norma_visitata.numero_atto,
                'numero_articolo': article_number,
                'versione': norma_visitata.versione,
                'data_versione': norma_visitata.data_versione if norma_visitata.data_versione else None
            }
            try:
                response = requests.post(url, json=payload)
                if response.status_code == 200:
                    response_data = response.json()
                    return response_data.get('html', 'No content found')
                else:
                    console.print(f"Error: {response.status_code}")
            except requests.exceptions.RequestException as e:
                console.print(f"Request failed: {e}")
        return 'No content found'

    def navigate_articles(tree, current_article):
        while True:
            tree_slice = get_tree_slice(tree, current_article)
            tree_view = Tree("Struttura dell'Atto")
            add_to_tree(tree_view, tree_slice, current_article)
            console.clear()

            article_text = fetch_article_text(norma_visitata, current_article)
            table = Table(title="Dettagli Norma Visitata")
            table.add_column("Campo", justify="right", style="cyan", no_wrap=True)
            table.add_column("Valore", style="magenta")

            for key, value in norma_visitata.to_dict().items():
                table.add_row(key, str(value))
            
            table.add_row("Testo Estratto", article_text)
            console.print(table)

            tree_panel = Panel(tree_view, title="Struttura dell'Atto", subtitle="Articoli vicini all'articolo selezionato", expand=False)
            console.print(tree_panel)

            scelta = Prompt.ask("Naviga articoli", choices=["precedente", "successivo", "esci"])
            if scelta == "precedente":
                current_index = tree[0].index(current_article)
                if current_index > 0:
                    current_article = tree[0][current_index - 1]
            elif scelta == "successivo":
                current_index = tree[0].index(current_article)
                if current_index < len(tree[0]) - 1:
                    current_article = tree[0][current_index + 1]
            elif scelta == "esci":
                break

    if tree:
        navigate_articles(tree, norma_visitata.numero_articolo)
    else:
        console.print("No tree structure available")

if __name__ == '__main__':
    cli()
