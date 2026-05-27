def isola_solo_romanzo(testo: str) -> str:
    """Isola il romanzo usando .find() e lo slicing."""
    inizio = testo.find("INTRODUZIONE")
    if inizio != -1:
        testo = testo[inizio:]
    fine = testo.find("OPERE DI ALESSANDRO MANZONI")
    if fine != -1:
        testo = testo[:fine]
    return testo


def rimuovi_tag_illustrazioni(testo: str) -> str:
    """Rimuove i blocchi [Illustrazione: ...] cercando dinamicamente."""
    while "[Illustrazione:" in testo:
        inizio = testo.find("[Illustrazione:")
        fine = testo.find("]", inizio)
        if fine != -1:
            testo = testo[:inizio] + testo[fine+1:]
        else:
            break
    return testo


def pulisci_caratteri_e_spazi(testo: str) -> str:
    """Pulisce stile e spazi normalizzando le righe."""
    righe_pulite = []
    for riga in testo.splitlines():
        riga = " ".join(riga.replace("_", "").replace("=", "").split())
        if riga:
            righe_pulite.append(riga)
        elif righe_pulite and righe_pulite[-1] != "":
            righe_pulite.append("")
    return "\n".join(righe_pulite)


def conta_occorrenze_parole(testo: str) -> dict:
    """Conta le parole convertite in minuscolo e pulite."""
    conteggio = {}
    punteggiatura = ",.;:!?\"()«»-"
    testo_per_conteggio = testo.replace("'", " ")
    for parola in testo_per_conteggio.split():
        parola_pulita = parola.lower().strip(punteggiatura)
        if parola_pulita:
            conteggio[parola_pulita] = conteggio.get(parola_pulita, 0) + 1
    return conteggio


def filtra_parole_reali(conteggio_dict: dict, parole_da_escludere: set) -> dict:
    """Rimuove le stopwords dal dizionario."""
    return {p: c for p, c in conteggio_dict.items() if p not in parole_da_escludere}


def mostra_top_n(conteggio_dizionario: dict, n: int = 10, n_chars: int = 1, show_details: bool = False, file=None) -> None:
    """Mostra le N parole più frequenti."""
    min_len = n_chars * 2 if show_details else 0
    filtered = {p: c for p, c in conteggio_dizionario.items() if len(p) >= min_len}
    top_n = sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:n]
    
    titolo = f" TOP {n} PAROLE (min len {min_len}) "
    print(f"\n{titolo.center(40, '=')}", file=file)
    for i, (parola, count) in enumerate(top_n, 1):
        if show_details:
            print(f"{i:2d}. {parola:<15} ({parola[:n_chars]}-{parola[-n_chars:]}) -> {count:4d} occorrenze", file=file)
        else:
            print(f"{i:2d}. {parola:<20} -> {count:4d} occorrenze", file=file)


def mostra_bottom_n(conteggio_dizionario: dict, n: int = 10, n_chars: int = 1, show_details: bool = False, file=None) -> None:
    """Mostra le N parole più rare."""
    min_len = n_chars * 2 if show_details else 0
    filtered = {p: c for p, c in conteggio_dizionario.items() if len(p) >= min_len}
    bottom_n = sorted(filtered.items(), key=lambda x: x[1])[:n]
    
    titolo = f" {n} PAROLE PIÙ RARE (min len {min_len}) "
    print(f"\n{titolo.center(40, '=')}", file=file)
    if not bottom_n:
        print("Nessuna parola trovata.".center(40), file=file)
        return
    for i, (parola, count) in enumerate(bottom_n, 1):
        if show_details:
            print(f"{i:2d}. {parola:<15} ({parola[:n_chars]}-{parola[-n_chars:]}) -> {count:2d} occorrenze", file=file)
        else:
            print(f"{i:2d}. {parola:<20} -> {count:2d} occorrenze", file=file)


def mostra_media_conteggio(conteggio_dizionario: dict) -> None:
    totale = sum(conteggio_dizionario.values())
    uniche = len(conteggio_dizionario)
    print(f"\n{' MEDIA CONTEGGIO '.center(40, '=')}")
    if uniche > 0:
        print(f"Media del conteggio: {totale / uniche:.2f}".center(40))


