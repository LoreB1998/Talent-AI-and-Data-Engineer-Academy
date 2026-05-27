import random
import math

# -------------------------
#          LIBRO
# -------------------------

class Libro:
    def __init__(self, libro_id:str, titolo:str, disponibile:bool = True) -> None:
        self.libro_id = libro_id
        self.titolo = titolo
        self.disponibile = disponibile
        self.in_manutenzione = False
    
    def __str__(self) -> str:
        return f"ID: {self.libro_id} • Titolo: {self.titolo} • Disponibile {'Si' if self.disponibile else 'No'}"
    
class LibroFisico(Libro):
    def __init__(self, libro_id: str, titolo: str, disponibile: bool = True, peso_grammi: float = 0.0) -> None:
        super().__init__(libro_id, titolo, disponibile)
        self.peso_grammi = peso_grammi
    
    def __str__(self) -> str:
        return f"{super().__str__()} • Peso: {self.peso_grammi}g"

class LibroRaro(Libro):
    ANNI_ISCRIZIONE_MINIMI = 2

    def __init__(self, libro_id: str, titolo: str, disponibile: bool, valore_assicurativo_euro: float) -> None:
        super().__init__(libro_id, titolo, disponibile)
        self.valore_assicurativo_euro = valore_assicurativo_euro

    def __str__(self) -> str:
        return f"{super().__str__()} • Valore Assicurativo: {self.valore_assicurativo_euro}€"

# -------------------------
#         ANAGRAFICA
# -------------------------
    
class Anagrafica:
    def __init__(self, persona_id: str, nome: str, cognome: str) -> None:
        self.persona_id = persona_id
        self.nome = nome
        self.cognome = cognome
    
    @property
    def nome_completo(self) -> str:
        return f"{self.nome} {self.cognome}"
    
    def __str__(self) -> str:
        return f"ID: {self.persona_id} • Nome: {self.nome_completo}"

class Socio(Anagrafica):
    def __init__(self, socio_id: str, nome: str, cognome: str, anni_iscrizione: int) -> None:
        super().__init__(socio_id, nome, cognome)
        self.socio_id = socio_id
        self.anni_iscrizione = anni_iscrizione
        self.prestiti = []
        self.attivo = True
        self.bibliotecario = None
    
    def puo_prendere(self, libro: Libro) -> bool:
        """
        Un socio può prendere un libro se il libro è disponibile, 
        e può prendere un libro raro solo se è iscritto da almeno 2 anni.
        """
        if not libro.disponibile:
            return False
        if isinstance(libro, LibroRaro) and self.anni_iscrizione < LibroRaro.ANNI_ISCRIZIONE_MINIMI:
            return False
        return True

    def __str__(self) -> str:
        return f"{super().__str__()} • Anni Iscrizione: {self.anni_iscrizione} • Prestiti: {len(self.prestiti)} • Attivo {'Si' if self.attivo else 'No'}"
    
class Bibliotecario(Anagrafica):
    def __init__(self, bibliotecario_id: str, nome: str, cognome: str, matricola: str) -> None:
        super().__init__(bibliotecario_id, nome, cognome)
        self.matricola = matricola
        self.prestiti_gestiti = []
    
    def __str__(self) -> str:
        return f"{super().__str__()} • Matricola: {self.matricola}"
    
# -------------------------
#         PRESTITO
# -------------------------

class Prestito:
    def __init__(self, prestito_id: str, socio: Socio, libro: Libro, bibliotecario: Bibliotecario, durata_giorni: int) -> None:
        if not libro.disponibile:
            raise ValueError(f"Il libro '{libro.titolo}' non è disponibile per il prestito.")
        if not socio.puo_prendere(libro):
            raise ValueError(f"Il socio '{socio.nome_completo}' non può prendere in prestito il libro '{libro.titolo}'.")

        self.prestito_id = prestito_id
        self.socio = socio
        self.libro = libro
        self.bibliotecario = bibliotecario
        self.durata_giorni = durata_giorni
        libro.disponibile = False
    
    def __str__(self) -> str:
        return f"ID Prestito: {self.prestito_id} • Socio: {self.socio.nome_completo} • Libro: {self.libro.titolo} • Bibliotecario: {self.bibliotecario.nome_completo} • Durata: {self.durata_giorni} giorni"
    
# -------------------------
#         BIBLIOTECA
# -------------------------

