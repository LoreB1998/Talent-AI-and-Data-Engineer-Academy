import asyncio
import threading

import numpy as np
import sounddevice as sd
from azure.ai.voicelive.aio import connect
from azure.ai.voicelive.models import (
    AudioInputTranscriptionOptions, # Serve per la trascrizione dell'audio in input
    AzureSemanticVad,               # Serve per la rilevazione della voce in input
    AzureStandardVoice,             # Serve per la sintesi vocale in output
    FunctionCallOutputItem,         # Serve per inviare il risultato di una funzione chiamata dall'assistente
    Modality,                       # Serve per specificare le modalità di input/output supportate dalla sessione 
    RequestSession,                 # Serve per configurare la sessione di conversazione con l'assistente vocale
)
from azure.identity.aio import DefaultAzureCredential

import config
import catalog
from cart import Cart
from tools import TOOLS_SCHEMA, esegui_funzione


_ISTRUZIONI_BASE = """
Sei l'assistente vocale di ACME Systems s.r.l. Aiuti clienti non vedenti
a completare un acquisto di articoli di ferramenta tramite voce, senza
alcuna interfaccia visiva.

Regole di comportamento:
1. Parla in modo chiaro, semplice e mai ambiguo: l'utente non può vedere
   nulla, quindi ogni informazione importante (prezzi, quantità, totali)
   va detta esplicitamente a voce, mai sottintesa.
2. Quando il cliente descrive cosa cerca (anche in modo vago o con una
   frase come "qualcosa per attaccare due pezzi di legno"), usa il catalogo
   riportato di seguito per individuare gli articoli pertinenti. Se ne trovi
   più di uno, leggili con codice e prezzo e chiedi quale interessa al cliente.
3. Per aggiungere un articolo al carrello usa aggiungi_al_carrello, ma solo
   dopo aver confermato col cliente quale articolo e quale quantità vuole.
4. Quando il cliente chiede cosa c'è nel carrello o quanto deve pagare, usa
   sempre mostra_carrello: non calcolare mai tu i totali a mente, fidati
   solo del risultato di questa funzione.
5. Il processo termina in tre modi:
   - il cliente chiede di pagare/confermare: chiama conferma_acquisto e chiudi.
   - il cliente chiede di annullare: chiama annulla_acquisto e chiudi.
   - il cliente vuole fermarsi e riprendere dopo: chiama sospendi_acquisto e chiudi.
   Non aggiungere messaggi di saluto dopo le chiamate di chiusura.
6. All'avvio, presentati con un breve messaggio di benvenuto (es. "Benvenuto
   all'assistente vocale ACME. Sono pronto, dimmi pure cosa cerchi."). Se il
   carrello è già stato ripristinato da una sessione precedente, informane il
   cliente leggendo il contenuto con mostra_carrello dopo il benvenuto.
7. Non inventare mai prezzi, quantità o descrizioni di articoli: usa sempre
   le funzioni fornite per consultare il catalogo reale.
8. Se il cliente chiede quali prodotti avete o quali categorie, descrivi
   sinteticamente il catalogo reale riportato di seguito, senza inventare
   nulla che non sia in elenco.

CATALOGO ACME (solo questi articoli esistono — niente altro):
{catalogo}
""".strip()


def _costruisci_istruzioni() -> str:
    righe = []
    for p in catalog.get_tutti_i_prodotti():
        righe.append(
            f"- [{p.codice}] {p.descrizione} | cat: {p.categoria} | "
            f"{p.prezzo:.2f}€/{p.unita_misura}"
        )
    catalogo_testo = "\n".join(righe) if righe else "(catalogo vuoto)"
    return _ISTRUZIONI_BASE.format(catalogo=catalogo_testo)


SAMPLE_RATE = 24000
CHANNELS = 1
CHUNK_MS = 20
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_MS / 1000)


