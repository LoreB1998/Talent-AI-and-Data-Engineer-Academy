/*
                       TIPI DI JOIN IN SQL

   [INNER JOIN]
   -> Prende solo l'intersezione: righe con corrispondenza in ENTRAMBE le tabelle.

   [LEFT JOIN]
   -> Prende TUTTO a sinistra + righe compatibili a destra (NULL se non ci sono).
   -> Esclusivo (WHERE B.Key IS NULL): solo elementi di A che NON stanno in B.

   [RIGHT JOIN]
   -> Specchio della Left: prende TUTTO a destra + righe compatibili a sinistra.

   [FULL (OUTER) JOIN]
   -> Unione totale: prende tutte le righe di ENTRAMBE le tabelle (riempie con NULL).

   [CROSS JOIN]
   -> Prodotto cartesiano: accoppia ogni riga di A con ogni riga di B (Righe A x Righe B).

   [SELF JOIN]
   -> Tecnico: JOIN di una tabella con se stessa (es. gerarchie Dipendente -> Capo).
*/

-- INNER JOIN
SELECT h.SalesOrderID, OrderDate, CustomerID, TotalDue, -- colonne prese dalla tabella SalesorderHeader
       ProductID, UnitPrice, OrderQty                   -- colonne prese dalla tabella SalesorderDetail
FROM SalesLT.SalesOrderHeader h
INNER JOIN SalesLT.SalesOrderDetail d ON h.SalesOrderID = d.SalesOrderID;

-- Utilizzando un JOIN, trova i prodotti che hanno generato un ricavo superiore a 20.000.
SELECT P.ProductID, Name, ProductNumber, SUM(OrderQty * UnitPrice)  AS tot
FROM SalesLT.Product P
LEFT JOIN SalesLT.SalesOrderDetail SOD on P.ProductID = SOD.ProductID
GROUP BY P.ProductID, Name, ProductNumber
HAVING SUM(OrderQty * UnitPrice) > 20000
ORDER BY 4;

-- Trova i prodotti venduti in più di 20 unità e con un ricavo superiore a 5.000.
SELECT P.Name,
       SUM(SOD.OrderQty) AS TotalOrdered,
       SUM(OrderQty * UnitPrice) AS Revenue
FROM SalesLT.Product AS P
INNER JOIN SalesLT.SalesOrderDetail SOD ON P.ProductID = SOD.ProductID
GROUP BY P.Name
HAVING  SUM(SOD.OrderQty)> 20 AND SUM(SOD.OrderQty * SOD.UnitPrice) > 5000;


-- Raggruppa i prodotti per colore (gestendo i valori mancanti) e
-- calcola il prezzo medio con la relativa fascia (Alto/Medio/Basso).
SELECT COALESCE(Color, 'No Color') AS Color,
       AVG(ListPrice) AS PrezzoMedio,
       CASE WHEN AVG(ListPrice) > 1000 THEN 'Alto'
            WHEN AVG(ListPrice) > 500  THEN 'Medio'
            ELSE 'Basso'
       END AS GruppoPrezzo
FROM SalesLT.Product
GROUP BY Color
HAVING AVG(ListPrice) > 100
ORDER BY PrezzoMedio DESC;


-- Mostra il nome e il cognome dei clienti in maiuscolo e senza spazi iniziali/finali
-- CONCAT -> Unisce più stringhe
-- TRIM   -> Rimuove gli spazi
-- UPPER  -> Maiuscolo

SELECT DISTINCT CONCAT(TRIM(UPPER(FirstName)),' ', TRIM(UPPER(LastName))) NomeCompleto
FROM SalesLT.Customer
ORDER BY 1;


/*
Definizione della Stored Procedure, per trovare prodotti presenti in ordini con ricavo superiore
a una certa soglia
*/
GO
CREATE OR ALTER PROCEDURE SalesLT.GetProductsByRevenueThreshold
    @RevenueThreshold MONEY = 20000 -- Parametro di ingresso con valore di default a 20.000
