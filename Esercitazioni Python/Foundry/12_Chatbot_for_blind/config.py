import os

from dotenv import load_dotenv

load_dotenv()  # Carica le variabili da .env nell'ambiente, se il file esiste


FOUNDRY_ENDPOINT = os.getenv("FOUNDRY_ENDPOINT", "https://<la-tua-risorsa>.services.ai.azure.com")


MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5.4-nano")

VOICE_LIVE_API_VERSION = os.getenv("VOICE_LIVE_API_VERSION", "2026-04-10")

VOICE_LANGUAGE = os.getenv("VOICE_LANGUAGE", "it-IT")

VOICE_NAME = os.getenv("VOICE_NAME", "it-IT-IsabellaNeural")

CSV_PATH = os.getenv("CSV_PATH", "knowledgebase683.csv")