class AudioIO:
    def __init__(self):
        self.input_stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=CHUNK_SAMPLES,
        )
        self.output_stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
        )
        self.input_stream.start()
        self.output_stream.start()

    def leggi_chunk(self) -> bytes:
        frames, _overflow = self.input_stream.read(CHUNK_SAMPLES)
        return frames.tobytes()

    def scrivi_audio(self, audio_bytes: bytes) -> None:
        array = np.frombuffer(audio_bytes, dtype="int16").reshape(-1, CHANNELS)
        self.output_stream.write(array)

    def chiudi(self):
        self.input_stream.stop()
        self.input_stream.close()
        self.output_stream.stop()
        self.output_stream.close()


def _costruisci_session_config() -> RequestSession:
    return RequestSession(
        modalities=[Modality.TEXT, Modality.AUDIO],
        instructions=_costruisci_istruzioni(),
        voice=AzureStandardVoice(name=config.VOICE_NAME),
        input_audio_transcription=AudioInputTranscriptionOptions(
            model="azure-speech",
            language=config.VOICE_LANGUAGE,
        ),
        tools=TOOLS_SCHEMA,
        turn_detection=AzureSemanticVad(),
    )


async def _invia_audio_microfono(connection, audio_io: AudioIO, stop_event: threading.Event, saluto_pronto: asyncio.Event):
    await saluto_pronto.wait()
    loop = asyncio.get_event_loop()
    while not stop_event.is_set():
        chunk = await loop.run_in_executor(None, audio_io.leggi_chunk)
        await connection.input_audio_buffer.append(audio=chunk)


async def _gestisci_eventi(connection, audio_io: AudioIO, cart: Cart, stop_event: threading.Event, saluto_pronto: asyncio.Event):
    async for evento in connection:
        tipo = evento.type

        if tipo == "response.audio.delta":
            audio_io.scrivi_audio(evento.delta)

        elif tipo == "input_audio_buffer.speech_started":
            print("[utente] ...")

        elif tipo == "conversation.item.input_audio_transcription.completed":
            print(f"[utente] {evento.transcript.strip()}")

        elif tipo == "response.function_call_arguments.done":
            print(f"[funzione] {evento.name}({evento.arguments})")
            risultato = esegui_funzione(evento.name, evento.arguments, cart)
            print(f"[risultato] {risultato}")

            await connection.conversation.item.create(
                item=FunctionCallOutputItem(
                    call_id=evento.call_id,
                    output=risultato,
                )
            )
            try:
                await connection.response.create()
            except Exception:
                pass

            if cart.is_terminato():
                print(f"[sistema] Sessione terminata — carrello: {cart.stato}")
                stop_event.set()
                saluto_pronto.set()
                break

        elif tipo == "response.audio_transcript.done":
            print(f"[assistente] {evento.transcript.strip()}")

        elif tipo == "response.done":
            saluto_pronto.set()

        elif tipo == "error":
            error_code = getattr(getattr(evento, "error", None), "code", None)
            if error_code != "conversation_already_has_active_response":
                print(f"[errore] {evento}")


async def main():
    catalog.carica_catalogo()
    cart = Cart.carica()
    audio_io = AudioIO()
    stop_event = threading.Event()

    print("[sistema] Connessione alla sessione Voice Live in corso...")
    async with DefaultAzureCredential() as credential:
        async with connect(
            endpoint=config.FOUNDRY_ENDPOINT,
            credential=credential,
            model=config.MODEL_NAME,
        ) as connection:

            await connection.session.update(session=_costruisci_session_config())
            print("[sistema] Sessione pronta. Parla pure: l'assistente ACME ti ascolta.")

            await connection.response.create()

            saluto_pronto = asyncio.Event()
            invio_audio_task = asyncio.create_task(
                _invia_audio_microfono(connection, audio_io, stop_event, saluto_pronto)
            )
            gestione_eventi_task = asyncio.create_task(
                _gestisci_eventi(connection, audio_io, cart, stop_event, saluto_pronto)
            )

            await gestione_eventi_task
            stop_event.set()
            invio_audio_task.cancel()

    audio_io.chiudi()
    print(f"[sistema] Sessione terminata. Stato finale carrello: {cart.stato}")


if __name__ == "__main__":
    asyncio.run(main())
