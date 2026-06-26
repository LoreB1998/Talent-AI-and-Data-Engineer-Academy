# Identificatore di giochi — Agente vero, configurato su Foundry

Architettura: l'**agente** (istruzioni, modello, eventuali tool) è definito e
pubblicato interamente nel **portale Foundry**. Il codice Python **non** contiene
più nessuna logica dell'agente: si limita a chiamare l'endpoint pubblicato,
usando la tua **API key** (niente `az login`, niente Entra ID, niente
`azure-ai-projects`).

```
identificatore-giochi/
├── requirements.txt   # dipendenze (solo openai + dotenv)
├── .env.example        # copia in .env e compila
├── agent_config.py     # costruisce l'URL dell'agente pubblicato + legge la key
├── identify.py         # chiama l'agente per identificare un gioco
└── README.md
```

---

## Come funziona il collegamento

Quando pubblichi un agente sul portale Foundry come **Agent Application**, ottieni
un endpoint stabile di questa forma:

```
https://<risorsa>.services.ai.azure.com/api/projects/<progetto>/applications/<nome-app>/protocols/openai
```

Questo endpoint **accetta l'autenticazione via API key** (la stessa che hai già),
a patto che l'agente non usi tool configurati con autenticazione *On-Behalf-Of*
(OBO) — es. certe connessioni "knowledge base" ad Azure AI Search. In quel caso
specifico servirebbe per forza un token Entra ID. Per il nostro caso (identificare
un gioco da una descrizione) non è un problema: bastano modello + istruzioni,
ed eventualmente tool semplici (web search, OpenAPI con auth "anonymous" o
"api key").

`agent_config.py` costruisce questo URL da `AZ_FOUNDRY_EP` (che hai già) + un
nuovo nome che scegli tu in fase di pubblicazione, `AZ_FOUNDRY_AGENT_APP_NAME`.

---

## Parte 1 — Crea l'agente sul portale Foundry

> Portale: https://ai.azure.com — qui sei già autenticato con il tuo account
> (browser), quindi questa parte non richiede `az login` né alcuna chiave: è
> tutto "click" sul sito.

1. Apri il tuo progetto (`proj-default`).
2. Vai nella sezione **Agents** del progetto e crea un nuovo agente.
3. Compila:
   - **Instructions**: il comportamento dell'agente. Esempio di partenza
     (puoi copiarlo/adattarlo direttamente nel campo Instructions):

     ```text
     Sei un esperto di videogiochi e giochi da tavolo con conoscenza enciclopedica
     di titoli di ogni epoca, genere e piattaforma.

     COMPITO
     Dato il testo dell'utente che descrive un gioco (meccaniche, ambientazione,
     epoca, piattaforma, stile grafico, numero di giocatori, personaggi o elementi
     memorabili, ecc.), capisci DI QUALE GIOCO si tratta.

     LINEE GUIDA
     - Proponi da 1 a 3 candidati, ordinati dal più probabile al meno probabile.
     - Per ogni candidato indica: Titolo, Tipo (videogioco o gioco da tavolo),
       Anno/Editore o sviluppatore (se lo conosci), Confidenza (Alta/Media/Bassa)
       e una breve motivazione legata agli indizi della descrizione.
     - Se la descrizione è vaga, fai 1-2 domande mirate per restringere il campo.
     - Non inventare titoli: se non riconosci il gioco, dillo apertamente.
     - Rispondi sempre in italiano, in modo chiaro e conciso.

     FORMATO RISPOSTA
     Candidato 1: <titolo>
     - Tipo: <videogioco | gioco da tavolo>
     - Anno/Editore: <... oppure "non noto">
     - Confidenza: <Alta | Media | Bassa>
     - Perché: <motivazione>
     ```

   - **Model**: scegli il deployment già presente nel progetto (es. `gpt-4o` o
     `gpt-4o-mini`).
   - **Tools** (opzionale): puoi aggiungere Web Search se vuoi che riconosca
     titoli molto recenti. Evita tool con autenticazione OBO se vuoi continuare
     a chiamarlo con la sola API key.
4. Salva/testa l'agente nel playground del portale finché sei contento delle
   risposte.

## Parte 2 — Pubblicalo come Agent Application

1. Dalla pagina dell'agente, usa l'azione **Publish**.
2. Dai un nome alla Agent Application — **questo nome va copiato in
   `AZ_FOUNDRY_AGENT_APP_NAME`** nel tuo `.env`.
3. Il portale ti mostrerà l'endpoint pubblicato. Deve avere la forma:
   ```
   .../api/projects/proj-default/applications/<nome-che-hai-scelto>/protocols/openai
   ```
   Se il nome nell'URL coincide con quello scelto al passo 2, sei a posto.

> Se aggiorni le istruzioni o i tool dell'agente in futuro, ripeti **Publish**:
> l'endpoint rimane lo stesso, il traffico passa automaticamente alla versione
> aggiornata.

---

## Parte 3 — Configurazione Python

### 1. Crea l'ambiente e installa le dipendenze
```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Compila il file `.env`
```bash
cp .env.example .env      # Windows:  copy .env.example .env
```
Inserisci:
- `AZ_FOUNDRY_EP` — lo hai già.
- `AZ_FOUNDRY_KEY` — portale Azure → risorsa "foundyperagents" → **Keys and
  Endpoint** → copia KEY 1.
- `AZ_FOUNDRY_AGENT_APP_NAME` — il nome scelto in fase di Publish (Parte 2).

---

## Uso

```bash
python identify.py "Gioco da tavolo cooperativo, 4 personaggi con poteri diversi, si combattono malattie che si diffondono su una mappa del mondo, obiettivo: trovare 4 cure prima che scoppino le epidemie."
```

Oppure in modalità interattiva:
```bash
python identify.py
```

`identify.py` non passa più nessun `model`, nessuna `instructions`: l'Agent
Application pubblicata già sa tutto questo. Lo script manda solo `input`
(la tua descrizione) e legge `output_text`.

---

## Limite da conoscere: niente memoria tra i turni (per ora)

Il protocollo delle Agent Applications espone solo l'endpoint **stateless**
`POST /responses`: ogni chiamata è indipendente, senza una conversazione
persistita lato server. Per il nostro caso (identificare un gioco da UNA
descrizione) va benissimo. Se in futuro volessi un follow-up con memoria del
turno precedente, andrebbe gestito lato Python accumulando i messaggi e
rimandandoli ad ogni chiamata — al momento `identify.py` non lo fa, per
restare semplice.

---

## Personalizzazione

Il comportamento dell'agente si modifica **solo nel portale Foundry** (campo
Instructions / Tools dell'agente), seguito da **Publish**. Il codice Python non
va più toccato per questo.

---

## Risoluzione problemi

| Sintomo | Causa probabile | Soluzione |
|---|---|---|
| `AuthenticationError` | `AZ_FOUNDRY_KEY` errata o mancante | Ricontrolla la key nel portale ("Keys and Endpoint") |
| `NotFoundError` (404) | `AZ_FOUNDRY_AGENT_APP_NAME` errato, o agente non pubblicato | Verifica il nome esatto usato in "Publish"; pubblica l'agente se non l'hai fatto |
| `BadRequestError` con menzione di OBO | Un tool dell'agente usa autenticazione On-Behalf-Of | Rimuovi/riconfigura quel tool nel portale, oppure passa a Entra ID per chiamare questo agente |
| `APIConnectionError` | `AZ_FOUNDRY_EP` errato | Verifica l'URL nel `.env` |
