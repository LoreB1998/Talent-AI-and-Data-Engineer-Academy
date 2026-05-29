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
