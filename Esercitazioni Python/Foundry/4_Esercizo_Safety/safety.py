import os
import json
from dotenv import load_dotenv
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from openai import OpenAI, BadRequestError

load_dotenv()

KEY = os.getenv("AZ_CONTENTSAFETY_KEY")
ENDPOINT = os.getenv("AZ_CONTENTSAFETY_ENDPOINT")
AZ_OPENAI_KEY = os.getenv("AZ_OPENAI_KEY")
AZ_OPENAI_ENDPOINT = os.getenv("AZ_OPENAI_ENDPOINT")
AZ_OPENAI_DEPLOYMENT = os.getenv("AZ_OPENAI_DEPLOYMENT")
AZ_OPENAI_API_VERSION = os.getenv("AZ_OPENAI_API_VERSION", "2024-02-01")

client_openai = OpenAI(
    api_key=AZ_OPENAI_KEY,
    base_url=AZ_OPENAI_ENDPOINT
)


def analizza_post(testo_post: str):
    """
    Invia il testo ad Azure Content Safety per rilevare violazioni esplicite.
    Restituisce il risultato dell'analisi o None in caso di errore.
    """
    if not KEY or not ENDPOINT:
        print("Credenziali Content Safety mancanti.")
        return None

    client = ContentSafetyClient(ENDPOINT, AzureKeyCredential(KEY))  # type: ignore
    request = AnalyzeTextOptions(text=testo_post)
    try:
        return client.analyze_text(request)
    except HttpResponseError as e:
        print(f"Errore API Content Safety: {e}")
        return None


def elabora_risultato(i: int, testo: str, risultato, report_ok: list, report_ko: list):
    """
    Analizza il risultato di Content Safety, stampa a video
    e aggiorna le liste di report OK / KO per lo Step 1.
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
                "post_id": i,
                "testo": testo,
                "violazione": str(v.category),
                "gravita": v.severity
            })
    else:
        print("Stato: OK")
        report_ok.append({
            "post_id": i,
            "testo": testo
        })


def analizza_con_openai(testo: str) -> dict:
    """
    Invia il testo ad Azure OpenAI per un controllo qualitativo semantico.
    Gestisce in modo sicuro le censure dei filtri di Azure sia in ingresso che in uscita.
    """
    system_prompt = """Sei un moderatore di contenuti social estremamente acuto e attento alle sfumature di significato.
Il tuo compito è rilevare contenuti problematici, sia ESPLICITI che VELATI, IMPLICITI o CAMUFFATI.

Presta massima attenzione a:
1. Insulti velati, commenti passivo-aggressivi o bullismo espresso tramite sarcasmo malevolo.
2. Incitamento all'odio mascherato (dog-whistling, stereotipi sottili, discriminazione indiretta).
3. Tentativi di aggirare la moderazione (es. uso di asterischi, leetspeak, parole storpiate come "m0rt3", "stst").
4. Contenuti illegali, pericolosi o spam mascherato da raccomandazione disinteressata.

IMPORTANTE: 
- Un post generico, banale, stupido o poco interessante NON va rifiutato.
- Opinioni forti, critiche accese o ironia sana e non offensiva VANNO APPROVATE.
- Rifiuta SOLO se percepisci un reale intento dannoso, discriminatorio, offensivo o ingannevole, anche se nascosto tra le righe.

