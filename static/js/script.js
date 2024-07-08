/*******************************
 * PARTE 1: GESTIONE DELLA SOTTOMISSIONE DEL FORM
 *******************************/
let lastUrn = ''; // Variabile per memorizzare l'URN ottenuto
let articleTree = [];
let lastFetchedUrl = '';

// Listener per la sottomissione del form
document.getElementById('scrape-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    if (data.article) {
        data.article = data.article.replace(/\s+/g, '');
    }

    setLoading(true);

    try {
        console.log('Sending request to /fetch_norm with data:', data);
        const response = await fetch('/fetch_norm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        setLoading(false);

        console.log('Received response from /fetch_norm:', result);
        
        const normaDataContainer = document.getElementById('norma-data');
        const resultContainer = document.getElementById('result');
        const brocardiInfoContainer = document.getElementById('brocardi-info-container');

        if (result.error) {
            handleError(result.error, resultContainer);
        } else {
            displayNormaData(result.norma_data, result.result);
            lastUrn = result.urn; // Memorizza l'URN ottenuto

            if (lastFetchedUrl !== result.norma_data.url) {
                lastFetchedUrl = result.norma_data.url;
                setArticleTree(result.tree);
            }

            // Aggiorna la cronologia dopo la ricerca
            updateHistory();

            // Mostra le informazioni di Brocardi
            if (result.brocardi_info) {
                displayBrocardiInfo(result.brocardi_info);
                brocardiInfoContainer.style.display = 'block';
            } else {
                brocardiInfoContainer.style.display = 'none';
            }
        }
    } catch (error) {
        setLoading(false);
        handleError(error, document.getElementById('result'));
    }
});

// Funzione per visualizzare i dati della norma
function displayNormaData(normaData, resultText) {
    console.log('Displaying norma data:', normaData);
    const normaDataContainer = document.getElementById('norma-data');
    normaDataContainer.innerHTML = `
        <h2>Informazioni della Norma Visitata</h2>
        <p><strong>Tipo atto:</strong> ${normaData.tipo_atto}</p>
        <p><strong>Data:</strong> ${normaData.data}</p>
        <p><strong>Numero atto:</strong> ${normaData.numero_atto}</p>
        <p><strong>Numero articolo:</strong> ${normaData.numero_articolo}</p>
        <p><strong>Versione:</strong> ${normaData.versione}</p>
        <p><strong>Data versione:</strong> ${normaData.data_versione}</p>
        <p><strong>URL:</strong> <a href="${normaData.url}" target="_blank">${normaData.url}</a></p>
        <p><strong>Timestamp:</strong> ${normaData.timestamp}</p>
    `;
    const resultContainer = document.getElementById('result');
    resultContainer.textContent = resultText;
}

// Funzione per visualizzare le informazioni di Brocardi
function displayBrocardiInfo(info) {
    console.log('Displaying brocardi info:', info);
    const brocardiInfoContainer = document.getElementById('brocardi-info');
    brocardiInfoContainer.innerHTML = `
        <h2>Informazioni aggiuntive</h2>
        ${info.position ? `<p><strong>Posizione:</strong> ${info.position}</p>` : ''}
        ${info.info.Brocardi ? `<h3>Brocardi:</h3><ul>${info.info.Brocardi.map(text => `<li>${text}</li>`).join('')}</ul>` : ''}
        ${info.info.Ratio ? `<h3>Ratio:</h3><p>${info.info.Ratio}</p>` : ''}
        ${info.info.Spiegazione ? `<h3>Spiegazione:</h3><p>${info.info.Spiegazione}</p>` : ''}
        ${info.info.Massime ? `<h3>Massime:</h3><p>${info.info.Massime}</p>` : ''}
    `;
}

/*******************************
 * PARTE 2: GESTIONE DEGLI ARTICOLI E URL
 *******************************/
function setArticleTree(tree) {
    console.log('Setting article tree:', tree);

    // Assicurati che `tree` sia un array e prendi il primo elemento
    if (Array.isArray(tree) && Array.isArray(tree[0])) {
        articleTree = tree[0].map(item => {
            if (typeof item === 'object' && item !== null) {
                return Object.keys(item)[0];
            }
            return item;
        });
    } else {
        console.error('Invalid tree format:', tree);
    }

    console.log('Formatted article tree:', articleTree);
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

    console.log('Initializing version date input');
    initializeVersionDateInput(elements.versionVigente, elements.versionDateInput);
    setupVersionDateToggle(elements.versionVigente, elements.versionOriginale, elements.versionDateInput);

    console.log('Setting up article buttons');
    setupArticleButtons(elements.decrementButton, elements.incrementButton, elements.articleInput, elements.actTypeInput);
    setupPdfButton(elements.viewPdfButton, elements.pdfFrame, elements.downloadPdfButton, elements.fullscreenButton, elements.collapsibleButton, elements.collapsibleContent);

    elements.collapsibleButton.addEventListener('click', toggleCollapsibleContent);
    updateHistory();
});

