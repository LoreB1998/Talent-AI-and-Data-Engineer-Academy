class Materiale:
    # Attributo di classe: conterrà automaticamente tutti i materiali creati
    catalogo: list['Materiale'] = []

    def __init__(self, titolo: str, autore: str, anno: int, codice: int, disponibile: bool = True):
        self.titolo = titolo
        self.autore = autore
        self.anno = anno
        self.codice = codice
        self.disponibile = disponibile
        # Ogni volta che un oggetto viene creato, si aggiunge da solo al catalogo unico
        Materiale.catalogo.append(self)

    def mostra_info(self):
        stato = "Sì" if self.disponibile else "No"
        print(f"[{self.__class__.__name__}] Titolo: {self.titolo} | Autore: {self.autore} | "
              f"Anno: {self.anno} | Codice: {self.codice} | Disponibile: {stato}")

    def presta(self):
        self.disponibile = False

    def restituisci(self):
        self.disponibile = True

    @classmethod
    def mostra_stato(cls):
        disponibili = sum(1 for m in cls.catalogo if m.disponibile)
        non_disponibili = len(cls.catalogo) - disponibili
        print(f"Totale materiali: {len(cls.catalogo)} | Disponibili: {disponibili} | Non disponibili: {non_disponibili}")


class Libro(Materiale):
    def __init__(self, titolo: str, autore: str, anno: int, codice: int, numero_pagine: int, disponibile: bool = True):
        super().__init__(titolo, autore, anno, codice, disponibile)
        self.numero_pagine = numero_pagine

    def mostra_info(self):
        super().mostra_info()
        print(f"  Numero pagine: {self.numero_pagine}")


class Ebook(Libro):
    def __init__(self, titolo: str, autore: str, anno: int, codice: int, numero_pagine: int, dimensione_mb: float, disponibile: bool = True):
        # Passiamo correttamente i parametri a Libro nell'ordine esatto richiesto dal suo __init__
        super().__init__(titolo, autore, anno, codice, numero_pagine, disponibile)
        self.dimensione_mb = dimensione_mb

    def mostra_info(self):
        super().mostra_info()
        print(f"  Dimensione: {self.dimensione_mb} MB")


class Rivista(Materiale):
    def __init__(self, titolo: str, autore: str, anno: int, codice: int, numero_edizione: int, disponibile: bool = True):
        super().__init__(titolo, autore, anno, codice, disponibile)
        self.numero_edizione = numero_edizione

    def mostra_info(self):
        super().mostra_info()
        print(f"  Numero edizione: {self.numero_edizione}") 


class DVD(Materiale):
    def __init__(self, titolo: str, autore: str, anno: int, codice: int, durata_minuti: int, disponibile: bool = True):
        super().__init__(titolo, autore, anno, codice, disponibile)
        self.durata_minuti = durata_minuti

    def mostra_info(self):
        super().mostra_info()
        print(f"  Durata: {self.durata_minuti} minuti")


# ── Utente ──────────────────────────────────────────────────────────────────

class Utente:
    MAX_PRESTITI = 3
    elenco_utenti: list['Utente'] = []  # Lista unica di classe per gli utenti

    def __init__(self, nome: str, cognome: str, matricola: int):
        self.nome = nome
        self.cognome = cognome
        self.matricola = matricola
        self.prestiti: list[Materiale] = []
        Utente.elenco_utenti.append(self)

    def mostra_info(self):
        print(f"Nome: {self.nome} {self.cognome} | Matricola: {self.matricola} | Prestiti attivi: {self.conta_prestiti()}")

    def aggiungi_prestito(self, materiale: Materiale) -> bool:
        if self.conta_prestiti() >= self.MAX_PRESTITI:
            print(f"Errore: {self.nome} {self.cognome} ha già raggiunto il limite di {self.MAX_PRESTITI} prestiti.")
            return False
        self.prestiti.append(materiale)
        return True

    def restituisci_prestito(self, codice_materiale: int) -> Materiale | None:
        for m in self.prestiti:
            if m.codice == codice_materiale:
                self.prestiti.remove(m)
                return m
        return None

    def mostra_prestiti(self):
        if not self.prestiti:
            print(f"{self.nome} {self.cognome} non ha prestiti attivi.")
        else:
            print(f"\nPrestiti di {self.nome} {self.cognome}:")
            for m in self.prestiti:
                m.mostra_info()

    def conta_prestiti(self) -> int:
        return len(self.prestiti)


# ── Popolamento iniziale dei dati ───────────────────────────────────────────

Libro("Il Nome della Rosa", "Umberto Eco", 1980, 101, 502)
Libro("1984", "George Orwell", 1949, 102, 328)
Libro("Il Piccolo Principe", "Antoine de Saint-Exupéry", 1943, 103, 96)
Rivista("Focus", "AA.VV.", 2024, 201, numero_edizione=312)
Rivista("National Geographic", "AA.VV.", 2024, 202, numero_edizione=89)
DVD("Interstellar", "Christopher Nolan", 2014, 301, durata_minuti=169)
DVD("La Grande Bellezza", "Paolo Sorrentino", 2013, 302, durata_minuti=142)

