import re

from config import SOGLIA_TOLLERANZA_PREZZO, QUANTITA_MASSIMA_PLAUSIBILE


def normalizza(testo: str) -> str:
    testo = testo.lower()
    testo = re.sub(r"[^\w\s]", " ", testo)
    testo = re.sub(r"\s+", " ", testo).strip()
    return testo


def trova_cliente(dati_estratti: dict, clienti: list[dict]) -> dict | None:
    piva_doc = (dati_estratti.get("cliente_partita_iva") or "").strip()
    if piva_doc:
        for cliente in clienti:
            if cliente.get("partitaIva", "").strip().lower() == piva_doc.lower():
                return cliente
    ragione_doc = normalizza(dati_estratti.get("cliente_ragione_sociale") or "")
    if ragione_doc:
        for cliente in clienti:
            if normalizza(cliente.get("ragioneSociale", "")) == ragione_doc:
                return cliente
        # match parziale, nel caso la ragione sociale non sia scritta identica
        for cliente in clienti:
            ragione_cat = normalizza(cliente.get("ragioneSociale", ""))
            if ragione_cat and (ragione_cat in ragione_doc or ragione_doc in ragione_cat):
                return cliente
    return None


def trova_articolo_per_codice(codice: str, articoli: list[dict]) -> dict | None:
    if not codice:
        return None
    codice_norm = codice.strip().upper()
    for articolo in articoli:
        if articolo.get("codice", "").strip().upper() == codice_norm:
            return articolo
    return None


def trova_articolo_per_descrizione(descrizione: str, articoli: list[dict]) -> tuple[dict | None, str]:
    desc_norm = normalizza(descrizione)
    parole_desc = set(desc_norm.split())
    migliore, miglior_punteggio = None, 0
    for articolo in articoli:
        parole_cat = set(normalizza(articolo.get("descrizione", "")).split())
        punteggio = len(parole_desc & parole_cat)
        if punteggio > miglior_punteggio:
            miglior_punteggio, migliore = punteggio, articolo
    if migliore is None or miglior_punteggio == 0:
        return None, "bassa"
    if miglior_punteggio >= 3:
        return migliore, "alta"
    if miglior_punteggio >= 2:
        return migliore, "media"
    return migliore, "bassa"


def verifica_coerenza_riga(riga_dichiarata: dict, articolo_match: dict | None, unita_dichiarata: str | None) -> list[str]:
    """Confronta i dati dichiarati nel documento con quelli reali di
    catalogo, e restituisce una lista di messaggi di anomalia (vuota se
    tutto è coerente). Non blocca mai l'elaborazione: la riga resta nel
    risultato comunque, con le anomalie segnalate a parte."""
    anomalie = []

    quantita = riga_dichiarata.get("quantita")
    prezzo_dichiarato = riga_dichiarata.get("prezzo_unitario")

    if quantita is not None:
        if quantita <= 0:
            anomalie.append(f"Quantità non plausibile: {quantita}")
        elif quantita > QUANTITA_MASSIMA_PLAUSIBILE:
            anomalie.append(f"Quantità sospettosamente alta: {quantita}")

    if articolo_match is not None:
        prezzo_listino = articolo_match.get("prezzoListino")
        if prezzo_dichiarato is not None and prezzo_listino is not None and prezzo_listino > 0:
            scostamento = abs(prezzo_dichiarato - prezzo_listino) / prezzo_listino
            if scostamento > SOGLIA_TOLLERANZA_PREZZO:
                anomalie.append(
                    f"Prezzo dichiarato ({prezzo_dichiarato}) diverso dal listino "
                    f"({prezzo_listino}), scostamento {scostamento:.0%}"
                )

        unita_catalogo = articolo_match.get("unitaMisura")
        if unita_dichiarata and unita_catalogo:
            if unita_dichiarata.strip().lower() != unita_catalogo.strip().lower():
                anomalie.append(
                    f"Unità di misura dichiarata ('{unita_dichiarata}') diversa da "
                    f"quella di vendita a catalogo ('{unita_catalogo}')"
                )

    return anomalie


