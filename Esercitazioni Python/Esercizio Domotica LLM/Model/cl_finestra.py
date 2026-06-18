class Finestra:
    """Finestra con apertura graduale espressa in percentuale (0-100)."""
    def __init__(self,stanza):
        self.stanza = stanza
        self.apertura = 0  # Percentuale di apertura (0-100)

    def apri(self, percentuale):
        self.apertura = max(0, min(percentuale, 100))
        if self.apertura == 100:
            return f"Finestra in {self.stanza} completamente aperta."
        else:
            return f"Finestra in {self.stanza} aperta al {self.apertura}%."
        
    def chiudi(self):
        if self.apertura > 0:
            self.apertura = 0
            return f"Finestra in {self.stanza} chiusa."
        else:
            return f"Finestra in {self.stanza} è già chiusa."
        
    def stato(self):
        return {
            "stanza": self.stanza,
            "apertura": self.apertura
        }
