import pandas as pd
import math
import random
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from typing import List, Tuple, Dict, Any, Optional

# ─────────────────────────────────────────
# VEICOLI (GERARCHIA E FACTORY PATTERN)
# ─────────────────────────────────────────

class Veicolo:
    def __init__(self, veicolo_id: str, patente_richiesta: str, peso_max_kg: float, disponibile: bool = True):
        self.id = veicolo_id
        self.patente_richiesta = patente_richiesta
        self.disponibile = disponibile
        self.peso_max_kg = peso_max_kg
        self.stand_by = False
        self.velocita_media_kmh = 30.0  # Velocità di default

    @classmethod
    def da_csv(cls, path: str) -> list:
        """Factory method che legge un CSV e restituisce una lista di oggetti Veicolo (o sue sottoclassi)."""
        records = pd.read_csv(path).to_dict(orient="records")
        mappa_classi = {
            "Bicicletta": Bicicletta,
            "Scooter": Scooter,
            "Auto": Auto,
            "Furgone": Furgone
        }
        veicoli = []
        for r in records:
            classe_target = mappa_classi.get(r["tipo"], cls)
            disponibile_bool = r["stato"] == "DISPONIBILE"
            
            v = classe_target(
                veicolo_id          = r["veicolo_id"],
                patente_richiesta   = r["patente_richiesta"],
                disponibile         = disponibile_bool,
                peso_max_kg         = float(r["peso_max_kg"])
            )
            veicoli.append(v)
        return veicoli
    
    def compatibile_con_patente(self, patente: str) -> bool:
        """Verifica se il veicolo è compatibile con la patente del rider."""
        if self.patente_richiesta == "Nessuna":
            return True
        opzioni = self.patente_richiesta.split("|") 
        return patente in opzioni
    
    @property
    def peso_max_per_collo(self) -> float:
        return self.peso_max_kg / 20


class Bicicletta(Veicolo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.velocita_media_kmh = 15.0

    def compatibile_con_patente(self, patente: str) -> bool:
        return True


class Scooter(Veicolo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.velocita_media_kmh = 35.0

    def compatibile_con_patente(self, patente: str) -> bool:
        return patente in ["A", "A2", "B"]


class Auto(Veicolo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.velocita_media_kmh = 45.0

    def compatibile_con_patente(self, patente: str) -> bool:
        return patente in ["B"]


class Furgone(Veicolo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.velocita_media_kmh = 50.0

    def compatibile_con_patente(self, patente: str) -> bool:
        return patente in ["C", "CE"]

# ─────────────────────────────────────────
# ANAGRAFICA
# ─────────────────────────────────────────

class Anagrafica:
    def __init__(self, persona_id: str, nome: str, cognome: str) -> None:
        self.persona_id = persona_id
        self.nome = nome
        self.cognome = cognome

    @property
    def nome_completo(self) -> str:
        return f"{self.nome} {self.cognome}"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.persona_id}, {self.nome_completo})"
    
    def __str__(self) -> str:
        return self.nome_completo

# ─────────────────────────────────────────
# RIDER
# ─────────────────────────────────────────

class Rider(Anagrafica):
    DEPOSITO_LAT = 45.4064
    DEPOSITO_LON = 11.8768

    def __init__(self, rider_id: str, nome: str, cognome: str, patente: str) -> None:
        super().__init__(rider_id, nome, cognome)
        self.patente = patente
        self.veicolo = None
        self.consegne = []
        self.disponibile = True
    
    @classmethod
    def da_csv(cls, path: str) -> list:
        """Factory method che legge un CSV e restituisce una lista di oggetti Riders."""
        records = pd.read_csv(path).to_dict(orient="records")
        return [
            cls(
                rider_id        = r["rider_id"],
                nome            = r["nome"],
                cognome         = r["cognome"],
                patente         = r["patente"],
            )
            for r in records
        ]
    
    @property
    def posizione_deposito(self) -> tuple:
        """Restituisce le coordinate del deposito associato al rider."""
        return self.DEPOSITO_LAT, self.DEPOSITO_LON

    def assegna_veicolo(self, veicolo: Veicolo):
        """Assegna un veicolo al rider dopo aver verificato la compatibilità della patente."""
        if not veicolo.compatibile_con_patente(self.patente):
            raise ValueError(
                f"{self} non può guidare {veicolo} (patente richiesta: {veicolo.patente_richiesta}, rider: {self.patente})"
            )
        self.veicolo = veicolo

    def clienti_per_distanza(self, clienti: list) -> list:
        """Ordina i clienti in base alla distanza dal deposito del rider (Greedy Approach)."""
        rimanenti = clienti.copy()
        ordinati = []
        lat, lon = self.posizione_deposito
        while rimanenti:
            piu_vicino = min(rimanenti, key=lambda c: c.distanza_da(lat, lon))
            lat, lon = piu_vicino.latitudine, piu_vicino.longitudine
            ordinati.append(piu_vicino)
            rimanenti.remove(piu_vicino)
        return ordinati
        
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.persona_id}, {self.nome_completo}, Patente: {self.patente})"
    
    def __str__(self) -> str:
        return f"{self.nome_completo} (ID: {self.persona_id}, Patente: {self.patente})"

