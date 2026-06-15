import os
import json
from dotenv import load_dotenv
from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential
from openai import OpenAI


# ---------------------------------------------------------------------------
# Configurazione
# ---------------------------------------------------------------------------

# Dizionario che mappa ogni chiave misura alla domanda corrispondente in italiano.
# Le domande verranno poi tradotte dinamicamente nella lingua dell'utente prima di essere poste.
QUESTIONS = {
    "neck":         "Qual è il diametro del collo (in cm)?",
    "collar_style": "Che tipo di colletto preferisci? (es. italiano, button-down, diplomatico)",
    "shoulders":    "Qual è la larghezza delle spalle (in cm)?",
    "sleeves":      "Qual è la lunghezza delle maniche (in cm)?",
    "length":       "Qual è la lunghezza della camicia (in cm)?",
}

# System prompt che definisce la "personalità" e le regole di comportamento del modello LLM.
# Viene iniettato come primo messaggio con ruolo "system" in ogni conversazione.
TAILOR_SYSTEM_PROMPT = """
Sei un sarto esperto e cordiale. Parli in modo naturale e diretto, come faresti con un cliente in negozio.
Riceverai i dettagli per confezionare una camicia, divisi tra preferenze di stile e misure fisiche (in cm).

Il tuo compito è:
1. Verificare che le misure numeriche rientrino nei range di plausibilità.
2. Verificare la coerenza geometrica tra i parametri.
3. Segnalare eventuali problemi e chiedere chiarimenti o correzioni.
4. Quando TUTTE le misure sono valide e l'utente ha confermato, invocare la funzione 'conferma_ordine'.

GLOSSARIO MISURE
- Collo: circonferenza del collo in cm
- Spalle: larghezza piatta spalla-spalla in cm (NON circonferenza)
- Maniche: lunghezza dal punto spalla al polso in cm (NON circonferenza)
- Lunghezza: lunghezza verticale della camicia in cm

RANGE DI PLAUSIBILITÀ (adulti)
Se un valore è fuori range, rifiutalo e chiedi all'utente di reinserirlo.
Non accettare mai valori fuori da questi limiti, nemmeno se l'utente insiste.
- Collo:     35-48 cm
- Spalle:    38-56 cm
- Maniche:   55-72 cm
- Lunghezza: 65-90 cm

COERENZA TRA PARAMETRI
Verifica nell'ordine. Se una relazione non è rispettata, segnala il problema
e chiedi quale delle due misure è errata prima di procedere.
- spalle - collo deve essere tra 2 e 10 cm
- maniche - spalle deve essere tra 10 e 20 cm

SEGNALE DI CONFUSIONE LINEARE/CIRCONFERENZA
Se spalle > 70 cm oppure maniche > 80 cm, l'utente sta probabilmente
inserendo una circonferenza al posto di una misura lineare.
In quel caso spiega la differenza e chiedi di rimisurare.

Passa alla funzione i valori definitivi emersi ALLA FINE della conversazione (possono differire da quelli iniziali).
Non simulare la chiamata nei messaggi di testo: usa lo strumento apposito.
Niente elenchi, niente grassetti, niente emoji. Solo conversazione normale.
Rispondi sempre nella lingua dell'utente.
"""

# Definizione dello strumento (tool) che l'LLM può invocare tramite tool calling.
# Segue il formato OpenAI: "type": "function" con nome, descrizione e schema JSON dei parametri.
# L'LLM chiamerà questa funzione solo quando tutte le misure sono validate e l'utente ha confermato.
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "conferma_ordine",
        "description": "Conferma definitivamente l'ordine con le misure finali e corrette.",
        "parameters": {
            "type": "object",
            "properties": {
                # Ogni proprietà descrive un parametro atteso: tipo e descrizione guidano l'LLM
                # su quali valori inserire quando invoca la funzione.
                "neck":         {"type": "string", "description": "Misura finale del collo in cm"},
                "collar_style": {"type": "string", "description": "Stile del colletto scelto"},
                "shoulders":    {"type": "string", "description": "Misura finale delle spalle in cm"},
                "sleeves":      {"type": "string", "description": "Misura finale delle maniche in cm"},
                "length":       {"type": "string", "description": "Misura finale della lunghezza in cm"},
            },
            # "required" elenca i parametri obbligatori: l'LLM non può invocare la funzione
            # senza averli tutti valorizzati.
            "required": ["neck", "collar_style", "shoulders", "sleeves", "length"],
        },
    },
}


