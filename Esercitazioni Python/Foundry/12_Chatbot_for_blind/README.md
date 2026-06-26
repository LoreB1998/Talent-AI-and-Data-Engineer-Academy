# Chatbot Vocale per Non Vedenti — ACME Systems

Assistente vocale pensato per permettere a clienti non vedenti di completare un acquisto di articoli di ferramenta **interamente tramite voce**, senza alcuna interfaccia visiva. Il sistema si connette ad Azure AI Voice Live (modello real-time), ascolta il cliente tramite microfono, risponde a voce tramite speaker, e gestisce il carrello chiamando funzioni Python reali ogni volta che il modello AI lo richiede.

**Flusso generale:**
1. Il programma carica il catalogo prodotti da CSV.
2. Apre una sessione Voice Live su Azure con le istruzioni di sistema e gli schemi delle funzioni disponibili.
3. Cattura continuamente l'audio dal microfono e lo invia ad Azure.
4. Riceve in streaming l'audio sintetizzato dal modello e lo riproduce sugli speaker.
5. Quando il modello decide di chiamare una funzione (es. aggiungere un prodotto), la esegue localmente e rimanda il risultato testuale al modello.
6. La sessione si chiude quando il cliente conferma, annulla o sospende l'acquisto.
7. Se il carrello è stato sospeso, al riavvio viene ripristinato automaticamente da `carrello.json`.

---

## Script per script

### `config.py` — Configurazione centralizzata

Carica le variabili d'ambiente (da `.env` se presente) e le espone come costanti usate dagli altri moduli.

| Costante | Descrizione |
|---|---|
| `FOUNDRY_ENDPOINT` | URL della risorsa Azure AI Foundry |
| `MODEL_NAME` | Nome del modello da usare (es. `gpt-5.4-nano`) |
| `VOICE_LIVE_API_VERSION` | Versione API di Voice Live |
| `VOICE_LANGUAGE` | Lingua della trascrizione audio (default: `it-IT`) |
| `VOICE_NAME` | Voce sintetizzata (default: `it-IT-IsabellaNeural`) |
| `CSV_PATH` | Percorso del file CSV con il catalogo prodotti |

---

### `catalog.py` — Catalogo prodotti

Gestisce il caricamento degli articoli di ferramenta dal file CSV.

#### `Prodotto` (dataclass)
Rappresenta un singolo articolo del catalogo con i campi: `codice`, `descrizione`, `categoria`, `unita_misura`, `prezzo`.

#### `carica_catalogo(path=None)`
Legge il file CSV indicato (o quello in `config.CSV_PATH`) e popola il dizionario interno `_catalogo` con tutti i prodotti. Va chiamata **una sola volta** all'avvio. Le righe malformate vengono saltate con un avviso in console.

#### `get_prodotto(codice)`
Restituisce il `Prodotto` corrispondente al codice esatto, oppure `None` se non esiste. Usata internamente da `tools.py` per recuperare un prodotto prima di aggiungerlo al carrello.

#### `get_tutti_i_prodotti()`
Restituisce la lista di tutti i `Prodotto` nel catalogo. Usata da `main.py` per iniettare il catalogo completo nelle istruzioni di sistema all'avvio.

---

### `cart.py` — Gestione del carrello

Contiene tutta la logica del carrello: aggiunta, modifica, rimozione, descrizione vocale, salvataggio e conclusione dell'acquisto.

#### `RigaCarrello` (dataclass)
Rappresenta una riga del carrello: un `Prodotto` e la `quantita` richiesta. La proprietà calcolata `totale_riga` restituisce `prezzo × quantità` arrotondato a 2 decimali.

#### `Cart`
Classe principale che gestisce l'intero ciclo del carrello. Lo stato interno può essere `"aperto"`, `"pagato"`, `"annullato"` o `"sospeso"`.

