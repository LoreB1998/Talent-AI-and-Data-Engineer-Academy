from Model.cl_finestra import Finestra
from Model.cl_climatizzatore import Climatizzatore
from Model.cl_porta import Porta
from Model.cl_luci import Luce


class Stanza:
    """Aggrega tutti i dispositivi presenti in una stanza"""

    def __init__(self, nome):
        self.nome = nome
        self.porta = Porta(nome)
        self.finestra = Finestra(nome)
        self.luce = Luce(nome)
        self.clima = Climatizzatore(nome)
    
    def stato(self):
        return {
            "nome" : self.nome,
            "porta_aperta": self.porta.stato(),
            "finestra_aperta": self.finestra.stato(),
            "luce_accesa": self.luce.stato(),
            "clima_acceso": self.clima.stato()
        }