# ---------------------------------------------------------------------------
# Translator
# ---------------------------------------------------------------------------

def get_translator_client(api_key: str, endpoint: str, region: str) -> TextTranslationClient:
    """
    Crea e restituisce un client autenticato per Azure Cognitive Services Translator.

    Args:
        api_key:  Chiave di sottoscrizione Azure per il servizio Translator.
        endpoint: URL base del servizio (es. "https://api.cognitive.microsofttranslator.com").
        region:   Regione Azure associata alla risorsa (es. "westeurope").

    Returns:
        Un'istanza di TextTranslationClient pronta all'uso.
    """
    return TextTranslationClient(
        endpoint=endpoint,
        # AzureKeyCredential è il wrapper standard per autenticarsi con una chiave API
        # nei servizi Azure Cognitive; astrae la gestione dell'header "Ocp-Apim-Subscription-Key".
        credential=AzureKeyCredential(api_key),
        region=region,
    )


def detect_language(client: TextTranslationClient, text: str) -> str:
    """
    Rileva automaticamente la lingua di un testo sfruttando l'API Translator.

    Invece di chiamare un endpoint di rilevamento dedicato, si esegue una traduzione
    verso l'inglese: il servizio restituisce in risposta anche la lingua sorgente
    rilevata, evitando così una chiamata API separata.

    Args:
        client: Client Azure Translator già autenticato.
        text:   Testo di cui rilevare la lingua.

    Returns:
        Codice ISO 639-1 della lingua rilevata (es. "it", "en", "fr").
    """
    # La chiamata traduce il testo verso "en"; ci interessa però solo il campo
    # detected_language della risposta, non la traduzione in sé.
    result = client.translate(body=[text], to_language=["en"])
    # result è una lista (una voce per ogni testo inviato); prendiamo il primo elemento
    # e accediamo al codice lingua del campo detected_language.
    return result[0].detected_language.language  # type: ignore


def translate_texts(client: TextTranslationClient, texts: list[str], target_language: str) -> list[str]:
    """
    Traduce una lista di stringhe verso la lingua indicata con una singola chiamata API.

    Raggruppare più testi in un'unica richiesta è più efficiente rispetto a chiamate
    separate, poiché riduce la latenza di rete e il numero di round-trip verso il servizio.

    Args:
        client:          Client Azure Translator già autenticato.
        texts:           Lista di stringhe da tradurre.
        target_language: Codice ISO 639-1 della lingua di destinazione (es. "fr", "de").

    Returns:
        Lista di stringhe tradotte, nello stesso ordine dell'input.
    """
    # body accetta una lista di testi; to_language è una lista perché il servizio
    # supporta anche traduzioni multi-target simultanee (qui ne usiamo solo uno).
    result = client.translate(body=texts, to_language=[target_language])
    # Ogni elemento di result corrisponde a un testo inviato; .translations è una lista
    # di traduzioni (una per ogni lingua target), da cui estraiamo solo il testo (.text).
    return [item.translations[0].text for item in result]


# ---------------------------------------------------------------------------
# Raccolta misure
# ---------------------------------------------------------------------------

def collect_measurements(translator: TextTranslationClient, user_language: str) -> dict:
    """
    Traduce le domande in batch nella lingua dell'utente, le pone in sequenza
    e raccoglie le risposte in un dizionario strutturato.

    Usare una singola chiamata batch al Translator (anziché una per domanda)
    è più efficiente e riduce i costi API.

    Args:
        translator:     Client Azure Translator già autenticato.
        user_language:  Codice ISO 639-1 della lingua in cui porre le domande.

    Returns:
        Dizionario {chiave_misura: risposta_utente} con le misure inserite.
    """
    # Separiamo chiavi e testi in due liste parallele per poterle riassociare dopo
    # la traduzione (translate_texts restituisce solo i testi, non le chiavi).
    keys = list(QUESTIONS.keys())
    questions_it = list(QUESTIONS.values())

    # Traduzione batch: una sola chiamata per tutte le domande invece di N chiamate.
    translated_questions = translate_texts(translator, questions_it, user_language)

    measurements = {}
    # zip accoppia ogni chiave alla corrispondente domanda tradotta, mantenendo l'ordine.
    for key, question in zip(keys, translated_questions):
        answer = input(f"{question} ").strip()
        measurements[key] = answer

    return measurements


