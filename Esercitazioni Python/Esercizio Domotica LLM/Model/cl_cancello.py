class Cancello:
    """Cancello/garage, unico per l'intera abitazione."""

    def __init__(self):
        self.apertura = 0 # Percentuale di apertura (0-100)

    def apri(self, percentuale=100):
        self.apertura = max(0, min(percentuale, 100))
        if self.apertura == 100:
            return f"Cancello completamente aperto."
        else:
            return f"Cancello aperto al {self.apertura}%."

    def chiudi(self):
        if self.apertura > 0:
            self.apertura = 0
            return f"Cancello chiuso."
        else:
            return f"Il cancello è già chiuso."

    def stato(self):
        return {
            "apertura": self.apertura
        }
    