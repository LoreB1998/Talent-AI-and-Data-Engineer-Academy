# Obiettivo

Il sistema gestisce l’ingresso e l’uscita dei veicoli in un parcheggio, assegna un ticket all’entrata, calcola il costo alla chiusura e produce una rendicontazione finale. Il progetto deve funzionare da riga di comando e mantenere lo stato dei ticket durante l’esecuzione.

## Funzioni richieste

- Registrare l’ingresso di un veicolo.
- Stampare un ticket con codice univoco, targa, data/ora di ingresso e posto assegnato (su file).
- Registrare l’uscita del veicolo.
- Calcolare durata della sosta e importo dovuto.
- Stampare un riepilogo del ticket chiuso.
- Mostrare lo stato del parcheggio.
- Generare una rendicontazione finale con incassi e statistiche.

## Regole di business

- Ogni veicolo riceve un solo ticket aperto alla volta.
- Un posto occupato non può essere assegnato a un altro veicolo.
- La tariffa può essere oraria o a scatti, ma va definita in modo esplicito all’inizio del programma.
- Se il parcheggio è pieno, il sistema deve rifiutare nuovi ingressi.
- Se una targa non esiste tra i ticket aperti, l’uscita deve essere rifiutata con messaggio chiaro.

## Dati da salvare

Per ogni ticket:

- ID ticket.
- Targa.
- Data/ora ingresso.
- Data/ora uscita.
- Posto assegnato.
- Durata.
- Importo.

Per il parcheggio:

- Numero totale posti.
- Posti liberi.
- Posti occupati.
- Lista ticket aperti.
- Storico ticket chiusi.

## Menu utente

Il programma deve mostrare un menu testuale con almeno queste voci:

- Nuovo ingresso.
- Nuova uscita.
- Mostra stato parcheggio.
- Mostra ticket aperti.
- Mostra rendiconto.
- Esci.

## Rendicontazione

La rendicontazione finale deve mostrare:

- Numero totale ticket emessi.
- Numero ticket chiusi.
- Numero ticket ancora aperti.
- Incasso totale.
- Durata media delle soste.
- Numero massimo di posti occupati contemporaneamente.

## Requisiti tecnici

- Linguaggio: Python.
- Interfaccia: console.
- Strutture dati: liste, dizionari, classi.
- Data e ora: modulo datetime.
- Persistenza: file JSON o CSV per salvare lo storico.

## Criteri di accettazione

Il progetto è corretto se:

- registra almeno 5 ingressi e 5 uscite senza errori;
- gestisce il caso di parcheggio pieno;
- rifiuta uscite non valide;
- calcola importi e totale incassi in modo coerente;
- produce una rendicontazione finale leggibile.

## Estensioni facoltative

- Ricerca ticket per targa.
- Tariffe diverse per auto, moto e furgoni.
- Storico giornaliero salvato su file.
- Generazione QRCode o Barcode per il ticket (https://note.nkmk.me/en/python-pillow-qrcode/ - https://www.geeksforgeeks.org/python/generate-qr-code-using-qrcode-in-python/ - https://pypi.org/project/qrcode/).

