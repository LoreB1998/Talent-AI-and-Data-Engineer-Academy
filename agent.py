import json
import time
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from config import ENDPOINT, AGENT_NAME, AGENT_VERSION, PROMPT_ESTRAZIONE


def get_openai_client():
    project_client = AIProjectClient(endpoint=ENDPOINT, credential=DefaultAzureCredential())
    return project_client.get_openai_client()


def carica_pdf(openai_client, pdf_path: Path, max_tentativi: int = 3) -> str:
    """Carica il PDF come file 'assistants'. A volte il backend restituisce
    un id 'file-xxx' invece di 'assistant-xxx' (rifiutato da
    responses.create): in quel caso ritenta l'upload."""
    ultimo_id = None
    for tentativo in range(1, max_tentativi + 1):
        with open(pdf_path, "rb") as f:
            uploaded = openai_client.files.create(file=f, purpose="assistants")
        ultimo_id = uploaded.id
        if ultimo_id.startswith("assistant-") or ultimo_id.startswith("assistant_"):
            return ultimo_id
        print(f"  [avviso] id '{ultimo_id}' senza prefisso corretto, riprovo l'upload...")
    raise RuntimeError(
        f"Upload di '{pdf_path.name}' non ha mai prodotto un id con prefisso "
        f"'assistant-' dopo {max_tentativi} tentativi (ultimo: '{ultimo_id}')."
    )


def estrai_testo_da_pdf(openai_client, file_id: str, max_tentativi: int = 3) -> str:
    """Chiede all'agente di trascrivere il PDF, senza alcun tool call. Con
    retry, dato che il servizio si è dimostrato occasionalmente instabile
    anche su richieste semplici."""
    ultimo_errore = None
    for tentativo in range(1, max_tentativi + 1):
        try:
            response = openai_client.responses.create(
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": PROMPT_ESTRAZIONE},
                            {"type": "input_file", "file_id": file_id},
                        ],
                    }
                ],
                extra_body={
                    "agent_reference": {
                        "name": AGENT_NAME,
                        "version": AGENT_VERSION,
                        "type": "agent_reference",
                    }
                },
            )
            return response.output_text
        except Exception as e:
            ultimo_errore = e
            if tentativo < max_tentativi:
                attesa = 5 * tentativo
                print(f"  [avviso] estrazione tentativo {tentativo}/{max_tentativi} fallito, riprovo in {attesa}s...")
                time.sleep(attesa)
    raise ultimo_errore  # type: ignore


def parsa_json_estrazione(testo: str) -> dict:
    """Estrae l'oggetto JSON dalla risposta dell'agente, tollerando
    eventuali code fence markdown residui."""
    pulito = testo.strip()
    if pulito.startswith("```"):
        pulito = pulito.strip("`")
        if pulito.lower().startswith("json"):
            pulito = pulito[4:]
        pulito = pulito.strip()
    try:
        return json.loads(pulito)
    except json.JSONDecodeError:
        start, end = pulito.find("{"), pulito.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(pulito[start : end + 1])
        raise
