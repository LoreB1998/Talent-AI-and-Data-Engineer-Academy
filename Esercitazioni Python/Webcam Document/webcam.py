import os
import json
import time
import base64
import threading
from pathlib import Path

from dotenv import load_dotenv
import cv2
import azure.cognitiveservices.speech as speechsdk
from azure.core.credentials import AzureKeyCredential
from azure.ai.vision.face import FaceClient
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from openai import OpenAI


PAROLE_ATTIVAZIONE = ("attiva", "apri", "accendi", "webcam", "telecamera", "via", "start")

PAROLE_DOCUMENTO = ("card", "credit", "identity", "id card", "document",
                    "passport", "license", "driver", "paper", "badge")

INTERVALLO_ANALISI = 2.0
INTERVALLO_DOCUMENTO = 5.0
MAX_INTERVALLO_DOCUMENTO = 30.0
TENTATIVI_PER_AVVISO_VOCALE = 3

CARTELLA_SALVATAGGI = Path(__file__).resolve().parent / "documenti_letti"

BLU = (255, 0, 0)
VERDE = (0, 200, 0)
ARANCIO = (0, 165, 255)
GRIGIO = (180, 180, 180)

PROMPT_DOCUMENTO = """
    Sei un sistema OCR specializzato in documenti d'identità.
    Analizza l'immagine e restituisci SOLO un oggetto JSON (nessun testo aggiuntivo, nessun markdown) con i campi del documento.
    Usa sempre questi nomi di chiave in Inglese:
    FirstName, LastName, DocumentNumber, DateOfBirth, DateOfExpiry, Nationality, Sex, Address
    Includi solo i campi effettivamente leggibili nell'immagine. Se un campo non è visibile o leggibile, omettilo.
    Se nell'immagine non vedi nessun documento d'identità valido, restituisci: {"error": "nessun documento rilevato"}
    """

stato = {
    "nome": None,
    "cognome": None,
    "doc_letto": False,
    "lettura_in_corso": False,
    "salvato": False,
    "messaggio": "Mostra il documento alla webcam",
    "tentativi_falliti": 0,
}
lock = threading.Lock()

analisi_stato = {
    "volti": [],
    "documento": (None, None),
    "analisi_in_corso": False,
}
analisi_lock = threading.Lock()


def _val(oggetto, *nomi, default=None):
    for nome in nomi:
        valore = getattr(oggetto, nome, None)
        if valore is not None:
            return valore
        try:
            if oggetto[nome] is not None:
                return oggetto[nome]
        except (TypeError, KeyError, IndexError):
            pass
    return default


def configura():
    load_dotenv(Path(__file__).resolve().parent / ".env")

    endpoint = os.getenv("AZ_ENDPOINT")
    key = os.getenv("AZ_KEY")
    if not endpoint or not key:
        raise SystemExit("Mancano AZ_ENDPOINT / AZ_KEY nel .env.")

    credenziale = AzureKeyCredential(key)
    face_client = FaceClient(endpoint=endpoint, credential=credenziale)
    image_client = ImageAnalysisClient(endpoint=endpoint, credential=credenziale)

    az_openai_key = os.getenv("AZ_OPENAI_KEY")
    az_openai_endpoint = os.getenv("AZ_OPENAI_ENDPOINT")
    az_openai_deployment = os.getenv("AZ_OPENAI_DEPLOYMENT")
    az_openai_version = os.getenv("AZ_OPENAI_API_VERSION", "2024-02-01")
    if not az_openai_key or not az_openai_endpoint or not az_openai_deployment:
        raise SystemExit("Mancano AZ_OPENAI_KEY / AZ_OPENAI_ENDPOINT / AZ_OPENAI_DEPLOYMENT nel .env.")

    openai_client = OpenAI(
        api_key=az_openai_key,
        base_url=az_openai_endpoint,
    )

    speech_config = None
    speech_key = os.getenv("AZ_SPEECH_KEY")
    speech_region = os.getenv("AZ_SPEECH_REGION")
    if speech_key and speech_region:
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        speech_config.speech_recognition_language = os.getenv("AZ_SPEECH_LANGUAGE") or "it-IT"
        speech_config.speech_synthesis_voice_name = os.getenv("AZ_SPEECH_VOICE") or "it-IT-IsabellaNeural"

    return face_client, image_client, openai_client, az_openai_deployment, speech_config


def parla(speech_config, testo):
    if speech_config is None:
        return
    audio = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    sintetizzatore = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio)
    sintetizzatore.speak_text_async(testo).get()


