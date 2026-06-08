from datetime import datetime, timedelta
import math
from config import TARIFFA_ORARIA, TIPO_TARIFFA, SCATTO_MINUTI  


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
        if self.durata is None:  
            return None
        
        minuti_totali = self.durata.total_seconds() / 60
        
        if TIPO_TARIFFA == 'oraria':
            # Arrotonda alle ore successive
            ore_da_pagare = math.ceil(minuti_totali / 60)
            return round(ore_da_pagare * TARIFFA_ORARIA, 2)
        else:
            # Calcolo a scatti
            scatti = math.ceil(minuti_totali / SCATTO_MINUTI)
            costo_singolo_scatto = (TARIFFA_ORARIA * SCATTO_MINUTI) / 60
            return round(scatti * costo_singolo_scatto, 2)
    
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

    def dati_qr(self) -> str:
        """Restituisce una stringa formattata elegantemente per la lettura del QR Code."""
        orario = self.ingresso.strftime("%d/%m/%Y %H:%M:%S")
        return (
            f"TICKET PARCHEGGIO\n"
            f"-------------------\n"
            f"ID: {self.id_ticket}\n"
            f"TARGA: {self.targa}\n"
            f"POSTO: {self.posto}\n"
            f"INGRESSO: {orario}"
        )
