from matching import valida_ordine
from quotazione import prepara_quotazione
from richiesta_informazioni import prepara_risposta_informazioni


TIPI_DOCUMENTO_VALIDI = {"ordine", "quotazione", "richiesta_informazioni", "non_determinabile"}


def elabora_documento(dati_estratti: dict, clienti: list[dict], articoli: list[dict]) -> dict:
    """Instrada il documento al percorso corretto in base alla
    classificazione fatta dall'agente in fase di estrazione
    (dati_estratti['tipo_documento']), e restituisce il risultato finale
    con la struttura specifica per quel tipo di documento."""
    tipo_documento = dati_estratti.get("tipo_documento")
    if tipo_documento not in TIPI_DOCUMENTO_VALIDI:
        tipo_documento = "non_determinabile"

    if tipo_documento == "non_determinabile":
        motivo = dati_estratti.get("motivo_non_determinabile") or "Tipo di documento non determinabile"
        risultato = {
            "intervento_umano_necessario": True,
            "motivo_intervento_umano": [f"Documento non automatizzabile: {motivo}"],
            "note_generali": dati_estratti.get("note_generali"),
        }

    elif tipo_documento == "ordine":
        risultato = valida_ordine(dati_estratti, clienti, articoli)

    elif tipo_documento == "quotazione":
        risultato = prepara_quotazione(dati_estratti, clienti, articoli)

    elif tipo_documento == "richiesta_informazioni":
        risultato = prepara_risposta_informazioni(dati_estratti, clienti, articoli)

    risultato["tipo_documento"] = tipo_documento
    return risultato