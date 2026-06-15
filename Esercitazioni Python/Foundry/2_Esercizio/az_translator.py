import os
from dotenv import load_dotenv
from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential


# Lingue supportate (sottoinsieme significativo)
SUPPORTED_LANGUAGES = {
    "en": "Inglese",
    "fr": "Francese",
    "de": "Tedesco",
    "es": "Spagnolo",
    "pt": "Portoghese",
    "ru": "Russo",
    "ja": "Giapponese",
    "zh-Hans": "Cinese semplificato",
    "tr": "Turco",
    "it": "Italiano",
}


def translate(client: TextTranslationClient, text: str, target_languages: list[str]) -> None:
    """Traduce il testo nelle lingue target tramite SDK Azure Translator."""

    result = client.translate(
        body=[text],
        to_language=target_languages,
        client_trace_id=None
    )

    # Mostra la lingua sorgente rilevata automaticamente
    detected = result[0].detected_language
    print(f"  Lingua rilevata: {SUPPORTED_LANGUAGES.get(detected.language, detected.language)} " # type: ignore
          f"(confidenza: {detected.score:.2f})") #type: ignore

    print()

    # Traduzioni
    for t in result[0].translations:
        lang_name = SUPPORTED_LANGUAGES.get(t.language, t.language)
        print(f"  [{lang_name}] {t.text}")


def scegli_lingue() -> list[str]:
    """Mostra il menu delle lingue disponibili e restituisce quelle scelte dall'utente."""

    print("\nLingue disponibili:")
    for codice, nome in SUPPORTED_LANGUAGES.items():
        print(f"  {codice:<10} {nome}")
    print(f"  {'all':<10} Tutte le lingue")

    scelta = input("\nInserisci i codici delle lingue separati da virgola (es. en,fr,de) o 'all': ")

    if scelta.strip().lower() == "all":
        return list(SUPPORTED_LANGUAGES.keys())

    # Filtra solo i codici validi tra quelli inseriti dall'utente
    codici = [c.strip() for c in scelta.split(",")]
    validi = [c for c in codici if c in SUPPORTED_LANGUAGES]
    non_validi = [c for c in codici if c not in SUPPORTED_LANGUAGES]

    if non_validi:
        print(f"Codici non riconosciuti e ignorati: {', '.join(non_validi)}")

    if not validi:
        print("Nessuna lingua valida selezionata. Uso inglese come default.")
        return ["en"]

    return validi


def main():
    load_dotenv()

    api_key  = os.getenv("AZ_TRANSLATOR_KEY")
    endpoint = os.getenv("AZ_TRANSLATOR_ENDPOINT")
    region   = os.getenv("AZ_TRANSLATOR_REGION")

    assert api_key and region, "Mancano AZ_TRANSLATOR_KEY o AZ_TRANSLATOR_REGION nel .env"

    # Occhio alla regione: deve corrispondere a quella della risorsa Azure,
    # altrimenti l'autenticazione fallisce con 401.
    client = TextTranslationClient(
        endpoint=endpoint, #type: ignore
        credential=AzureKeyCredential(api_key),
        region=region
    )

    print("=== Azure Translator ===")
    print("Digita 'quit' per uscire.\n")

    while True:
        testo = input("Testo da tradurre: ").strip()

        if testo.lower() == "quit":
            print("Uscita dal programma.")
            break

        if not testo:
            print("Testo vuoto, riprova.")
            continue

        target_languages = scegli_lingue()

        print("\nTraduzioni:")
        translate(client, testo, target_languages)


if __name__ == "__main__":
    main()