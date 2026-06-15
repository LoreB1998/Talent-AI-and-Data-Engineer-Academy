import os
import json
from dotenv import load_dotenv
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeImageOptions, ImageData
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

load_dotenv()

KEY = os.getenv("AZ_CONTENTSAFETY_KEY")
ENDPOINT = os.getenv("AZ_CONTENTSAFETY_ENDPOINT")

# Estensioni supportate da Azure Content Safety
ESTENSIONI_AMMESSE = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif", ".tiff"}


def analizza_immagine(percorso_immagine: str):
    """
    Legge l'immagine in binario e la invia ad Azure Content Safety per rilevare violazioni.
    Restituisce il risultato dell'analisi o None in caso di errore.
    """
    if not KEY or not ENDPOINT:
        print("Credenziali Content Safety mancanti.")
        return None

    client = ContentSafetyClient(ENDPOINT, AzureKeyCredential(KEY))
    
    try:
        # Lettura dell'immagine in modalità binaria (bytes)
        with open(percorso_immagine, "rb") as f:
            image_bytes = f.read()
            
        request = AnalyzeImageOptions(image=ImageData(content=image_bytes))
        return client.analyze_image(request)
        
    except HttpResponseError as e:
        print(f"Errore API Content Safety per {os.path.basename(percorso_immagine)}: {e}")
        return None
    except Exception as e:
        print(f"Errore durante la lettura del file {os.path.basename(percorso_immagine)}: {e}")
        return None


def elabora_risultato(nome_file: str, risultato, report_ok: list, report_ko: list):
    """
    Analizza le categorie di Content Safety (Hate, SelfHarm, Sexual, Violence),
    stampa l'esito a video e popola le liste OK / KO.
    """
    violazioni_trovate = [
        cat for cat in risultato.categories_analysis
        if cat.severity is not None and cat.severity > 0
    ]

    if violazioni_trovate:
        print("Stato: VIOLAZIONE RILEVATA")
        for v in violazioni_trovate:
            print(f"  -> {v.category}: gravità {v.severity}")
            report_ko.append({
                "file_name": nome_file,
                "violazione": str(v.category),
                "gravita": v.severity
            })
    else:
        print("Stato: OK")
        report_ok.append({
            "file_name": nome_file
        })


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Cartella di input per le immagini
    dir_input = os.path.join(base_dir, "immagini_da_verificare")
    
    # File di output (ok_1 e ko_1)
    output_ok_1 = os.path.join(base_dir, "immagini_ok_step1.json")
    output_ko_1 = os.path.join(base_dir, "immagini_ko_step1.json")

    report_ok_1: list = []
    report_ko_1: list = []
    errori_elaborazione = 0

    # Creazione automatica della cartella di input se non esiste
    if not os.path.exists(dir_input):
        os.makedirs(dir_input)
        print(f"Cartella '{dir_input}' creata. Inserisci lì dentro le immagini da verificare e riavvia lo script.")
        return

    # Recupero e filtraggio dei file multimediali validi
    immagini_list = [
        f for f in os.listdir(dir_input)
        if os.path.splitext(f)[1].lower() in ESTENSIONI_AMMESSE
    ]
    
    totale_immagini = len(immagini_list)
    if totale_immagini == 0:
        print(f"Nessuna immagine valida trovata in: {dir_input}")
        print(f"Formati supportati: {', '.join(ESTENSIONI_AMMESSE)}")
        return

    print(f"=== Inizio Pipeline Immagini: {totale_immagini} file da analizzare ===")
    
    # --- FASE UNICA: Azure Content Safety Image ---
    for i, nome_file in enumerate(immagini_list, 1):
        percorso_completo = os.path.join(dir_input, nome_file)
        print(f"\n--- Analisi Immagine {i}/{totale_immagini} ---")
        print(f"File: {nome_file}")

        risultato = analizza_immagine(percorso_completo)
        if risultato:
            elabora_risultato(nome_file, risultato, report_ok_1, report_ko_1)
        else:
            print("Errore durante l'analisi — file saltato.")
            errori_elaborazione += 1

    # Scrittura dei file JSON parziali
    with open(output_ok_1, "w", encoding="utf-8") as f:
        json.dump(report_ok_1, f, indent=4, ensure_ascii=False)
    with open(output_ko_1, "w", encoding="utf-8") as f:
        json.dump(report_ko_1, f, indent=4, ensure_ascii=False)

    print(f"\nAnalisi completata. Salvati {output_ok_1} e {output_ko_1}")

    # --- RECAP FINALE A VIDEO ---
    print("\n" + "="*40)
    print("RECAP FINALE MODERAZIONE IMMAGINI")
    print("="*40)
    print(f"Immagini Approvate (immagini_ok_step1):  {len(report_ok_1)} / {totale_immagini}")
    print(f"Immagini Rifiutate (immagini_ko_step1):  {len(report_ko_1)} / {totale_immagini}")
    
    if errori_elaborazione > 0:
        print(f"Errori di caricamento/API:              {errori_elaborazione} / {totale_immagini}")
    print("="*40)


if __name__ == "__main__":
    main()