# ─────────────────────────────────────────
# CLIENTE
# ─────────────────────────────────────────

class Cliente(Anagrafica):
    def __init__(self, cliente_id: str, nome: str, cognome: str,
                 latitudine: float, longitudine: float) -> None:
        super().__init__(cliente_id, nome, cognome)
        self.latitudine  = latitudine
        self.longitudine = longitudine
    
    @classmethod
    def da_csv(cls, path: str) -> list:
        records = pd.read_csv(path).to_dict(orient="records")
        return [
            cls(
                cliente_id  = r["cliente_id"],
                nome        = r["nome"],
                cognome     = r["cognome"],
                latitudine  = r["latitudine"],
                longitudine = r["longitudine"],
            )
            for r in records
        ]
    
    def distanza_da(self, lat: float, lon: float) -> float:
        """Distanza in km usando la formula di Haversine."""
        R = 6371
        dlat = math.radians(self.latitudine - lat)
        dlon = math.radians(self.longitudine - lon)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat)) *
             math.cos(math.radians(self.latitudine)) *
             math.sin(dlon / 2) ** 2)
        return R * 2 * math.asin(math.sqrt(a))
    
    def __repr__(self):
        return f"Cliente({self.persona_id}, {self.nome_completo} - Lat: {self.latitudine}, Lon: {self.longitudine})"
    
    def __str__(self):
        return f"{self.nome_completo} (ID: {self.persona_id}) - Lat: {self.latitudine}, Lon: {self.longitudine}"

# ─────────────────────────────────────────
# COLLI 
# ─────────────────────────────────────────

class Collo:
    def __init__(self, collo_id: str, peso_kg: float):
        self.collo_id = collo_id
        self.peso_kg = peso_kg
    
    @classmethod
    def da_csv(cls, path: str) -> list:
        """Inizializza polimorficamente Collo o Collo3D a seconda dei dati presenti nel CSV."""
        records = pd.read_csv(path).to_dict(orient="records")
        colli = []
        for r in records:
            if "lunghezza_cm" in r and not pd.isna(r["lunghezza_cm"]):
                colli.append(Collo3D(
                    collo_id     = r["collo_id"],
                    peso_kg      = float(r["peso_kg"]),
                    lunghezza_cm = float(r["lunghezza_cm"]),
                    larghezza_cm = float(r["larghezza_cm"]),
                    altezza_cm   = float(r["altezza_cm"])
                ))
            else:
                colli.append(cls(collo_id = r["collo_id"], peso_kg = float(r["peso_kg"])))
        return colli
    
    def __repr__(self):
        return f"Collo({self.collo_id}, {self.peso_kg} kg)"


