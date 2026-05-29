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

-- LEFT JOIN
SELECT h.SalesOrderID, OrderDate, CustomerID, TotalDue, -- colonne prese dalla tabella SalesorderHeader
       ProductID, UnitPrice, OrderQty                   -- colonne prese dalla tabella SalesorderDetail
FROM SalesLT.SalesOrderHeader h
LEFT JOIN SalesLT.SalesOrderDetail d ON h.SalesOrderID = d.SalesOrderID;

-- INNER JOIN