import json

import catalog
from cart import Cart


TOOLS_SCHEMA = [
    {
        "type": "function",
        "name": "aggiungi_al_carrello",
        "description": "Aggiunge una quantità di un articolo (identificato per codice) al carrello.",
        "parameters": {
            "type": "object",
            "properties": {
                "codice": {
                    "type": "string",
                    "description": "Codice dell'articolo da aggiungere, ottenuto da una precedente cerca_prodotto.",
                },
                "quantita": {
                    "type": "integer",
                    "description": "Quantità da aggiungere.",
                },
            },
            "required": ["codice", "quantita"],
        },
    },
    {
        "type": "function",
        "name": "modifica_quantita_carrello",
        "description": "Cambia la quantità di un articolo già presente nel carrello.",
        "parameters": {
            "type": "object",
            "properties": {
                "codice": {"type": "string"},
                "nuova_quantita": {
                    "type": "integer",
                    "description": "Nuova quantità desiderata. Se zero o negativa, l'articolo viene rimosso.",
                },
            },
            "required": ["codice", "nuova_quantita"],
        },
    },
    {
        "type": "function",
        "name": "rimuovi_dal_carrello",
        "description": "Rimuove completamente un articolo dal carrello.",
        "parameters": {
            "type": "object",
            "properties": {
                "codice": {"type": "string"},
            },
            "required": ["codice"],
        },
    },
    {
        "type": "function",
        "name": "mostra_carrello",
        "description": (
            "Descrive il contenuto attuale del carrello: ogni riga con "
            "quantità, prezzo unitario, totale di riga, e il totale complessivo. "
            "Da usare ogni volta che il cliente chiede cosa c'è nel carrello "
            "o quanto deve pagare."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "conferma_acquisto",
        "description": (
            "Conferma il pagamento e conclude definitivamente l'acquisto. "
            "Da chiamare SOLO quando il cliente conferma esplicitamente di voler pagare."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "annulla_acquisto",
        "description": (
            "Annulla completamente l'acquisto e svuota il carrello. "
            "Da chiamare SOLO quando il cliente chiede esplicitamente di annullare."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "sospendi_acquisto",
        "description": (
            "Salva il carrello in stand-by senza svuotarlo, chiudendo la sessione. "
            "Da chiamare quando il cliente vuole interrompere ora e riprendere in seguito. "
            "Al prossimo avvio il carrello verrà ripristinato automaticamente."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
]



def esegui_funzione(nome_funzione: str, argomenti_json: str, cart: Cart) -> str:
    """
    nome_funzione: nome della funzione richiesta dal modello (es. "aggiungi_al_carrello")
    argomenti_json: stringa JSON con gli argomenti, come inviata dal modello
    cart: l'istanza di Cart della sessione corrente

    Ritorna sempre una stringa: è il testo che rimandiamo al modello
    come risultato della function call, perché lo usi per formulare
    la risposta vocale.
    """
    try:
        args = json.loads(argomenti_json) if argomenti_json else {}
    except json.JSONDecodeError:
        return "Errore: argomenti della funzione non validi."

    if nome_funzione == "aggiungi_al_carrello":
        prodotto = catalog.get_prodotto(args.get("codice", ""))
        if prodotto is None:
            return "Codice articolo non valido: prova prima a cercare l'articolo."
        return cart.aggiungi(prodotto, int(args.get("quantita", 0)))

    elif nome_funzione == "modifica_quantita_carrello":
        return cart.modifica_quantita(
            args.get("codice", ""), int(args.get("nuova_quantita", 0))
        )

    elif nome_funzione == "rimuovi_dal_carrello":
        return cart.rimuovi(args.get("codice", ""))

    elif nome_funzione == "mostra_carrello":
        return cart.descrivi()

    elif nome_funzione == "conferma_acquisto":
        return cart.conferma_pagamento()

    elif nome_funzione == "annulla_acquisto":
        return cart.svuota()

    elif nome_funzione == "sospendi_acquisto":
        return cart.sospendi()

    else:
        return f"Funzione non riconosciuta: {nome_funzione}"