def ascolta_attivazione(speech_config):
    if speech_config is None:
        input("Voce non configurata. Premi INVIO per attivare la webcam... ")
        return

    parla(speech_config, "Sono pronta. Di' attiva la webcam quando vuoi.")
    audio = speechsdk.audio.AudioConfig(use_default_microphone=True)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio)

    while True:
        print("In ascolto... (di' 'attiva la webcam')")
        risultato = recognizer.recognize_once_async().get()

        if risultato.reason == speechsdk.ResultReason.RecognizedSpeech: # type: ignore
            testo = risultato.text.lower() #type: ignore
            print(f"Ho sentito: {risultato.text}") #type: ignore
            if any(parola in testo for parola in PAROLE_ATTIVAZIONE):
                return
            print("Non ho colto il comando di attivazione, riprova.")
        elif risultato.reason == speechsdk.ResultReason.NoMatch: #type: ignore
            print("Non ho capito, riprova.")
        elif risultato.reason == speechsdk.ResultReason.Canceled: #type: ignore
            dettagli = risultato.cancellation_details #type: ignore
            print(f"Voce non disponibile ({dettagli.reason}). Attivo da tastiera.")
            input("Premi INVIO per attivare la webcam... ")
            return


def rileva_volti(face_client, immagine_jpg):
    volti = face_client.detect(
        image_content=immagine_jpg,
        detection_model="detection_03",
        recognition_model="recognition_04",
        return_face_id=False,
        return_face_landmarks=False,
        return_face_attributes=None,
    )
    riquadri = []
    for volto in volti:
        box = _val(volto, "face_rectangle", "faceRectangle", default={})
        x = _val(box, "left", "x", default=0)
        y = _val(box, "y", "top", default=0)
        w = _val(box, "width", "w", default=0)
        h = _val(box, "height", "h", default=0)
        riquadri.append((int(x), int(y), int(w), int(h)))
    return riquadri


def _parola_documento(testo):
    testo = (testo or "").lower()
    return any(parola in testo for parola in PAROLE_DOCUMENTO)


def rileva_documento(image_client, immagine_jpg):
    risultato = image_client.analyze(
        image_data=immagine_jpg,
        language="en",
        visual_features=[VisualFeatures.OBJECTS, VisualFeatures.TAGS, VisualFeatures.CAPTION],
    )

    oggetti = _val(risultato.objects, "list", "values", default=[]) if risultato.objects else []
    for oggetto in oggetti:
        tags = _val(oggetto, "tags", default=[]) or []
        nome = _val(tags[0], "name", default="") if tags else ""
        if _parola_documento(nome):
            box = _val(oggetto, "bounding_box", "boundingBox", default={})
            x = _val(box, "x", "left", default=0)
            y = _val(box, "y", "top", default=0)
            w = _val(box, "w", "width", default=0)
            h = _val(box, "h", "height", default=0)
            return nome, (int(x), int(y), int(w), int(h))

    tags = _val(risultato.tags, "list", "values", default=[]) if risultato.tags else []
    for tag in tags:
        nome = _val(tag, "name", default="")
        if _parola_documento(nome):
            return nome, None

    if risultato.caption and _parola_documento(_val(risultato.caption, "text", default="")):
        return _val(risultato.caption, "text"), None

    return None, None


def ritaglia(frame, box, margine=0.18):
    if not box:
        return frame
    h_img, w_img = frame.shape[:2]
    x, y, w, h = box
    mx, my = int(w * margine), int(h * margine)
    x0, y0 = max(0, x - mx), max(0, y - my)
    x1, y1 = min(w_img, x + w + mx), min(h_img, y + h + my)
    if x1 - x0 < 20 or y1 - y0 < 20:
        return frame
    return frame[y0:y1, x0:x1]


def leggi_id_gpt(openai_client, deployment, immagine_jpg):
    """Manda il ritaglio a GPT-4o come immagine base64 e restituisce
    (nome, cognome, tutti_i_campi) estratti dal JSON di risposta."""
    b64 = base64.b64encode(immagine_jpg).decode("utf-8")

    risposta = openai_client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "system",
                "content": "Sei un assistente esperto in estrazione di dati da immagini in formato JSON.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT_DOCUMENTO},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            },
        ],
        response_format={"type": "json_object"},
    )

    testo = (risposta.choices[0].message.content or "").strip()
    if not testo:
        raise ValueError("Il modello ha restituito una risposta vuota. "
                         "Verifica che il deployment supporti input visivi (es. gpt-4o).")

    dati = json.loads(testo)

    if "error" in dati:
        return None, None, {}

    nome = dati.get("FirstName")
    cognome = dati.get("LastName")
    return nome, cognome, dati