class Collo3D(Collo):
    """Collo con dimensioni (lunghezza, larghezza, altezza) in cm."""
    def __init__(self, collo_id: str, peso_kg: float, lunghezza_cm: float, larghezza_cm: float, altezza_cm: float):
        super().__init__(collo_id, peso_kg)
        self.lunghezza_cm = lunghezza_cm
        self.larghezza_cm = larghezza_cm
        self.altezza_cm = altezza_cm
    
    def volume_m3(self) -> float:
        """Calcola il volume in metri cubi."""
        return (self.lunghezza_cm / 100) * (self.larghezza_cm / 100) * (self.altezza_cm / 100)
    
    def __repr__(self):
        return f"Collo3D({self.collo_id}, {self.peso_kg} kg, {self.lunghezza_cm}x{self.larghezza_cm}x{self.altezza_cm} cm)"
    
# ─────────────────────────────────────────
# CONSEGNA
# ─────────────────────────────────────────

class Consegna:
    def __init__(self, consegna_id: str, rider: Rider, cliente: Cliente, collo: Collo, distanza_tratta: float):
        if rider.veicolo is None:
            raise ValueError(f"{rider} non ha un veicolo assegnato.")
        self.consegna_id = consegna_id
        self.rider       = rider
        self.veicolo     = rider.veicolo
        self.cliente     = cliente
        self.distanza_km = distanza_tratta
        self.collo       = collo
        
        # Calcolo del tempo: (Distanza / Velocità) in ore, moltiplicato per 60 per i minuti
        self.tempo_viaggio_min = (self.distanza_km / self.veicolo.velocita_media_kmh) * 60.0
        
        if collo.peso_kg > rider.veicolo.peso_max_kg:
            raise ValueError(f"{collo} troppo pesante per {rider.veicolo}")
    
    def __repr__(self):
        return f"Consegna({self.consegna_id} | {self.rider.nome_completo} → {self.cliente.nome_completo})"

# ─────────────────────────────────────────
# GIORNATA DI CONSEGNE
# ─────────────────────────────────────────

