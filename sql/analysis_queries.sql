-- ============================================================
-- NIFTY 100 SQL ANALYSIS
-- ============================================================

-- 1. Top companies by latest market capitalization
SELECT
    company_id,
    year,
    market_cap_crore
FROM market_cap
ORDER BY market_cap_crore DESC
LIMIT 10;


-- 2. Latest financial performance
SELECT
    company_id,
    year,
    sales,
    net_profit,
    eps
FROM profitandloss
ORDER BY year DESC, net_profit DESC
LIMIT 20;


-- 3. Companies with highest ROE
SELECT
    company_id,
    year,
    return_on_equity_pct
FROM financial_ratios
WHERE return_on_equity_pct IS NOT NULL
ORDER BY return_on_equity_pct DESC
LIMIT 10;


-- 4. Companies with lowest debt-to-equity
SELECT
    company_id,
    year,
    debt_to_equity
FROM financial_ratios
WHERE debt_to_equity IS NOT NULL
ORDER BY debt_to_equity ASC
LIMIT 10;


-- 5. Average profit by year
SELECT
    year,
    ROUND(AVG(net_profit), 2) AS avg_net_profit
FROM profitandloss
GROUP BY year
ORDER BY year;


-- 6. Average operating margin by year
SELECT
    year,
    ROUND(AVG(opm_percentage), 2) AS avg_opm
FROM profitandloss
GROUP BY year
ORDER BY year;


-- 7. Companies with highest market valuation
SELECT
    company_id,
    year,
    market_cap_crore,
    pe_ratio,
    pb_ratio
FROM market_cap
WHERE market_cap_crore IS NOT NULL
ORDER BY market_cap_crore DESC
LIMIT 20;


-- 8. Sector distribution
SELECT
    broad_sector,
    COUNT(*) AS company_count,
    ROUND(AVG(index_weight_pct), 2) AS avg_index_weight
FROM sectors
GROUP BY broad_sector
ORDER BY company_count DESC;


-- 9. Highest EPS companies
SELECT
    company_id,
    year,
    earnings_per_share
FROM financial_ratios
WHERE earnings_per_share IS NOT NULL
ORDER BY earnings_per_share DESC
LIMIT 10;


-- 10. Companies with strongest free cash flow
SELECT
    company_id,
    year,
    free_cash_flow_cr
FROM financial_ratios
WHERE free_cash_flow_cr IS NOT NULL
ORDER BY free_cash_flow_cr DESC
LIMIT 10;

-- ============================================================
-- NIFTY 100 CORE ANALYSIS
-- ============================================================

-- 11. Latest market cap for each company
SELECT m.company_id,
       m.year,
       m.market_cap_crore
FROM market_cap m
JOIN (
    SELECT company_id, MAX(year) AS latest_year
    FROM market_cap
    GROUP BY company_id
) x
ON m.company_id = x.company_id
AND m.year = x.latest_year
ORDER BY m.market_cap_crore DESC
LIMIT 10;


-- 12. Top companies by latest net profit
SELECT p.company_id,
       p.year,
       p.net_profit,
       p.sales,
       p.eps
FROM profitandloss p
JOIN (
    SELECT company_id, MAX(year) AS latest_year
    FROM profitandloss
    GROUP BY company_id
) x
ON p.company_id = x.company_id
AND p.year = x.latest_year
ORDER BY p.net_profit DESC
LIMIT 10;


-- 13. Top companies by latest ROE
SELECT r.company_id,
       r.year,
       r.return_on_equity_pct
FROM financial_ratios r
JOIN (
    SELECT company_id, MAX(year) AS latest_year
    FROM financial_ratios
    GROUP BY company_id
) x
ON r.company_id = x.company_id
AND r.year = x.latest_year
WHERE r.return_on_equity_pct IS NOT NULL
ORDER BY r.return_on_equity_pct DESC
LIMIT 10;


-- 14. Lowest debt-to-equity companies
SELECT r.company_id,
       r.year,
       r.debt_to_equity
FROM financial_ratios r
JOIN (
    SELECT company_id, MAX(year) AS latest_year
    FROM financial_ratios
    GROUP BY company_id
) x
ON r.company_id = x.company_id
AND r.year = x.latest_year
WHERE r.debt_to_equity IS NOT NULL
ORDER BY r.debt_to_equity ASC
LIMIT 10;


-- 15. Sector-wise company count and index weight
SELECT
    broad_sector,
    COUNT(*) AS company_count,
    ROUND(SUM(index_weight_pct), 2) AS total_index_weight_pct
FROM sectors
GROUP BY broad_sector
ORDER BY total_index_weight_pct DESC;


-- 16. Latest P&L growth comparison
SELECT
    company_id,
    MIN(year) AS first_year,
    MAX(year) AS latest_year,
    ROUND(MAX(net_profit) - MIN(net_profit), 2) AS profit_change
FROM profitandloss
GROUP BY company_id
ORDER BY profit_change DESC
LIMIT 10;