def valida_ordine(dati_estratti: dict, clienti: list[dict], articoli: list[dict]) -> dict:
    """Valida i dati già estratti in JSON dall'agente, confrontandoli con
    clienti e articoli reali presi dal backend."""
    tipo_documento = dati_estratti.get("tipo_documento", "non_determinabile")
    motivo_non_det = dati_estratti.get("motivo_non_determinabile")

    intervento_umano = tipo_documento == "non_determinabile"
    motivo_intervento = []
    if tipo_documento == "non_determinabile":
        motivo_intervento.append(f"Tipo documento non determinabile: {motivo_non_det or 'nessun dettaglio disponibile'}")

    cliente_match = trova_cliente(dati_estratti, clienti)
    if not cliente_match:
        intervento_umano = True
        motivo_intervento.append("Cliente non identificato in anagrafica")

    cliente_output = {
        "id_cliente_match": cliente_match["id"] if cliente_match else None,
        "ragione_sociale": cliente_match["ragioneSociale"] if cliente_match else dati_estratti.get("cliente_ragione_sociale"),
        "partita_iva": cliente_match.get("partitaIva") if cliente_match else dati_estratti.get("cliente_partita_iva"),
        "indirizzo": cliente_match.get("indirizzo") if cliente_match else dati_estratti.get("cliente_indirizzo"),
        "citta": cliente_match.get("citta") if cliente_match else dati_estratti.get("cliente_citta"),
        "provincia": cliente_match.get("provincia") if cliente_match else dati_estratti.get("cliente_provincia"),
        "email": cliente_match.get("email") if cliente_match else dati_estratti.get("cliente_email"),
        "telefono": cliente_match.get("telefono") if cliente_match else dati_estratti.get("cliente_telefono"),
        "fonte_cliente": "backend_verificato" if cliente_match else "documento_non_verificato",
    }

    righe_validate = []
    for riga in dati_estratti.get("righe", []):
        codice_dichiarato = (riga.get("codice_articolo") or "").strip()
        descrizione_dichiarata = riga.get("descrizione") or ""

        articolo = trova_articolo_per_codice(codice_dichiarato, articoli) if codice_dichiarato else None
        if articolo:
            confidenza, descrizione_match, codice_match = "alta", articolo["descrizione"], articolo["codice"]
            unita_misura = riga.get("unita_misura") or articolo.get("unitaMisura")
        else:
            articolo_simile, confidenza = trova_articolo_per_descrizione(descrizione_dichiarata, articoli)
            descrizione_match = articolo_simile["descrizione"] if articolo_simile else descrizione_dichiarata
            codice_match = articolo_simile["codice"] if articolo_simile else None
            unita_misura = riga.get("unita_misura") or (articolo_simile.get("unitaMisura") if articolo_simile else None)
            articolo = articolo_simile

        note_anomalia_parti = []
        if not codice_match:
            note_anomalia_parti.append(
                f"Nessun match certo trovato a catalogo per codice dichiarato '{codice_dichiarato or '(assente)'}'"
            )
            intervento_umano = True
            motivo_intervento.append(f"Articolo non identificato: '{codice_dichiarato or descrizione_dichiarata[:40]}'")
        if riga.get("nota"):
            note_anomalia_parti.append(f"Nota nel documento: {riga['nota']}")
            intervento_umano = True
            motivo_intervento.append(f"Riga '{codice_dichiarato or descrizione_dichiarata[:30]}': nota che richiede valutazione — {riga['nota'][:80]}")

        anomalie_coerenza = verifica_coerenza_riga(riga, articolo, riga.get("unita_misura"))
        note_anomalia_parti.extend(anomalie_coerenza)
        if anomalie_coerenza:
            intervento_umano = True
            for a in anomalie_coerenza:
                motivo_intervento.append(f"Riga '{codice_dichiarato}': {a}")

        righe_validate.append({
            "codice_dichiarato": codice_dichiarato or None,
            "descrizione_dichiarata": descrizione_dichiarata,
            "codice_articolo_match": codice_match,
            "descrizione_match": descrizione_match,
            "quantita": riga.get("quantita"),
            "unita_misura": unita_misura,
            "prezzo_dichiarato": riga.get("prezzo_unitario"),
            "prezzo_listino_catalogo": articolo.get("prezzoListino") if articolo else None,
            "confidenza_match": confidenza,
            "note_anomalia": " | ".join(note_anomalia_parti) if note_anomalia_parti else None,
        })

    return {
        "tipo_documento": tipo_documento,
        "intervento_umano_necessario": intervento_umano,
        "motivo_intervento_umano": list(dict.fromkeys(motivo_intervento)) if motivo_intervento else None,
        "cliente": cliente_output,
        "riferimento_ordine": dati_estratti.get("riferimento_ordine"),
        "data_ordine": dati_estratti.get("data_ordine"),
        "data_consegna_richiesta": dati_estratti.get("data_consegna_richiesta"),
        "condizioni_pagamento": dati_estratti.get("condizioni_pagamento"),
        "note_generali": dati_estratti.get("note_generali"),
        "righe": righe_validate,
    }
