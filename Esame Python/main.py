from gestore_parcheggio import GestoreParcheggio
from ticket import Ticket
from datetime import datetime, timedelta

def esegui_test_automatico(gestore: GestoreParcheggio) -> None:
    """
    Esegue una simulazione automatica di 5 ingressi e 5 uscite
    per verificare i criteri di accettazione del sistema.
    """
    print("\n" + "="*50)
    print("AVVIO SIMULAZIONE AUTOMATICA (5 INGRESSI / 5 USCITE)")
    print("="*50)

    # Lista di targhe fittizie per il test
    targhe_test = ["AA111AA", "BB222BB", "CC333CC", "DD444DD", "EE555EE"]
    
    print("\n--- FASE 1: INGRESSO DI 5 VEICOLI ---")
    orario_base = datetime.now()
    
    for i, targa in enumerate(targhe_test):
        print(f"\n[Test] Registrazione ingresso per targa: {targa}")
        
        posto = gestore.parcheggio.assegna_posto()
        id_ticket = f"TICK-TEST-{i+1:03d}"
        
        # Sfasamento degli ingressi di 45 minuti l'uno dall'altro per avere dati realistici nel rendiconto
        orario_ingresso = orario_base - timedelta(minutes=45 * (5 - i))
        
        nuovo_ticket = Ticket(id_ticket, targa, orario_ingresso, posto)
        gestore.parcheggio.ticket_aperti[targa] = nuovo_ticket
        
        # Scrittura del file di testo del singolo ticket e salvataggio dello stato
        gestore._scrivi_ticket_su_file(id_ticket, targa, posto, orario_ingresso)
        nuovo_ticket.stampa_riepilogo()
        
    gestore.salva_dati()
    print(f"\nStato del parcheggio dopo gli ingressi: {gestore.parcheggio.posti_liberi} posti liberi.")

    print("\n--- FASE 2: USCITA DI 5 VEICOLI ---")
    orario_uscita_base = datetime.now()
    
    for i, targa in enumerate(targhe_test):
        print(f"\n[Test] Registrazione uscita per targa: {targa}")
        
        if targa not in gestore.parcheggio.ticket_aperti:
            print(f"Errore inaspettato: Targa {targa} non trovata.")
            continue
            
        ticket = gestore.parcheggio.ticket_aperti.pop(targa)
        
        # Sfasiamo anche le uscite per generare durate di sosta variabili
        ticket.uscita = orario_uscita_base + timedelta(minutes=20 * i)
        
        gestore.parcheggio.libera_posto(ticket.posto)
        gestore.parcheggio.storico.append(ticket.to_dict())
        
        ticket.stampa_riepilogo()
        
    gestore.salva_dati()
    print("\n" + "="*50)
    print("SIMULAZIONE COMPLETATA CON SUCCESSO!")
    print("="*50 + "\n")


if __name__ == "__main__":
    gestore = GestoreParcheggio()
    
    while True:
        print("\n=== MENU PRINCIPALE DI AVVIO ===")
        print("1. Apri l'interfaccia di gestione standard (Menu Utente)")
        print("2. Esegui il Test Automatico (5 Ingressi/Uscite)")
        print("0. Esci")
        
        scelta = input("\nSeleziona un'opzione 1-3 (0 per uscire): ").strip()
        
        if scelta == "1":
            gestore.mostra_menu()
        elif scelta == "2":
            esegui_test_automatico(gestore)
            print("\nGenerazione automatica del rendiconto post-test:")
            gestore.mostra_rendiconto()
        elif scelta == "0":
            print("\nChiusura del programma.")
            break
        else:
            print("Opzione non valida. Riprova.")