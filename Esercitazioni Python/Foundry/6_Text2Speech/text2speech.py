import os
import platform
import subprocess
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
SPEECH_ENDPOINT = _env_value("AZ_SPEECH_ENDPOINT")  # L'endpoint completo della risorsa Azure AI Speech (opzionale, se si preferisce specificare direttamente l'endpoint invece di regione+chiave)

# Voce neurale italiana di default — cambiabile via .env se vuoi un'altra lingua/voce
VOICE_NAME = _env_value("AZ_SPEECH_VOICE") or "it-IT-IsabellaNeural"  # Puoi trovare i nomi delle voci disponibili qui: https://learn.microsoft.com/azure/cognitive-services/speech-service/language-support#text-to-speech


def leggi_testo(percorso_file: str) -> str:
    """
    Legge il contenuto di un file di testo e lo restituisce come stringa.
     - percorso_file: il percorso del file di testo da leggere
     - restituisce: il testo letto dal file, con eventuali spazi bianchi iniziali e finali rimossi
     - solleva un'eccezione se il file non esiste o non è leggibile
     - il file deve essere codificato in UTF-8 per supportare correttamente i caratteri speciali e le lingue diverse dall'inglese
    """
    with open(percorso_file, "r", encoding="utf-8") as f:
        return f.read().strip()


def leggi_testo_da_input() -> str:
    """
    Chiede all'utente di digitare il testo direttamente da tastiera.
    Supporta testo su più righe: termina l'inserimento con una riga vuota
    (premi semplicemente INVIO su una riga senza scrivere nulla).
    """
    print("Digita il testo da sintetizzare (premi INVIO su una riga vuota per terminare):")
    righe = []
    while True:
        riga = input()
        if riga == "":
            break
        righe.append(riga)
    return "\n".join(righe).strip()


def sintetizza_audio(testo: str, percorso_output: str) -> bool:
    """
    Invia il testo ad Azure AI Speech e salva il risultato come file audio (.wav).
    Restituisce True se la sintesi è andata a buon fine, False altrimenti.
    """
    if not SPEECH_KEY or (not SPEECH_REGION and not SPEECH_ENDPOINT):
        print("Credenziali Azure Speech mancanti (AZ_SPEECH_KEY e AZ_SPEECH_REGION o AZ_SPEECH_ENDPOINT).")
        return False

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
    speech_config.speech_synthesis_voice_name = VOICE_NAME  # Imposta la voce da usare per la sintesi (es. "it-IT-IsabellaNeural" per italiano, "en-US-JennyNeural" per inglese, ecc.)

    audio_config = speechsdk.audio.AudioOutputConfig(filename=percorso_output)  # Configura l'output audio per salvare su file

    synthesizer = speechsdk.SpeechSynthesizer(  # Crea un sintetizzatore di testo in voce usando la configurazione specificata
        speech_config=speech_config,
        audio_config=audio_config
    )

    print(f"Sintesi in corso (voce: {VOICE_NAME})...")
    risultato = synthesizer.speak_text_async(testo).get()

    if risultato is None:
        print("Sintesi fallita: nessun risultato restituito dal servizio.")
        return False

    if risultato.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"Audio generato correttamente: {percorso_output}")
        return True

    elif risultato.reason == speechsdk.ResultReason.Canceled:
        cancellation = risultato.cancellation_details
        print(f"Sintesi annullata: {cancellation.reason}")
        if cancellation.reason == speechsdk.CancellationReason.Error:
            print(f"Dettagli errore: {cancellation.error_details}")
            print("Verifica che la chiave appartenga alla risorsa Speech corretta e che regione/endpoint coincidano con quella risorsa.")
        return False

    else:
        print(f"Esito inatteso: {risultato.reason}")
        return False


def riproduci_audio(percorso_file: str) -> None:
    """
    Riproduce un file audio usando il player da riga di comando del sistema operativo.
    - macOS: usa 'afplay', incluso di default, nessuna dipendenza aggiuntiva richiesta.
    - Windows / Linux: tentativi alternativi (winsound / aplay), con avviso se non disponibili.
    """
    sistema = platform.system()

    try:
        if sistema == "Darwin":  # macOS
            subprocess.run(["afplay", percorso_file], check=True)
        elif sistema == "Windows":
            import winsound
            winsound.PlaySound(percorso_file, winsound.SND_FILENAME) # type: ignore
        elif sistema == "Linux":
            subprocess.run(["aplay", percorso_file], check=True)  # richiede alsa-utils
        else:
            print(f"Riproduzione automatica non supportata su questo sistema ({sistema}).")
    except FileNotFoundError:
        print("Player audio di sistema non trovato. Apri il file manualmente per ascoltarlo.")
    except subprocess.CalledProcessError as e:
        print(f"Errore durante la riproduzione: {e}")


def scegli_sorgente_testo(base_dir: str) -> str | None:
    """
    Chiede all'utente se vuole leggere il testo da un file .txt o digitarlo da tastiera,
    e restituisce il testo corrispondente.
    Restituisce None se la scelta non è valida, il file non viene trovato, o il testo è vuoto.
    """
    print("Scegli la sorgente del testo:")
    print("  [1] File di testo (.txt)")
    print("  [2] Testo digitato da tastiera")
    scelta = input("Selezione [1/2]: ").strip()

    if scelta == "1":
        file_input = os.path.join(base_dir, "testo_da_leggere.txt")
        if not os.path.exists(file_input):
            print(f"File non trovato: {file_input}")
            print("Crea un file 'testo_da_leggere.txt' nella stessa cartella dello script con il testo da convertire.")
            return None
        testo = leggi_testo(file_input)

    elif scelta == "2":
        testo = leggi_testo_da_input()

    else:
        print("Selezione non valida. Riprova scegliendo 1 o 2.")
        return None

    if not testo:
        print("Il testo è vuoto.")
        return None

    return testo


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_output = os.path.join(base_dir, "output_audio.wav")

    testo = scegli_sorgente_testo(base_dir)
    if testo is None:
        return

    print(f"Testo da sintetizzare ({len(testo)} caratteri):")
    print(f"  {testo[:100]}{'...' if len(testo) > 100 else ''}")

    successo = sintetizza_audio(testo, file_output)

    if successo:
        risposta = input("Vuoi ascoltare l'audio generato? [s/n]: ").strip().lower()
        if risposta == "s":
            riproduci_audio(file_output)


if __name__ == "__main__":
    main()