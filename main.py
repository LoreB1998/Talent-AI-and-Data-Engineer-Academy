import json
from pathlib import Path

from agent import get_openai_client, carica_pdf, estrai_testo_da_pdf, parsa_json_estrazione
from backend import get_clienti, get_articoli
from conferma_ordine import crea_conferma_da_risultato
from matching import valida_ordine
from config import PDF_DIR, OUTPUT_DIR, CREA_CONFERMA_ORDINE


def processa_pdf(openai_client, pdf_path: Path, clienti: list[dict], articoli: list[dict]) -> None:
    print(f"\n{'=' * 60}")
    print(f"Processo: {pdf_path.name}")
    print("=" * 60)

    print("Carico il file e chiedo l'estrazione all'agente...")
    file_id = carica_pdf(openai_client, pdf_path)
    testo_estratto = estrai_testo_da_pdf(openai_client, file_id)

    print("\n--- JSON estratto dal documento (grezzo, non validato) ---\n")
    print(testo_estratto)

    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / f"{pdf_path.stem}_ESTRATTO.txt").write_text(testo_estratto, encoding="utf-8")

    try:
        dati_estratti = parsa_json_estrazione(testo_estratto)
    except json.JSONDecodeError as e:
        print(f"\n[ERRORE] La risposta dell'agente non è un JSON valido: {e}")
        print(f"Testo grezzo salvato in: {OUTPUT_DIR / f'{pdf_path.stem}_ESTRATTO.txt'} per ispezione manuale.")
        return

    print("\nValido cliente e articoli in locale (Python + backend REST)...")
    risultato = valida_ordine(dati_estratti, clienti, articoli)

    print("\n--- Risultato validato ---\n")
    print(json.dumps(risultato, ensure_ascii=False, indent=2))

    if CREA_CONFERMA_ORDINE:
        print("\nCreo la conferma d'ordine in Assets...")
        esito_conferma = crea_conferma_da_risultato(risultato, pdf_path.stem)
        print(json.dumps(esito_conferma, ensure_ascii=False, indent=2))
        risultato["conferma_ordine"] = esito_conferma

    (OUTPUT_DIR / f"{pdf_path.stem}.json").write_text(
        json.dumps(risultato, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n[OK] Salvato in: {OUTPUT_DIR / f'{pdf_path.stem}.json'}")


def main():
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"Nessun PDF trovato in '{PDF_DIR}/'.")
        return

    print(f"Trovati {len(pdf_files)} PDF: {[p.name for p in pdf_files]}")
    print(f"Modalita': {'estrazione + validazione + creazione conferma' if CREA_CONFERMA_ORDINE else 'solo estrazione e validazione'}")

    print("\nScarico clienti e articoli dal backend...")
    clienti = get_clienti()
    articoli = get_articoli()
    print(f"  {len(clienti)} clienti, {len(articoli)} articoli caricati.")

    openai_client = get_openai_client()

    for pdf_path in pdf_files:
        processa_pdf(openai_client, pdf_path, clienti, articoli)

    print(f"\n{'=' * 60}\nCompletato. Risultati in '{OUTPUT_DIR}/'.\n{'=' * 60}")


if __name__ == "__main__":
    main()