class GiornataBiblioteca:
    def __init__(self) -> None:
        self.prestiti = []
    
    def metti_in_manutenzione(self, libri: list[Libro], perc_in_manutenzione: float) -> None:
        """Mette una parte dei libri in manutenzione, rendendoli non disponibili."""
        for libro in libri:
            libro.disponibile = True
            libro.in_manutenzione = False
        
        n_manutenzione = math.ceil(len(libri) * perc_in_manutenzione)
        libri_manutenzione = random.sample(libri, n_manutenzione)
        for libro in libri_manutenzione:
            libro.in_manutenzione = True
            libro.disponibile = False

    def assegna_bibliotecari(self, bibliotecari: list, soci: list):
        """Assegna un bibliotecario a ciascun socio attivo in modo bilanciato."""
        soci_attivi = [s for s in soci if s.attivo]
        if not soci_attivi:
            raise ValueError("Non ci sono soci attivi a cui assegnare un bibliotecario.")
        for i, socio in enumerate(soci_attivi):
            socio.bibliotecario = bibliotecari[i % len(bibliotecari)]
        
    def genera_prestiti(self, soci: list, libri: list,
                        n_per_socio: int) -> "GiornataBiblioteca":
        """Genera prestiti casuali rispettando disponibilità e vincoli per socio."""
        self.prestiti = []
        contatore = 1
        libri_disponibili = [l for l in libri if l.disponibile and not l.in_manutenzione]
 
        for socio in soci:
            if not socio.attivo or socio.bibliotecario is None:
                continue
 
            k_sample = min(n_per_socio, len(libri_disponibili))
            if k_sample == 0:
                continue
 
            candidati = [l for l in libri_disponibili if socio.puo_prendere(l)]
            k_sample = min(n_per_socio, len(candidati))
            if k_sample == 0:
                continue
 
            scelti = random.sample(candidati, k_sample)
 
            for libro in scelti:
                durata = random.randint(7, 30)
                p = Prestito(
                    prestito_id   = f"PRS{contatore:03d}",
                    socio         = socio,
                    libro         = libro,
                    bibliotecario = socio.bibliotecario,
                    durata_giorni = durata
                )
                socio.prestiti.append(p)
                socio.bibliotecario.prestiti_gestiti.append(p)
                self.prestiti.append(p)
                libri_disponibili.remove(libro)
                contatore += 1
 
        return self
 
 
# ─────────────────────────────────────────
# CLASSI DI VISUALIZZAZIONE
# ─────────────────────────────────────────
 
class VisualizzazioneSocio:
    """Report per i soci: lista dei prestiti del giorno."""
 
    def __init__(self, soci: list):
        self.soci = [s for s in soci if s.attivo and s.prestiti]
 
    def genera_report(self) -> str:
        linee = []
        linee.append("\n" + "="*85)
        linee.append(" REPORT SOCI - PRESTITI GIORNALIERI ".center(85, "═"))
        linee.append("="*85)
 
        for s in self.soci:
            linee.append(f"\nSOCIO:         {s.nome_completo:<30} | ID: {s.socio_id}")
            linee.append(f"ISCRIZIONE:    {s.anni_iscrizione} anni")
            linee.append(f"BIBLIOTECARIO: {s.bibliotecario.nome_completo}")
            linee.append("   " + "-"*75)
            linee.append(f"   {'ID':<10} | {'Titolo':<30} | {'Tipo':<15} | {'Durata':<10}")
            linee.append("   " + "-"*75)
 
            for p in s.prestiti:
                tipo = p.libro.__class__.__name__
                linee.append(f"   {p.prestito_id:<10} | {p.libro.titolo:<30} | {tipo:<15} | {p.durata_giorni} giorni")
 
            linee.append("   " + "-"*75)
            linee.append(f"   Totale prestiti: {len(s.prestiti)}")
            linee.append("   " + "-"*75)
 
        linee.append("\n" + "="*85)
        return "\n".join(linee)
 
 
