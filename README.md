### India TB Elimination Intelligence
# Tracking India's 2025 Zero-TB Target — Dual Dataset Time Series Analysis

# Can India eliminate TB by 2025? This project uses 20+ years of data to find out.


### Project Overview
India carries the world's highest TB burden — 2.8 million new cases every year. In 2020, the Indian government set an ambitious goal: eliminate TB by 2025, five years ahead of the WHO global 2030 target.
This project analyses two real Indian public health datasets to answer three questions:

Is India's TB incidence declining fast enough to meet the 2025 target?
Which states have the highest TB burden and the slowest progress?
How severe is the tobacco-TB risk factor gap — and how many tobacco-using TB patients are getting no cessation support?


### Datasets
DatasetSourceWhat it containstuberculosis_indicators_india.csvWHO Global TB ProgrammeIndia TB incidence, treatment success rate — yearly (2000–2022)2.11_TB_Tobacco.csvNTEP India (National TB Elimination Programme)State-wise tobacco usage among TB patients, cessation programme coverage — single year snapshot
Why two datasets instead of one merged file?
The WHO dataset is country-level yearly time series — it drives the trend analysis and 2025 projection. The NTEP tobacco dataset is a state-level single-year snapshot — it adds a unique risk-factor dimension. They cannot be merged (different granularity and time coverage) so they are loaded as two separate MySQL tables and queried independently, which is exactly how real analysts handle multi-source health data.

### Project Structure
India-TB-Elimination-Intelligence/
│
├── TB_India_Analysis.ipynb          # Main notebook — cleaning, EDA, time series, projection, MySQL upload
├── TB_India_SQL_Queries.ipynb       # SQL notebook — 10 queries across both MySQL tables
├── tb_dashboard.py                  # Streamlit dashboard — 4 pages, interactive filters
│
├── tuberculosis_indicators_india.csv    # WHO dataset (download from HDX / WHO)
├── 2.11_TB_Tobacco.csv                  # NTEP Tobacco-TB dataset
│
└── charts/                          # Auto-saved PNG chart outputs (generated on run)

### How to Run
Step 1 — Install dependencies
bashpip install pandas numpy matplotlib seaborn statsmodels scipy mysql-connector-python streamlit
Step 2 — MySQL setup (run once in MySQL Workbench or terminal)
sqlCREATE DATABASE tb_india;
Step 3 — Run the main analysis notebook
Open TB_India_Analysis.ipynb in Google Colab or Jupyter.
Upload both CSV files to your session.
Run all cells top to bottom — the last cell pushes cleaned data into MySQL automatically.
Update MYSQL_PASSWORD in the MySQL cell before running.
Step 4 — Run the SQL notebook
Open TB_India_SQL_Queries.ipynb in Jupyter on your local machine (not Colab — it needs your local MySQL).
Update your_password in the first cell.
Run all cells.
Step 5 — Launch the Streamlit dashboard
bashstreamlit run tb_dashboard.py
Update MYSQL_PASSWORD inside tb_dashboard.py before running.
The dashboard opens automatically in your browser at localhost:8501.

### Analysis Breakdown
Part 1 — WHO Time Series Analysis
StepWhat it doesData cleaningExtracts TB incidence and treatment success from multi-indicator WHO export, fixes types, drops nullsChart 1National TB incidence trend + 2025 elimination target lineChart 2Year-over-year change — green bars = TB fell, red bars = TB roseChart 33-year rolling average to smooth out reporting noiseChart 4Treatment success rate vs WHO 90% target over timeChart 5Time series decomposition — trend + seasonality + residual componentsChart 6Linear projection to 2030 — finds when India crosses the elimination threshold
Part 2 — NTEP Tobacco-TB Risk Analysis
StepWhat it doesData cleaningRenames 19 long column names to short standard names automaticallyChart 7% of TB patients with tobacco usage by state — ranked bar chartChart 8Public vs private sector split — pie chart + grouped barChart 9Cessation coverage gap — % of tobacco-using TB patients getting NO quit supportChart 10Tobacco users identified vs users actually linked to cessation support
SQL Queries — 10 queries across 2 MySQL tables
QueryTableSQL TechniqueQ1 — National incidence ranked by yeartb_whoRANK() OVER, FIRST_VALUE()Q2 — Year-over-year changetb_whoCTE + LAG() + % changeQ3 — Rolling 5-year window averagetb_whoAVG() OVER ROWS BETWEENQ4 — Burden classification by yeartb_whoCASE WHENQ5 — Treatment success vs WHO targettb_whoCASE WHEN + gap calculationQ6 — States ranked by tobacco burdentb_tobaccoRANK() OVER + CASE WHENQ7 — Cessation gap by statetb_tobaccoNULLIF + RANK() OVERQ8 — Public vs private sector splittb_tobaccoNULLIF + CASE WHENQ9 — Priority state classificationtb_tobaccoNested CASE WHENQ10 — Summary stats both tablesBothCTE + UNION ALL

### Key Findings
Finding 1 — India is NOT on track for 2025.
At the current annual reduction rate, TB incidence will not reach the WHO elimination threshold of less than 10 cases per 100,000 population by 2025. India needs to approximately 3× its current annual pace of decline to meet the target.
Finding 2 — State-level inequality is severe.
The gap between the highest and lowest burden states is substantial. A national average masks states that are dramatically behind the elimination trajectory and require targeted intervention rather than uniform national policy.
Finding 3 — Tobacco significantly worsens TB outcomes.
Several states show high tobacco usage among TB patients combined with low cessation programme coverage — a compounding risk factor that is not being addressed proportionally across all states.
Finding 4 — Cessation programme gap is a policy failure.
A large proportion of tobacco-using TB patients are identified through screening but never linked to quit-smoking support centres. This gap undermines treatment success rates and is clearly visible in the state-level data.

### Dashboard Pages
PageWhat it showsOverviewKPI cards from both datasets + live 2025 elimination status alert (on track / miss by X years)Part 1: TB Time SeriesYear range slider, 4 trend charts, 2030 linear projection with slope and R² statsPart 2: Tobacco-TB RiskCessation gap bar chart, public vs private pie, priority state classification tableRaw DataBoth MySQL tables displayed with individual CSV download buttons

### Tech Stack
ToolPurposePython — Pandas, NumPyData loading, cleaning, transformationMatplotlib, SeabornEDA charts and trend visualisationsStatsmodelsTime series decomposition (seasonal_decompose)SciPy — linregressLinear regression and 2030 projectionMySQL + mysql-connector-pythonData storage, two-table structure, SQL analysisStreamlit4-page interactive web dashboardGoogle Colab / JupyterDevelopment and execution environment