// Funzione per inizializzare lo stato dell'input della data di versione
function initializeVersionDateInput(versionVigente, versionDateInput) {
    console.log('Initializing version date input state');
    if (versionVigente.checked) {
        versionDateInput.disabled = false;
        versionDateInput.style.opacity = 1;
    } else {
        versionDateInput.disabled = true;
        versionDateInput.style.opacity = 0.5;
    }
}

// Funzione per configurare il toggle della data di versione
function setupVersionDateToggle(versionVigente, versionOriginale, versionDateInput) {
    console.log('Setting up version date toggle');
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

// Funzione per configurare i bottoni per l'articolo
function setupArticleButtons(decrementButton, incrementButton, articleInput, actTypeInput) {
    if (decrementButton && incrementButton && articleInput) {
        console.log('Setting up article buttons');
        decrementButton.addEventListener('click', () => updateArticleInput(articleInput, actTypeInput, decrementArticle));
        incrementButton.addEventListener('click', () => updateArticleInput(articleInput, actTypeInput, incrementArticle));
    }
}

// Funzione per aggiornare l'input dell'articolo
function updateArticleInput(articleInput, actTypeInput, updateFunction) {
    let currentValue = articleInput.value;
    console.log('Updating article input from:', currentValue);
    if (!actTypeInput.value) {
        currentValue = '1'; // Imposta l'articolo a 1 se il tipo di atto non è selezionato
    } else {
        currentValue = updateFunction(currentValue);
    }
    articleInput.value = currentValue;
    articleInput.focus();
    articleInput.dispatchEvent(new Event('input'));
    console.log('Updated article input to:', currentValue);
}

// Funzioni per incrementare e decrementare l'articolo
function incrementArticle(article) {
    return getUpdatedArticle(article, 1);
}

function decrementArticle(article) {
    return getUpdatedArticle(article, -1);
}

// Funzione per ottenere l'articolo aggiornato
function getUpdatedArticle(article, direction) {
    console.log('Updating article:', article, 'direction:', direction);
    if (!validateArticleInput(article)) {
        return '1'; // Imposta l'articolo a 1 se l'input non è valido
    }

    // Trova l'indice dell'articolo corrente
    let index = articleTree.indexOf(article);
    console.log('Current article index:', index);

    if (index < 0) {
        console.warn('Article not found in articleTree:', article);
        index = 0;
    } else {
        // Calcola il nuovo indice
        index = (index + direction + articleTree.length) % articleTree.length;
    }
    console.log('New article index:', index);

    // Ritorna l'articolo all'indice aggiornato
    return articleTree[index];
}

// Funzione per configurare il bottone del PDF
function setupPdfButton(viewPdfButton, pdfFrame, downloadPdfButton, fullscreenButton, collapsibleButton, collapsibleContent) {
    console.log('Setting up PDF button');
    viewPdfButton.addEventListener('click', async function() {
        if (!lastUrn) {
            alert('Per favore completa prima una ricerca.');
            return;
        }

        setLoading(true);

        try {
            console.log('Sending request to /export_pdf with URN:', lastUrn);
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

            console.log('PDF URL:', pdfUrl);
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

// Funzione per configurare il download e il fullscreen del PDF
function setupDownloadAndFullscreen(downloadPdfButton, fullscreenButton, pdfFrame, pdfUrl) {
    console.log('Setting up download and fullscreen buttons');
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

// Funzione per togglare il contenuto collapsible
function toggleCollapsibleContent() {
    console.log('Toggling collapsible content');
    this.classList.toggle('active');
    const content = this.nextElementSibling;
    content.style.display = content.style.display === 'block' ? 'none' : 'block';
}

/*******************************
 * FUNZIONI DI SUPPORTO
 *******************************/
// Funzione per gestire gli errori
function handleError(error, messageContainer) {
    console.error('Error:', error);
    if (messageContainer) {
        messageContainer.textContent = `Error: ${error.message || error}`;
    } else {
        alert(`Error: ${error.message || error}`);
    }
}

// Funzione per impostare lo stato di caricamento
function setLoading(isLoading) {
    const loadingElement = document.getElementById('loading');
    if (loadingElement) {
        loadingElement.style.display = isLoading ? 'block' : 'none';
    }
}

// Funzione per validare l'input dell'articolo
function validateArticleInput(article) {
    console.log('Validating article input:', article);
    if (!article || !articleTree.includes(article)) {
        console.error('Invalid article:', article);
        alert('Articolo non valido. Per favore inserisci un articolo valido.');
        return false;
    }
    return true;
}

// Funzione per aggiornare la cronologia
function updateHistory() {
    console.log('Updating history');
    fetch('/history')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok.');
            }
            return response.json();
        })
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
            console.log('History updated:', history);
        })
        .catch(error => {
            console.error('Errore nel recupero della cronologia:', error);
        });
}