class GiornataConsegne:
    def __init__(self) -> None:
        self.consegne = []

    def prepara_flotta(self, veicoli: list, perc_rotti: float = 0.20, perc_standby: float = 0.10):
        """Inizializza gli stati variabili della flotta per la giornata corrente."""
        for v in veicoli:
            v.disponibile = True
            v.stand_by = False
        
        # Gestione rotture casuali
        n_da_rompere = math.ceil(len(veicoli) * perc_rotti)
        for v_rotto in random.sample(veicoli, n_da_rompere):
            v_rotto.disponibile = False
            
        # Gestione veicoli in stand-by (solo tra quelli funzionanti)
        funzionanti = [v for v in veicoli if v.disponibile]
        n_stand_by = math.ceil(len(funzionanti) * perc_standby)
        for v_standby in random.sample(funzionanti, n_stand_by):
            v_standby.stand_by = True

    def assegna_veicoli_a_riders(self, veicoli: list, riders: list):
        """Coordina l'assegnazione dei veicoli attivi ai vari rider secondo idoneità delle patenti."""
        veicoli_disponibili = [v for v in veicoli if v.disponibile and not v.stand_by]
        for rider in riders:
            if not rider.disponibile:
                continue
            compatibili = [v for v in veicoli_disponibili if v.compatibile_con_patente(rider.patente)]

            if not compatibili:
                print(f"⚠️ Avviso: Nessun veicolo disponibile per {rider.nome_completo} (Patente: {rider.patente}). Rider impostato come non attivo.")
                rider.disponibile = False
                continue
            
            scelto = random.choice(compatibili)
            rider.assegna_veicolo(scelto)
            veicoli_disponibili.remove(scelto)
    
    def genera(self, riders: list, clienti: list, colli: list, n_per_rider: int) -> "GiornataConsegne":
            '''Genera consegne casuali assegnando clienti e colli ai rider senza superare i limiti di peso totale del mezzo.'''
            self.consegne = []
            colli_disponibili = colli.copy()
            contatore = 1
            
            # Filtriamo subito i rider operativi (guard clause per evitare nidificazioni)
            riders_attivi = [r for r in riders if r.disponibile and r.veicolo]
            
            for rider in riders_attivi:
                if not clienti:
                    break  # Se finiscono i clienti, interrompiamo la simulazione
                    
                # 1. Assegnazione casuale dei clienti al rider (fino al massimo richiesto)
                n_clienti = min(n_per_rider, len(clienti))
                clienti_casuali = random.sample(clienti, n_clienti)
                
                # Ordiniamo i clienti scelti partendo dal deposito (Greedy Approach)
                clienti_ordinati = rider.clienti_per_distanza(clienti_casuali)
                
                # 2. Stato del viaggio del rider
                lat_attuale, lon_attuale = rider.posizione_deposito
                carico_attuale = 0.0
                
                # 3. Assegnazione colli e creazione tratte
                for cliente in clienti_ordinati:
                    # Trova i colli che rispettano sia il limite del singolo collo che la portata residua del mezzo
                    compatibili = [
                        c for c in colli_disponibili 
                        if c.peso_kg <= rider.veicolo.peso_max_per_collo and
                        (carico_attuale + c.peso_kg) <= rider.veicolo.peso_max_kg
                    ]
                    
                    if not compatibili:
                        continue  # Salta il cliente se non ci sono pacchi compatibili/caricabili

                    # Assegnazione pacco e aggiornamento peso
                    collo_scelto = random.choice(compatibili)
                    colli_disponibili.remove(collo_scelto)
                    carico_attuale += collo_scelto.peso_kg

                    # Calcolo della tratta e creazione della consegna
                    distanza_tratta = cliente.distanza_da(lat_attuale, lon_attuale)
                    consegna = Consegna(f"DEL{contatore:03d}", rider, cliente, collo_scelto, distanza_tratta)
                    
                    # Registrazione consegna
                    rider.consegne.append(consegna)
                    self.consegne.append(consegna)
                    contatore += 1
                    
                    # Aggiornamento posizione per la tappa successiva
                    lat_attuale, lon_attuale = cliente.latitudine, cliente.longitudine
                    
            return self

# ─────────────────────────────────────────
# CLASSI DI VISUALIZZAZIONE
# ─────────────────────────────────────────