AS
BEGIN
    -- Disabilita il conteggio delle righe per ottimizzare le performance
    SET NOCOUNT ON;

    SELECT P.ProductID,
           P.Name,
           P.ProductNumber,
           SUM(SOD.OrderQty * SOD.UnitPrice) AS TotaleRicavo
    FROM SalesLT.Product P
    LEFT JOIN SalesLT.SalesOrderDetail SOD ON P.ProductID = SOD.ProductID
    GROUP BY P.ProductID, P.Name, P.ProductNumber
    HAVING SUM(SOD.OrderQty * SOD.UnitPrice) > @RevenueThreshold
    ORDER BY TotaleRicavo DESC;
END;
-- Per utilizzarla
GO
EXEC SalesLT.GetProductsByRevenueThreshold @RevenueThreshold = 5000;



/*
================================================================================
                      IL CUORE DI SQL: DDL vs DML
================================================================================

   [1] DDL - DATA DEFINITION LANGUAGE (Il Progettista)
   -----------------------------------------------------------------------------
   -> Definisce, modifica o distrugge la STRUTTURA degli oggetti del database.
   -> Opera a livello di schema (tabelle, viste, indici, stored procedure, utenti).
   -> Non manipola i singoli record, ma i "contenitori" che li ospitano.

   I COMANDI CHIAVE:
   * CREATE : Crea da zero un oggetto nel database.
              Es: CREATE TABLE SalesLT.NuoviClienti (ID INT, Nome VARCHAR(50));

   * ALTER  : Modifica la struttura di un oggetto già esistente (aggiunge/rimuove
              colonne, cambia tipi di dato, vincoli o definizioni di procedure).
              Es: ALTER TABLE SalesLT.Product ADD CodiceSconto VARCHAR(10);

   * DROP   : Elimina definitivamente un oggetto e tutto il suo contenuto dallo schema.
              Es: DROP PROCEDURE SalesLT.GetProductsByRevenueThreshold;

   * TRUNCATE: Svuota istantaneamente una tabella eliminando TUTTE le righe.
              [Nota Tecnica]: È un comando DDL e non DML. Non scorre le righe una
              a una, ma dealloca direttamente le pagine di memoria sul disco.
              Per questo è fulmineo, ma NON attiva i trigger di tipo DELETE.

   COMPORTAMENTO E TRANSAZIONI (Sfumatura importante):
   - In SQL Server (T-SQL): I comandi DDL possono essere inseriti dentro una
     transazione e annullati con un ROLLBACK se si cambia idea.
   - In Oracle/MySQL: I comandi DDL eseguono un COMMIT implicito automatico;
     una volta lanciati, non si può più tornare indietro.


   [2] DML - DATA MANIPULATION LANGUAGE (L'Operatore)
   -----------------------------------------------------------------------------
   -> Manipola, inserisce e modifica i DATI contenuti all'interno delle tabelle.
   -> È il linguaggio del lavoro quotidiano per l'analisi e l'aggiornamento.
   -> L'esecuzione di questi comandi attiva i relativi Trigger (INSERT/UPDATE/DELETE).

   I COMANDI CHIAVE:
   * INSERT : Inserisce una o più nuove righe in una tabella esistente.
              Es: INSERT INTO SalesLT.ProductLog (Note) VALUES ('Test log');

   * UPDATE : Modifica i valori di righe già presenti, basandosi su un filtro.
              Es: UPDATE SalesLT.Product SET ListPrice = 120 WHERE ProductID = 1;
              [Pericolo]: Se dimentichi la clausola WHERE, modifichi TUTTA la tabella.

   * DELETE : Rimuove una o più righe specifiche da una tabella.
              Es: DELETE FROM SalesLT.ProductLog WHERE LogDate < '2026-01-01';
              [Nota Tecnica]: Scrive ogni singola riga cancellata nel Transaction Log.
              Se devi svuotare tutta la tabella, usa TRUNCATE (DDL) per fare prima.

   * MERGE  : (Istruzione DML avanzata) Unisce INSERT, UPDATE e DELETE in un unico
              comando condizionale. Sincronizza una tabella di destinazione in base
              ai dati di una tabella sorgente.

   COMPORTAMENTO E TRANSAZIONI:
   - Tutti i comandi DML sono pienamente transazionali. Possono essere racchiusi
     tra BEGIN TRANSACTION e COMMIT/ROLLBACK per garantire l'integrità dei dati
*/

