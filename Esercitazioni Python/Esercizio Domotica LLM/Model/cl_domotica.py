import json
import os
from Model.cl_cancello import Cancello
from Controller.cl_stanza import Stanza

class CasaDomotica:
    """
    Espone un metodo pubblico per ciascuna funzione di domotica.
    I nomi di questi metodi corrispondono 1:1 ai "name" definiti in TOOLS,
    così il dispatch dal function-calling di GPT è immediato (getattr).
    """

    def __init__(self, stanze=None, stato_path=None):
        stanze = stanze or ["soggiorno", "cucina", "camera", "bagno", "cameretta"]
        self.stanze = {nome.lower(): Stanza(nome.lower()) for nome in stanze}
        self.cancello = Cancello()

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Config"))
        self._stato_path = stato_path or os.path.join(base_dir, "stato_domotica.json")
        self._carica_stato()

    def _get_stanza(self, stanza):
        nome = stanza.lower().strip()
        if nome not in self.stanze:
            # Stanza non prevista in anticipo: la creiamo al volo
            self.stanze[nome] = Stanza(nome)
        return self.stanze[nome]

    def _snapshot_stato(self):
        return {
            "cancello": self.cancello.stato(),
            "stanze": {nome: stanza.stato() for nome, stanza in self.stanze.items()},
        }

    def _salva_stato(self):
        os.makedirs(os.path.dirname(self._stato_path), exist_ok=True)
        with open(self._stato_path, "w", encoding="utf-8") as f:
            json.dump(self._snapshot_stato(), f, ensure_ascii=False, indent=2)

    def _carica_stato(self):
        if not os.path.exists(self._stato_path):
            return

        try:
            with open(self._stato_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        cancello = data.get("cancello", {})
        self.cancello.apertura = max(0, min(int(cancello.get("apertura", 0)), 100))

        for nome, stato_stanza in data.get("stanze", {}).items():
            stanza = self._get_stanza(nome)

            porta = stato_stanza.get("porta_aperta", {})
            stanza.porta.aperta = bool(porta.get("aperta", False))

            finestra = stato_stanza.get("finestra_aperta", {})
            stanza.finestra.apertura = max(0, min(int(finestra.get("apertura", 0)), 100))

            luce = stato_stanza.get("luce_accesa", {})
            stanza.luce.accesa = bool(luce.get("accesa", False))
            stanza.luce.intensita = max(0, min(int(luce.get("intensita", 0)), 100))
            stanza.luce.colore = str(luce.get("colore", "bianco"))

            clima = stato_stanza.get("clima_acceso", {})
            stanza.clima.acceso = bool(clima.get("acceso", False))
            stanza.clima.temperatura = int(clima.get("temperatura", 24))
            stanza.clima.modalita = str(clima.get("modalita", "auto"))

    # ---- Porta ----
    def apri_porta(self, stanza):
        risultato = self._get_stanza(stanza).porta.apri()
        self._salva_stato()
        return risultato

    def chiudi_porta(self, stanza):
        risultato = self._get_stanza(stanza).porta.chiudi()
        self._salva_stato()
        return risultato

    # ---- Cancello / garage ----
    def apri_cancello(self, percentuale=100):
        risultato = self.cancello.apri(percentuale)
        self._salva_stato()
        return risultato

    def chiudi_cancello(self):
        risultato = self.cancello.chiudi()
        self._salva_stato()
        return risultato

    def stato_cancello(self):
        apertura = self.cancello.stato().get("apertura", 0)
        if apertura <= 0:
            return "Stato cancello: chiuso."
        if apertura >= 100:
            return "Stato cancello: completamente aperto."
        return f"Stato cancello: aperto al {apertura}%."

    def stato_casa(self):
        righe = [self.stato_cancello(), ""]

        for nome_stanza in sorted(self.stanze.keys()):
            righe.append(self.stato_stanza(nome_stanza))
            righe.append("")

        return "\n".join(righe).strip()

    # ---- Luci ----
    def accendi_luce(self, stanza, intensita=100):
        risultato = self._get_stanza(stanza).luce.accendi(intensita)
        self._salva_stato()
        return risultato

    def spegni_luce(self, stanza):
        risultato = self._get_stanza(stanza).luce.spegni()
        self._salva_stato()
        return risultato

    def imposta_intensita_luce(self, stanza, intensita):
        risultato = self._get_stanza(stanza).luce.imposta_intensita(intensita)
        self._salva_stato()
        return risultato

    def varia_intensita_luce(self, stanza, delta):
        risultato = self._get_stanza(stanza).luce.varia_intensita(delta)
        self._salva_stato()
        return risultato

    def imposta_colore_luce(self, stanza, colore):
        risultato = self._get_stanza(stanza).luce.imposta_colore(colore)
        self._salva_stato()
        return risultato

    # ---- Finestre ----
    def apri_finestra(self, stanza, percentuale=100):
        risultato = self._get_stanza(stanza).finestra.apri(percentuale)
        self._salva_stato()
        return risultato

    def chiudi_finestra(self, stanza):
        risultato = self._get_stanza(stanza).finestra.chiudi()
        self._salva_stato()
        return risultato

    # ---- Climatizzatore ----
    def imposta_climatizzatore(self, stanza, temperatura=22, modalita="auto"):
        risultato = self._get_stanza(stanza).clima.imposta(temperatura, modalita)
        self._salva_stato()
        return risultato

    def spegni_climatizzatore(self, stanza):
        risultato = self._get_stanza(stanza).clima.spegni()
        self._salva_stato()
        return risultato

    # ---- Stato (bonus, comodo per debug/vocale "che luci sono accese?") ----
    def stato_stanza(self, stanza):
        stato = self._get_stanza(stanza).stato()

        nome = stato.get("nome", stanza)
        porta_aperta = stato.get("porta_aperta", {}).get("aperta", False)
        apertura_finestra = stato.get("finestra_aperta", {}).get("apertura", 0)

        luce = stato.get("luce_accesa", {})
        luce_accesa = luce.get("accesa", False)
        luce_intensita = luce.get("intensita", 0)
        luce_colore = luce.get("colore", "bianco")

        clima = stato.get("clima_acceso", {})
        clima_acceso = clima.get("acceso", False)
        clima_temp = clima.get("temperatura", 24)
        clima_modalita = clima.get("modalita", "auto")

        porta_txt = "aperta" if porta_aperta else "chiusa"

        if apertura_finestra <= 0:
            finestra_txt = "chiusa"
        elif apertura_finestra >= 100:
            finestra_txt = "completamente aperta"
        else:
            finestra_txt = f"aperta al {apertura_finestra}%"

        if luce_accesa:
            luce_txt = f"accesa ({luce_intensita}%, colore {luce_colore})"
        else:
            luce_txt = f"spenta (colore {luce_colore})"

        if clima_acceso:
            clima_txt = f"acceso ({clima_temp}°C, modalità {clima_modalita})"
        else:
            clima_txt = f"spento ({clima_temp}°C, modalità {clima_modalita})"

        return (
            f"Stato di {nome}:\n"
            f"- Porta: {porta_txt}\n"
            f"- Finestra: {finestra_txt}\n"
            f"- Luce: {luce_txt}\n"
            f"- Climatizzatore: {clima_txt}"
        )

    # ---- Ambiente romantico ----
    def crea_ambiente_romantico(self, stanza):
        s = self._get_stanza(stanza)
        passi = [
            s.luce.imposta_colore("rosso"),
            s.luce.imposta_intensita(35),
            s.clima.imposta(22, "relax"),
            s.porta.chiudi(),
            self._riproduci_musica(),
        ]
        self._salva_stato()
        return "✨ Ambiente romantico attivato.\n" + "\n".join(passi)

    @staticmethod
    def _riproduci_musica():
        # Integrazione reale con uno speaker/servizio musicale andrebbe qui.
        return "🎵 Riproduzione musica avviata: 'Never Gonna Give You Up' (Rick Astley)."