class VisualizzazioneDriver:
    """Rappresentazione per i Driver: accumula i dettagli del turno in una stringa, includendo i tempi."""
    
    def __init__(self, riders: list):
        self.riders = [r for r in riders if r.disponibile and r.veicolo]

    def genera_report(self) -> str:
        TEMPO_SOSTA_MIN = 5.0 # Minuti stimati per parcheggiare e consegnare il pacco al cliente
        linee = []
        linee.append("\n" + "="*95)
        linee.append(" DRIVER DASHBOARD - RIEPILOGO GIORNALIERO ".center(95, "═"))
        linee.append("="*95)
        
        for r in self.riders:
            linee.append(f"\nDRIVER: {r.nome_completo:<30} | ID: {r.persona_id}")
            linee.append(f"MEZZO:  {r.veicolo.__class__.__name__} | Velocità media: {r.veicolo.velocita_media_kmh} km/h")
            linee.append("   " + "-"*85)
            linee.append(f"   {'ID':<8} | {'Cliente Destinatario':<20} | {'Distanza':<10} | {'Tempo Viaggio':<15} | {'Pacco':<15}")
            linee.append("   " + "-"*85)
            
            if not r.consegne:
                linee.append("   Nessun pacco programmato per questo conducente.")
                linee.append("   " + "-"*85)
                continue
                
            distanza_totale = 0.0
            peso_totale = 0.0
            tempo_totale_min = 0.0
            
            for c in r.consegne:
                tempo_str = f"{c.tempo_viaggio_min:.1f} min"
                linee.append(f"   {c.consegna_id:<8} | {c.cliente.nome_completo:<20} | {c.distanza_km:>7.2f} km | {tempo_str:<15} | {c.collo.collo_id:<7} ({c.collo.peso_kg:.1f} kg)")
                
                distanza_totale += c.distanza_km
                peso_totale += c.collo.peso_kg
                tempo_totale_min += c.tempo_viaggio_min + TEMPO_SOSTA_MIN
            
            # Calcolo del rientro in sede
            ultimo_cliente = r.consegne[-1].cliente
            dep_lat, dep_lon = r.posizione_deposito
            distanza_rientro = ultimo_cliente.distanza_da(dep_lat, dep_lon)
            tempo_rientro_min = (distanza_rientro / r.veicolo.velocita_media_kmh) * 60.0
            
            distanza_totale += distanza_rientro
            tempo_totale_min += tempo_rientro_min
            
            ore = int(tempo_totale_min // 60)
            minuti = int(tempo_totale_min % 66)
            
            linee.append(f"   {'RTRN':<8} | {'Rientro in Deposito':<20} | {distanza_rientro:>7.2f} km | {tempo_rientro_min:.1f} min{'':<11} | -")
            linee.append("   " + "-"*85)
            linee.append(f"   Riepilogo Turno: {len(r.consegne)} consegne effettuate | Distanza totale: {distanza_totale:.2f} km")
            linee.append(f"   Tempo Totale (incluse soste): {ore}h {minuti}m")
            linee.append(f"   Carico Totale:   {peso_totale:.2f} kg / Capacità Max Mezzo: {r.veicolo.peso_max_kg:.2f} kg")
            linee.append("   " + "-"*85)
            
        linee.append("\n" + "="*95)
        return "\n".join(linee)


class VisualizzazioneManager:
    """Rappresentazione per il Manager: accumula lo stato della flotta in una stringa."""

    def __init__(self, veicoli: list):
        self.veicoli = veicoli

    def genera_report(self) -> str:
        rotti       = [v for v in self.veicoli if not v.disponibile]
        stand_by    = [v for v in self.veicoli if v.disponibile and v.stand_by]
        disponibili = [v for v in self.veicoli if v.disponibile and not v.stand_by]

        linee = []
        linee.append("\n" + "="*85)
        linee.append(" MANAGEMENT DASHBOARD - FLOTTA AZIENDALE ".center(85, "═"))
        linee.append("="*85)
        
        linee.append(f"\n VEICOLI DISPONIBILI / IN SERVIZIO SU STRADA ({len(disponibili)})")
        linee.append(" ─────────────────────────────────────────────────────────────────────────────")
        if not disponibili:
            linee.append("   Attenzione: nessun veicolo operativo disponibile per i rider!")
        else:
            for v in disponibili:
                linee.append(f"   ID: {v.id:<6} | {v.__class__.__name__:<15} (Max Cap: {v.peso_max_kg} kg)")

        linee.append(f"\n VEICOLI IN STAND-BY / FERMI IN DEPOSITO ({len(stand_by)}) [Target: 10% di quelli OK]")
        linee.append(" ─────────────────────────────────────────────────────────────────────────────")
        if not stand_by:
            linee.append("   Nessun veicolo in stand-by; tutti i mezzi operativi sono su strada.")
        else:
            for v in stand_by:
                linee.append(f"   ID: {v.id:<6} | {v.__class__.__name__:<15}")

        linee.append(f"\n VEICOLI ROTTI / FUORI SERVIZIO ({len(rotti)}) [Target: 20%]")
        linee.append(" ─────────────────────────────────────────────────────────────────────────────")
        if not rotti:
            linee.append("   Nessun veicolo guasto segnalato.")
        else:
            for v in rotti:
                linee.append(f"   ID: {v.id:<6} | {v.__class__.__name__:<15}")
                
        linee.append("\n" + "="*85)
        return "\n".join(linee)

class VisualizzazioneMappa:
    """Genera una mappa geografica con i percorsi dei driver e la salva come immagine."""
    @staticmethod
    def mostra_percorsi(riders: list, output_path: str, max_esempi: int = 3, context: Optional[str] = None):
        # 1. Raggruppiamo i rider attivi per classe del veicolo
        rider_per_tipo = {}
        for r in riders:
            if r.disponibile and r.consegne and r.veicolo:
                tipo = r.veicolo.__class__.__name__
                if tipo not in rider_per_tipo:
                    rider_per_tipo[tipo] = []
                rider_per_tipo[tipo].append(r)
        
        if not rider_per_tipo:
            print("⚠️ Nessun percorso da mostrare o salvare in questo turno.")
            return

        # 2. Impostiamo le dimensioni della griglia
        tipi_veicolo = list(rider_per_tipo.keys())
        righe = len(tipi_veicolo)
        colonne = max_esempi
        
        # 3. Impostiamo lo stile di Matplotlib per un look più pulito
        plt.style.use('seaborn-v0_8-whitegrid')
        
        fig, axes = plt.subplots(righe, colonne, figsize=(6 * colonne, 6 * righe), squeeze=False)
        
        colori = {'Bicicletta': '#3498db', 'Scooter': '#e67e22', 'Auto': '#2ecc71', 'Furgone': '#e74c3c'}
        dep_lat, dep_lon = Rider.DEPOSITO_LAT, Rider.DEPOSITO_LON

        # 4. Popoliamo la griglia riga per riga
        for i, tipo in enumerate(tipi_veicolo):
            lista_completa = rider_per_tipo[tipo]
            # Assicuriamoci di non superare il numero di esempi disponibili
            n_esempi = min(max_esempi, len(lista_completa))
            selezionati = random.sample(lista_completa, n_esempi)
            colore_base = colori.get(tipo, '#9b59b6')

            for j in range(colonne):
                ax = axes[i, j]
                
                if j < n_esempi:
                    r = selezionati[j]
                    
                    # Plot del deposito (più grande e visibile)
                    deposito = ax.plot(dep_lon, dep_lat, marker='*', color='#2c3e50', markersize=18, zorder=10, label='Deposito')
                    # Etichetta Deposito
                    ax.annotate('DEP', (dep_lon, dep_lat), xytext=(5, 5), textcoords="offset points", fontweight='bold')

                    # Coordinate per il tracciato
                    lats = [dep_lat] + [c.cliente.latitudine for c in r.consegne] + [dep_lat]
                    lons = [dep_lon] + [c.cliente.longitudine for c in r.consegne] + [dep_lon]
                    
                    # Tracciato del percorso (linea più spessa)
                    ax.plot(lons, lats, linestyle='-', color=colore_base, alpha=0.6, 
                             linewidth=3, zorder=1, label='Percorso')
                    
                    # Marcatori per le tappe (diversi per deposito e clienti)
                    # Deposito
                    ax.plot(dep_lon, dep_lat, marker='o', color='#2c3e50', markersize=10, zorder=5)
                    # Clienti (con etichette ID)
                    for k, c in enumerate(r.consegne):
                        # Colore diverso per ogni tappa (sfumature del colore base)
                        ax.plot(c.cliente.longitudine, c.cliente.latitudine, marker='o', color=colore_base, 
                                 markersize=10, markeredgecolor='white', markeredgewidth=1.5, zorder=5)
                        ax.annotate(f"{k+1}: {c.cliente.persona_id}", 
                                     (c.cliente.longitudine, c.cliente.latitudine),
                                     textcoords="offset points", xytext=(0,10), ha='center', fontsize=8, color='#34495e')

                    # Freccette di direzione (opzionali, per maggiore chiarezza)
                    for k in range(len(lons) - 1):
                         dx = lons[k+1] - lons[k]
                         dy = lats[k+1] - lats[k]
                         ax.arrow(lons[k], lats[k], dx, dy, head_width=0.001, head_length=0.002, fc=colore_base, ec=colore_base, alpha=0.4, zorder=2)
                    
                    # Titolo più informativo
                    ax.set_title(f"{tipo} - Driver: {r.nome_completo}\nN. Consegne: {len(r.consegne)}", fontsize=12, fontweight='bold', color='#2c3e50')
                    
                    # Rimuoviamo le etichette degli assi per pulizia
                    ax.set_xticklabels([])
                    ax.set_yticklabels([])
                    ax.tick_params(axis='both', which='both', bottom=False, top=False, left=False, right=False)

                    # Legenda specifica per il plot (se utile)
                    # ax.legend(loc='upper right', fontsize=8)
                
                else:
                    ax.axis('off')

        # 5. Titolo generale e legenda globale
        plt.suptitle(f"Routing per Tipo di Mezzo (Esempi - Max {max_esempi} per categoria)", fontsize=18, fontweight='bold', color='#2c3e50')
        
        # Creiamo patches per la legenda globale separando i tipi per Pylance
        legend_patches = [mpatches.Patch(color=colori[tipo], label=tipo) for tipo in tipi_veicolo]
        
        # Creiamo le linee separatamente
        legend_lines = [
            mlines.Line2D([], [], color='#2c3e50', marker='*', linestyle='None', markersize=10, label='Deposito'),
            mlines.Line2D([], [], color='gray', linestyle='-', linewidth=2, alpha=0.6, label='Percorso')
        ]
        
        # Uniamo le liste in una nuova variabile per fornire i "handles" completi
        tutti_handles = legend_patches + legend_lines
        
        fig.legend(handles=tutti_handles, loc='lower center', ncol=len(tutti_handles), fontsize=12, frameon=True, facecolor='white', edgecolor='#bdc3c7', bbox_to_anchor=(0.5, 0.02))

        plt.tight_layout()
        plt.subplots_adjust(top=0.90, bottom=0.1) # Spazio per titolo e legenda
        
        # 6. Salvataggio su file e chiusura del plot
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close(fig) 
        print(f"🖼️  Mappa salvata con successo in: {output_path}")

# ─────────────────────────────────────────
# MAIN SIMULAZIONE
# ─────────────────────────────────────────

if __name__ == "__main__":
    BASE = "/Users/lorenzo/Desktop/Talent Al & Data Engineer Academy/Lezione 5-6-7 - Veicoli/"
    try:
        veicoli = Veicolo.da_csv(BASE + "veicoli.csv")
        clienti = Cliente.da_csv(BASE + "clienti.csv")
        riders  = Rider.da_csv(BASE + "riders.csv")
        colli   = Collo.da_csv(BASE + "colli.csv")

        giornata = GiornataConsegne()

        giornata.prepara_flotta(veicoli, perc_rotti=0.20, perc_standby=0.10)
        giornata.assegna_veicoli_a_riders(veicoli, riders)
        giornata.genera(riders, clienti, colli, n_per_rider=20)

        manager_vista = VisualizzazioneManager(veicoli)
        driver_vista = VisualizzazioneDriver(riders)
        
        # Generiamo le stringhe dei report (Disaccoppiamento I/O)
        report_manager = manager_vista.genera_report()
        report_driver = driver_vista.genera_report()
        
        # Stampa su console standard
        print(report_manager)
        print(report_driver)

        # Scrittura pulita su file senza alterare sys.stdout
        percorso_file = BASE + "risultati.txt"
        with open(percorso_file, "w", encoding="utf-8") as file_out:
            file_out.write(report_manager)
            file_out.write("\n"*3)
            file_out.write(report_driver)
            
        print(f"\n✅ Risultati salvati con successo in: {percorso_file}")
        
        # Lancia il salvataggio della mappa grafica
        percorso_mappa = BASE + "mappa_percorsi.png"
        print("🗺️  Generazione e salvataggio della mappa in corso...")
        VisualizzazioneMappa.mostra_percorsi(riders, output_path=percorso_mappa)
        
    except FileNotFoundError as e:
        print(f"Errore caricamento file CSV. Controlla il percorso BASE: {e}")