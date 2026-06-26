"""Identifica un gioco a partire dalla sua descrizione, usando AIProjectClient
con autenticazione Entra ID (DefaultAzureCredential) per invocare l'agente
pubblicato sul portale Foundry.

Prerequisito: aver eseguito "az login" prima di lanciare questo script.

Uso:
    python identify.py "un gioco di costruzione a blocchi, mondo cubico infinito, crafting..."
    python identify.py            # modalità interattiva, con memoria tra i turni
"""

import sys

from azure.ai.projects import AIProjectClient
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import DefaultAzureCredential
from openai import (
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
)

from agent_config import AGENT_NAME, AGENT_VERSION, FOUNDRY_PROJECT_ENDPOINT, require_config

EXIT_COMMANDS = {"quit", "exit"}


def identify(openai_client, description: str, previous_response_id: str | None = None):
    """Invia la descrizione all'agente pubblicato.

    Restituisce (testo_risposta, response_id) — il response_id va passato
    alla chiamata successiva per mantenere il contesto della conversazione.
    """
    kwargs = {}
    if previous_response_id is not None: # se è la prima chiamata, previous_response_id è None e non lo includiamo
        kwargs["previous_response_id"] = previous_response_id # se non è None, lo includiamo nei parametri della richiesta
    response = openai_client.responses.create( 
        input=description, # il testo della descrizione del gioco
        extra_body={"agent_reference": {
            "name": AGENT_NAME, # il nome dell'agente da chiamare, definito nel .env e corrispondente a quello del portale Foundry
            **({"version": AGENT_VERSION} if AGENT_VERSION else {}), # se AGENT_VERSION è definita, la includiamo, altrimenti no
            "type": "agent_reference", # tipo di input per indicare che vogliamo chiamare un agente specifico
        }},
        **kwargs, # includiamo previous_response_id solo se non è None, per mantenere il contesto della conversazione
    )
    return response.output_text, response.id # restituiamo il testo della risposta e l'id della risposta, che può essere usato come previous_response_id nella chiamata successiva


def main() -> None:
    require_config()

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=FOUNDRY_PROJECT_ENDPOINT, credential=credential) as project_client, # type: ignore
        project_client.get_openai_client() as openai_client,
    ):
        description_arg = " ".join(sys.argv[1:]).strip()

        if description_arg:
            text, _ = identify(openai_client, description_arg)
            print(text)
            return

        print("Descrivi il gioco e premi Invio (riga vuota o scrivi 'quit' per uscire).\n")
        previous_response_id = None
        while True:
            try:
                description = input("Descrizione> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not description or description.lower() in EXIT_COMMANDS:
                break
            print()
            text, previous_response_id = identify(openai_client, description, previous_response_id)
            print(text)
            print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except ClientAuthenticationError:
        print("\nNon sei autenticato con Azure. Esegui 'az login' nel terminale e riprova.")
    except AuthenticationError:
        print("\nErrore di autenticazione lato Foundry. Esegui 'az login' e riprova.")
    except PermissionDeniedError as e:
        print(
            "\nAccesso negato (403). Controlla di avere il ruolo 'Foundry User' "
            "(ex Azure AI User) sul progetto: Azure Portal -> risorsa AI -> "
            f"Access control (IAM).\nDettagli: {e}"
        )
    except NotFoundError as e:
        print(
            "\nAgente non trovato. Controlla che AZ_FOUNDRY_AGENT_APP_NAME nel .env "
            "corrisponda esattamente al nome dell'agente nel portale (quello in alto "
            f"nella pagina dell'editor dell'agente).\nDettagli: {e}"
        )
    except BadRequestError as e:
        print(f"\nRichiesta non valida: {e}")
    except APIConnectionError as e:
        print(f"\nErrore di connessione: controlla AZ_FOUNDRY_EP nel file .env.\n{e}")