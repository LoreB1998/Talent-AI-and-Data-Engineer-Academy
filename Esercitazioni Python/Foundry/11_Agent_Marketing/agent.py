import os
import json
from datetime import datetime
from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder, ConnectedAgentTool
from dotenv import load_dotenv

OUTPUT_FILE = "Esercitazioni Python/Foundry/11_Agent_Marketing/campagne_marketing.json"


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
        # Rimuove eventuali backtick markdown (```json ... ```)
        testo_pulito = testo_risposta.strip()
        if testo_pulito.startswith("```"):
            testo_pulito = testo_pulito.split("```")[1]
            if testo_pulito.startswith("json"):
                testo_pulito = testo_pulito[4:]
        return json.loads(testo_pulito.strip())
    except (json.JSONDecodeError, IndexError):
        return {"raw": testo_risposta}


def estrai_chiamate_connected_agents(agents_client, thread_id, run_id):
    """
    Recupera i run step dell'orchestratore per vedere quali sub-agent sono
    stati chiamati e cosa hanno risposto. Utile per debug/logging: ti mostra
    cosa ha deciso di fare l'orchestratore "dietro le quinte".
    """
    chiamate = []
    run_steps = agents_client.run_steps.list(thread_id=thread_id, run_id=run_id)
    for step in run_steps:
        step_details = getattr(step, "step_details", None)
        if step_details is None:
            continue
        tool_calls = getattr(step_details, "tool_calls", None)
        if not tool_calls:
            continue
        for tc in tool_calls:
            connected_agent = getattr(tc, "connected_agent", None)
            if connected_agent is not None:
                chiamate.append(
                    {
                        "nome_agente_chiamato": getattr(tc, "name", None),
                        "output": getattr(connected_agent, "output", None),
                    }
                )
    return chiamate


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
    orchestrator_agent = None

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
        #    (passate dall'orchestratore) e scrive la newsletter.
        # ------------------------------------------------------------------
        marketer_agent = agents_client.create_agent(
            model=str(AZ_FOUNDRY_MODEL_NAME),
            name="MarketerAgent",
            instructions=(
                "Sei un esperto di Marketing. Riceverai la descrizione di un prodotto "
                "insieme alle informazioni sul pubblico target (categoria prodotto, target "
                "demografico, interessi, tono di comunicazione consigliato).\n\n"
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
        # 4) CONNECTED AGENT TOOLS
        #    Wrappiamo i tre agenti come "tool" utilizzabili dall'orchestratore.
        #    La description e' FONDAMENTALE: e' il testo che il modello legge
        #    per decidere quando e perche' chiamare ciascun sub-agente.
        # ------------------------------------------------------------------
        targeting_tool = ConnectedAgentTool(
            id=targeting_agent.id,
            name="targeting_agent",
            description=(
                "Analizza la descrizione di un prodotto e restituisce il pubblico target "
                "ideale (categoria prodotto, target demografico, interessi, tono di "
                "comunicazione). Usa questo agente PRIMA di scrivere qualsiasi contenuto "
                "di marketing, per sapere a chi ti stai rivolgendo."
            ),
        )

        marketer_tool = ConnectedAgentTool(
            id=marketer_agent.id,
            name="marketer_agent",
            description=(
                "Scrive il testo di una newsletter promozionale per un prodotto. Richiede "
                "in input sia la descrizione del prodotto sia le informazioni sul target "
                "(categoria, target demografico, interessi, tono di comunicazione). Usa "
                "questo agente DOPO aver ottenuto le informazioni sul target dal "
                "targeting_agent. Puoi richiamarlo una seconda volta, passando anche i "
                "problemi rilevati dal content_safety_agent, per ottenere una versione "
                "corretta della newsletter."
            ),
        )

        content_safety_tool = ConnectedAgentTool(
            id=content_safety_agent.id,
            name="content_safety_agent",
            description=(
                "Verifica che il testo di una newsletter sia sicuro e conforme: assenza di "
                "claim esagerati/non veritieri, linguaggio discriminatorio o problemi di "
                "compliance. Usa questo agente DOPO aver ottenuto la newsletter dal "
                "marketer_agent, come ultimo controllo prima di restituire il risultato "
                "finale all'utente."
            ),
        )

        # ------------------------------------------------------------------
        # 5) ORCHESTRATOR AGENT
        #    E' lui stesso un agente: nelle istruzioni gli spieghiamo il
        #    flusso che deve seguire (targeting -> marketer -> content safety)
        #    e gli passiamo i tre sub-agent come tool disponibili.
        # ------------------------------------------------------------------
        orchestrator_agent = agents_client.create_agent(
            model=str(AZ_FOUNDRY_MODEL_NAME),
            name="OrchestratorAgent",
            instructions=(
                "Sei un orchestratore di campagne marketing. Quando l'utente ti fornisce "
                "la descrizione di un prodotto, segui SEMPRE questo flusso, in questo "
                "ordine:\n"
                "1. Chiama 'targeting_agent' passando la descrizione del prodotto, per "
                "individuare il pubblico target.\n"
                "2. Chiama 'marketer_agent' passando sia la descrizione originale del "
                "prodotto sia il risultato completo ottenuto da 'targeting_agent', cosi' "
                "che la newsletter sia scritta per il target corretto.\n"
                "3. Chiama 'content_safety_agent' passando il testo della newsletter "
                "ottenuta, per verificarne la conformita'.\n"
                "4. Se 'content_safety_agent' segnala 'approvato': false, richiama UNA "
                "SOLA VOLTA 'marketer_agent', passando anche i 'problemi_rilevati' e i "
                "'suggerimenti_correzione', per ottenere una versione corretta. Poi "
                "procedi con quella versione SENZA richiamare di nuovo "
                "'content_safety_agent' (per evitare loop). Se anche dopo la correzione "
                "pensi che restino dei dubbi, procedi comunque ma segnalalo nel campo "
                "'revisione_manuale_consigliata'.\n"
                "5. Componi la risposta finale come un UNICO oggetto JSON valido (senza "
                "testo aggiuntivo, senza markdown, senza backtick) con questa struttura "
                "esatta, unendo i risultati di tutti i sub-agent:\n"
                "{\n"
                '  "targeting": { ...output di targeting_agent... },\n'
                '  "marketing": { ...output finale di marketer_agent... },\n'
                '  "content_safety": { ...output di content_safety_agent... },\n'
                '  "revisione_manuale_consigliata": true oppure false\n'
                "}\n\n"
                "Non saltare mai il passaggio dal targeting_agent o dal "
                "content_safety_agent, anche se pensi di sapere già il target o che il "
                "testo sia sicuro. Rispondi sempre e solo con l'oggetto JSON finale."
            ),
            tools=(
                targeting_tool.definitions
                + marketer_tool.definitions
                + content_safety_tool.definitions
            ),
        )

        # ------------------------------------------------------------------
        # 6) LOOP PRINCIPALE
        #    Parliamo SOLO con l'orchestratore: e' lui che, internamente,
        #    decide di chiamare i tre sub-agent nell'ordine giusto.
        # ------------------------------------------------------------------
        storico = carica_storico()

        while True:
            articolo = input("Inserisci la descrizione del prodotto: (QUIT per uscire) ")
            if articolo.upper() == "QUIT":
                break

            th1 = agents_client.threads.create() # crea un nuovo thread per ogni prodotto

            agents_client.messages.create( # invia la descrizione del prodotto all'orchestratore
                thread_id=th1.id,
                role="user",
                content=articolo,
            )

            run = agents_client.runs.create_and_process( # chiede all'orchestratore di processare il thread, che a sua volta chiamerà i sub-agent
                thread_id=th1.id,
                agent_id=orchestrator_agent.id,
            )

            print(f"Status of run {run.id}: {run.status}")

            if run.status == "failed":
                print(f"Run failed. Error: {run.last_error}")
                continue

            if run.status == "completed":
                # Log di debug: vediamo quali sub-agent sono stati chiamati
                # e cosa hanno risposto, prima ancora della risposta finale.
                chiamate = estrai_chiamate_connected_agents(agents_client, th1.id, run.id)
                for chiamata in chiamate:
                    print(f"  → Chiamato '{chiamata['nome_agente_chiamato']}'")

                messages = agents_client.messages.list(
                    thread_id=th1.id,
                    order=ListSortOrder.ASCENDING,
                )

                for message in messages:
                    if message.role == "assistant":
                        testo_risposta = estrai_testo_risposta(message)
                        if testo_risposta is None:
                            continue

                        print(f"Assistant response: {testo_risposta}")

                        dati_strutturati = parse_risposta_json(testo_risposta)

                        record = {
                            "timestamp": datetime.now().isoformat(),
                            "prodotto_input": articolo,
                            "thread_id": th1.id,
                            "run_id": run.id,
                            "sub_agent_calls": chiamate,
                            "risultato": dati_strutturati,
                        }

                        storico.append(record)
                        salva_storico(storico)
                        print(f"✓ Salvato in {OUTPUT_FILE}")

    finally:
        # delete agent - eseguito sempre, anche in caso di errori o Ctrl+C
        for agent in (orchestrator_agent, content_safety_agent, marketer_agent, targeting_agent):
            if agent is not None:
                try:
                    agents_client.delete_agent(agent_id=agent.id)
                except Exception as e:
                    print(f"Errore durante la cancellazione dell'agente {agent.id}: {e}")
        print("Agenti eliminati.")


if __name__ == "__main__":
    load_dotenv()  # Carica le variabili d'ambiente dal file .env
    main()