-- [1] DDL: Creiamo una tabella di test per non alterare i dati di produzione
CREATE TABLE SalesLT.Address_Test (
    AddressID INT IDENTITY(1,1) PRIMARY KEY, -- ID auto-incrementale (specifico per SQL Server)
    AddressLine1 VARCHAR(50) NOT NULL,
    AddressLine2 VARCHAR(50) NULL,
    City VARCHAR(30) NOT NULL,
    StateProvince VARCHAR(10) NOT NULL,
    CountryRegion VARCHAR(20) NOT NULL,
    PostalCode VARCHAR(10) NOT NULL
);

-- [Verifica DDL]: La tabella esiste ma è vuota
SELECT * FROM SalesLT.Address_Test;


-- [2] DML: Inseriamo i dati (INSERT)
INSERT INTO SalesLT.Address_Test (AddressLine1, AddressLine2, City, StateProvince, CountryRegion, PostalCode)
VALUES ('Indirizzo1', 'Indirizzo2', 'Milano', 'MI', 'Italia', '20100'),
       ('Indirizzo1', 'Indirizzo2', 'Milano', 'MI', 'Italia', '20100'),
       ('Indirizzo1', 'Indirizzo2', 'Milano', 'MI', 'Italia', '20100');

-- [Verifica DML]: Vediamo i 3 record inseriti
SELECT * FROM SalesLT.Address_Test;


-- [3] DML: Aggiorniamo i dati appena inseriti (UPDATE)
UPDATE SalesLT.Address_Test
SET PostalCode = '20101'
WHERE AddressLine1 = 'Indirizzo1';

-- [Verifica DML]: Il PostalCode è cambiato in '20101' per tutte e 3 le righe
SELECT * FROM SalesLT.Address_Test;


-- [4] DDL: Modifichiamo la struttura della tabella aggiungendo una colonna (ALTER)
ALTER TABLE SalesLT.Address_Test ADD Note VARCHAR(100);

-- [Verifica DDL]: Noterai la nuova colonna 'Note' in fondo, valorizzata a NULL
SELECT * FROM SalesLT.Address_Test;


-- [5] DML: Eliminiamo le righe specifiche (DELETE)
-- In questo scenario eliminiamo tutto usando il filtro applicato prima
DELETE FROM SalesLT.Address_Test
WHERE AddressLine1 = 'Indirizzo1';

-- [Verifica DML]: La tabella è tornata vuota, ma la struttura (e la colonna Note) esiste ancora
SELECT * FROM SalesLT.Address_Test;


-- [6] DML/DDL: Reinseriamo un record per testare la TRUNCATE
INSERT INTO SalesLT.Address_Test (AddressLine1, City, StateProvince, CountryRegion, PostalCode)
VALUES ('Indirizzo_Temp', 'Roma', 'RM', 'Italia', '00100');

-- [7] DDL: Svuotamento istantaneo della tabella (TRUNCATE)
-- Elimina tutti i dati deallocando le pagine di memoria, senza loggare riga per riga
TRUNCATE TABLE SalesLT.Address_Test;


-- [8] DDL: RIPRISTINO TOTALE DEL DATABASE (DROP)
-- Eliminiamo definitivamente la tabella e la sua struttura dal database.
DROP TABLE SalesLT.Address_Test;







