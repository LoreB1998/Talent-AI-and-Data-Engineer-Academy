import os
import json
from datetime import datetime
from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder
from dotenv import load_dotenv

OUTPUT_FILE = "Esercitazioni Python/Foundry/11_Agent_Marketing/campagne_marketing_no_orch.json"


def carica_storico():
    """Carica lo storico esistente dal file JSON, se presente."""
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def salva_storico(storico):
    """Salva lo storico aggiornato nel file JSON."""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(storico, f, ensure_ascii=False, indent=2)


def estrai_testo_risposta(message):
    """Estrae il testo dal primo blocco di contenuto del messaggio assistant."""
    for block in message.content:
        if hasattr(block, "text"):
            txt = getattr(block, "text")
            if hasattr(txt, "value"):
                return txt.value
            return str(txt)
        elif isinstance(block, dict):
            if "text" in block:
                t = block.get("text")
                if isinstance(t, dict) and "value" in t:
                    return t["value"]
                return str(t)
            return str(block)
        else:
            return str(block)
    return None


def parse_risposta_json(testo_risposta):
    """
    Tenta di parsare la risposta dell'agente come JSON.
    Se fallisce (es. l'agente ha aggiunto testo extra), ritorna un dict
    con il testo grezzo in un campo 'raw'.
    """
    try:
        testo_pulito = testo_risposta.strip()
        if testo_pulito.startswith("```"):
            testo_pulito = testo_pulito.split("```")[1]
            if testo_pulito.startswith("json"):
                testo_pulito = testo_pulito[4:]
        return json.loads(testo_pulito.strip())
    except (json.JSONDecodeError, IndexError):
        return {"raw": testo_risposta}


def chiama_agente(agents_client, agent_id, messaggio_input):
    """
    Funzione centrale dell'orchestrazione manuale: crea un thread nuovo,
    invia un messaggio a un agente specifico, attende il completamento
    del run e ritorna la risposta già parsata come dict.

    E' QUESTA la funzione che il tuo codice Python chiama "a mano" ogni
    volta che vuole far lavorare un agente specifico - non c'e' nessun
    agente-LLM che decide al posto tuo quale invocare.

    Ritorna una tupla (dati_strutturati, info_run) dove info_run contiene
    i metadati utili per il log/JSON (thread_id, run_id, status).
    """
    thread = agents_client.threads.create()

    agents_client.messages.create(
        thread_id=thread.id,
        role="user",
        content=messaggio_input,
    )

    run = agents_client.runs.create_and_process(
        thread_id=thread.id,
        agent_id=agent_id,
    )

    info_run = {
        "thread_id": thread.id,
        "run_id": run.id,
        "status": str(run.status),
    }

    if run.status == "failed":
        info_run["error"] = str(run.last_error)
        return None, info_run

    messages = agents_client.messages.list(
        thread_id=thread.id,
        order=ListSortOrder.ASCENDING,
    )

    testo_risposta = None
    for message in messages:
        if message.role == "assistant":
            testo_risposta = estrai_testo_risposta(message)

    if testo_risposta is None:
        return None, info_run

    return parse_risposta_json(testo_risposta), info_run


