class Climatizzatore:
    def __init__(self, stanza):
        self.stanza = stanza
        self.acceso = False
        self.temperatura = 24   # Temperatura di default
        self.modalita = "auto"  # Modalità di default

    def imposta(self, temperatura, modalita="auto"):
        self.temperatura = temperatura
        self.modalita = modalita
        self.acceso = True
        return f"Climatizzatore in {self.stanza} impostato a {self.temperatura}°C in modalità {self.modalita}."
    
    def spegni(self):
        self.acceso = False
        return f"Climatizzatore in {self.stanza} spento."
    
    def stato(self):
        return {
            "stanza": self.stanza,
            "acceso": self.acceso,
            "temperatura": self.temperatura,
            "modalita": self.modalita
        }
    