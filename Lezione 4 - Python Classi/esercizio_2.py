class ContoCorrente:
    def __init__(self, intestatario: str, cf: str, saldo_iniziale: float):
        self.intestatario = intestatario
        self.cf = cf.upper()
        self.saldo_iniziale = saldo_iniziale
    
    def deposita(self, importo):
        if importo > 0:
            self.saldo_iniziale += importo
            print(f"Ciao {self.intestatario}, hai depositato {importo}€, nel conto hai: {self.saldo_iniziale}€")
        else:
            print("Non puoi depositare valori negativi")
    
    def prelievo(self, importo):
        if self.saldo_iniziale >= importo:
            self.saldo_iniziale -= importo
            print(f"Ciao {self.intestatario}, hai prelevato {importo}€, nel conto hai: {self.saldo_iniziale}€")
        else:
            print(f"{self.intestatario} nel tuo conto hai: {self.saldo_iniziale}€, non puoi prelevare {importo}€!")
    
    def stampa(self):
        print(f"Il conto di {self.intestatario} (CF: {self.cf}): {self.saldo_iniziale}€")


banca = dict()
programma_attivo = True  # Questo flag controllerà la vita del ciclo principale

print("=== SISTEMA BANCARIO AUTOMATIZZATO ===")

while programma_attivo:
    print("\n" + "=" * 40)
    cf_utente = input("Inserisci il codice fiscale o 0 per uscire dal programma: ").strip().upper()

    if cf_utente == "0":
        programma_attivo = False
        break  # Interrompe il ciclo principale ed esce

    if cf_utente in banca:
        conto_corrente = banca[cf_utente]
        print(f"Bentornato, {conto_corrente.intestatario}!")

        while True:
            print("\n--- OPERAZIONI DISPONIBILI ---")
            print("1. Deposita")
            print("2. Preleva")
            print("3. Mostra Saldo")
            print("4. Cambia utente (Torna al menu principale)")
            print("5. Chiudi del tutto il programma")
            scelta = input("Seleziona un'operazione (1-5): ").strip()
        
            if scelta == "1":
                valore = float(input("Inserisci l'importo da depositare: "))
                conto_corrente.deposita(valore)
            elif scelta == "2":
                valore = float(input("Inserisci l'importo da prelevare: "))
                conto_corrente.prelievo(valore)
            elif scelta == "3":
                conto_corrente.stampa()
            elif scelta == "4":
                print("Uscita dal conto effettuata. Ritorno al menu principale.")
                break  # Esce SOLO dal ciclo interno delle operazioni
            elif scelta == "5":
                print("Chiusura del programma in corso...")
                programma_attivo = False  # Spegne il ciclo principale esterno
                break  # Esce dal ciclo interno
            else:
                print("Operazione non valida")
        
    else:
        print("\nCodice Fiscale non trovato nei nostri archivi. Procediamo alla creazione di un NUOVO conto.")
        nome = input("Inserisci il nome dell'intestatario: ").strip()
        saldo = float(input("Inserisci il saldo iniziale di apertura: "))
        
        banca[cf_utente] = ContoCorrente(nome, cf_utente, saldo)
        print(f"Conto creato con successo per {nome}!")

# --- FINE DEL PROGRAMMA: STAMPA DEI CONTI FINALI ---
print("\n" + "=" * 40)
print("       STATO FINALE DI TUTTI I CONTI")
print("=" * 40)

if not banca:
    print("Nessun conto presente nel sistema.")
else:
    for k, v in banca.items():
        v.stampa()