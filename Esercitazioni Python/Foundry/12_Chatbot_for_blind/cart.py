import json
import os
from dataclasses import dataclass
from datetime import datetime

from catalog import Prodotto


@dataclass
class RigaCarrello:
    prodotto: Prodotto
    quantita: int

    @property
    def totale_riga(self) -> float:
        return round(self.prodotto.prezzo * self.quantita, 2)


class Cart:
    def __init__(self):
        self._righe: dict[str, RigaCarrello] = {}  # chiave: codice articolo
        self.stato: str = "aperto"  # "aperto" | "pagato" | "annullato" | "sospeso"

    @classmethod
    def carica(cls, path: str = "carrello.json") -> "Cart":
        """Crea un Cart ripristinando un carrello sospeso da file JSON."""
        cart = cls()
        if not os.path.exists(path):
            return cart
        try:
            with open(path, encoding="utf-8") as f:
                dati = json.load(f)
            if dati.get("stato") != "sospeso":
                return cart
            for a in dati.get("articoli", []):
                prodotto = Prodotto(
                    codice=a["codice"],
                    descrizione=a["descrizione"],
                    prezzo=a["prezzo_unitario"],
                    unita_misura=a["unita_misura"],
                    categoria="",
                )
                cart._righe[prodotto.codice] = RigaCarrello(
                    prodotto=prodotto, quantita=a["quantita"]
                )
            cart.stato = "aperto"
            print(f"[cart] Carrello sospeso ripristinato da {path}: {len(cart._righe)} articoli")
        except Exception as e:
            print(f"[cart] Impossibile caricare il carrello: {e}")
        return cart

    def aggiungi(self, prodotto: Prodotto, quantita: int) -> str:
        """Aggiunge un prodotto al carrello, o ne aumenta la quantità se già presente."""
        if quantita <= 0:
            return f"Quantità non valida per {prodotto.descrizione}: deve essere maggiore di zero."

        if prodotto.codice in self._righe:
            self._righe[prodotto.codice].quantita += quantita
        else:
            self._righe[prodotto.codice] = RigaCarrello(prodotto=prodotto, quantita=quantita)

        riga = self._righe[prodotto.codice]
        return (
            f"Aggiunto: {quantita} {prodotto.unita_misura} di {prodotto.descrizione}. "
            f"Ora nel carrello ci sono {riga.quantita} {prodotto.unita_misura}, "
            f"per un totale di riga di {riga.totale_riga:.2f} euro."
        )

    def modifica_quantita(self, codice: str, nuova_quantita: int) -> str:
        """Imposta una quantità esatta per un articolo già nel carrello."""
        if codice not in self._righe:
            return "Quell'articolo non è nel carrello."

        if nuova_quantita <= 0:
            return self.rimuovi(codice)

        riga = self._righe[codice]
        riga.quantita = nuova_quantita
        return (
            f"Quantità di {riga.prodotto.descrizione} aggiornata a "
            f"{riga.quantita} {riga.prodotto.unita_misura}. "
            f"Totale di riga: {riga.totale_riga:.2f} euro."
        )

    def rimuovi(self, codice: str) -> str:
        """Rimuove completamente un articolo dal carrello."""
        if codice not in self._righe:
            return "Quell'articolo non è nel carrello."
        descrizione = self._righe.pop(codice).prodotto.descrizione
        return f"{descrizione} rimosso dal carrello."

    def totale(self) -> float:
        return round(sum(r.totale_riga for r in self._righe.values()), 2)

    def descrivi(self) -> str:
        """
        Genera una descrizione testuale del carrello pensata per essere
        letta ad alta voce: riga per riga, con prezzo unitario, totale
        di riga, e totale complessivo in fondo.
        """
        if not self._righe:
            return "Il carrello è vuoto."

        parti = ["Ecco il contenuto del carrello."]
        for riga in self._righe.values():
            parti.append(
                f"{riga.quantita} {riga.prodotto.unita_misura} di {riga.prodotto.descrizione}, "
                f"prezzo unitario {riga.prodotto.prezzo:.2f} euro, "
                f"totale di riga {riga.totale_riga:.2f} euro."
            )
        parti.append(f"Il totale complessivo è {self.totale():.2f} euro.")
        return " ".join(parti)

    def salva(self, path: str = "carrello.json") -> None:
        """Salva lo stato del carrello su file JSON."""
        dati = {
            "timestamp": datetime.now().isoformat(),
            "stato": self.stato,
            "articoli": [
                {
                    "codice": r.prodotto.codice,
                    "descrizione": r.prodotto.descrizione,
                    "quantita": r.quantita,
                    "prezzo_unitario": r.prodotto.prezzo,
                    "unita_misura": r.prodotto.unita_misura,
                    "totale_riga": r.totale_riga,
                }
                for r in self._righe.values()
            ],
            "totale": self.totale(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dati, f, ensure_ascii=False, indent=2)
        print(f"[cart] Carrello salvato in {path}")

    def sospendi(self) -> str:
        """Salva il carrello in stand-by senza svuotarlo, per riprendere in seguito."""
        if not self._righe:
            return "Il carrello è vuoto, non c'è nulla da sospendere."
        self.stato = "sospeso"
        self.salva()
        return (
            f"Carrello sospeso e salvato con {len(self._righe)} articoli "
            f"per un totale di {self.totale():.2f} euro. "
            "Alla prossima sessione troverai tutto qui."
        )

    def svuota(self) -> str:
        """Annulla l'acquisto: vuota il carrello e chiude la sessione come annullata."""
        self._righe.clear()
        self.stato = "annullato"
        self.salva()
        return "Il carrello è stato annullato e svuotato. Acquisto interrotto."

    def conferma_pagamento(self) -> str:
        """Conferma l'acquisto: chiude la sessione come pagata."""
        if not self._righe:
            return "Il carrello è vuoto, non c'è nulla da pagare."
        totale = self.totale()
        self.stato = "pagato"
        self.salva()
        return f"Pagamento confermato. Totale addebitato: {totale:.2f} euro. Grazie per l'acquisto."

    def is_terminato(self) -> bool:
        """True quando il ciclo di acquisto è concluso (pagato, annullato o sospeso)."""
        return self.stato in ("pagato", "annullato", "sospeso")