class Luce:
    """Rappresenta la luce di una stanza: stato, intensità (0-100) e colore."""
    def __init__(self, stanza):
        self.stanza = stanza
        self.accesa = False
        self.intensita = 0
        self.colore = "bianco"
    
    def accendi(self, intensita=100):
        self.intensita = max(0, min(intensita, 100))
        self.accesa = self.intensita > 0
        return f"Luce in {self.stanza} accesa con intensità {self.intensita}%."
    
    def spegni(self):
        self.accesa = False
        self.intensita = 0
        return f"Luce in {self.stanza} spenta."
    
    def imposta_intensita(self, intensita):
        self.intensita = max(0, min(intensita, 100))
        self.accesa = self.intensita > 0
        return f"Intensità luce in {self.stanza} impostata a {self.intensita}%."
    
    def varia_intensita(self, delta):
        return self.imposta_intensita(self.intensita + delta)
    
    def imposta_colore(self, colore):
        self.colore = colore
        if self.accesa:
            self.accendi(self.intensita)  # Mantieni l'intensità attuale
        return f"Colore luce in {self.stanza} impostato a {self.colore}."
    
    def stato(self):
        return {
            "stanza": self.stanza,
            "accesa": self.accesa,
            "intensita": self.intensita,
            "colore": self.colore
        }