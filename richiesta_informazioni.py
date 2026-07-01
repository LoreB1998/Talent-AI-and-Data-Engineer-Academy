from matching import trova_cliente, trova_articolo, cliente_completo


def prepara_risposta_informazioni(dati_estratti: dict, clienti: list[dict], articoli: list[dict]) -> dict:
    """Prepara una bozza di risposta per una richiesta di informazioni:
    cerca nel catalogo (Assets) gli articoli che l'utente nomina o descrive,
    raccoglie le informazioni disponibili (descrizione, prezzo, unità di
    misura), e prepara una bozza da inoltrare a un operatore - non invia mai
    una risposta automatica al cliente."""
    cliente_match = trova_cliente(dati_estratti, clienti)

    # Le richieste di informazioni possono nominare articoli nelle "righe"
    # (stesso schema di estrazione usato per gli ordini, riusato qui per
    # qualsiasi prodotto/codice menzionato nella richiesta) oppure essere
    # generiche (nessuna riga, solo una domanda testuale nelle note).
    articoli_trovati = []
    articoli_non_trovati = []

    for riga in dati_estratti.get("righe", []):
        codice_dichiarato = (riga.get("codice_articolo") or "").strip()
        descrizione_dichiarata = riga.get("descrizione") or ""

        articolo, confidenza, codice_match = trova_articolo(codice_dichiarato, descrizione_dichiarata, articoli)
        if articolo:
            articoli_trovati.append({
                "richiesto_come": codice_dichiarato or descrizione_dichiarata,
                "codice": articolo["codice"],
                "descrizione": articolo["descrizione"],
                "categoria": articolo.get("categoria"),
                "unita_misura": articolo.get("unitaMisura"),
                "prezzo_listino": articolo.get("prezzoListino"),
                "confidenza_match": confidenza,
            })
        else:
            articoli_non_trovati.append(codice_dichiarato or descrizione_dichiarata)

    note_richiesta = dati_estratti.get("note_generali")

    return {
        "intervento_umano_necessario": True,  # ogni risposta va sempre rivista da un operatore prima dell'invio
        "motivo_intervento_umano": ["Bozza di risposta a richiesta informazioni: richiede revisione e invio da parte di un operatore"],
        "cliente": cliente_completo(dati_estratti, cliente_match),
        "domanda_o_richiesta": note_richiesta,
        "articoli_trovati_in_catalogo": articoli_trovati,
        "articoli_non_trovati": articoli_non_trovati,
        "bozza_risposta": _genera_bozza_testuale(cliente_match, articoli_trovati, articoli_non_trovati, note_richiesta),
    }


def _genera_bozza_testuale(cliente_match: dict | None, articoli_trovati: list[dict], articoli_non_trovati: list[str], note_richiesta: str | None) -> str:
    """Compone un testo semplice di bozza risposta, basato solo sui dati
    verificati nel catalogo - non è un testo definitivo, va sempre rivisto
    da un operatore prima dell'invio."""
    righe_testo = []
    saluto = f"Gentile {cliente_match['ragioneSociale']}," if cliente_match else "Gentile Cliente,"
    righe_testo.append(saluto)
    righe_testo.append("")
    righe_testo.append("in risposta alla Sua richiesta, Le forniamo le informazioni disponibili sui prodotti indicati:")
    righe_testo.append("")

    for art in articoli_trovati:
        prezzo = f"{art['prezzo_listino']:.2f} EUR" if art["prezzo_listino"] is not None else "prezzo da verificare"
        righe_testo.append(
            f"- {art['codice']}: {art['descrizione']} — {prezzo} / {art['unita_misura'] or 'unità non specificata'}"
        )

    if articoli_non_trovati:
        righe_testo.append("")
        righe_testo.append("Per i seguenti prodotti non abbiamo trovato corrispondenza nel nostro catalogo, ce ne occuperemo a parte:")
        for nome in articoli_non_trovati:
            righe_testo.append(f"- {nome}")

    righe_testo.append("")
    righe_testo.append("Restiamo a disposizione per ulteriori chiarimenti.")
    righe_testo.append("")
    righe_testo.append("[BOZZA — da rivedere e completare a cura dell'operatore prima dell'invio]")

    return "\n".join(righe_testo)