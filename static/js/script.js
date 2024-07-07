/*******************************
 * PARTE 1: GESTIONE DELLA SOTTOMISSIONE DEL FORM
 *******************************/
let lastUrn = ''; // Variabile per memorizzare l'URN ottenuto
let articleTree = [];
let lastFetchedUrl = '';

document.getElementById('scrape-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    if (data.article) {
        data.article = data.article.replace(/\s+/g, '');
    }

    setLoading(true);

    try {
        const response = await fetch('/fetch_norm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        setLoading(false);

        const normaDataContainer = document.getElementById('norma-data');
        const resultContainer = document.getElementById('result');

        if (result.error) {
            handleError(result.error, resultContainer);
        } else {
            displayNormaData(result.norma_data, result.result);
            lastUrn = result.urn; // Memorizza l'URN ottenuto

            if (lastFetchedUrl !== result.norma_data.url) {
                lastFetchedUrl = result.norma_data.url;
                fetchTree(result.norma_data.url);
            }

            // Aggiorna la cronologia dopo la ricerca
            updateHistory();
        }
    } catch (error) {
        setLoading(false);
        handleError(error, document.getElementById('result'));
    }
});

function displayNormaData(normaData, resultText) {
    const normaDataContainer = document.getElementById('norma-data');
    normaDataContainer.innerHTML = `
        <h2>Informazioni della Norma Visitata</h2>
        <p><strong>Tipo atto:</strong> ${normaData.tipo_atto}</p>
        <p><strong>Data:</strong> ${normaData.data}</p>
        <p><strong>Numero atto:</strong> ${normaData.numero_atto}</p>
        <p><strong>Numero articolo:</strong> ${normaData.numero_articolo}</p>
        <p><strong>URL:</strong> <a href="${normaData.url}" target="_blank">${normaData.url}</a></p>
    `;
    const resultContainer = document.getElementById('result');
    resultContainer.textContent = resultText;
}

/*******************************
 * PARTE 2: GESTIONE DEGLI ARTICOLI E URL
 *******************************/
async function fetchTree(urn) {
    try {
        const response = await fetch('/fetch_tree', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ urn })
        });
        const result = await response.json();
        if (result.error) {
            handleError(result.error);
        } else {
            setArticleTree(result.tree);
        }
    } catch (error) {
        handleError(error);
    }
}

function setArticleTree(tree) {
    articleTree = tree;
    console.log(articleTree);
}

/*******************************
 * PARTE 3: GESTIONE DEGLI EVENTI DEL DOM
 *******************************/
document.addEventListener('DOMContentLoaded', function() {
    const elements = {
        decrementButton: document.querySelector('.decrement'),
        incrementButton: document.querySelector('.increment'),
        articleInput: document.getElementById('article'),
        actTypeInput: document.getElementById('act_type'),
        versionVigente: document.getElementById('vigente'),
        versionOriginale: document.getElementById('originale'),
        versionDateInput: document.getElementById('version_date'),
        viewPdfButton: document.getElementById('view-pdf'),
        pdfFrame: document.getElementById('pdf-frame'),
        downloadPdfButton: document.getElementById('download-pdf'),
        fullscreenButton: document.getElementById('fullscreen-button'),
        collapsibleButton: document.querySelector('.collapsible'),
        collapsibleContent: document.querySelector('.content')
    };

    initializeVersionDateInput(elements.versionVigente, elements.versionDateInput);
    setupVersionDateToggle(elements.versionVigente, elements.versionOriginale, elements.versionDateInput);

    setupArticleButtons(elements.decrementButton, elements.incrementButton, elements.articleInput, elements.actTypeInput);
    setupPdfButton(elements.viewPdfButton, elements.pdfFrame, elements.downloadPdfButton, elements.fullscreenButton, elements.collapsibleButton, elements.collapsibleContent);

    elements.collapsibleButton.addEventListener('click', toggleCollapsibleContent);
    updateHistory();
});

function initializeVersionDateInput(versionVigente, versionDateInput) {
    if (versionVigente.checked) {
        versionDateInput.disabled = false;
        versionDateInput.style.opacity = 1;
    } else {
        versionDateInput.disabled = true;
        versionDateInput.style.opacity = 0.5;
    }
}

function setupVersionDateToggle(versionVigente, versionOriginale, versionDateInput) {
    versionVigente.addEventListener('change', () => {
        versionDateInput.disabled = false;
        versionDateInput.style.opacity = 1;
    });

    versionOriginale.addEventListener('change', () => {
        versionDateInput.disabled = true;
        versionDateInput.style.opacity = 0.5;
        versionDateInput.value = '';
    });
}

