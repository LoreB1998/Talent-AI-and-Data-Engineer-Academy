import os
from dotenv import load_dotenv
from openai import OpenAI

deployment_name = "gpt-5.4-nano"

load_dotenv()

api_key = os.getenv("AI_SERVICE_KEY")
endpoint = os.getenv("AI_SERVICE_ENDPOINT")

assert api_key and endpoint, "Mancano le variabili nel .env"

client = OpenAI(api_key=api_key, base_url=endpoint)

# Storico della conversazione
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
]

print("Chat avviata. Scrivi 'quit' per uscire.\n")

while True:
    user_input = input("Tu: ")
    if user_input.lower() == "quit":
        print("Uscita dalla chat.")
        break

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model=deployment_name,
        messages=messages #type:ignore
    )

    reply = response.choices[0].message.content
    print(f"Assistente: {reply}\n")

    # Aggiunge la risposta allo storico per mantenere il contesto
    messages.append({"role": "assistant", "content": reply})  #type:ignore