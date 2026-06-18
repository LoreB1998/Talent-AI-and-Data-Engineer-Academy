import os
import argparse
from openai import OpenAI, BadRequestError, AuthenticationError, APIConnectionError
from dotenv import load_dotenv

from Controller.cl_handler import Handler

load_dotenv()

AZ_SPEECH_ENDPOINT= os.getenv("AZ_SPEECH_ENDPOINT")
AZ_SPEECH_KEY= os.getenv("AZ_SPEECH_KEY")
AZ_SPEECH_REGION= os.getenv("AZ_SPEECH_REGION")
AZ_SPEECH_VOICE= os.getenv("AZ_SPEECH_VOICE")

AZ_OPENAI_KEY = os.getenv("AZ_OPENAI_KEY")
AZ_OPENAI_ENDPOINT = os.getenv("AZ_OPENAI_ENDPOINT")
AZ_OPENAI_DEPLOYMENT = os.getenv("AZ_OPENAI_DEPLOYMENT")
AZ_OPENAI_API_VERSION = os.getenv("AZ_OPENAI_API_VERSION", "2024-02-01")

client_openai = OpenAI(
    api_key=AZ_OPENAI_KEY, 
    base_url=AZ_OPENAI_ENDPOINT
    )


def scegli_modo_interattivo() -> str:
    while True:
        print("Seleziona modalita:")
        print("  [1] Chat")
        print("  [2] Vocale")
        scelta = input("Scelta [1/2]: ").strip().lower()

        if scelta in {"1", "chat", "testo"}:
            return "testo"
        if scelta in {"2", "vocale", "voce"}:
            return "voce"

        print("Scelta non valida. Inserisci 1 o 2.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sistema domotica: modalita testo o voce")
    parser.add_argument(
        "--modo",
        choices=["testo", "chat", "voce", "vocale"],
        default=None,
        help="Modalita opzionale: chat/testo oppure voce/vocale.",
    )
    args = parser.parse_args()

    modo = args.modo
    if modo is None:
        modo = scegli_modo_interattivo()
    elif modo in {"chat", "testo"}:
        modo = "testo"
    else:
        modo = "voce"

    Handler(client_openai, AZ_OPENAI_DEPLOYMENT, modo=modo).start()