# ---------------------------------------------------------------------------
# Validazione LLM con Tool Calling
# ---------------------------------------------------------------------------

def get_openai_client(api_key: str, endpoint: str) -> OpenAI:
    """
    Crea e restituisce un client OpenAI puntato su Azure OpenAI Service.

    Il client OpenAI standard supporta Azure tramite il parametro base_url:
    passando l'endpoint Azure, tutte le chiamate vengono indirizzate al deployment
    configurato su Azure anziché all'API pubblica di OpenAI.

    Args:
        api_key:  Chiave API del deployment Azure OpenAI.
        endpoint: URL base del deployment Azure (include già il path del modello).

    Returns:
        Un'istanza di OpenAI configurata per Azure OpenAI Service.
    """
    return OpenAI(api_key=api_key, base_url=endpoint)


def validate_measurements(
    openai_client: OpenAI,
    deployment_name: str,
    measurements: dict,
    first_input: str,
    user_language: str,
) -> None:
    """
    Avvia e gestisce il dialogo tra l'utente e il sarto LLM fino alla conferma dell'ordine.

    Il flusso si basa su tool calling: l'LLM può invocare 'conferma_ordine' quando
    ritiene le misure valide e l'utente ha confermato. La conversazione continua
    in un loop sincrono finché il tool non viene chiamato o l'utente non invia input vuoto.

    La history viene mantenuta lato client e inviata integralmente a ogni turno,
    poiché i modelli LLM sono stateless (non ricordano i turni precedenti da soli).

    Args:
        openai_client:   Client OpenAI/Azure OpenAI già configurato.
        deployment_name: Nome del deployment Azure (o model ID per OpenAI standard).
        measurements:    Dizionario delle misure raccolte dall'utente.
        first_input:     Prima stringa digitata dall'utente (usata come messaggio iniziale).
        user_language:   Codice ISO 639-1 della lingua dell'utente, passato al sarto
                         per garantire risposte nella lingua corretta.
    """
    # Costruisce un riepilogo testuale delle misure da passare all'LLM come contesto iniziale.
    measurements_text = "\n".join(f"- {k}: {v}" for k, v in measurements.items())

    # Messaggio "finto" dell'assistente che introduce le misure raccolte nella conversazione.
    # Questo trucco evita di inserire le misure nel system prompt (che è fisso) e permette
    # di trattarle come parte naturale del dialogo.
    # IMPORTANTE: scritto in inglese (lingua neutra) per non condizionare il modello
    # a rispondere in italiano indipendentemente dalla lingua rilevata. I modelli tendono
    # a imitare la lingua del turno "assistant" precedente, che era la causa del bug.
    first_assistant_prompt = (
        f"Here are the measurements provided by the user:\n{measurements_text}\n\n"
        f"The user's language code is: {user_language}. Always reply in that language."
    )

    # History iniziale con tre ruoli: system (istruzioni), user (primo input reale),
    # assistant (riepilogo misure). I modelli LLM si aspettano questo formato a turni alternati.
    history = [
        {"role": "system",    "content": TAILOR_SYSTEM_PROMPT},
        {"role": "user",      "content": first_input},
        {"role": "assistant", "content": first_assistant_prompt},
    ]

    print()

    while True:
        response = openai_client.chat.completions.create(
            model=deployment_name,
            messages=history,          # type: ignore — tutta la history viene inviata ogni turno
            tools=[TOOL_DEFINITION],   # type: ignore — lista degli strumenti disponibili per l'LLM
            tool_choice="auto",        # "auto": l'LLM decide autonomamente se e quando invocare un tool
        )

        # Estrae il messaggio generato dall'assistente dalla prima (e unica) scelta restituita.
        assistant_message = response.choices[0].message

        # Aggiunge il messaggio dell'assistente alla history PRIMA di qualsiasi controllo:
        # è obbligatorio farlo anche quando contiene tool_calls, perché la history deve
        # includere l'invocazione del tool prima del relativo tool_result.
        history.append(assistant_message)  # type: ignore

        # --- Caso 1: l'LLM ha deciso di invocare un tool ---
        if assistant_message.tool_calls:
            # Prendiamo il primo tool call (in questo progetto ne è previsto al massimo uno).
            tool_call = assistant_message.tool_calls[0]

            if tool_call.function.name == "conferma_ordine":  # type: ignore
                # Gli argomenti della funzione arrivano come stringa JSON; li deserializziamo
                # in un dizionario Python per poterli stampare a schermo.
                final_data = json.loads(tool_call.function.arguments)  # type: ignore

                # Il tool_result deve essere aggiunto alla history con ruolo "tool" e
                # l'ID del tool_call a cui risponde: è un requisito del protocollo OpenAI
                # per mantenere la history valida (anche se qui il loop termina subito dopo).
                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps({"status": "ok"}),
                })

                # Alcuni modelli includono anche un messaggio testuale insieme al tool_call;
                # se presente, lo stampiamo prima del riepilogo finale.
                if assistant_message.content:
                    print(f"Sarto: {assistant_message.content}\n")

                # Stampa il riepilogo finale dell'ordine confermato ed esce dal loop.
                print("=" * 40)
                print("  ORDINE CONFERMATO")
                print("=" * 40)
                for k, v in final_data.items():
                    print(f"  {k:<14}: {v}")
                print("=" * 40)
                break  # Ordine confermato: termina il loop di dialogo

        # --- Caso 2: l'LLM sta ancora dialogando (nessun tool call) ---
        if assistant_message.content:
            print(f"Sarto: {assistant_message.content}\n")

        user_reply = input("Tu: ").strip()
        if not user_reply:
            # Input vuoto: l'utente non vuole continuare, usciamo senza conferma.
            print("(Nessun input ricevuto, uscita.)")
            break

        # Aggiunge la risposta dell'utente alla history per il prossimo turno.
        history.append({"role": "user", "content": user_reply})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """
    Entry point dell'applicazione.

    Carica le variabili d'ambiente dal file .env, inizializza i client Azure,
    rileva la lingua dell'utente, raccoglie le misure e avvia la validazione LLM.
    """
    # Carica le variabili definite nel file .env nella memoria di processo,
    # rendendole accessibili tramite os.getenv().
    load_dotenv()

    # Legge le credenziali per Azure Translator dall'ambiente.
    translator_key      = os.getenv("AZ_TRANSLATOR_KEY")
    translator_endpoint = os.getenv("AZ_TRANSLATOR_ENDPOINT")
    translator_region   = os.getenv("AZ_TRANSLATOR_REGION")

    # Legge le credenziali per Azure OpenAI dall'ambiente.
    openai_key        = os.getenv("AZ_OPENAI_KEY")
    openai_endpoint   = os.getenv("AZ_OPENAI_ENDPOINT")
    openai_deployment = os.getenv("AZ_OPENAI_DEPLOYMENT")

    # Validazione anticipata: meglio sollevare un errore esplicito qui piuttosto che
    # ricevere un errore criptico dall'SDK quando si tenta di usare una credenziale None.
    if not all([translator_key, translator_endpoint, translator_region]):
        raise ValueError("Mancano le credenziali Azure Translator nel file .env")
    if not all([openai_key, openai_endpoint, openai_deployment]):
        raise ValueError("Mancano le credenziali Azure OpenAI nel file .env")

    # Inizializza i due client una sola volta; vengono poi passati alle funzioni
    # che ne hanno bisogno, evitando di ricrearli a ogni chiamata (costoso e inutile).
    translator    = get_translator_client(translator_key, translator_endpoint, translator_region)  # type: ignore
    openai_client = get_openai_client(openai_key, openai_endpoint)  # type: ignore

    print("=== Shirt Order Assistant ===\n")

    # Il primo input serve a due scopi: rilevare la lingua e aprire la conversazione
    # con un messaggio reale dell'utente (non viene scartato, entra nella history).
    first_input   = input("Scrivi qualcosa per iniziare (in qualsiasi lingua): ").strip()
    user_language = detect_language(translator, first_input)
    print(f"  [Lingua rilevata: {user_language}]\n")

    # Raccoglie le misure in modo interattivo nella lingua dell'utente.
    measurements = collect_measurements(translator, user_language)

    # Avvia la sessione di validazione con l'LLM e attende la conferma o l'uscita.
    validate_measurements(openai_client, openai_deployment, measurements, first_input, user_language)  # type: ignore


if __name__ == "__main__":
    main()