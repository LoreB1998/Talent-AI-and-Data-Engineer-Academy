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






