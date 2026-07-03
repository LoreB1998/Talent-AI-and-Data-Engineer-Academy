import time

import requests

from config import BACKEND_BASE_URL


def _request_con_retry(metodo: str, url: str, max_tentativi: int = 4, attesa_iniziale: float = 3.0, **kwargs) -> requests.Response:
    """Esegue una richiesta HTTP con retry su 503/errori di connessione."""
    attesa = attesa_iniziale
    ultimo_errore = None
    for tentativo in range(1, max_tentativi + 1):
        try:
            resp = requests.request(metodo, url, timeout=15, **kwargs)
            if resp.status_code == 503:
                print(f"    [avviso] 503 (tentativo {tentativo}/{max_tentativi}), riprovo in {attesa:.0f}s...")
                ultimo_errore = requests.exceptions.HTTPError(f"503 su {url}")
                time.sleep(attesa)
                attesa *= 2
                continue
            return resp
        except requests.exceptions.ConnectionError as e:
            print(f"    [avviso] errore di connessione (tentativo {tentativo}/{max_tentativi}), riprovo in {attesa:.0f}s...")
            ultimo_errore = e
            time.sleep(attesa)
            attesa *= 2
    raise RuntimeError(f"Impossibile contattare '{url}' dopo {max_tentativi} tentativi. Ultimo errore: {ultimo_errore}")


def get_clienti() -> list[dict]:
    resp = _request_con_retry("GET", f"{BACKEND_BASE_URL}/api/clienti")
    resp.raise_for_status()
    return resp.json()


def get_articoli() -> list[dict]:
    resp = _request_con_retry("GET", f"{BACKEND_BASE_URL}/api/articoli")
    resp.raise_for_status()
    return resp.json()


def get_conferma_ordine(id_conferma: str) -> dict | None:
    resp = _request_con_retry("GET", f"{BACKEND_BASE_URL}/api/conferme-ordine/{id_conferma}")
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def crea_conferma_ordine(id_conferma: str, id_cliente: str, data_conferma: str, riferimento_cliente: str) -> dict:
    body = {
        "idConferma": id_conferma,
        "cliente": {"id": id_cliente},
        "dataConferma": data_conferma,
        "riferimentoCliente": riferimento_cliente,
    }
    resp = _request_con_retry("POST", f"{BACKEND_BASE_URL}/api/conferme-ordine", json=body)
    if resp.status_code == 409:
        raise RuntimeError(f"Conflitto (409): esiste già una conferma ordine con id '{id_conferma}'.")
    resp.raise_for_status()
    return resp.json()


def crea_dettaglio_conferma_ordine(id_conferma: str, codice_articolo: str, quantita: float, prezzo_unitario: float, importo_riga: float) -> dict:
    body = {
        "confermaOrdine": {"idConferma": id_conferma},
        "articolo": {"codice": codice_articolo},
        "quantita": quantita,
        "prezzoUnitario": prezzo_unitario,
        "importoRiga": importo_riga,
    }
    resp = _request_con_retry("POST", f"{BACKEND_BASE_URL}/api/dettagli-conferma-ordine", json=body)
    resp.raise_for_status()
    return resp.json()
