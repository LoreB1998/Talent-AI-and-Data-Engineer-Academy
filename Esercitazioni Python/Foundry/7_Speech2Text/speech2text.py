import os
import threading
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()  # Carica le variabili d'ambiente da un file .env (se presente)

def _env_value(name: str) -> str | None:
    """
    Restituisce il valore di una variabile d'ambiente, o None se non definita.
    Se la variabile è definita ma vuota, restituisce None.
    Se la variabile contiene un commento (es. "valore # commento"), restituisce solo la parte prima del commento.
    """
    value = os.getenv(name)
    if value is None:
        return None
    return value.split("#", 1)[0].strip() or None


SPEECH_KEY = _env_value("AZ_SPEECH_KEY")  # La chiave API per Azure AI Speech (obbligatoria)
SPEECH_REGION = _env_value("AZ_SPEECH_REGION")  # La regione della risorsa Azure AI Speech (obbligatoria se non si usa un endpoint personalizzato)
SPEECH_ENDPOINT = _env_value("AZ_SPEECH_ENDPOINT")  # L'endpoint completo della risorsa Azure AI Speech (opzionale)

# Lingua di riconoscimento di default — cambiabile via .env se vuoi un'altra lingua
RECOGNITION_LANGUAGE = _env_value("AZ_SPEECH_RECOGNITION_LANGUAGE") or "it-IT"  # Codici lingua: https://learn.microsoft.com/azure/ai-services/speech-service/language-support?tabs=stt


def trascrivi_audio(audio_config: speechsdk.audio.AudioConfig, attesa_manuale: bool = False) -> str | None:
    """
    Invia audio (da file o da microfono) ad Azure AI Speech e restituisce il testo trascritto.
    Usa il riconoscimento continuo per gestire audio di qualsiasi durata.

    - audio_config: la sorgente audio già configurata (file o microfono)
    - attesa_manuale: se True, attende che l'utente prema INVIO per terminare
      (necessario per il microfono, che non ha una fine naturale dello stream).
      Se False, attende che lo stream finisca da solo (caso del file .wav).
    Restituisce la trascrizione come stringa, oppure None in caso di errore.
    """
    if not SPEECH_KEY or (not SPEECH_REGION and not SPEECH_ENDPOINT):
        print("Credenziali Azure Speech mancanti (AZ_SPEECH_KEY e AZ_SPEECH_REGION o AZ_SPEECH_ENDPOINT).")
        return None

    if SPEECH_ENDPOINT:  # Se è specificato un endpoint completo, usalo direttamente. Altrimenti, costruisci la configurazione usando chiave e regione.
        speech_config = speechsdk.SpeechConfig(
            subscription=SPEECH_KEY,
            endpoint=SPEECH_ENDPOINT
        )
    else:  # Configurazione standard con chiave e regione
        speech_config = speechsdk.SpeechConfig(
            subscription=SPEECH_KEY,
            region=SPEECH_REGION
        )
    speech_config.speech_recognition_language = RECOGNITION_LANGUAGE  # Imposta la lingua da riconoscere (es. "it-IT" per italiano, "en-US" per inglese, ecc.)

    recognizer = speechsdk.SpeechRecognizer(  # Crea un riconoscitore vocale usando la configurazione specificata
        speech_config=speech_config,
        audio_config=audio_config
    )

    trascrizione_completa = []
    errore_riscontrato = None
    evento_fine = threading.Event()  # Sostituisce il busy-loop: si "sveglia" solo quando la sessione termina

    def su_riconosciuto(evt):
        # Callback invocata ogni volta che viene riconosciuto un segmento di frase
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech and evt.result.text:
            trascrizione_completa.append(evt.result.text)

    def su_annullato(evt):
        nonlocal errore_riscontrato
        cancellation = evt.cancellation_details
        if cancellation.reason == speechsdk.CancellationReason.Error:
            errore_riscontrato = cancellation.error_details
        evento_fine.set()

    def su_fine_sessione(evt):
        evento_fine.set()

    recognizer.recognized.connect(su_riconosciuto)
    recognizer.canceled.connect(su_annullato)
    recognizer.session_stopped.connect(su_fine_sessione)

    print(f"Trascrizione in corso (lingua: {RECOGNITION_LANGUAGE})...")
    recognizer.start_continuous_recognition()

    if attesa_manuale:
        # Caso microfono: la registrazione continua finché l'utente non preme INVIO
        input("Registrazione dal microfono in corso... Premi INVIO per terminare.\n")
        recognizer.stop_continuous_recognition()
        evento_fine.wait(timeout=5)  # margine per lasciare processare gli ultimi eventi
    else:
        # Caso file: lo stream termina da solo a fine audio, attendiamo l'evento
        evento_fine.wait()
        recognizer.stop_continuous_recognition()

    if errore_riscontrato:
        print(f"Trascrizione annullata. Dettagli errore: {errore_riscontrato}")
        print("Verifica che la chiave appartenga alla risorsa Speech corretta e che regione/endpoint coincidano con quella risorsa.")
        return None

    if not trascrizione_completa:
        print("Nessun parlato riconosciuto.")
        return None

    return " ".join(trascrizione_completa)


def salva_testo(testo: str, percorso_output: str) -> None:
    """
    Salva il testo trascritto in un file .txt (UTF-8).
    """
    with open(percorso_output, "w", encoding="utf-8") as f:
        f.write(testo)


def scegli_sorgente_audio(base_dir: str) -> tuple[speechsdk.audio.AudioConfig, bool] | None:
    """
    Chiede all'utente se vuole usare il microfono o un file .wav,
    e restituisce la AudioConfig corrispondente insieme al flag attesa_manuale.
    Restituisce None se la scelta non è valida o il file non viene trovato.
    """
    print("Scegli la sorgente audio:")
    print("  [1] Microfono (registrazione in tempo reale)")
    print("  [2] File audio (.wav)")
    scelta = input("Selezione [1/2]: ").strip()

    if scelta == "1":
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        return audio_config, True

    elif scelta == "2":
        file_input = os.path.join(base_dir, "input_audio.wav")
        if not os.path.exists(file_input):
            print(f"File non trovato: {file_input}")
            print("Inserisci un file 'input_audio.wav' nella stessa cartella dello script con l'audio da trascrivere.")
            return None
        audio_config = speechsdk.audio.AudioConfig(filename=file_input)
        return audio_config, False

    else:
        print("Selezione non valida. Riprova scegliendo 1 o 2.")
        return None


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_output = os.path.join(base_dir, "testo_trascritto.txt")

    risultato_scelta = scegli_sorgente_audio(base_dir)
    if risultato_scelta is None:
        return

    audio_config, attesa_manuale = risultato_scelta

    testo = trascrivi_audio(audio_config, attesa_manuale=attesa_manuale)
    if testo is None:
        return

    print(f"Testo trascritto ({len(testo)} caratteri):")
    print(f"  {testo[:100]}{'...' if len(testo) > 100 else ''}")

    salva_testo(testo, file_output)
    print(f"Trascrizione salvata correttamente: {file_output}")


if __name__ == "__main__":
    main()