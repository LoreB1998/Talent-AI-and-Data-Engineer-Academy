# Creare una rubrica telefonica usando un dizionario.
# Il programma deve permettere di:
# aggiungere un contatto
# cercare un numero tramite nome
# stampare tutta la rubrica
 
import json
rubrica = {}
 
def inserisci(nome, numero):
    nome = nome.title()
    if nome in rubrica:
        print("Record già presente")
        return
    rubrica[nome] = {"numero": numero, "blocked": False}
 
def delete(nome):
    nome = nome.title()
    if nome in rubrica:
        del rubrica[nome]
        print("Record eliminato")
    else:
        print("Record non trovato")
 
def ricerca(nome):
    nome = nome.lower()
    found = False
    for name, dict in rubrica.items():
        if nome in name.lower():
            print(name + ":", dict['numero'])
            print("Bloccato: ", "Sì" if dict['blocked'] else "No")
            found = True
    if not found:
        print("record non presente\n")
    # if nome in rubrica:
    #     print(nome + ":", rubrica[nome])
 
def stampa():
    for nome in sorted(rubrica):
        print(nome + ": ", rubrica[nome]["numero"])
        print("Bloccato: ", "Sì" if rubrica[nome]['blocked'] else "No")
    print()
 
 
def toggleBlock(nome):
    nome = nome.title()
    if nome in rubrica:
        rubrica[nome]["blocked"] = not rubrica[nome]["blocked"]
    else:
        print("Record non Trovato\n")
 
while True:
    print("1) Inserisci contatto")
    print("2) Ricerca contatto")
    print("3) Stampa rubrica")
    print("4) Elimina contatto")
    print("5) Exit")
 
    choice = int(input("Inserire opzione: "))
    if choice == 1:
        name = input("Inserire nome: ")
        phone = input("Inserire telefono: ")
        inserisci(name, phone)
    elif choice == 2:
        name = input("Inserire nome: ")
        ricerca(name)
    elif choice == 3:
        stampa()
    elif choice == 4:
        name = input("Inserire nome: ")
        delete(name)
    elif choice == 5:
        break
    else:
        print("Scelta non valida")