# PDF-Analyzer

Script locale per l'analisi automatica di ordini in PDF. Usa un agente Azure AI per estrarre il contenuto dei PDF, poi valida clienti e articoli chiamando direttamente il backend REST (`ja.4labs.it:8080`), bypassando il tool-calling dell'agente (intermittente su quel percorso).

## Architettura

```
pdf_da_processare/          # PDF da analizzare (input)
output/                     # Risultati (output)
  ├── <nome>_ESTRATTO.txt   # Testo grezzo estratto dall'agente
  └── <nome>.json           # Ordine validato (cliente + righe matchate)

config.py                   # Costanti: endpoint, URL, path, soglie, prompt
agent.py                    # Interazione con Azure AI (upload PDF, estrazione JSON)
backend.py                  # Chiamate HTTP al backend REST con retry
matching.py                 # Matching cliente/articoli e validazione ordine
conferma_ordine.py          # Creazione conferma d'ordine e righe di dettaglio
main.py                     # Orchestrazione e punto d'ingresso
```

## Requisiti

```bash
pip install azure-ai-projects>=2.1.0 azure-identity requests
az login
```

## Utilizzo

1. Metti i PDF da analizzare in `pdf_da_processare/`
2. Esegui:

```bash
python main.py
```

Per abilitare anche la **creazione della conferma d'ordine** sul backend, imposta in `config.py`:

```python
CREA_CONFERMA_ORDINE = True
```

> Lascialo a `False` finché non hai verificato manualmente i risultati JSON in `output/`.

## Flusso

1. **Estrazione** — l'agente legge ogni PDF e restituisce un JSON strutturato (tipo documento, dati cliente, righe con codici, quantità e prezzi)
2. **Validazione** — Python confronta i dati estratti con clienti e articoli reali dal backend; segnala anomalie su prezzi, unità di misura e quantità sospette
3. **Creazione conferma** *(opzionale)* — se tutto è valido e `CREA_CONFERMA_ORDINE = True`, crea la conferma d'ordine e le sue righe sul backend

## Output JSON

Ogni PDF produce un file `output/<nome>.json` con questa struttura:

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

Il campo `intervento_umano_necessario` è `true` se il cliente non è stato identificato, un articolo non ha match certo, una riga contiene note, o i prezzi/unità di misura non corrispondono al catalogo.

## Configurazione

Le variabili principali sono in `config.py`:

| Variabile | Default | Descrizione |
|---|---|---|
| `ENDPOINT` | Azure AI endpoint | Endpoint del progetto Azure AI Foundry |
| `BACKEND_BASE_URL` | `http://ja.4labs.it:8080` | URL del backend REST |
| `CREA_CONFERMA_ORDINE` | `False` | Abilita la scrittura sul backend |
| `SOGLIA_TOLLERANZA_PREZZO` | `0.01` (1%) | Scostamento prezzo oltre il quale segnalare anomalia |
| `QUANTITA_MASSIMA_PLAUSIBILE` | `100000` | Soglia oltre la quale la quantità è segnalata come sospetta |
