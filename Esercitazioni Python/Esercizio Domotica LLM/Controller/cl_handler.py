
from Model.cl_assistente_vocale import AssistenteVocale
from Model.cl_domotica import CasaDomotica
from Controller.cl_interpreter import InterpreteComandi

class Handler:
    def __init__(self, client_openai, deployment, modo="testo"):
            casa = CasaDomotica()
            self.__interprete = InterpreteComandi(client_openai, deployment, casa)
            self.__modo = (modo or "testo").strip().lower()
            self.__assistente = None

            if self.__modo == "voce":
                try:
                    self.__assistente = AssistenteVocale()
                except Exception as e:
                    print(f"Modalita voce non disponibile: {e}")
                    print("Passo automaticamente alla modalita testo.")
                    self.__modo = "testo"
    
    def start(self):
        while True:
            if self.__modo == "testo":
                try:
                    testo = input("Tu: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nUscita.")
                    break

                if testo.lower() in {"esci", "exit", "quit"}:
                    print("Uscita.")
                    break
            else:
                if self.__assistente is None:
                    print("Modalita voce non disponibile. Uscita.")
                    break
                testo = self.__assistente.ascolta()

            if not testo:
                continue

            #print(f"🗣️ Hai detto: {testo}")
            for risultato in self.__interprete.interpreta(testo):
                print(f"{risultato}")
                if self.__modo == "voce" and self.__assistente is not None:
                    self.__assistente.parla(risultato)