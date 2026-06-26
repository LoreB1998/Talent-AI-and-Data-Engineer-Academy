import csv
from dataclasses import dataclass
from typing import Optional

import config

COL_CODICE = "codice"
COL_DESCRIZIONE = "descrizione"
COL_CATEGORIA = "categoria"
COL_UNITA_MISURA = "unita_misura"
COL_PREZZO = "prezzo_listino"

@dataclass
class Prodotto:
    codice: str
    descrizione: str
    categoria: str
    unita_misura: str
    prezzo: float


# Catalogo caricato in memoria, popolato da carica_catalogo()
_catalogo: dict[str, Prodotto] = {}


def carica_catalogo(path: str = None) -> None:  # type: ignore
    """
    Legge il CSV da disco e popola il catalogo in memoria.
    Va chiamata una sola volta all'avvio del programma, in main.py.
    """
    percorso = path or config.CSV_PATH
    _catalogo.clear()

    with open(percorso, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for riga in reader:
            try:
                prodotto = Prodotto(
                    codice=riga[COL_CODICE].strip(),
                    descrizione=riga[COL_DESCRIZIONE].strip(),
                    categoria=riga[COL_CATEGORIA].strip(),
                    unita_misura=riga[COL_UNITA_MISURA].strip(),
                    prezzo=float(riga[COL_PREZZO]),
                )
                _catalogo[prodotto.codice] = prodotto
            except (KeyError, ValueError) as e:
                print(f"[catalog] Riga ignorata per errore ({e}): {riga}")

    print(f"[catalog] Catalogo caricato: {len(_catalogo)} prodotti.")


def get_prodotto(codice: str) -> Optional[Prodotto]:
    return _catalogo.get(codice)


def get_tutti_i_prodotti() -> list[Prodotto]:
    return list(_catalogo.values())


 