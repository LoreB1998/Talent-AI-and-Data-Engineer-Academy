class Porta:
    """Classe che rappresenta una porta con metodi per aprire e chiudere la porta."""
    def __init__(self, stanza):
        self.stanza = stanza
        self.aperta = False
    
    def apri(self):
        if not self.aperta:
            self.aperta = True
            return f"Porta in {self.stanza} aperta."
        else:
            return f"Porta in {self.stanza} è già aperta."
    
    def chiudi(self):
        if self.aperta:
            self.aperta = False
            return f"Porta in {self.stanza} chiusa."
        else:
            return f"Porta in {self.stanza} è già chiusa."
    
    def stato(self):
        return {
            "stanza": self.stanza,
            "aperta": self.aperta
        }
        