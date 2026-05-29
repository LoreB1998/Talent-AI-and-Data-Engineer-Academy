/*
ORDINE DI RUN:
    - FROM / JOIN — identifica le tabelle e costruisce il dataset di partenza
    - WHERE — filtra le righe prima dell'aggregazione
    - GROUP BY — raggruppa le righe
    - HAVING — filtra i gruppi dopo l'aggregazione
    - SELECT — calcola le colonne (inclusi alias e window functions)
    - DISTINCT — rimuove i duplicati
    - ORDER BY — ordina il risultato
    - LIMIT / OFFSET / TOP — limita le righe restituite
*/


-- Analisi esplorativa
SELECT TOP 10 *
FROM SalesLT.Address;

SELECT TOP 10 *
FROM SalesLT.Customer;

SELECT TOP 10 *
FROM SalesLT.CustomerAddress;

SELECT TOP 10 *
FROM SalesLT.Product;

SELECT TOP 10 *
FROM SalesLT.ProductCategory;

SELECT TOP 10 *
FROM SalesLT.ProductDescription;

SELECT TOP 10 *
FROM SalesLT.ProductModel;

SELECT TOP 10 *
FROM SalesLT.ProductModelProductDescription;

SELECT TOP 10 *
FROM SalesLT.SalesOrderDetail;

SELECT TOP 10 *
FROM SalesLT.SalesOrderHeader;


-- Verifica e pulizia delle tabelle
SELECT
    TABLE_SCHEMA,
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH AS max_lunghezza,
    IS_NULLABLE AS accetta_null
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'SalesLT'
ORDER BY TABLE_NAME, ORDINAL_POSITION;



-- Colori con media StandardCost > 550
WITH color_cost AS (
    SELECT  Color, AVG(StandardCost) OVER (PARTITION BY Color) AS avg_by_color
    FROM SalesLT.Product
    WHERE Color IS NOT NULL)
SELECT DISTINCT Color
FROM color_cost
WHERE avg_by_color > 550;

-- Percentuale di colori
WITH color_cnt_pct AS (
    SELECT Color,
           COUNT(ProductID) AS cnt,
           SUM(COUNT(ProductID)) OVER () AS tot
    FROM SalesLT.Product
    WHERE Color IS NOT NULL
    GROUP BY Color)
SELECT Color,
       CONCAT(CAST((cnt * 100.0 / tot) AS DECIMAL(5, 2)), '%') AS pct
FROM color_cnt_pct;

-- Query Professore 1
SELECT Name, ListPrice
FROM SalesLT.Product P;

SELECT Name, ListPrice
FROM SalesLT.Product
ORDER BY 2 DESC;

SELECT FirstName, LastName, CompanyName
FROM SalesLT.Customer
WHERE CompanyName IS NOT NULL;

-- Elenca gli ordini con un valore superiore a 1000,
-- mostrando prima quelli di maggior valore.

SELECT SalesOrderID AS ID, TotalDue AS TotaleDovuto
FROM SalesLT.SalesOrderHeader
WHERE TotalDue > 1000
ORDER BY 2 DESC;

-- Trova tutti i prodotti di colore Rosso e ordinali per prezzo (dal più economico).

SELECT ProductID, Name, Color, ListPrice
FROM SalesLT.Product
WHERE Color LIKE 'Red'
ORDER BY 4;

-- Selezionare gli ordini in un determinato anno solare

SELECT SalesOrderID, OrderDate, TotalDue
FROM SalesLT.SalesOrderHeader
WHERE OrderDate BETWEEN '20080101' AND  '20090101';

-- Trova i clienti il cui cognome inizia con la lettera da 'A' a 'C'.

SELECT CustomerID, FirstName, LastName
FROM SalesLT.Customer
WHERE LastName LIKE '[A-C]%'
ORDER BY 2,3;

-- Trova i clienti il cui cognome non inizia con la lettera da 'A' a 'C'.

SELECT CustomerID, FirstName, LastName
FROM SalesLT.Customer
WHERE LastName LIKE '[^A-C]%'
ORDER BY 2,3;

-- Trova i clienti il cui cognome inizia con la lettera 'A' o 'C' o 'S'.

SELECT CustomerID, FirstName, LastName
FROM SalesLT.Customer
WHERE LastName LIKE '[A/C/S]%'
ORDER BY 2,3;

-- Totale delle vendite per ogni anno

SELECT CustomerID,
       COUNT(*) NumOrdini
FROM SalesLT.SalesOrderHeader
GROUP BY CustomerID
ORDER BY 2 DESC;

--Calcola il prezzo medio per ogni colore di prodotto (escludendo i colori nulli) il cui prezzo medio è superiore a 100
SELECT Color, AVG(ListPrice) AS PrezzoMedio
FROM SalesLT.Product
WHERE Color IS NOT NULL
GROUP BY Color
HAVING AVG(ListPrice) > 100
ORDER BY 2 DESC;

--Trova i primi i clienti che hanno speso di più in totale, togli le prime 10 righe e mostra le 5 successive
DECLARE @num1 int
DECLARE @num2 int

SET @num1 = 10
SET @num2 = 5

SELECT CustomerID,
             SUM(TotalDue) AS TotaleSpeso
FROM SalesLT.SalesOrderHeader
GROUP BY CustomerID
ORDER BY 2 DESC
OFFSET @num1 ROWS FETCH NEXT @num2 ROWS ONLY;

--Calcola il prezzo medio per ogni combinazione di colore e taglia.
SELECT Color, Size, AVG(ListPrice) AS AvgPrice
FROM SalesLT.Product
WHERE Size IS NOT NULL AND Color IS NOT NULL
GROUP BY Color, Size
ORDER BY 3 DESC;