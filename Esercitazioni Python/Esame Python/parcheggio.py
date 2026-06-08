from ticket import Ticket
import random
from config import CAPIENZA

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