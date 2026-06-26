"""Configurazione condivisa.

Questa versione usa AIProjectClient con autenticazione Entra ID
(DefaultAzureCredential) per chiamare l'agente pubblicato su Foundry.
Prerequisito: aver eseguito "az login" almeno una volta (il token scade
periodicamente, va rifatto se l'autenticazione smette di funzionare).
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

FOUNDRY_PROJECT_ENDPOINT = os.getenv("AZ_FOUNDRY_EP")
AGENT_NAME = os.getenv("AZ_FOUNDRY_AGENT_APP_NAME")
AGENT_VERSION = os.getenv("AZ_FOUNDRY_AGENT_VERSION")


def require_config() -> None:
    """Verifica che le variabili obbligatorie siano impostate."""
    missing = []
    if not FOUNDRY_PROJECT_ENDPOINT:
        missing.append("AZ_FOUNDRY_EP")
    if not AGENT_NAME:
        missing.append("AZ_FOUNDRY_AGENT_APP_NAME")

    if missing:
        sys.exit(
            "ERRORE: variabili mancanti nel file .env: " + ", ".join(missing) + "\n"
            "Compila il file .env (vedi README.md)."
        )