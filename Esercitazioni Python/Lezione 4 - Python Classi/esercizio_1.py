class Studente:
    # Il costruttore inizializza l'oggetto con i dati richiesti
    def __init__(self, nome, cognome, eta, classe):
        self.nome = nome
        self.cognome = cognome
        self.eta = eta
        self.classe = classe
    
    # Metodo per stampare le informazioni in modo leggibile
    def stampa_info(self):
        print(f"--- Scheda Studente ---")
        print(f"Nome: {self.nome}")
        print(f"Cognome: {self.cognome}")
        print(f"Età: {self.eta} anni")
        print(f"Classe: {self.classe}")
        print("-" * 23 + "\n")

# --- Creazione degli studenti ---

# Opzione 1: Creazione diretta passando i dati (Hardcoded)
studente1 = Studente("Mario", "Rossi", 16, "3A")

# Opzione 2: Creazione tramite input dell'utente (Dinamica)
print("Inserisci i dati per il secondo studente:")
nome_input = input("Nome: ")
cognome_input = input("Cognome: ")
eta_input = int(input("Età: "))  # Convertito in intero
classe_input = input("Classe: ")

studente2 = Studente(nome_input, cognome_input, eta_input, classe_input)

# --- Stampa delle informazioni ---
studente1.stampa_info()
studente2.stampa_info()