# 🏠 Sistema di Domotica Vocale

Sistema di automazione domestica controllabile tramite comandi vocali o testuali, basato su **Azure OpenAI** (GPT con function calling) e **Azure Cognitive Services Speech** per il riconoscimento e la sintesi vocale.

## Funzionalità richieste

| | Base |
|---|---|
|🚪 **Porta** | Aprire/Chiudere la porta di una stanza specifica |
| 🚧 **Cancello/Garage** | Aprire/Chiudere il cancello o il garage |
| 💡 **Luci** | Accendere/Spegnere le luci di una stanza |

| | Avanzate |
|---|---|
| 🔆 **Intensità luci** | Aumento, diminuizione o impostare un valore assoluto (0–100%) |
| 🪟 **Finestre** | Apertura parziale o totale (percentuale configurabile) |
| 🌡️ **Climatizzatore** | Impostare temperatura e modalità (auto, relax, raffreddamento, riscaldamento) |
| ✨ **Ambiente romantico** | Attivazione luci rosse soffuse, climatizzazione, chiusura porta e musica |


## Architettura logica del sistema

```
┌─────────────────────────────────────────┐
│            Interfaccia Utente           │
│      (voce via microfono / testo)       │
└───────────────────┬─────────────────────┘
                    │
          ┌─────────▼──────────┐
          │  AssistenteVocale  │  ← Azure Speech SDK (STT + TTS)
          └─────────┬──────────┘
                    │ testo trascritto
          ┌─────────▼──────────┐
          │ InterpreteComandi  │  ← Azure OpenAI GPT + Function Calling
          └─────────┬──────────┘
                    │ tool_calls
          ┌─────────▼──────────┐
          │   CasaDomotica     │  ← Orchestratore stanze e dispositivi
          └─────────┬──────────┘
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
   Stanza        Stanza       Cancello
  (Luce,        (Luce,
  Porta,        Porta,
  Finestra,     Finestra,
  Clima)        Clima)
```

### Classi principali

| Classe | Responsabilità |
|---|---|
| `Luce` | Gestione stato, intensità (0–100) e colore |
| `Porta` | Apertura/chiusura porta interna |
| `Finestra` | Apertura graduale in percentuale |
| `Climatizzatore` | Temperatura e modalità di funzionamento |
| `Cancello` | Cancello/garage dell'abitazione |
| `Stanza` | Aggregatore di tutti i dispositivi di una stanza |
| `CasaDomotica` | Orchestratore globale; espone i metodi mappati ai tool GPT |
| `InterpreteComandi` | Traduce linguaggio naturale in chiamate a funzione via GPT |
| `AssistenteVocale` | Speech-to-text e text-to-speech tramite Azure Speech SDK |



## Prerequisiti

- Python 3.9+
- Account **Azure** con:
  - Risorsa **Azure OpenAI** (deployment GPT-4 o GPT-3.5-turbo con function calling)
  - Risorsa **Azure Cognitive Services Speech** (opzionale, solo per la modalità vocale)



## Installazione programma

```bash
# 1. Clonazione repository
git clone https://github.com/non-ci-provare-a-copiare-la-mia-idea/domotica-vocale.git
cd domotica-vocale

# 2. Creare e attivare un ambiente virtuale
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Installare le dipendenze
pip install openai azure-cognitiveservices-speech python-dotenv
```

---

## Configurazione del sistema

Creare un file `.env` nella root del progetto con le seguenti variabili:

```env
# Azure OpenAI
AZ_OPENAI_KEY=<la-tua-api-key>
AZ_OPENAI_ENDPOINT=<https://tuo-endpoint.openai.azure.com/>
AZ_OPENAI_DEPLOYMENT=<nome-deployment-gpt>
AZ_OPENAI_API_VERSION=2024-02-01

# Azure Speech (opzionale, solo per la modalità vocale)
AZ_SPEECH_KEY=<la-tua-speech-key>
AZ_SPEECH_REGION=<es. westeurope>
AZ_SPEECH_ENDPOINT=<endpoint-speech>
AZ_SPEECH_VOICE=<es. it-IT-IsabellaNeural>
```

---

## Esempi di Casi d'Uso

### Modalità testo (senza microfono)

```bash
python main.py --modo testo
```

Si può digitare comandi in linguaggio naturale italiano:

```
Tu: Accendi la luce in cucina al 50%
🏠 💡 Luce di cucina accesa al 50%.

Tu: Apri il cancello
🏠 🚧 Cancello/garage aperto.

Tu: Crea un'atmosfera romantica in camera
🏠 ✨ Ambiente romantico attivato.
🏠 💡 Colore luce di camera impostato su rosso.
🏠 💡 Intensità luce di camera impostata al 35%.
🏠 🌡️ Climatizzatore di camera impostato a 22°C (relax).
🏠 🚪 Porta di camera chiusa.
🏠 🎵 Riproduzione musica avviata: 'Never Gonna Give You Up' (Rick Astley).
```

### Modalità vocale (con microfono e Azure Speech)

```bash
python main.py --modo voce
```

Il sistema rimane in ascolto continuo; pronuncia un comando in italiano e attendi la risposta audio.

## Tool disponibili (Function Calling)

| Tool | Parametri | Descrizione |
|---|---|---|
| `apri_porta` | `stanza` | Apre la porta di una stanza |
| `chiudi_porta` | `stanza` | Chiude la porta di una stanza |
| `apri_cancello` | — | Apre il cancello/garage |
| `chiudi_cancello` | — | Chiude il cancello/garage |
| `accendi_luce` | `stanza`, `intensita` (opt.) | Accende la luce |
| `spegni_luce` | `stanza` | Spegne la luce |
| `imposta_intensita_luce` | `stanza`, `intensita` | Intensità assoluta 0–100 |
| `varia_intensita_luce` | `stanza`, `delta` | Variazione relativa dell'intensità |
| `apri_finestra` | `stanza`, `percentuale` (opt.) | Apre la finestra |
| `chiudi_finestra` | `stanza` | Chiude la finestra |
| `imposta_climatizzatore` | `stanza`, `temperatura`, `modalita` | Configura il clima |
| `stato_stanza` | `stanza` | Restituisce lo stato di tutti i dispositivi |
| `crea_ambiente_romantico` | `stanza` | Attiva la modalità romantica |



## Stanze predefinite

Il sistema è inizializzato con le seguenti stanze: `soggiorno`, `cucina`, `camera`, `bagno`, `cameretta`.

Le stanze non presenti di default sono create in modo automatico al primo utilizzo.


## Struttura del progetto

```
domotica-vocale/
├── main.py          # Entry point e loop principale
├── .env             # Variabili d'ambiente
├── .env.example     # Template per la configurazione
├── requirements.txt # Dipendenze Python
└── README.md        # File descrittivo
```


## Note e limitazioni

- La **riproduzione musicale** è attualmente simulata; per un'integrazione reale è necessario collegare un servizio musicale.
- La totale logica dei dispositivi è **in memoria**: al riavvio del programma lo stato è azzerato. Se c'è bisogno della persistenza degli stati si può aggiungere un backend (file JSON, database, MQTT, ecc.).
- Il riconoscimento vocale funziona esclusivamente in **italiano** (`it-IT`).
