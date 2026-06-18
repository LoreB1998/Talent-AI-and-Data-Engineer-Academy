import os
import threading
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()

def _env_value(name: str) -> str | None:
    """Estrae il valore della variabile d'ambiente rimuovendo eventuali commenti."""
    value = os.getenv(name)
    if value is None:
        return None
    return value.split("#", 1)[0].strip() or None


class AssistenteVocale:
    """Classe per gestire input/output vocale usando Azure Speech."""
    
    def __init__(self):
        speech_key = _env_value("AZ_SPEECH_KEY")
        speech_region = _env_value("AZ_SPEECH_REGION")
        speech_endpoint = _env_value("AZ_SPEECH_ENDPOINT")
        speech_voice = _env_value("AZ_SPEECH_VOICE")
        recognition_lang = _env_value("AZ_SPEECH_RECOGNITION_LANGUAGE") or "it-IT"

        if not speech_key or (not speech_region and not speech_endpoint):
            raise ValueError("Credenziali Azure Speech mancanti o incomplete nel file .env.")

        # Gestione flessibile Endpoint / Region
        if speech_endpoint:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=speech_key, endpoint=speech_endpoint
            )
        else:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=speech_key, region=speech_region
            )

        self.speech_config.speech_recognition_language = recognition_lang
        
        if speech_voice:
            self.speech_config.speech_synthesis_voice_name = speech_voice

    def ascolta(self, attesa_manuale: bool = False, timeout_secondi: int = 8) -> str | None:
        """Registra dal microfono e restituisce il testo riconosciuto.

        Usa il riconoscimento continuo per ridurre i problemi del riconoscimento one-shot.
        - attesa_manuale=True: termina quando l'utente preme INVIO.
        - attesa_manuale=False: attende fino a timeout o fino a fine sessione.
        """
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config, audio_config=audio_config
        )

        trascrizione_completa = []
        errore_riscontrato = None
        evento_fine = threading.Event()

        def su_riconosciuto(evt):
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

        print("Ascoltando...")
        recognizer.start_continuous_recognition()

        if attesa_manuale:
            input("Registrazione dal microfono in corso... Premi INVIO per terminare.\n")
            recognizer.stop_continuous_recognition()
            evento_fine.wait(timeout=5)
        else:
            evento_fine.wait(timeout=max(1, timeout_secondi))
            recognizer.stop_continuous_recognition()

        if errore_riscontrato:
            print(f"Trascrizione annullata. Dettagli errore: {errore_riscontrato}")
            return None

        if not trascrizione_completa:
            print("Non ho capito. Riprova.")
            return None

        return " ".join(trascrizione_completa)
        
    def parla(self, testo: str) -> None:
        """Sintetizza vocalmente la risposta testuale."""
        if not testo:
            return
            
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=audio_config
        )
        synthesizer.speak_text_async(testo).get()