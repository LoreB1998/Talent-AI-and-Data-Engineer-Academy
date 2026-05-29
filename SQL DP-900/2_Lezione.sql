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

-- LEFT JOIN
SELECT c.CustomerID, FirstName, LastName, SalesOrderID, OrderDate, TotalDue
FROM SalesLT.Customer c
LEFT JOIN SalesLT.SalesOrderHeader h ON c.CustomerID = h.CustomerID

-- Utilizzando un JOIN, trova i prodotti che hanno generato un ricavo superiore a 20.000.
SELECT P.ProductID, Name, ProductNumber, SUM(OrderQty * UnitPrice)  AS tot
FROM SalesLT.Product P
LEFT OUTER JOIN SalesLT.SalesOrderDetail SOD on P.ProductID = SOD.ProductID
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

-- Percentuale Colorati
SELECT AVG(IIF(Color IS NOT NULL, 1.0, 0.0))*100 AS PercentualeColorati
FROM SalesLT.Product;

--- Raggruppa i prodotti per una categoria di colore mostrando solo i gruppi con prezzo medio > 100.
SELECT Color, AVG(ListPrice) AS avg_price
FROM SalesLT.Product
GROUP BY Color
HAVING AVG(ListPrice)>100
ORDER BY 2 DESC;