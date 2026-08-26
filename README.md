\# Nifty 100 Financial Analytics



\## Project Overview



This project builds a complete data analytics and financial ratio engine for Nifty 100 companies.



The project covers data ingestion, normalization, data-quality validation, SQLite database creation, exploratory data analysis, SQL analysis, financial KPI calculation, CAGR analysis, cash-flow analysis, and capital-allocation classification.



\## Project Objectives



\- Load Nifty 100 financial datasets from Excel files.

\- Normalize company identifiers and financial years.

\- Validate data using 16 data-quality rules.

\- Store structured data in SQLite.

\- Calculate financial ratios and KPIs.

\- Calculate 3-year, 5-year, and 10-year CAGR metrics.

\- Analyze cash flow and capital allocation.

\- Provide SQL-based financial analysis.

\- Maintain automated unit tests for ETL and KPI calculations.



\## Project Structure



```text

nifty100/

│

├── data/

│   ├── raw/                  # Source Excel datasets

│   ├── processed/            # Processed datasets

│   └── database/

│       └── nifty100.db       # SQLite database

│

├── notebooks/

│   └── eda.ipynb             # Exploratory Data Analysis

│

├── output/

│   ├── capital\_allocation.csv

│   ├── load\_audit.csv

│   ├── ratio\_edge\_cases.log

│   └── validation\_failures.csv

│

├── scripts/

│   └── run\_sql\_analysis.py

│

├── sql/

│   └── analysis\_queries.sql

│

├── src/

│   ├── analytics/

│   │   ├── ratios.py

│   │   ├── cagr.py

│   │   ├── cashflow\_kpis.py

│   │   └── run\_ratio\_engine.py

│   │

│   ├── etl/

│   │   ├── loader.py

│   │   ├── load\_database.py

│   │   ├── normaliser.py

│   │   ├── validator.py

│   │   ├── db.py

│   │   └── schema.sql

│   │

│   ├── api/

│   └── dashboard/

│

├── tests/

│   ├── etl/

│   │   └── test\_normaliser.py

│   └── kpi/

│       ├── test\_cagr.py

│       ├── test\_cashflow.py

│       └── test\_ratios.py

│

├── .env.template

├── .gitignore

├── requirements.txt

└── README.md

