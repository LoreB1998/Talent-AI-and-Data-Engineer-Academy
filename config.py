import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.environ["ENDPOINT"]
AGENT_NAME = os.environ["AGENT_NAME"]
AGENT_VERSION = os.environ["AGENT_VERSION"]

BACKEND_BASE_URL = os.environ["BACKEND_BASE_URL"]

PDF_DIR = Path("pdf_da_processare")
OUTPUT_DIR = Path("output")

# Imposta a True solo quando vuoi che lo script crei davvero la conferma
# d'ordine sul backend condiviso (dopo aver controllato i risultati a mano).
CREA_CONFERMA_ORDINE = False

SOGLIA_TOLLERANZA_PREZZO = 0.01   # differenza percentuale minima per segnalare uno scostamento (1%)
QUANTITA_MASSIMA_PLAUSIBILE = 100_000  # oltre questa soglia, segnala come sospetta

PROMPT_ESTRAZIONE = (
    "Without calling any function or tool, read the attached PDF file "
    "carefully and extract its content into a JSON object, with this exact "
    "structure:\n"
    "{\n"
    '  "tipo_documento": one of "ordine", "quotazione", '
    '"richiesta_informazioni", "non_determinabile" — classify the document '
    "based on its content: use 'ordine' only if it is clearly a purchase "
    "order (with specific quantities and prices requested for delivery); "
    "'quotazione' if it is a request for a price quote or offer; "
    "'richiesta_informazioni' if it is asking for information without "
    "ordering anything; 'non_determinabile' if the document is ambiguous "
    "or does not fit any of the above,\n"
    '  "motivo_non_determinabile": string or null — if tipo_documento is '
    '"non_determinabile", briefly explain why (e.g. missing quantities, '
    "ambiguous intent, unreadable content),\n"
    '  "cliente_ragione_sociale": string or null,\n'
    '  "cliente_partita_iva": string or null,\n'
    '  "cliente_indirizzo": string or null,\n'
    '  "cliente_citta": string or null,\n'
    '  "cliente_provincia": string or null,\n'
    '  "cliente_email": string or null,\n'
    '  "cliente_telefono": string or null,\n'
    '  "riferimento_ordine": string or null,\n'
    '  "data_ordine": string or null,\n'
    '  "data_consegna_richiesta": string or null,\n'
    '  "condizioni_pagamento": string or null,\n'
    '  "note_generali": string or null (any general notes not tied to a '
    "specific order line, e.g. delivery instructions, general conditions),\n"
    '  "righe": [\n'
    "    {\n"
    '      "codice_articolo": string or null,\n'
    '      "descrizione": string,\n'
    '      "quantita": number or null,\n'
    '      "unita_misura": string or null,\n'
    '      "prezzo_unitario": number or null,\n'
    '      "nota": string or null (free-text note tied to this specific '
    "line, even if written elsewhere in the document)\n"
    "    }\n"
    "  ]\n"
    "}\n"
    "Transcribe values exactly as they appear in the document. If a value "
    "is not present, use null. For 'righe', include ALL lines/items "
    "mentioned in the document, even if quantities or prices are missing. "
    "Return ONLY the JSON object, no markdown fences, no extra text."
)