| Metodo | Descrizione |
|---|---|
| `carica(path)` _(classmethod)_ | Legge `carrello.json` e, se lo stato è `"sospeso"`, ricostruisce le righe e restituisce un `Cart` già popolato. Se il file non esiste o lo stato è diverso, restituisce un carrello vuoto. |
| `aggiungi(prodotto, quantita)` | Aggiunge un prodotto al carrello. Se il codice è già presente, incrementa la quantità esistente. Restituisce una stringa descrittiva da leggere al cliente. |
| `modifica_quantita(codice, nuova_quantita)` | Imposta una quantità esatta per un articolo già nel carrello. Se la nuova quantità è ≤ 0, rimuove l'articolo chiamando `rimuovi`. |
| `rimuovi(codice)` | Rimuove completamente un articolo dal carrello tramite il suo codice. |
| `totale()` | Calcola e restituisce il totale complessivo del carrello in euro. |
| `descrivi()` | Genera una descrizione testuale ottimizzata per la lettura vocale: elenca ogni riga con quantità, prezzo unitario e totale di riga, poi chiude con il totale complessivo. |
| `salva(path)` | Serializza lo stato del carrello (timestamp, stato, articoli, totale) in un file JSON. Chiamata automaticamente da `conferma_pagamento`, `svuota` e `sospendi`. |
| `sospendi()` | Salva il carrello in stand-by con gli articoli intatti (stato `"sospeso"`). La sessione si chiude, ma al prossimo avvio il carrello viene ripristinato da `carica()`. |
| `svuota()` | Annulla l'acquisto: svuota le righe, imposta lo stato a `"annullato"` e salva il file JSON. |
| `conferma_pagamento()` | Conferma l'acquisto: imposta lo stato a `"pagato"`, salva il JSON e restituisce un messaggio di conferma con il totale addebitato. |
| `is_terminato()` | Restituisce `True` se il carrello è in stato `"pagato"`, `"annullato"` o `"sospeso"`, segnalando che la sessione può chiudersi. |

---

### `tools.py` — Bridge tra il modello AI e le funzioni Python

Definisce gli schemi delle funzioni esposte al modello e il dispatcher che le esegue realmente.

#### `TOOLS_SCHEMA` (lista)
Lista di dizionari JSON Schema che descrive al modello AI le 8 funzioni disponibili, con nome, descrizione e parametri attesi. Il modello usa questi schemi per decidere quale funzione chiamare e con quali argomenti.

| Funzione esposta al modello | Scopo |
|---|---|
| `aggiungi_al_carrello` | Aggiunge una quantità di un articolo (per codice) al carrello |
| `modifica_quantita_carrello` | Cambia la quantità di un articolo già nel carrello |
| `rimuovi_dal_carrello` | Rimuove completamente un articolo dal carrello |
| `mostra_carrello` | Descrive il contenuto e il totale del carrello |
| `conferma_acquisto` | Conferma il pagamento e chiude la sessione |
| `annulla_acquisto` | Annulla l'acquisto e svuota il carrello |
| `sospendi_acquisto` | Salva il carrello in stand-by e chiude la sessione; al riavvio il carrello viene ripristinato |

#### `esegui_funzione(nome_funzione, argomenti_json, cart)`
Dispatcher centrale: riceve il nome della funzione e gli argomenti JSON scelti dal modello, li deserializza, chiama la funzione Python corrispondente (su `catalog` o `cart`) e restituisce sempre una stringa. Questa stringa viene rimandata al modello come risultato della function call, così il modello può formulare la risposta vocale al cliente. In caso di funzione sconosciuta o argomenti malformati, restituisce un messaggio di errore.

---

### `main.py` — Punto di ingresso e gestione della sessione

Orchestra tutti i componenti: audio locale, connessione a Azure Voice Live, invio del microfono e gestione degli eventi in arrivo.

#### Costanti audio
`SAMPLE_RATE` (24 kHz), `CHANNELS` (mono), `CHUNK_MS` (20 ms) e `CHUNK_SAMPLES` definiscono il formato PCM16 usato sia in ingresso (microfono) che in uscita (speaker), compatibile con l'API Voice Live.

