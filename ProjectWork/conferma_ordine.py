from datetime import date

from backend import crea_conferma_ordine, crea_dettaglio_conferma_ordine, get_conferma_ordine


def crea_conferma_da_risultato(risultato: dict, pdf_stem: str) -> dict:
    id_cliente = risultato["cliente"]["id_cliente_match"]
    if not id_cliente:
        return {"creata": False, "motivo": "Cliente non identificato con certezza, conferma non creata."}

    righe_ok = [r for r in risultato["righe"] if r["codice_articolo_match"] and r["confidenza_match"] == "alta"]
    righe_scartate = [r for r in risultato["righe"] if r not in righe_ok]
    id_conferma_base = f"CONF-{pdf_stem.upper()}"
    id_conferma = id_conferma_base
    tentativo_suffisso = 0

    while True:
        try:
            crea_conferma_ordine(
                id_conferma=id_conferma,
                id_cliente=id_cliente,
                data_conferma=date.today().isoformat(),
                riferimento_cliente=pdf_stem,
            )
            break
        except RuntimeError as e:
            if "409" in str(e) or "Conflitto" in str(e):
                esistente = get_conferma_ordine(id_conferma)
                if esistente is not None:
                    print(f"  [info] Conferma '{id_conferma}' già esistente, la riuso per le righe di dettaglio.")
                    break
                tentativo_suffisso += 1
                id_conferma = f"{id_conferma_base}-{tentativo_suffisso}"
                continue
            raise

    righe_create, righe_fallite = [], []
    for riga in righe_ok:
        try:
            crea_dettaglio_conferma_ordine(
                id_conferma=id_conferma,
                codice_articolo=riga["codice_articolo_match"],
                quantita=riga["quantita"],
                prezzo_unitario=riga["prezzo_dichiarato"],
                importo_riga=round(riga["quantita"] * riga["prezzo_dichiarato"], 2),
            )
            righe_create.append(riga["codice_articolo_match"])
        except Exception as e:
            righe_fallite.append({"codice": riga["codice_articolo_match"], "errore": str(e)})

    return {
        "creata": True,
        "id_conferma": id_conferma,
        "righe_create": righe_create,
        "righe_fallite": righe_fallite,
        "righe_scartate_per_bassa_confidenza": [r["codice_dichiarato"] or r["descrizione_dichiarata"] for r in righe_scartate],
    }