class VisualizzazioneBibliotecario:
    """Report per i bibliotecari: riepilogo prestiti gestiti."""
 
    def __init__(self, bibliotecari: list):
        self.bibliotecari = bibliotecari
 
    def genera_report(self) -> str:
        linee = []
        linee.append("\n" + "="*85)
        linee.append(" REPORT BIBLIOTECARI - RIEPILOGO GIORNALIERO ".center(85, "═"))
        linee.append("="*85)
 
        for b in self.bibliotecari:
            linee.append(f"\nBIBLIOTECARIO: {b.nome_completo:<30} | Matricola: {b.matricola}")
            linee.append("   " + "-"*75)
 
            if not b.prestiti_gestiti:
                linee.append("   Nessun prestito gestito oggi.")
                linee.append("   " + "-"*75)
                continue
 
            linee.append(f"   {'ID Prestito':<12} | {'Socio':<25} | {'Titolo':<25} | {'Durata'}")
            linee.append("   " + "-"*75)
 
            soci_seguiti = set()
            for p in b.prestiti_gestiti:
                soci_seguiti.add(p.socio.nome_completo)
                linee.append(
                    f"   {p.prestito_id:<12} | {p.socio.nome_completo:<25} | "
                    f"{p.libro.titolo:<25} | {p.durata_giorni} giorni"
                )
 
            linee.append("   " + "-"*75)
            linee.append(f"   Prestiti gestiti: {len(b.prestiti_gestiti)} | Soci seguiti: {len(soci_seguiti)}")
            linee.append("   " + "-"*75)
 
        linee.append("\n" + "="*85)
        return "\n".join(linee)
 
 
# ─────────────────────────────────────────
# GENERAZIONE DATI CASUALI
# ─────────────────────────────────────────
 
def genera_libri(n: int) -> list:
    titoli = [
        "Il Nome della Rosa", "1984", "Cent'anni di solitudine", "Il Processo",
        "Delitto e Castigo", "Don Chisciotte", "Moby Dick", "Anna Karenina",
        "Orgoglio e Pregiudizio", "Il Signore degli Anelli", "Lolita", "Ulisse",
        "La Metamorfosi", "Madame Bovary", "Guerra e Pace", "I Miserabili",
        "Frankenstein", "Il Grande Gatsby", "Cime Tempestose", "Jane Eyre"
    ]
    libri = []
    for i in range(n):
        libro_id = f"LIB{i+1:03d}"
        titolo = random.choice(titoli) + f" (Vol.{i+1})"
        tipo = random.choices(["fisico", "raro"], weights=[0.75, 0.25])[0]
        if tipo == "fisico":
            libri.append(LibroFisico(libro_id, titolo, peso_grammi=random.randint(200, 1200)))
        else:
            libri.append(LibroRaro(libro_id=libro_id, titolo=titolo, disponibile=True, valore_assicurativo_euro=round(random.uniform(500, 5000), 2)))
    return libri
 
 
def genera_soci(n: int) -> list:
    nomi = ["Luca", "Sara", "Marco", "Anna", "Giulia", "Paolo", "Elena", "Matteo", "Chiara", "Roberto"]
    cognomi = ["Rossi", "Bianchi", "Ferrari", "Esposito", "Conti", "Ricci", "Marino", "Greco", "Bruno", "Costa"]
    soci = []
    for i in range(n):
        soci.append(Socio(
            socio_id        = f"SOC{i+1:03d}",
            nome            = random.choice(nomi),
            cognome         = random.choice(cognomi),
            anni_iscrizione = random.randint(0, 10)
        ))
    return soci
 
 
def genera_bibliotecari(n: int) -> list:
    nomi = ["Giorgio", "Marta", "Filippo", "Laura", "Nicola"]
    cognomi = ["Fontana", "Villa", "Serra", "Colombo", "Ferrara"]
    bibliotecari = []
    for i in range(n):
        bibliotecari.append(Bibliotecario(
            bibliotecario_id = f"BIB{i+1:02d}",
            nome             = random.choice(nomi),
            cognome          = random.choice(cognomi),
            matricola        = f"MAT{random.randint(1000,9999)}"
        ))
    return bibliotecari
 
 
# ─────────────────────────────────────────
# MAIN SIMULAZIONE
# ─────────────────────────────────────────
 
if __name__ == "__main__":
    random.seed(42)
 
    libri        = genera_libri(n=60)
    soci         = genera_soci(n=15)
    bibliotecari = genera_bibliotecari(n=3)
 
    giornata = GiornataBiblioteca()
    giornata.metti_in_manutenzione(libri, perc_in_manutenzione=0.10)
    giornata.assegna_bibliotecari(bibliotecari, soci)
    giornata.genera_prestiti(soci, libri, n_per_socio=3)
 
    vista_soci    = VisualizzazioneSocio(soci)
    vista_biblio  = VisualizzazioneBibliotecario(bibliotecari)
 
    report_soci   = vista_soci.genera_report()
    report_biblio = vista_biblio.genera_report()
 
    print(report_soci)
    print(report_biblio)