def salva_documento(crop_jpg, nome, cognome, tutti_i_campi):
    CARTELLA_SALVATAGGI.mkdir(exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    base = f"{timestamp}_{nome or 'sconosciuto'}_{cognome or 'sconosciuto'}".replace(" ", "_")

    percorso_jpg = CARTELLA_SALVATAGGI / f"{base}.jpg"
    percorso_json = CARTELLA_SALVATAGGI / f"{base}.json"

    percorso_jpg.write_bytes(crop_jpg)
    with open(percorso_json, "w", encoding="utf-8") as file_json:
        json.dump(tutti_i_campi, file_json, ensure_ascii=False, indent=2)

    return CARTELLA_SALVATAGGI / base


def worker_documento(openai_client, deployment, speech_config, crop_jpg):
    try:
        nome, cognome, tutti_i_campi = leggi_id_gpt(openai_client, deployment, crop_jpg)
    except Exception as errore:
        print(f"Lettura GPT non riuscita: {errore}")
        nome, cognome, tutti_i_campi = None, None, {}

    completo = bool(nome and cognome)
    parlare_fallimento = False
    tentativi_correnti = 0

    with lock:
        if nome:
            stato["nome"] = nome
        if cognome:
            stato["cognome"] = cognome
        stato["doc_letto"] = completo
        stato["lettura_in_corso"] = False

        if completo:
            stato["tentativi_falliti"] = 0
            stato["messaggio"] = "Documento letto"
        else:
            stato["tentativi_falliti"] += 1
            tentativi_correnti = stato["tentativi_falliti"]
            stato["messaggio"] = f"Documento non leggibile (tentativo {tentativi_correnti})"
            if tentativi_correnti % TENTATIVI_PER_AVVISO_VOCALE == 1:
                parlare_fallimento = True

    if completo:
        print(f"Documento: Nome={nome}  Cognome={cognome}")
        try:
            percorso = salva_documento(crop_jpg, nome, cognome, tutti_i_campi)
            with lock:
                stato["salvato"] = True
                stato["messaggio"] = "Documento letto e salvato"
            print(f"Dati e ritaglio salvati in: {percorso}.jpg / {percorso}.json")
        except Exception as errore:
            print(f"Salvataggio su disco non riuscito: {errore}")
        parla(speech_config, f"Documento letto. Benvenuto {nome} {cognome}.")
    else:
        print(f"Documento non leggibile (tentativo {tentativi_correnti}).")
        if parlare_fallimento:
            parla(speech_config, "Non riesco a leggere il documento. "
                                 "Avvicinalo alla webcam e tienilo bene a fuoco, per favore.")


def worker_analisi(face_client, image_client, immagine_jpg):
    volti = None
    documento = None
    try:
        volti = rileva_volti(face_client, immagine_jpg)
    except Exception as errore:
        print(f"Rilevamento volti non riuscito: {errore}")
    try:
        documento = rileva_documento(image_client, immagine_jpg)
    except Exception as errore:
        print(f"Rilevamento documento non riuscito: {errore}")

    with analisi_lock:
        if volti is not None:
            analisi_stato["volti"] = volti
        if documento is not None:
            analisi_stato["documento"] = documento
        analisi_stato["analisi_in_corso"] = False


def _banner(frame, testo, x, y_alto, colore):
    font = cv2.FONT_HERSHEY_SIMPLEX
    scala, spessore = 0.7, 2
    (tw, th), base = cv2.getTextSize(testo, font, scala, spessore)
    x = max(0, x)
    y_alto = max(0, y_alto)
    cv2.rectangle(frame, (x, y_alto), (x + tw + 12, y_alto + th + base + 10), colore, -1)
    cv2.putText(frame, testo, (x + 6, y_alto + th + 4), font, scala, (0, 0, 0), spessore, cv2.LINE_AA)


def pannello(frame, righe, colore):
    font = cv2.FONT_HERSHEY_SIMPLEX
    scala, spessore, h_riga = 0.6, 2, 28
    larghezza = max(cv2.getTextSize(t, font, scala, spessore)[0][0] for t in righe) + 20
    cv2.rectangle(frame, (10, 10), (10 + larghezza, 18 + h_riga * len(righe)), (0, 0, 0), -1)
    for i, testo in enumerate(righe):
        cv2.putText(frame, testo, (20, 38 + i * h_riga), font, scala, colore, spessore, cv2.LINE_AA)


def disegna(frame, volti, documento, snapshot):
    doc_letto = snapshot["doc_letto"]
    nome, cognome = snapshot["nome"], snapshot["cognome"]

    for (x, y, w, h) in volti:
        cv2.rectangle(frame, (x, y), (x + w, y + h), BLU, 2)
        if doc_letto:
            _banner(frame, f"{nome} {cognome}", x, y + h + 6, VERDE)

    _, box = documento
    if box:
        x, y, w, h = box
        cv2.rectangle(frame, (x, y), (x + w, y + h), ARANCIO, 2)

    colore = VERDE if doc_letto else ARANCIO
    if snapshot["lettura_in_corso"]:
        stato_riga = "Lettura documento in corso..."
        colore = GRIGIO
    else:
        stato_riga = snapshot["messaggio"]

    righe = [
        stato_riga,
        f"Nome:    {nome or '...'}",
        f"Cognome: {cognome or '...'}",
    ]
    if doc_letto:
        righe.append("Dati salvati su disco" if snapshot["salvato"] else "Salvataggio in corso...")
    pannello(frame, righe, colore)


def apri_webcam():
    for indice in (int(os.getenv("CAM_INDEX", "0")), 0, 1):
        cam = cv2.VideoCapture(indice)
        if cam.isOpened():
            return cam
        cam.release()
    raise SystemExit("Impossibile aprire la webcam.")


def main():
    face_client, image_client, openai_client, deployment, speech_config = configura()

    ascolta_attivazione(speech_config)
    parla(speech_config, "Webcam attivata. Mostrami il tuo documento.")
    print("Webcam attivata. Tasti: 'q' esci, 's' forza analisi, 'r' rileggi documento.")

    cam = apri_webcam()

    ultimo_scan = 0.0
    ultimo_doc = 0.0
    forza_doc = False

    while True:
        ok, frame = cam.read()
        if not ok:
            print("Errore nella lettura del fotogramma.")
            break

        adesso = time.time()

        # Face + Image Analysis in background
        with analisi_lock:
            analisi_in_corso = analisi_stato["analisi_in_corso"]
        if not analisi_in_corso and adesso - ultimo_scan >= INTERVALLO_ANALISI:
            ultimo_scan = adesso
            ok_jpg, dati = cv2.imencode(".jpg", frame)
            if ok_jpg:
                with analisi_lock:
                    analisi_stato["analisi_in_corso"] = True
                threading.Thread(
                    target=worker_analisi,
                    args=(face_client, image_client, dati.tobytes()),
                    daemon=True,
                ).start()

        with analisi_lock:
            volti = list(analisi_stato["volti"])
            documento = analisi_stato["documento"]

        documento_presente = documento[0] is not None

        with lock:
            doc_letto = stato["doc_letto"]
            lettura_in_corso = stato["lettura_in_corso"]
            tentativi_falliti = stato["tentativi_falliti"]

        intervallo_corrente = min(
            INTERVALLO_DOCUMENTO + tentativi_falliti * 3.0,
            MAX_INTERVALLO_DOCUMENTO,
        )

        # Manda il crop a GPT solo se Image Analysis ha rilevato un documento
        if (not doc_letto and not lettura_in_corso
                and (forza_doc or (documento_presente and adesso - ultimo_doc >= intervallo_corrente))):
            ultimo_doc = adesso
            forza_doc = False
            crop = ritaglia(frame, documento[1])
            ok_crop, dati_crop = cv2.imencode(".jpg", crop)
            if ok_crop:
                with lock:
                    stato["lettura_in_corso"] = True
                    stato["messaggio"] = "Lettura documento in corso..."
                threading.Thread(
                    target=worker_documento,
                    args=(openai_client, deployment, speech_config, dati_crop.tobytes()),
                    daemon=True,
                ).start()

        with lock:
            snapshot = dict(stato)
        disegna(frame, volti, documento, snapshot)
        cv2.imshow("Viso + documento", frame)

        tasto = cv2.waitKey(1) & 0xFF
        if tasto == ord("q"):
            break
        if tasto == ord("s"):
            ultimo_scan = 0.0
            ultimo_doc = 0.0
            forza_doc = True
        if tasto == ord("r"):
            with lock:
                stato.update(nome=None, cognome=None, doc_letto=False, salvato=False,
                             messaggio="Mostra il documento alla webcam", tentativi_falliti=0)
            ultimo_doc = 0.0

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
