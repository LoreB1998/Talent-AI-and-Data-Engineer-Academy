# Importazione delle librerie standard di Python
import os               # Per interagire con il sistema operativo (es. leggere variabili d'ambiente)
import json             # Per serializzare e deserializzare i dati in formato JSON
import urllib.request   # Per effettuare richieste HTTP dirette (approccio REST)
import urllib.error     # Per gestire le eccezioni relative alle richieste HTTP

# Importazione di librerie di terze parti
from dotenv import load_dotenv # Per caricare le variabili d'ambiente da un file .env locale

# Importazione dei moduli dell'SDK di Azure per gestire l'autenticazione e i vari servizi AI
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.translation.text import TextTranslationClient
from openai import AzureOpenAI


def detect_language_rest(endpoint: str, key: str, text: str) -> None:
    """Rileva la lingua del testo tramite chiamata REST a Text Analytics."""

    # 1. Costruzione del payload: le API di Azure si aspettano un JSON con una lista di "documents".
    # Ogni documento deve avere un ID univoco e il testo da analizzare.
    payload = {
        "documents": [
            {"id": "1", "text": text}
        ]
    }

    # 2. Configurazione degli Header HTTP:
    # Ocp-Apim-Subscription-Key è l'header standard di Azure per passare la chiave API in modo sicuro.
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "application/json"
    }

    # 3. Composizione dell'URL: concatena l'endpoint base con il path specifico per l'API della lingua (v3.1).
    target_url = endpoint + "/text/analytics/v3.1/languages"

    # 4. Preparazione della richiesta: il dizionario Python viene convertito in una stringa JSON
    # e poi codificato in bytes (UTF-8), che è il formato richiesto per il body della richiesta HTTP.
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(target_url, body, headers)

    try:
        # 5. Esecuzione della richiesta e lettura della risposta.
        response = urllib.request.urlopen(request)
        # La risposta viene decodificata da bytes a stringa e poi parsata in un dizionario Python.
        result = json.loads(response.read().decode("utf-8"))

        # 6. Estrazione dei dati: itera sui documenti restituiti (in questo caso solo uno)
        # per estrarre e stampare il nome della lingua, il codice ISO e il livello di confidenza.
        for doc in result["documents"]:
            lang = doc["detectedLanguage"]
            print(f"[REST] Lingua rilevata: {lang['name']} "
                  f"(codice: {lang['iso6391Name']}, "
                  f"confidenza: {lang['confidenceScore']:.2f})")

    # Gestione specifica degli errori HTTP (es. 401 Unauthorized, 404 Not Found)
    except urllib.error.HTTPError as e:
        print(f"Errore HTTP {e.code}: {e.reason}")


def detect_language_sdk(client: TextAnalyticsClient, text: str) -> None:
    """Rileva la lingua del testo tramite SDK Azure Text Analytics."""

    # 1. Chiamata tramite SDK: rispetto all'approccio REST, l'SDK astrae la creazione del JSON,
    # la gestione degli header e l'invio della richiesta HTTP. Passiamo semplicemente una lista di testi.
    result = client.detect_language(documents=[text])

    # 2. Gestione della risposta: l'SDK restituisce oggetti Python strutturati anziché un JSON grezzo.
    for doc in result:
        if not doc.is_error:
            # Se l'analisi è andata a buon fine, si accede direttamente agli attributi dell'oggetto.
            lang = doc.primary_language
            print(f"[SDK] Lingua rilevata: {lang.name} "
                  f"(codice: {lang.iso6391_name}, "
                  f"confidenza: {lang.confidence_score:.2f})")
        else:
            # Gestione degli errori interna all'SDK
            print(f"Errore: {doc.error}") # type: ignore


# Le funzioni seguenti sono al momento stub (segnaposto) vuoti preparati per implementazioni future.
# Il 'pass' indica a Python di non fare nulla e procedere.

def check_content_safety(client: ContentSafetyClient, text: str) -> None:
    """Analizza il testo per contenuti inappropriati o dannosi."""
    pass


def analyze_document(client: DocumentIntelligenceClient, document_url: str) -> None:
    """Estrae testo e struttura da un documento (PDF, immagine, ecc.)."""
    pass


def translate_text(client: TextTranslationClient, text: str, target_language: str) -> None:
    """Traduce il testo nella lingua di destinazione specificata."""
    pass


def ask_openai(client: AzureOpenAI, prompt: str) -> None:
    """Invia un prompt al modello Azure OpenAI e stampa la risposta."""
    pass


def main():
    # 1. Caricamento configurazione: cerca un file '.env' nella directory corrente e ne carica
    # il contenuto nel dizionario os.environ, rendendo le variabili accessibili tramite os.getenv.
    load_dotenv()

    # Recupero delle credenziali di Azure.
    endpoint = os.getenv("AZURE_ENDPOINT")
    key = os.getenv("AZURE_KEY")
    
    # Controllo di sicurezza: se endpoint o key sono vuoti/None, il programma si blocca
    # restituendo il messaggio di errore specificato, evitando crash successivi più difficili da debuggare.
    assert endpoint and key, "Mancano le variabili AZURE_ENDPOINT o AZURE_KEY nel .env"

    # 2. Inizializzazione dei client Azure AI SDK.
    # Ogni client gestisce la connessione a un servizio specifico di Azure,
    # utilizzando l'endpoint e un oggetto AzureKeyCredential costruito con la chiave.
    text_client = TextAnalyticsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )
    safety_client = ContentSafetyClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )
    doc_client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )
    # TextTranslationClient utilizza solo la credenziale (e opzionalmente una regione), l'endpoint è spesso standard.
    translation_client = TextTranslationClient(
        credential=AzureKeyCredential(key)
    )
    # L'inizializzazione di OpenAI richiede parametri leggermente diversi per definire la versione dell'API.
    openai_client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=key,
        api_version="2024-02-01"
    )

    # 3. Loop interattivo: mantiene il programma in esecuzione permettendo all'utente
    # di testare più input consecutivamente senza dover riavviare lo script.
    user_text = ""
    while user_text.lower() != "quit":
        # Attende l'input dall'utente dal terminale.
        user_text = input("Inserisci un testo da analizzare (o 'quit' per uscire): ")
        
        # Verifica se l'utente vuole uscire prima di eseguire le API.
        if user_text.lower() != "quit":
            # Esegue e stampa il risultato usando il metodo raw HTTP/REST
            detect_language_rest(endpoint, key, user_text)
            # Esegue e stampa il risultato usando il metodo semplificato dell'SDK
            detect_language_sdk(text_client, user_text)
        else:
            print("Uscita dal programma.")


# Punto di ingresso standard degli script Python.
# Assicura che la funzione main() venga eseguita solo se il file è lanciato direttamente,
# e non se viene importato come modulo in un altro script.
if __name__ == "__main__":
    main()