function setupArticleButtons(decrementButton, incrementButton, articleInput, actTypeInput) {
    if (decrementButton && incrementButton && articleInput) {
        decrementButton.addEventListener('click', () => updateArticleInput(articleInput, actTypeInput, decrementArticle));
        incrementButton.addEventListener('click', () => updateArticleInput(articleInput, actTypeInput, incrementArticle));
    }
}

function updateArticleInput(articleInput, actTypeInput, updateFunction) {
    let currentValue = articleInput.value;
    if (!actTypeInput.value) {
        currentValue = '1'; // Imposta l'articolo a 1 se il tipo di atto non è selezionato
    } else {
        currentValue = updateFunction(currentValue);
    }
    articleInput.value = currentValue;
    articleInput.focus();
    articleInput.dispatchEvent(new Event('input'));
}

function incrementArticle(article) {
    return getUpdatedArticle(article, 1);
}

function decrementArticle(article) {
    return getUpdatedArticle(article, -1);
}

function getUpdatedArticle(article, direction) {
    if (!validateArticleInput(article)) {
        return '1'; // Imposta l'articolo a 1 se l'input non è valido
    }
    let index = articleTree.indexOf(article);
    if (index < 0) index = 0;
    else index = (index + direction + articleTree.length) % articleTree.length;
    return articleTree[index];
}

function setupPdfButton(viewPdfButton, pdfFrame, downloadPdfButton, fullscreenButton, collapsibleButton, collapsibleContent) {
    viewPdfButton.addEventListener('click', async function() {
        if (!lastUrn) {
            alert('Per favore completa prima una ricerca.');
            return;
        }

        setLoading(true);

        try {
            const response = await fetch('/export_pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ urn: lastUrn })
            });

            if (!response.ok) {
                throw new Error(`Errore nella richiesta: ${response.statusText}`);
            }

            const blob = await response.blob();
            const pdfUrl = URL.createObjectURL(blob);

            setLoading(false);

            pdfFrame.src = pdfUrl + "#" + new Date().getTime(); // Aggiungi un timestamp per evitare il caching
            pdfFrame.style.display = 'block';
            
            downloadPdfButton.style.display = 'block';
            fullscreenButton.style.display = 'block';
            collapsibleButton.style.display = 'block';
            collapsibleContent.style.display = 'block';

            setupDownloadAndFullscreen(downloadPdfButton, fullscreenButton, pdfFrame, pdfUrl);
        } catch (error) {
            setLoading(false);
            handleError(error, document.getElementById('result'));
        }
    });
}

function setupDownloadAndFullscreen(downloadPdfButton, fullscreenButton, pdfFrame, pdfUrl) {
    downloadPdfButton.addEventListener('click', () => {
        const a = document.createElement('a');
        a.href = pdfUrl;
        a.download = 'norma.pdf';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    });

    fullscreenButton.addEventListener('click', () => {
        if (pdfFrame.requestFullscreen) pdfFrame.requestFullscreen();
        else if (pdfFrame.mozRequestFullScreen) pdfFrame.mozRequestFullScreen(); // Firefox
        else if (pdfFrame.webkitRequestFullscreen) pdfFrame.webkitRequestFullscreen(); // Chrome, Safari and Opera
        else if (pdfFrame.msRequestFullscreen) pdfFrame.msRequestFullscreen(); // IE/Edge
    });
}

function toggleCollapsibleContent() {
    this.classList.toggle('active');
    const content = this.nextElementSibling;
    content.style.display = content.style.display === 'block' ? 'none' : 'block';
}

/*******************************
 * FUNZIONI DI SUPPORTO
 *******************************/
function handleError(error, messageContainer) {
    console.error('Error:', error);
    if (messageContainer) {
        messageContainer.textContent = `Error: ${error.message || error}`;
    } else {
        alert(`Error: ${error.message || error}`);
    }
}

function setLoading(isLoading) {
    const loadingElement = document.getElementById('loading');
    if (loadingElement) {
        loadingElement.style.display = isLoading ? 'block' : 'none';
    }
}

function validateArticleInput(article) {
    if (!article || !articleTree.includes(article)) {
        alert('Articolo non valido. Per favore inserisci un articolo valido.');
        return false;
    }
    return true;
}

function updateHistory() {
    fetch('/history')
        .then(response => response.json())
        .then(history => {
            const historyList = document.getElementById('history-list');
            historyList.innerHTML = '';

            history.forEach(entry => {
                const listItem = document.createElement('li');
                listItem.innerHTML = `
                    <strong>${entry.tipo_atto}</strong>: ${entry.data}, n. ${entry.numero_atto}, art. ${entry.numero_articolo} 
                    <br>
                    <a href="${entry.url}" target="_blank">Link</a>
                    <br>
                    <small>Timestamp: ${entry.timestamp}</small>
                `;
                historyList.appendChild(listItem);
            });
        })
        .catch(error => {
            console.error('Errore nel recupero della cronologia:', error);
        });
}
