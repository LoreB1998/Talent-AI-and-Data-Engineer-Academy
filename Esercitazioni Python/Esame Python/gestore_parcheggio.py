from parcheggio import Parcheggio
from ticket import Ticket
from datetime import datetime, timedelta
import json
import os
import random
import qrcode  
from config import FILE_STORICO

class GestoreParcheggio:
    def __init__(self) -> None:
        self.parcheggio = Parcheggio()
        self.carica_dati()  
    
    def _targa_valida(self, targa: str) -> bool:
        """Verifica che la targa sia nel formato AA000AA."""
        if len(targa) != 7:
            return False
        if not targa[:2].isalpha():
            return False
        if not targa[2:5].isdigit():
            return False
        if not targa[5:].isalpha():
            return False
        return True

    def nuovo_ingresso(self) -> None: 
        """Registra l'ingresso di un veicolo, stampa su file, genera QR Code e aggiorna lo stato."""
        targa = input("Inserisci la targa del veicolo (formato AA000AA): ").strip().upper()
        if not targa:
            print("Errore: La targa non può essere vuota.")
            return

        if not self._targa_valida(targa):
            print("Errore: La targa non è nel formato corretto (AA000AA).")
            return

        if targa in self.parcheggio.ticket_aperti:
            print(f"Errore: Il veicolo con targa {targa} ha già un ticket aperto!")
            return

        try:
            posto = self.parcheggio.assegna_posto()
            orario_attuale = datetime.now()
            id_ticket = f"TICK-{orario_attuale.strftime('%H%M%S')}-{random.randint(100, 999)}"
            
            nuovo_ticket = Ticket(id_ticket, targa, orario_attuale, posto)
            self.parcheggio.ticket_aperti[targa] =  nuovo_ticket
            
            self._scrivi_ticket_su_file(id_ticket, targa, posto, orario_attuale)
            
            print(f"\nIngresso registrato! Ticket generato con successo.")
            nuovo_ticket.stampa_riepilogo()
            
            print("\n[ SCANSIONA IL QR CODE DAL TERMINALE ]")
            qr_console = qrcode.QRCode()
            qr_console.add_data(nuovo_ticket.dati_qr())
            qr_console.print_ascii(invert=True)
            
            self.salva_dati()
            
        except ValueError as e:
            print(f"Errore: {e}")

    def nuova_uscita(self) -> None:
        """Registra l'uscita del veicolo, calcola la tariffa e archivia il ticket."""
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
        """Mostra la lista dei veicoli attualmente presenti nel parcheggio."""
        print("\n--- TICKETS APERTI IN QUESTO MOMENTO ---")
        if not self.parcheggio.ticket_aperti:
            print("Nessun veicolo presente nel parcheggio.")
            return
        
        for targa, ticket in self.parcheggio.ticket_aperti.items():
            print(f"• Targa: {targa} | Posto: {ticket.posto} | Ingresso: {ticket.ingresso.strftime('%Y-%m-%d %H:%M:%S')}")

    def mostra_rendiconto(self) -> None:
        """Genera le statistiche di rendicontazione richieste dai criteri di accettazione."""
        tot_chiusi = len(self.parcheggio.storico)
        tot_aperti = len(self.parcheggio.ticket_aperti)
        tot_emessi = tot_chiusi + tot_aperti
        
        incasso_totale = sum(tk["importo"] for tk in self.parcheggio.storico if tk.get("importo") is not None)
        
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
    
    def cerca_ticket_per_targa(self) -> None:
        """Cerca un ticket attivo o archiviato tramite la targa del veicolo."""
        targa = input("Inserisci la targa da cercare: ").strip().upper()
        
        if targa in self.parcheggio.ticket_aperti:
            print("\nTICKET TROVATO (Attivo in parcheggio):")
            self.parcheggio.ticket_aperti[targa].stampa_riepilogo()
            return
            
        ticket_trovati_storico = [tk for tk in self.parcheggio.storico if tk["targa"] == targa]
        
        if ticket_trovati_storico:
            print(f"\nTROVATI {len(ticket_trovati_storico)} TICKET PASSATI NEL RECENTE STORICO:")
            for tk_data in reversed(ticket_trovati_storico):
                ticket_obj = Ticket.from_dict(tk_data)
                ticket_obj.stampa_riepilogo()
                print("-" * 30)
        else:
            print(f"\nNessun ticket trovato per la targa {targa}.")

    def _scrivi_ticket_su_file(self, id_ticket: str, targa: str, posto: int, orario: datetime) -> None:
        """Esporta il ticket in formato testuale e genera l'immagine PNG del QR Code."""
        cartella_destinazione = os.path.dirname(FILE_STORICO)
        cartella_biglietti = os.path.join(cartella_destinazione, "elenco_biglietti")
        os.makedirs(cartella_biglietti, exist_ok=True)
        
        nome_file_ticket = os.path.join(cartella_biglietti, f"ticket_{id_ticket}.txt")
        with open(nome_file_ticket, "w", encoding="utf-8") as f:
            f.write(f"=== TICKET DI INGRESSO ===\n")
            f.write(f"Ticket ID: {id_ticket}\n")
            f.write(f"Targa    : {targa}\n")
            f.write(f"Posto    : {posto}\n")
            f.write(f"Ingresso : {orario.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"==========================\n")

        ticket_obj = self.parcheggio.ticket_aperti[targa]
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=1,  
            box_size=10,
            border=4,
        )
        qr.add_data(ticket_obj.dati_qr())
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        nome_file_qr = os.path.join(cartella_biglietti, f"qrcode_{id_ticket}.png")
        
        with open(nome_file_qr, "wb") as f_img:
            img.save(f_img)
        
        print(f"QR Code salvato come immagine: {nome_file_qr}")

    def salva_dati(self) -> None:
        """Salva lo stato corrente dell'applicazione in un file JSON."""
        aperti_serializzati = {targa: tk.to_dict() for targa, tk in self.parcheggio.ticket_aperti.items()}
        struttura_dati = {
            "max_veicoli_presenti": self.parcheggio.max_veicoli_presenti,
            "storico": self.parcheggio.storico,
            "ticket_aperti": aperti_serializzati
        }
        with open(FILE_STORICO, "w", encoding="utf-8") as f:
            json.dump(struttura_dati, f, indent=4)

    def carica_dati(self) -> None:
        """Ripristina lo stato dell'applicazione caricando i dati dal file JSON."""
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
            print(f"Errore nel caricamento dei dati salvati ({e}). Avvio con parcheggio vuoto.")

    def mostra_menu(self) -> None:
        """Menu interattivo per la gestione del parcheggio."""
        while True:
            print("\n=== MENU UTENTE ===")
            print("1. Nuovo ingresso")
            print("2. Nuova uscita")
            print("3. Mostra stato parcheggio")
            print("4. Mostra ticket aperti")
            print("5. Mostra rendiconto")
            print("6. Cerca ticket per targa")
            print("0. Esci")
            
            scelta = input("\nSeleziona un'opzione 1-6 (0 per uscire): ").strip()
            
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
                self.cerca_ticket_per_targa()
            elif scelta == "0":
                print("\nUscita dal programma. Arrivederci!")
                break
            else:
                print("Opzione non valida. Riprova.")