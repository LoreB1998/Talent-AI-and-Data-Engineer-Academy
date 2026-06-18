import json
import os

from openai import APIConnectionError, AuthenticationError, BadRequestError

class InterpreteComandi:
    def __init__(self, 
                 client,
                 deployment,
                 domotica,
                 sys_prompt_path=None,
                 tool_path=None):
        
        self.__client = client
        self.__deployment = deployment
        self.__domotica = domotica

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Config"))
        sys_prompt_path = sys_prompt_path or os.path.join(base_dir, "prompt.txt")
        tool_path = tool_path or os.path.join(base_dir, "tools.json")
        
        with open(tool_path, "r") as f:
            self.__tools = json.load(f)
        
        with open(sys_prompt_path, "r") as f:
            self.__prompt = "\n".join(f.readlines())

        # Storico conversazione: mantiene il contesto tra una frase e la successiva.
        self.__messages = [{"role": "system", "content": self.__prompt}]
            
    def interpreta(self, testo_utente):
        self.__messages.append({"role": "user", "content": testo_utente})

        try:
            response = self.__client.chat.completions.create(
                model=self.__deployment,
                messages=self.__messages,
                tools=self.__tools,
                tool_choice="auto",
            )
        except AuthenticationError:
            self.__messages.pop()
            return ["Errore di autenticazione con Azure OpenAI: controlla AZ_OPENAI_KEY."]
        except APIConnectionError:
            self.__messages.pop()
            return ["Impossibile contattare il servizio Azure OpenAI: controlla la connessione/endpoint."]
        except BadRequestError as e:
            self.__messages.pop()
            return [f"Richiesta non valida verso il modello: {e}"]

        msg = response.choices[0].message
        risultati = []

        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                nome_funzione = tool_call.function.name
                try:
                    argomenti = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    argomenti = {}
                risultati.append(self._esegui_comando(nome_funzione, argomenti))
        else:
            risultati.append(msg.content or "Non ho capito il comando, puoi ripetere?")

        # Aggiunge la risposta allo storico per mantenere il contesto.
        self.__messages.append({"role": "assistant", "content": "\n".join(risultati)})

        return risultati

    def _esegui_comando(self, nome_funzione, argomenti):
        metodo = getattr(self.__domotica, nome_funzione, None)
        if metodo is None:
            return f"⚠️ Comando non riconosciuto: {nome_funzione}"
        try:
            return metodo(**argomenti)
        except TypeError as e:
            return f"⚠️ Parametri non validi per '{nome_funzione}': {e}"
    
    
        