Utente("Mario", "Rossi", 1001)
Utente("Laura", "Bianchi", 1002)
Utente("Giorgio", "Verdi", 1003)


# ── Funzioni di supporto ─────────────────────────────────────────────────────

def trova_utente(matricola: int) -> Utente | None:
    return next((u for u in Utente.elenco_utenti if u.matricola == matricola), None)

def trova_materiale(codice: int) -> Materiale | None:
    return next((m for m in Materiale.catalogo if m.codice == codice), None)


# ── Voci di menu conformi alla traccia ────────────────────────────────────────

def mostra_tutti():
    print("\n── Tutti i materiali (ordinati per titolo) ──")
    Materiale.mostra_stato()
    for m in sorted(Materiale.catalogo, key=lambda x: x.titolo):
        m.mostra_info()

def mostra_disponibili():
    disponibili = [m for m in Materiale.catalogo if m.disponibile]
    print(f"\n── Materiali disponibili: {len(disponibili)} ──")
    for m in sorted(disponibili, key=lambda x: x.titolo):
        m.mostra_info()

def cerca_per_titolo_o_autore():
    scelta = input("Cercare per (1) Titolo o (2) Autore?: ").strip()
    chiave = input("Inserisci il testo da cercare: ").strip().lower()
    
    if scelta == "1":
        risultati = [m for m in Materiale.catalogo if chiave in m.titolo.lower()]
    else:
        risultati = [m for m in Materiale.catalogo if chiave in m.autore.lower()]

    if risultati:
        for m in sorted(risultati, key=lambda x: x.titolo):
            m.mostra_info()
    else:
        print("Nessun materiale trovato.")

def mostra_utenti():
    print("\n── Utenti registrati ──")
    for u in Utente.elenco_utenti:
        u.mostra_info()

def effettua_prestito():
    try:
        matricola = int(input("Matricola utente: "))
    except ValueError:
        print("Matricola non valida.")
        return
    utente = trova_utente(matricola)
    if not utente:
        print("Utente non trovato.")
        return
    try:
        codice = int(input("Codice materiale: "))
    except ValueError:
        print("Codice non valido.")
        return
    materiale = trova_materiale(codice)
    if not materiale:
        print("Materiale non trovato.")
        return
    if not materiale.disponibile:
        print(f"Il materiale '{materiale.titolo}' non è disponibile.")
        return
    if utente.aggiungi_prestito(materiale):
        materiale.presta()
        print(f"Prestito effettuato: '{materiale.titolo}' → {utente.nome} {utente.cognome}.")

def restituisci_materiale():
    try:
        matricola = int(input("Matricola utente: "))
    except ValueError:
        print("Matricola non valida.")
        return
    utente = trova_utente(matricola)
    if not utente:
        print("Utente non trovato.")
        return
    try:
        codice = int(input("Codice materiale: "))
    except ValueError:
        print("Codice non valido.")
        return
    materiale = utente.restituisci_prestito(codice)
    if materiale:
        materiale.restituisci()
        print(f"Restituzione completata: '{materiale.titolo}' da {utente.nome} {utente.cognome}.")
    else:
        print("Il materiale non risulta tra i prestiti di questo utente.")

def mostra_prestiti_utente():
    try:
        matricola = int(input("Matricola utente: "))
    except ValueError:
        print("Matricola non valida.")
        return
    utente = trova_utente(matricola)
    if not utente:
        print("Utente non trovato.")
    else:
        utente.mostra_prestiti()


# ── Menu principale ───────────────────────────────────────────────────────────

MENU = """
╔══════════════════════════════════════╗
║         BIBLIOTECA SCOLASTICA        ║
╠══════════════════════════════════════╣
║  1. Mostra tutti i materiali         ║
║  2. Mostra solo materiali disponibili║
║  3. Cerca materiale per titolo/autore║
║  4. Mostra utenti                    ║
║  5. Effettua prestito                ║
║  6. Restituisci materiale            ║
║  7. Mostra prestiti di un utente     ║
║  8. Esci                             ║
╚══════════════════════════════════════╝"""

AZIONI = {
    "1": mostra_tutti,
    "2": mostra_disponibili,
    "3": cerca_per_titolo_o_autore,
    "4": mostra_utenti,
    "5": effettua_prestito,
    "6": restituisci_materiale,
    "7": mostra_prestiti_utente,
}

def main():
    while True:
        print(MENU)
        scelta = input("Scelta: ").strip()
        if scelta == "8":
            print("Arrivederci!")
            break
        azione = AZIONI.get(scelta)
        if azione:
            azione()  # <-- Corretto da "action()" a "azione()"
        else:
            print("Scelta non valida.")

if __name__ == "__main__":
    main()