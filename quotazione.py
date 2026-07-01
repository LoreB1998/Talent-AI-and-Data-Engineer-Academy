from matching import trova_cliente, trova_articolo, cliente_completo


def prepara_quotazione(dati_estratti: dict, clienti: list[dict], articoli: list[dict]) -> dict:
    """Prepara una bozza di quotazione: verifica cliente e articoli come per
    un ordine, ma calcola SEMPRE il prezzo dal listino di catalogo (ignora
    eventuali prezzi scritti nel documento, che in una richiesta di
    preventivo sono al più un'aspettativa del cliente, non un dato da
    validare). Va sempre inoltrata a un operatore prima di essere inviata
    al cliente: non è mai un'azione completamente automatica."""
    cliente_match = trova_cliente(dati_estratti, clienti)
    righe_quotazione = []
    totale_quotazione = 0.0
    righe_non_quotabili = []

    for riga in dati_estratti.get("righe", []):
        codice_dichiarato = (riga.get("codice_articolo") or "").strip()
        descrizione_dichiarata = riga.get("descrizione") or ""
        quantita = riga.get("quantita")

        articolo, confidenza, codice_match = trova_articolo(codice_dichiarato, descrizione_dichiarata, articoli)

        if not articolo or quantita is None:
            righe_non_quotabili.append({
                "codice_dichiarato": codice_dichiarato or None,
                "descrizione_dichiarata": descrizione_dichiarata,
                "motivo": "Articolo non identificato a catalogo" if not articolo else "Quantità non specificata",
            })
            continue

        prezzo_listino = articolo.get("prezzoListino")
        importo_riga = round(quantita * prezzo_listino, 2) if prezzo_listino is not None else None
        if importo_riga is not None:
            totale_quotazione += importo_riga

        righe_quotazione.append({
            "codice_dichiarato": codice_dichiarato or None,
            "descrizione_dichiarata": descrizione_dichiarata,
            "codice_articolo_match": codice_match,
            "descrizione_match": articolo["descrizione"],
            "quantita": quantita,
            "unita_misura": articolo.get("unitaMisura"),
            "prezzo_unitario_listino": prezzo_listino,
            "importo_riga": importo_riga,
            "confidenza_match": confidenza,
        })

    intervento_umano = True  # ogni quotazione richiede sempre revisione/invio da parte di un operatore
    motivo_intervento = ["Bozza di quotazione: richiede revisione e invio da parte di un operatore"]
    if not cliente_match:
        motivo_intervento.append("Cliente non identificato in anagrafica")
    if righe_non_quotabili:
        motivo_intervento.append(f"{len(righe_non_quotabili)} riga/he non quotabile/i: verificare manualmente")

    return {
        "intervento_umano_necessario": intervento_umano,
        "motivo_intervento_umano": motivo_intervento,
        "cliente": cliente_completo(dati_estratti, cliente_match),
        "riferimento_richiesta": dati_estratti.get("riferimento_ordine"),
        "data_richiesta": dati_estratti.get("data_ordine"),
        "note_generali": dati_estratti.get("note_generali"),
        "righe_quotazione": righe_quotazione,
        "righe_non_quotabili": righe_non_quotabili,
        "totale_quotazione_stimato": round(totale_quotazione, 2) if righe_quotazione else None,
    }