def main():
    AZ_FOUNDRY_ENDPOINT = os.getenv("AZ_FOUNDRY_ENDPOINT")
    AZ_FOUNDRY_MODEL_NAME = os.getenv("AZ_FOUNDRY_MODEL_NAME")
    if not AZ_FOUNDRY_ENDPOINT:
        raise ValueError("AZ_FOUNDRY_ENDPOINT environment variable is required")
    if not AZ_FOUNDRY_MODEL_NAME:
        raise ValueError("AZ_FOUNDRY_MODEL_NAME environment variable is required")

    # create client
    agents_client = AgentsClient(
        endpoint=AZ_FOUNDRY_ENDPOINT,  # type: ignore
        credential=DefaultAzureCredential(),  # az login !!
    )

    targeting_agent = None
    marketer_agent = None
    content_safety_agent = None

    try:
        # ------------------------------------------------------------------
        # 1) AGENTE 1: TargetingAgent
        #    Riceve la descrizione del prodotto e individua il pubblico
        #    target più adatto in base alla tipologia di prodotto.
        # ------------------------------------------------------------------
        targeting_agent = agents_client.create_agent(
            model=str(AZ_FOUNDRY_MODEL_NAME),
            name="TargetingAgent",
            instructions=(
                "Sei un esperto di Market Research. Quando ricevi la descrizione di un "
                "prodotto, analizza la tipologia di prodotto e individua il pubblico target "
                "più adatto.\n\n"
                "Restituisci SOLO un oggetto JSON valido (senza testo aggiuntivo, senza "
                "markdown, senza backtick) con questa struttura esatta:\n"
                "{\n"
                '  "categoria_prodotto": "categoria di appartenenza del prodotto",\n'
                '  "target_demografico": "fascia di eta, genere, reddito, etc.",\n'
                '  "interessi_target": ["interesse 1", "interesse 2", "..."],\n'
                '  "tono_comunicazione": "tono di voce consigliato per parlare a questo target"\n'
                "}\n\n"
                "Rispondi sempre e solo con l'oggetto JSON, nessun commento prima o dopo. "
                "Usa la lingua italiana."
            ),
        )

        # ------------------------------------------------------------------
        # 2) AGENTE 2: MarketerAgent
        #    Riceve la descrizione del prodotto E le informazioni sul target
        #    (gliele passiamo noi nel prompt, costruendolo a mano) e scrive
        #    la newsletter.
        # ------------------------------------------------------------------
        marketer_agent = agents_client.create_agent(
            model=str(AZ_FOUNDRY_MODEL_NAME),
            name="MarketerAgent",
            instructions=(
                "Sei un esperto di Marketing. Riceverai la descrizione di un prodotto "
                "insieme alle informazioni sul pubblico target (categoria prodotto, target "
                "demografico, interessi, tono di comunicazione consigliato). Se ricevi "
                "anche dei 'problemi rilevati' da una precedente revisione, correggi il "
                "testo per risolverli.\n\n"
                "Componi il testo per una campagna di marketing (newsletter promozionale) "
                "di massimo 200 parole, focalizzata sui benefici, scritta usando il tono di "
                "comunicazione indicato e pensata specificamente per il target ricevuto.\n\n"
                "Restituisci SOLO un oggetto JSON valido (senza testo aggiuntivo, senza "
                "markdown, senza backtick) con questa struttura esatta:\n"
                "{\n"
                '  "caratteristiche_principali": ["...", "..."],\n'
                '  "punti_di_forza": ["USP 1", "USP 2", "..."],\n'
                '  "newsletter": "testo della newsletter promozionale"\n'
                "}\n\n"
                "Rispondi sempre e solo con l'oggetto JSON, nessun commento prima o dopo. "
                "Usa la lingua italiana."
            ),
        )

        # ------------------------------------------------------------------
        # 3) AGENTE 3: ContentSafetyAgent
        #    Riceve la newsletter scritta dal MarketerAgent e verifica che
        #    non contenga claim esagerati/non veritieri, linguaggio
        #    discriminatorio o problemi di compliance, prima che diventi
        #    output finale.
        # ------------------------------------------------------------------
        content_safety_agent = agents_client.create_agent(
            model=str(AZ_FOUNDRY_MODEL_NAME),
            name="ContentSafetyAgent",
            instructions=(
                "Sei un revisore di compliance per contenuti di marketing. Riceverai il "
                "testo di una newsletter promozionale (ed eventualmente la descrizione del "
                "prodotto e del target a cui e' indirizzata) e devi verificare che il "
                "contenuto sia appropriato e sicuro da pubblicare.\n\n"
                "Controlla in particolare:\n"
                "- Claim esagerati, non veritieri o non verificabili (es. \"cura tutte le "
                "malattie\", \"il migliore al mondo\" senza alcuna prova).\n"
                "- Claim a rischio legale/regolatorio per la categoria di prodotto (es. "
                "affermazioni di tipo medico o salutistico su alimenti, cosmetici, "
                "integratori).\n"
                "- Linguaggio discriminatorio, offensivo o stereotipi negativi verso il "
                "target o altri gruppi.\n"
                "- Contenuto manipolativo o ingannevole verso il consumatore.\n\n"
                "Restituisci SOLO un oggetto JSON valido (senza testo aggiuntivo, senza "
                "markdown, senza backtick) con questa struttura esatta:\n"
                "{\n"
                '  "approvato": true oppure false,\n'
                '  "problemi_rilevati": ["descrizione problema 1", "..."],\n'
                '  "suggerimenti_correzione": "indicazioni su come correggere il testo, '
                'vuoto se approvato"\n'
                "}\n\n"
                "Se il testo non presenta alcun problema, imposta 'approvato' a true e "
                "lascia gli altri due campi vuoti. Sii rigoroso ma ragionevole: non "
                "segnalare il normale linguaggio enfatico tipico della pubblicita' (es. "
                "\"gusto autentico\", \"qualita' superiore\"), solo claim realmente "
                "problematici. Rispondi sempre e solo con l'oggetto JSON. Usa la lingua "
                "italiana."
            ),
        )

        # ------------------------------------------------------------------
        # 4) LOOP PRINCIPALE - ORCHESTRAZIONE MANUALE
        #    A differenza della versione con Connected Agents, qui SIAMO NOI
        #    (il codice Python) a decidere l'ordine di chiamata, a costruire
        #    i messaggi da passare a ciascun agente, e a gestire la logica
        #    "se non approvato, riscrivi". Non c'e' nessun agente-LLM che
        #    decide al posto nostro: ogni passaggio e' un if/else esplicito.
        # ------------------------------------------------------------------
        storico = carica_storico()

        while True:
            articolo = input("Inserisci la descrizione del prodotto: (QUIT per uscire) ")
            if articolo.upper() == "QUIT":
                break

            sub_agent_calls = []  # log di debug, analogo a "chiamate" nella versione precedente

            # --- STEP 1: Targeting ------------------------------------------------
            risultato_targeting, info_targeting = chiama_agente(
                agents_client,
                targeting_agent.id,
                articolo,
            )
            sub_agent_calls.append({"agente": "targeting_agent", "info_run": info_targeting})

            print(f"[1/3] targeting_agent -> status: {info_targeting['status']}")

            if risultato_targeting is None:
                print(f"  Errore: {info_targeting.get('error', 'risposta vuota')}")
                continue  # salta al prossimo prodotto, non ha senso proseguire senza target

            # --- STEP 2: Marketing --------------------------------------------------
            # Costruiamo NOI il messaggio per il marketer, includendo l'output
            # del targeting. Questo e' l'equivalente "manuale" di quello che
            # nella versione Connected Agent faceva il modello orchestratore.
            messaggio_marketer = (
                f"Descrizione prodotto: {articolo}\n\n"
                f"Informazioni sul target:\n{json.dumps(risultato_targeting, ensure_ascii=False, indent=2)}"
            )

            risultato_marketing, info_marketer = chiama_agente(
                agents_client,
                marketer_agent.id,
                messaggio_marketer,
            )
            sub_agent_calls.append({"agente": "marketer_agent", "info_run": info_marketer})

            print(f"[2/3] marketer_agent -> status: {info_marketer['status']}")

            if risultato_marketing is None:
                print(f"  Errore: {info_marketer.get('error', 'risposta vuota')}")
                continue

            # --- STEP 3: Content Safety ---------------------------------------------
            newsletter_testo = risultato_marketing.get("newsletter", "")
            messaggio_safety = (
                f"Newsletter da verificare:\n{newsletter_testo}\n\n"
                f"Descrizione prodotto originale: {articolo}\n"
                f"Target a cui e' indirizzata: {json.dumps(risultato_targeting, ensure_ascii=False)}"
            )

            risultato_safety, info_safety = chiama_agente(
                agents_client,
                content_safety_agent.id,
                messaggio_safety,
            )
            sub_agent_calls.append({"agente": "content_safety_agent", "info_run": info_safety})

            print(f"[3/3] content_safety_agent -> status: {info_safety['status']}")

            revisione_manuale_consigliata = False

            if risultato_safety is None:
                print(f"  Errore: {info_safety.get('error', 'risposta vuota')}")
                # Il safety check e' fallito tecnicamente (non "non approvato",
                # ma un errore di esecuzione): per prudenza segnaliamo la
                # newsletter per revisione manuale invece di pubblicarla alla cieca.
                revisione_manuale_consigliata = True

            elif not risultato_safety.get("approvato", False):
                # --- STEP 4 (condizionale): Riscrittura ------------------------------
                # Qui e' il punto chiave dell'orchestrazione manuale: decidiamo
                # NOI, con un if esplicito, di richiamare il marketer una sola
                # volta, passandogli i problemi rilevati.
                print("  ⚠ Contenuto non approvato, richiedo una correzione al marketer_agent...")

                messaggio_correzione = (
                    f"Descrizione prodotto: {articolo}\n\n"
                    f"Informazioni sul target:\n{json.dumps(risultato_targeting, ensure_ascii=False, indent=2)}\n\n"
                    f"La newsletter precedente NON è stata approvata dal revisore di "
                    f"compliance. Correggi il testo per risolvere questi problemi:\n"
                    f"{json.dumps(risultato_safety.get('problemi_rilevati', []), ensure_ascii=False)}\n\n"
                    f"Suggerimenti di correzione: {risultato_safety.get('suggerimenti_correzione', '')}"
                )

                risultato_marketing_corretto, info_marketer_2 = chiama_agente(
                    agents_client,
                    marketer_agent.id,
                    messaggio_correzione,
                )
                sub_agent_calls.append(
                    {"agente": "marketer_agent (correzione)", "info_run": info_marketer_2}
                )

                print(f"  marketer_agent (correzione) -> status: {info_marketer_2['status']}")

                if risultato_marketing_corretto is not None:
                    # Sostituiamo il risultato di marketing con la versione corretta.
                    # NOTA: come deciso, non richiamiamo di nuovo il content_safety_agent
                    # per evitare loop infiniti; segnaliamo solo che e' stata corretta.
                    risultato_marketing = risultato_marketing_corretto
                else:
                    # Anche la correzione e' fallita: meglio segnalare per revisione
                    # manuale piuttosto che procedere con un testo non approvato.
                    revisione_manuale_consigliata = True

            # --- Composizione del risultato finale e salvataggio --------------------
            record = {
                "timestamp": datetime.now().isoformat(),
                "prodotto_input": articolo,
                "sub_agent_calls": sub_agent_calls,
                "risultato": {
                    "targeting": risultato_targeting,
                    "marketing": risultato_marketing,
                    "content_safety": risultato_safety,
                    "revisione_manuale_consigliata": revisione_manuale_consigliata,
                },
            }

            storico.append(record)
            salva_storico(storico)

            print("\n--- Risultato finale ---")
            print(json.dumps(record["risultato"], ensure_ascii=False, indent=2))
            print(f"✓ Salvato in {OUTPUT_FILE}\n")

    finally:
        # delete agent - eseguito sempre, anche in caso di errori o Ctrl+C
        for agent in (content_safety_agent, marketer_agent, targeting_agent):
            if agent is not None:
                try:
                    agents_client.delete_agent(agent_id=agent.id)
                except Exception as e:
                    print(f"Errore durante la cancellazione dell'agente {agent.id}: {e}")
        print("Agenti eliminati.")


if __name__ == "__main__":
    load_dotenv()  # Carica le variabili d'ambiente dal file .env
    main()