#### `AudioIO`
Wrapper su `sounddevice` che astrae le operazioni audio in tre metodi:

| Metodo | Descrizione |
|---|---|
| `leggi_chunk()` | Legge un chunk dal microfono e lo restituisce come `bytes` PCM16 |
| `scrivi_audio(audio_bytes)` | Riceve `bytes` PCM16 e li riproduce sullo speaker in tempo reale |
| `chiudi()` | Ferma e chiude i flussi audio di input e output |

#### `_costruisci_istruzioni()`
Assembla il testo delle istruzioni di sistema iniettando il catalogo completo (tutti i prodotti con codice, descrizione, prezzo e categoria) dentro il template `_ISTRUZIONI_BASE`. In questo modo il modello conosce l'intero catalogo sin dall'inizio e può rispondere a domande semantiche ("cosa avete per attaccare due pezzi di legno?") senza ricorrere a una ricerca per parole chiave.

#### `_costruisci_session_config()`
Assembla l'oggetto `RequestSession` da inviare ad Azure al momento dell'apertura della sessione. Include: modalità testo+audio, istruzioni di sistema (generate da `_costruisci_istruzioni()`), voce sintetizzata, lingua di trascrizione, schemi delle funzioni (`TOOLS_SCHEMA`) e rilevamento automatico del silenzio (`AzureSemanticVad`).

#### `_invia_audio_microfono(connection, audio_io, stop_event)` _(async)_
Task asincrono che gira in loop continuo: legge chunk dal microfono tramite `audio_io.leggi_chunk()` e li invia all'`input_audio_buffer` della sessione Voice Live. Si ferma quando `stop_event` viene impostato (cioè quando l'acquisto è concluso).

#### `_gestisci_eventi(connection, audio_io, cart, stop_event)` _(async)_
Loop principale degli eventi in arrivo dal server. Gestisce tre tipi di evento:
- `response.audio.delta` — pezzo di audio sintetizzato: lo riproduce subito tramite `audio_io.scrivi_audio`.
- `response.function_call_arguments.done` — il modello ha scelto una funzione: la esegue tramite `esegui_funzione`, rimanda il risultato come `FunctionCallOutputItem`, chiede al modello di continuare la risposta, e controlla se la sessione è terminata.
- `error` — errore dalla sessione: lo stampa in console.

#### `main()` _(async)_
Funzione principale che:
1. Carica il catalogo (`catalog.carica_catalogo()`).
2. Ripristina il carrello con `Cart.carica()`: se esiste un `carrello.json` sospeso, lo ricarica; altrimenti crea un carrello vuoto.
3. Istanzia l'audio I/O.
4. Si connette ad Azure con `DefaultAzureCredential` e apre la sessione Voice Live.
5. Aggiorna la configurazione della sessione.
6. Avvia in parallelo i due task asincroni (`_invia_audio_microfono` e `_gestisci_eventi`).
7. Attende la fine della gestione eventi, poi cancella il task del microfono e chiude l'audio.

---

## File di dati

| File | Descrizione |
|---|---|
| `articoli.csv` | Catalogo prodotti di ferramenta (codice, descrizione, categoria, unità misura, prezzo) |
| `carrello.json` | Generato automaticamente a fine sessione con lo stato finale del carrello |
| `requirements.txt` | Dipendenze Python del progetto |

---

## Requisiti e avvio

```bash
pip install -r requirements.txt
```

Creare un file `.env` con le variabili necessarie:

```env
FOUNDRY_ENDPOINT=https://<la-tua-risorsa>.services.ai.azure.com
MODEL_NAME=gpt-5.4-nano
VOICE_LANGUAGE=it-IT
VOICE_NAME=it-IT-IsabellaNeural
CSV_PATH=articoli.csv
```

Autenticarsi ad Azure (la connessione usa `DefaultAzureCredential`):

```bash
az login
```

Avviare il chatbot:

```bash
python main.py
```
