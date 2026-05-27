#   =====================
#      LORENZO BARBATO
#   =====================

import random
import math
import json
import os
import time
from datetime import datetime, timedelta

# Costanti di Configurazione
TARIFFA_ORARIA = 2.0      # €/ora
TIPO_TARIFFA = "oraria"   # "oraria" | "scatti"
SCATTO_MINUTI = 30        
CAPIENZA = 20
FILE_STORICO = "Esame Python/storico.json"

class Ticket:
    def __init__(self, id_ticket: str, targa: str, ingresso: datetime, posto: int, uscita: datetime | None = None) -> None:
        self.id_ticket = id_ticket
        self.targa = targa
        self.ingresso = ingresso
        self.posto = posto
        self.uscita = uscita  

    @property
    def durata(self) -> timedelta | None:
        """Restituisce la durata se il ticket è chiuso, altrimenti None."""
        if self.uscita is None:
            return None
        return self.uscita - self.ingresso
    
    @property
    def importo(self) -> float | None:
        """Restituisce l'importo dovuto se il ticket è chiuso, altrimenti None."""
        if self.durata is None:  
            return None
        
        ore = self.durata.total_seconds() / 3600
        
        if TIPO_TARIFFA == 'oraria':
            return round(ore * TARIFFA_ORARIA, 2)
        else:
            scatti = math.ceil(ore * 60 / SCATTO_MINUTI)
            return round(scatti * TARIFFA_ORARIA, 2)
    
    def to_dict(self) -> dict:
        """Serializza il ticket escludendo la durata per evitare dati ridondanti."""
        return {
            "id_ticket": self.id_ticket,
            "targa": self.targa,
            "ingresso": self.ingresso.isoformat(),
            "uscita": self.uscita.isoformat() if self.uscita else None,
            "posto": self.posto,
            "importo": self.importo  
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Ticket':
        """Ricostruisce l'oggetto Ticket dal dizionario salvato nel JSON."""
        return cls(
            id_ticket=data["id_ticket"],
            targa=data["targa"],
            ingresso=datetime.fromisoformat(data["ingresso"]),
            posto=data["posto"],
            uscita=datetime.fromisoformat(data["uscita"]) if data["uscita"] else None
        )
    
    def stampa_riepilogo(self) -> None:
        print(f"Ticket ID: {self.id_ticket}")
        print(f"Targa: {self.targa}")
        print(f"Posto Assegnato: {self.posto}")
        print(f"Ingresso: {self.ingresso.strftime('%Y-%m-%d %H:%M:%S')}")
        if self.uscita:
            print(f"Uscita: {self.uscita.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Durata sosta: {self.durata}")
            print(f"Importo dovuto: €{self.importo:.2f}")
        else:
            print("Stato: Veicolo ancora in parcheggio")


class Parcheggio:
    def __init__(self) -> None:
        self.capienza = CAPIENZA 
        self.posti_occupati: set[int] = set() 
        self.ticket_aperti: dict[str, Ticket] = {} 
        self.storico: list[dict] = [] 
        self.max_veicoli_presenti = 0 

    @property
    def posti_liberi(self) -> int:
        return self.capienza - len(self.posti_occupati)

    @property
    def e_pieno(self) -> bool:
        return self.posti_liberi == 0
     
    def assegna_posto(self) -> int:
        if self.e_pieno:
            raise ValueError("Impossibile assegnare un posto: il parcheggio è pieno!")
        
        posti_disponibili = [p for p in range(1, self.capienza + 1) if p not in self.posti_occupati]
        posto = random.choice(posti_disponibili)
        
        self.posti_occupati.add(posto)
        
        if len(self.posti_occupati) > self.max_veicoli_presenti:
            self.max_veicoli_presenti = len(self.posti_occupati)
            
        return posto
    
    def libera_posto(self, posto: int) -> None:
        if posto in self.posti_occupati:
            self.posti_occupati.remove(posto)
        else:
            raise ValueError(f"Il posto {posto} risulta già libero.")

    def mostra_stato(self) -> None:
        print("\n--- STATO PARCHEGGIO ---")
        print(f"Capienza Totale: {self.capienza}")
        print(f"Posti Liberi   : {self.posti_liberi}")
        print(f"Posti Occupati : {len(self.posti_occupati)}")
        print(f"Ticket Aperti  : {len(self.ticket_aperti)}")
        print("------------------------")


class GestoreParcheggio:
    def __init__(self) -> None:
        self.parcheggio = Parcheggio()
        self.carica_dati()  

    def nuovo_ingresso(self) -> None:
        """Registra l'ingresso di un veicolo, stampa su file e aggiorna lo stato."""
        targa = input("Inserisci la targa del veicolo: ").strip().upper()
        if not targa:
            print("❌ Errore: La targa non può essere vuota.")
            return

        if targa in self.parcheggio.ticket_aperti:
            print(f"❌ Errore: Il veicolo con targa {targa} ha già un ticket aperto!")
            return

        try:
            posto = self.parcheggio.assegna_posto()
            orario_attuale = datetime.now()
            id_ticket = f"TICK-{orario_attuale.strftime('%H%M%S')}-{random.randint(100, 999)}"
            
            nuovo_ticket = Ticket(id_ticket, targa, orario_attuale, posto)
            self.parcheggio.ticket_aperti[targa] = nuovo_ticket
            
            # Stampa su file
            self._scrivi_ticket_su_file(id_ticket, targa, posto, orario_attuale)
            
            print(f"\nIngresso registrato! Ticket generato su file.")
            nuovo_ticket.stampa_riepilogo()
            self.salva_dati()
            
        except ValueError as e:
            print(f"Errore: {e}")

    def nuova_uscita(self) -> None:
        targa = input("Inserisci la targa del veicolo in uscita: ").strip().upper()
        
        if targa not in self.parcheggio.ticket_aperti:
            print(f"Errore: Targa non trovata tra i ticket aperti. Uscita rifiutata.")
            return

        ticket = self.parcheggio.ticket_aperti.pop(targa)
        ticket.uscita = datetime.now()
        
        self.parcheggio.libera_posto(ticket.posto)
        self.parcheggio.storico.append(ticket.to_dict())
        
        print("\nVeicolo uscito! Ecco il riepilogo del pagamento:")
        ticket.stampa_riepilogo()
        self.salva_dati()

    def mostra_ticket_aperti(self) -> None:
        print("\n--- TICKETS APERTI IN QUESTO MOMENTO ---")
        if not self.parcheggio.ticket_aperti:
            print("Nessun veicolo presente nel parcheggio.")
            return
        
        for targa, ticket in self.parcheggio.ticket_aperti.items():
            print(f"• Targa: {targa} | Posto: {ticket.posto} | Ingresso: {ticket.ingresso.strftime('%H:%M:%S')}")

    def mostra_rendiconto(self) -> None:
        tot_chiusi = len(self.parcheggio.storico)
        tot_aperti = len(self.parcheggio.ticket_aperti)
        tot_emessi = tot_chiusi + tot_aperti
        
        incasso_totale = sum(tk["importo"] for tk in self.parcheggio.storico if tk["importo"] is not None)
        
        durate_secondi = []
        for tk in self.parcheggio.storico:
            if tk["uscita"] and tk["ingresso"]:
                delta = datetime.fromisoformat(tk["uscita"]) - datetime.fromisoformat(tk["ingresso"])
                durate_secondi.append(delta.total_seconds())
        
        media_secondi = sum(durate_secondi) / tot_chiusi if tot_chiusi > 0 else 0
        durata_media = timedelta(seconds=int(media_secondi))

        print("\n================ RENDICONTAZIONE FINALE ================")
        print(f"Numero totale ticket emessi            : {tot_emessi}")
        print(f"Numero ticket chiusi                   : {tot_chiusi}")
        print(f"Numero ticket ancora aperti            : {tot_aperti}")
        print(f"Incasso totale                         : €{incasso_totale:.2f}")
        print(f"Durata media delle soste               : {durata_media}")
        print(f"Massimo posti occupati simultaneamente : {self.parcheggio.max_veicoli_presenti}")
        print("========================================================")

    def esegui_test_automatico(self) -> None:
        """Genera automaticamente 5 ingressi e 5 uscite con orari falsati per testare il sistema."""
        print("\n Avvio simulazione di test automatico (Criteri di accettazione)...")
        
        # Reset pulito dello stato attuale per il test (opzionale, ma consigliato per dati precisi)
        self.parcheggio = Parcheggio()
        if os.path.exists(FILE_STORICO):
            os.remove(FILE_STORICO)
            
        targhe_test = ["AA123BB", "CC456DD", "EE789FF", "GG012HH", "II345JJ"]
        orario_base = datetime.now() - timedelta(days=1) # Inizia da ieri per simulare ore reali
        
        # 1. Simula 5 Ingressi a intervalli di tempo diversi
        print("\n--- Fase 1: Generazione di 5 Ingressi automatici ---")
        for i, targa in enumerate(targhe_test):
            posto = self.parcheggio.assegna_posto()
            id_ticket = f"TEST-{i:02d}-{random.randint(100, 999)}"
            
            # Falsiamo l'orario di ingresso (ogni auto entra 1 ora dopo la precedente)
            orario_ingresso = orario_base + timedelta(hours=i)
            
            nuovo_ticket = Ticket(id_ticket, targa, orario_ingresso, posto)
            self.parcheggio.ticket_aperti[targa] = nuovo_ticket
            
            self._scrivi_ticket_su_file(id_ticket, targa, posto, orario_ingresso)
            print(f"  [INGRESSO] Auto {targa} assegnata al posto {posto} alle {orario_ingresso.strftime('%H:%M:%S')}")
        
        # 2. Simula 5 Uscite con calcolo della sosta
        print("\n--- Fase 2: Generazione di 5 Uscite automatiche con calcolo tariffe ---")
        # Cambiamo l'ordine di uscita rispetto all'ingresso per rendere il test più realistico
        random.shuffle(targhe_test) 
        
        for i, targa in enumerate(targhe_test):
            ticket = self.parcheggio.ticket_aperti.pop(targa)
            
            # Falsiamo l'orario di uscita aggiungendo ore casuali all'orario di ingresso
            ore_di_sosta = random.randint(1, 5) + 0.5  # es. 2.5 ore, 4.5 ore...
            ticket.uscita = ticket.ingresso + timedelta(hours=ore_di_sosta)
            
            self.parcheggio.libera_posto(ticket.posto)
            self.parcheggio.storico.append(ticket.to_dict())
            
            print(f"  [USCITA] Auto {targa} rimasta {ticket.durata} -> Importo calcolato: €{ticket.importo}")

        # Salva i dati della simulazione
        self.salva_dati()
        print("\nTest automatico completato con successo! Lo storico è stato salvato.")
        print("Puoi selezionare l'opzione 5 dal menu per vedere il rendiconto complessivo del test.")

    def _scrivi_ticket_su_file(self, id_ticket: str, targa: str, posto: int, orario: datetime) -> None:
            """Metodo privato di supporto per salvare fisicamente il file del ticket nella stessa cartella del JSON."""
            # Estrae la cartella (es. "Esame Python") dal percorso del file storico
            cartella_destinazione = os.path.dirname(FILE_STORICO)
            
            # Se la costante contiene una cartella (non è una stringa vuota), si assicura che esista
            if cartella_destinazione:
                os.makedirs(cartella_destinazione, exist_ok=True)
                nome_file_ticket = os.path.join(cartella_destinazione, f"ticket_{id_ticket}.txt")
            else:
                nome_file_ticket = f"ticket_{id_ticket}.txt"

            with open(nome_file_ticket, "w", encoding="utf-8") as f:
                f.write(f"=== TICKET DI INGRESSO ===\n")
                f.write(f"Ticket ID: {id_ticket}\n")
                f.write(f"Targa    : {targa}\n")
                f.write(f"Posto    : {posto}\n")
                f.write(f"Ingresso : {orario.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"==========================\n")

    def salva_dati(self) -> None:
        aperti_serializzati = {targa: tk.to_dict() for targa, tk in self.parcheggio.ticket_aperti.items()}
        struttura_dati = {
            "max_veicoli_presenti": self.parcheggio.max_veicoli_presenti,
            "storico": self.parcheggio.storico,
            "ticket_aperti": aperti_serializzati
        }
        with open(FILE_STORICO, "w", encoding="utf-8") as f:
            json.dump(struttura_dati, f, indent=4)

    def carica_dati(self) -> None:
        if not os.path.exists(FILE_STORICO):
            return
        try:
            with open(FILE_STORICO, "r", encoding="utf-8") as f:
                dati = json.load(f)
            self.parcheggio.max_veicoli_presenti = dati.get("max_veicoli_presenti", 0)
            self.parcheggio.storico = dati.get("storico", [])
            aperti_raw = dati.get("ticket_aperti", {})
            for targa, ticket_data in aperti_raw.items():
                ticket_obj = Ticket.from_dict(ticket_data)
                self.parcheggio.ticket_aperti[targa] = ticket_obj
                self.parcheggio.posti_occupati.add(ticket_obj.posto)
        except Exception as e:
            print(f"⚠️ Errore nel caricamento dei dati salvati ({e}). Avvio con parcheggio vuoto.")

    def mostra_menu(self) -> None:
        while True:
            print("\n=== MENU UTENTE ===")
            print("1. Nuovo ingresso")
            print("2. Nuova uscita")
            print("3. Mostra stato parcheggio")
            print("4. Mostra ticket aperti")
            print("5. Mostra rendiconto")
            print("6. [TEST] Esegui simulazione automatica (5 ingressi/uscite)")
            print("7. Esci")
            
            scelta = input("\nSeleziona un'opzione (1-7): ").strip()
            
            if scelta == "1":
                self.nuovo_ingresso()
            elif scelta == "2":
                self.nuova_uscita()
            elif scelta == "3":
                self.parcheggio.mostra_stato()
            elif scelta == "4":
                self.mostra_ticket_aperti()
            elif scelta == "5":
                self.mostra_rendiconto()
            elif scelta == "6":
                self.esegui_test_automatico()
            elif scelta == "7":
                print("\nUscita dal programma. Arrivederci!")
                break
            else:
                print("Opzione non valida. Riprova.")

if __name__ == "__main__":
    gestore = GestoreParcheggio()
    gestore.mostra_menu()