Rispondi SOLO con un oggetto JSON valido, senza markdown né testo aggiuntivo:
{"esito": "APPROVATO" oppure "RIFIUTATO", "motivazione": "breve spiegazione che specifichi la violazione esplicita o il sottotesto rilevato"}"""

    try:
        response = client_openai.chat.completions.create(
            model=AZ_OPENAI_DEPLOYMENT,  # type: ignore
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": testo}
            ]
        )
        
        content = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason

        # 1. GESTIONE FILTRI DI SICUREZZA IN USCITA
        if content is None:
            if finish_reason == "content_filter":
                return {
                    "esito": "RIFIUTATO", 
                    "motivazione": "Bloccato in USCITA: la risposta generata viola le policy di Azure OpenAI"
                }
            else:
                return {
                    "esito": "ERRORE", 
                    "motivazione": f"Risposta vuota dall'API. Finish reason: {finish_reason}"
                }

        return json.loads(content)
        
    except BadRequestError as e:
        # 2. GESTIONE FILTRI DI SICUREZZA IN INGRESSO
        if "content_filter" in str(e):
            return {
                "esito": "RIFIUTATO", 
                "motivazione": "Bloccato in INGRESSO: il testo del post viola le policy di Azure (es. violenza, odio)"
            }
        print(f"Errore di richiesta (Bad Request): {e}")
        return {"esito": "ERRORE", "motivazione": f"Richiesta non valida: {str(e)}"}
        
    except json.JSONDecodeError as e:
        print(f"Errore parsing JSON risposta LLM: {e}")
        return {"esito": "ERRORE", "motivazione": f"JSON non valido: {e}"}
        
    except Exception as e:
        print(f"Errore OpenAI generico: {e}")
        return {"esito": "ERRORE", "motivazione": str(e)}


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_input = os.path.join(base_dir, "post_da_verificare.txt")
    
    # Definizione pulita dei file di output per ogni step
    output_ok_1 = os.path.join(base_dir, "post_ok_step1.json")
    output_ko_1 = os.path.join(base_dir, "post_ko_step1.json")
    output_ko_2 = os.path.join(base_dir, "post_rifiutati_step2.json")
    output_finale = os.path.join(base_dir, "post_approvati_finali.json")

    report_ok_1: list = []
    report_ko_1: list = []
    report_ko_2: list = []
    report_approvati_finali: list = []
    report_errori_step2: list = []

    # --- Lettura iniziale ---
    if not os.path.exists(file_input):
        print(f"File non trovato: {file_input}")
        return

    with open(file_input, "r", encoding="utf-8") as f:
        post_list = [line.strip() for line in f.readlines() if line.strip()]
    
    totale_post = len(post_list)
    if totale_post == 0:
        print("Il file di input è vuoto o contiene solo righe bianche.")
        return

    print(f"=== Inizio Pipeline: {totale_post} post da analizzare ===")
    
    # --- FASE 1: Azure Content Safety ---
    print("\n=== Fase 1: Azure Content Safety ===")
    for i, testo in enumerate(post_list, 1):
        print(f"\n--- Analisi Post {i} ---")
        print(f"Testo: {testo[:80]}{'...' if len(testo) > 80 else ''}")

        risultato = analizza_post(testo)
        if risultato:
            elabora_risultato(i, testo, risultato, report_ok_1, report_ko_1)
        else:
            print("Errore durante l'analisi Content Safety — post saltato.")

    # Scrittura dei file dello Step 1 (ok_1 e ko_1)
    with open(output_ok_1, "w", encoding="utf-8") as f:
        json.dump(report_ok_1, f, indent=4, ensure_ascii=False)
    with open(output_ko_1, "w", encoding="utf-8") as f:
        json.dump(report_ko_1, f, indent=4, ensure_ascii=False)

    print(f"\nFase 1 completata. Salvati {output_ok_1} e {output_ko_1}")

    # --- FASE 2: Analisi qualitativa OpenAI ---
    print("\n=== Fase 2: Analisi qualitativa Azure OpenAI ===")

    if not report_ok_1:
        print("Nessun post ha superato il primo step. Fase 2 saltata.")
    else:
        for entry in report_ok_1:
            print(f"\nControllo post ID {entry['post_id']} con LLM...")
            risultato_llm = analizza_con_openai(entry["testo"])
            
            esito = risultato_llm.get("esito")
            dati_post = {
                "post_id": entry["post_id"],
                "testo": entry["testo"],
                "motivazione": risultato_llm.get("motivazione")
            }

            # Smistamento chirurgico in base all'esito dell'LLM
            if esito == "APPROVATO":
                report_approvati_finali.append(dati_post)
            elif esito == "RIFIUTATO":
                report_ko_2.append(dati_post)
            else:
                report_errori_step2.append(dati_post)

            print(f"  Esito LLM: {esito} — {risultato_llm.get('motivazione')}")

        # Scrittura dei file dello Step 2 (ko_2 e Accettati da entrambi)
        with open(output_ko_2, "w", encoding="utf-8") as f:
            json.dump(report_ko_2, f, indent=4, ensure_ascii=False)
        with open(output_finale, "w", encoding="utf-8") as f:
            json.dump(report_approvati_finali, f, indent=4, ensure_ascii=False)

    # --- RECAP FINALE A VIDEO (Nessun file di report generato) ---
    print("\n" + "="*40)
    print("RECAP FINALE PIPELINE DI MODERAZIONE")
    print("="*40)
    print(f"Approvati finali (Entrambi i controlli): {len(report_approvati_finali)} / {totale_post}")
    print(f"Rifiutati al primo step (ko_1):          {len(report_ko_1)} / {totale_post}")
    print(f"Rifiutati al secondo step (ko_2):        {len(report_ko_2)} / {totale_post}")
    
    if len(report_errori_step2) > 0:
        print(f"Errori di elaborazione LLM:              {len(report_errori_step2)} / {totale_post}")
    print("="*40)
    print("I file parziali e finali sono stati aggiornati correttamente.")


if __name__ == "__main__":
    main()