def cerca_sottoparole(conteggio_dizionario: dict, frammento: str):
    frammento = frammento.lower()
    risultati = sorted({p: c for p, c in conteggio_dizionario.items() if frammento in p}.items(), key=lambda x: x[1], reverse=True)
    print(f"\n{' ' + frammento.upper() + ' (' + str(len(risultati)) + ' trovate) ':=^40}")
    for p, c in risultati:
        print(f"{p:<20} -> {c:2d} occorrenze")


def _is_ascii_alpha(char: str) -> bool:
    return ('a' <= char <= 'z') or ('A' <= char <= 'Z')

def cifra_testo(testo: str, shift: int = 7, cifra_spazi: bool = True) -> str:
    shift = shift % 26
    risultato = []
    for char in testo:
        if _is_ascii_alpha(char):
            base = ord('a') if char.islower() else ord('A')
            risultato.append(chr((ord(char) - base + shift) % 26 + base))
        elif cifra_spazi and char.isprintable() and ord(char) < 128:
            risultato.append(chr(ord(char) + shift))
        else:
            risultato.append(char)  # \n, \t, accentate → invariati
    return "".join(risultato)

def decifra_testo(testo: str, shift: int = 7, decifra_spazi: bool = True) -> str:
    shift = shift % 26
    risultato = []
    for char in testo:
        if _is_ascii_alpha(char):
            base = ord('a') if char.islower() else ord('A')
            risultato.append(chr((ord(char) - base - shift) % 26 + base))
        elif decifra_spazi and char.isprintable() and ord(char) < 128:
            risultato.append(chr(ord(char) - shift))
        else:
            risultato.append(char)  # \n, \t, accentate → invariati
    return "".join(risultato)

def test_reversibilita():
    testo_prova = "INTRODUZIONE L'historia si può veramente deffinire una guerra illustre contro il Tempo"
    shift = 7
    
    # Test cifratura/decifratura TOTALE
    cifrato = cifra_testo(testo_prova, shift=shift, cifra_spazi=True)
    decifrato = decifra_testo(cifrato, shift=shift, decifra_spazi=True)
    
    print(f"Originale: {testo_prova}")
    print(f"Cifrato:   {cifrato}")
    print(f"Decifrato: {decifrato}")
    
    if testo_prova == decifrato:
        print("✅ Test reversibilità superato!")
    else:
        print("❌ ERRORE: Il testo decifrato non coincide.")

test_reversibilita()

def main():
    file_input = "Esercizio Promessi sposi/psposi_pg45334.txt"
    file_output = "Esercizio Promessi sposi/promessi_sposi_pulito.txt"
    
    try:
        with open(file_input, 'r', encoding='utf-8') as f_in:
            contenuto = f_in.read()
            
        testo_pulito = pulisci_caratteri_e_spazi(rimuovi_tag_illustrazioni(isola_solo_romanzo(contenuto)))
        
        with open(file_output, 'w', encoding='utf-8') as f_out:
            f_out.write(testo_pulito)
            
        # Cifratura
        with open("Esercizio Promessi sposi/cifrato_solo_parole.txt", 'w', encoding='utf-8') as f1:
            f1.write(cifra_testo(testo_pulito, shift=7, cifra_spazi=False))
        with open("Esercizio Promessi sposi/cifrato_totale.txt", 'w', encoding='utf-8') as f2:
            f2.write(cifra_testo(testo_pulito, shift=7, cifra_spazi=True))
            
        dizionario_frequenze = conta_occorrenze_parole(testo_pulito)
        parole_da_escludere = {"il", "lo", "la", "i", "gli", "le", "un", "di", "a", "da", "in", "con", "su", "per", "e", "o", "ma", "che", "non", "si", "questo"}
        dizionario_filtrato = filtra_parole_reali(dizionario_frequenze, parole_da_escludere)
        
        # Output Console e File
        mostra_top_n(dizionario_filtrato, n=5)
        with open("Esercizio Promessi sposi/top_20_parole.txt", 'w', encoding='utf-8') as f_top:
            mostra_top_n(dizionario_filtrato, n=20, n_chars=3, show_details=True, file=f_top)
            
        mostra_bottom_n(dizionario_filtrato, n=5)
        mostra_media_conteggio(dizionario_filtrato)
        cerca_sottoparole(dizionario_frequenze, 'arma')
        print(f"\n{' FINE ':=^40}\n")

    except FileNotFoundError:
        print(f"Errore: Il file '{file_input}' non è stato trovato.")

if __name__ == "__main__":
    main()

