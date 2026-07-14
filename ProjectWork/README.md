# PDF-Analyzer

Progetto finale del percorso: analisi automatica di documenti PDF (ordini, richieste di quotazione, richieste di informazioni) ricevuti via email. Un agente Azure AI estrae il contenuto dei PDF; il risultato viene poi instradato in base al tipo di documento rilevato e validato confrontandolo con clienti e articoli reali tramite il backend REST (`ja.4labs.it:8080`), bypassando il tool-calling dell'agente (intermittente su quel percorso).

**Implementazione finale interamente su Microsoft Fabric**: gli script `.py` nella radice della cartella sono il prototipo locale con cui è stata validata la logica (estrazione, matching, instradamento); tutta la pipeline è poi stata tradotta in notebook PySpark eseguiti in Fabric, che è l'implementazione di riferimento del progetto.

📊 **Presentazione**: [loreb1998.github.io/Talent-AI-and-Data-Engineer-Academy/ProjectWork/presentazione.html](https://loreb1998.github.io/Talent-AI-and-Data-Engineer-Academy/ProjectWork/presentazione.html)

## Pipeline dati su Microsoft Fabric (implementazione finale)

La cartella [`Fabric Notebooks`](./Fabric%20Notebooks) contiene i notebook PySpark eseguiti in un Lakehouse Fabric, con architettura a medaglione (Bronze → Silver → Gold):

- **`01_estrai_e_valida.ipynb`** — legge i PDF da `Files/pdf_inbox` nel Lakehouse, chiama l'agente Azure AI Foundry per estrarre il contenuto, applica matching/instradamento (stessa logica del prototipo: ordine / quotazione / richiesta_informazioni / non_determinabile) e scrive una riga per documento nella tabella Bronze `bronze_documenti_estratti` (JSON grezzo in una colonna stringa, schema flessibile)
- **`02_bronze_to_silver.ipynb`** — scompone il JSON di Bronze in tabelle Silver tipizzate, una per tipo di documento (ordini, quotazioni e richieste di informazioni hanno schemi diversi)
- **`02b_storico_da_assets.ipynb`** — importa da Assets (backend REST, nessuna autenticazione richiesta) i dati maestri (clienti, articoli) e lo storico ordini già presente nel gestionale, da unire in Gold ai nuovi documenti estratti dai PDF
- **`03_silver_to_gold.ipynb`** — costruisce le dimensioni condivise (`dim_cliente`, `dim_articolo`, `dim_data`) e le fact table (storico vs. nuovi documenti tenute separate perché semanticamente diverse), pronte per il reporting

I dati del livello Gold alimentano la dashboard `DashBoard-ProjectWork.pbix`.

> ⚠️ Il notebook `01_estrai_e_valida.ipynb` contiene, in output di una cella, un token Azure AD usato durante lo sviluppo (già scaduto). Andrebbe rimosso dall'output prima di condividere ulteriormente il notebook.

## Prototipo locale (script Python)

Gli script Python nella radice della cartella sono il proof-of-concept su cui è stata sviluppata e testata la logica di estrazione/validazione prima di portarla in Fabric. Restano nel repository come riferimento, ma non sono la versione eseguita in produzione.

```
pdf_da_processare/          # PDF da analizzare (input)
output/                     # Risultati (output)
  ├── <nome>_ESTRATTO.txt   # Testo grezzo estratto dall'agente
  └── <nome>.json           # Risultato validato (cliente + righe matchate)

config.py                   # Costanti: endpoint, URL, path, soglie, prompt di estrazione
agent.py                    # Interazione con Azure AI (upload PDF, estrazione JSON)
backend.py                  # Chiamate HTTP al backend REST con retry
instradamento.py            # Instrada il documento al percorso corretto in base al tipo rilevato
matching.py                 # Matching cliente/articoli e validazione ordine
quotazione.py               # Preparazione bozza di quotazione (prezzo sempre da listino)
richiesta_informazioni.py   # Preparazione bozza di risposta a richieste di informazioni
conferma_ordine.py          # Creazione conferma d'ordine e righe di dettaglio (solo per gli ordini)
main.py                     # Orchestrazione e punto d'ingresso
```

### Requisiti

```bash
pip install -r requirements.txt
az login
```

Crea un file `.env` nella cartella con le variabili richieste da `config.py`:

```
ENDPOINT=<endpoint del progetto Azure AI Foundry>
AGENT_NAME=<nome dell'agente>
AGENT_VERSION=<versione dell'agente>
BACKEND_BASE_URL=http://ja.4labs.it:8080
```

### Utilizzo

1. Metti i PDF da analizzare in `pdf_da_processare/`
2. Esegui:

```bash
python main.py
```

Per abilitare anche la **creazione della conferma d'ordine** sul backend (solo per i documenti classificati come "ordine"), imposta in `config.py`:

```python
CREA_CONFERMA_ORDINE = True
```

> Lascialo a `False` finché non hai verificato manualmente i risultati JSON in `output/`.

### Flusso

1. **Estrazione** — l'agente legge ogni PDF e restituisce un JSON strutturato (tipo documento, dati cliente, righe con codici, quantità e prezzi)
2. **Classificazione e instradamento** — in base al campo `tipo_documento` estratto (`ordine`, `quotazione`, `richiesta_informazioni` o `non_determinabile`), il documento viene elaborato dal modulo corrispondente:
   - **`ordine`** — Python confronta i dati estratti con clienti e articoli reali dal backend; segnala anomalie su prezzi, unità di misura e quantità sospette
   - **`quotazione`** — prepara una bozza di quotazione ricalcolando i prezzi dal listino di catalogo (i prezzi indicati nel documento non vengono mai usati come dato di validazione)
   - **`richiesta_informazioni`** — cerca a catalogo gli articoli nominati e prepara una bozza di risposta con le informazioni disponibili
   - **`non_determinabile`** — segnala che il documento richiede intervento umano
3. **Creazione conferma** *(opzionale, solo per gli ordini)* — se tutto è valido e `CREA_CONFERMA_ORDINE = True`, crea la conferma d'ordine e le sue righe sul backend

Per quotazioni e richieste di informazioni non viene mai eseguita alcuna scrittura automatica sul backend: si producono solo bozze da far rivedere a un operatore. La stessa logica di instradamento è replicata (in PySpark, senza dipendenze aggiuntive perché è codice Python puro) nel notebook `01_estrai_e_valida.ipynb` su Fabric.

### Output JSON

Ogni PDF produce un file `output/<nome>.json`. Per un ordine la struttura è ad esempio:

```json
{
  "tipo_documento": "ordine",
  "intervento_umano_necessario": false,
  "motivo_intervento_umano": null,
  "cliente": { "id_cliente_match": "...", "ragione_sociale": "...", ... },
  "riferimento_ordine": "...",
  "data_ordine": "...",
  "righe": [
    {
      "codice_articolo_match": "ART-015",
      "confidenza_match": "alta",
      "note_anomalia": null,
      ...
    }
  ]
}
```

Il campo `intervento_umano_necessario` è `true` se il cliente non è stato identificato, un articolo non ha match certo, una riga contiene note, o i prezzi/unità di misura non corrispondono al catalogo. Per quotazioni e richieste di informazioni è sempre `true`, dato che ogni bozza va comunque rivista da un operatore.

### Configurazione

Le variabili principali sono in `config.py`:

| Variabile | Default | Descrizione |
|---|---|---|
| `ENDPOINT` | *(da `.env`)* | Endpoint del progetto Azure AI Foundry |
| `AGENT_NAME` / `AGENT_VERSION` | *(da `.env`)* | Nome e versione dell'agente Azure AI usato per l'estrazione |
| `BACKEND_BASE_URL` | *(da `.env`)* | URL del backend REST |
| `CREA_CONFERMA_ORDINE` | `False` | Abilita la scrittura sul backend per gli ordini |
| `SOGLIA_TOLLERANZA_PREZZO` | `0.01` (1%) | Scostamento prezzo oltre il quale segnalare anomalia |
| `QUANTITA_MASSIMA_PLAUSIBILE` | `100000` | Soglia oltre la quale la quantità è segnalata come sospetta |
