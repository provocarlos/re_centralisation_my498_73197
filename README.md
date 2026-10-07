# The (Re)centralisation of Health Services in Mexico

**A Difference-in-Differences Analysis of Household Out-of-Pocket Spending**

Replication code and data for the MSc Applied Social Data Science capstone (MY498, London School of Economics, candidate 73197). The full dissertation is in [`mexico_health_recentralisation_my498_73197.pdf`](mexico_health_recentralisation_my498_73197.pdf).

## Summary

In 2020 Mexico dismantled Seguro Popular and moved health services for people without contributory social security to the federal level: first under INSABI, then under an expanded IMSS-Bienestar. The government's main argument for the change was that it would protect households from paying for care out of pocket (OOP). This project tests that claim.

States joined the federal system one by one. **24 states** transferred their health services, and **8 states** never did: Aguascalientes, Coahuila, Chihuahua, Durango, Guanajuato, Jalisco, Nuevo León and Querétaro. Using ENIGH household survey waves from 2016 to 2024, the study compares OOP health spending among uninsured households in the two groups of states.

**Main finding:** affiliation with the centralised institutions is associated with a **23.0% *increase*** in expected household OOP health spending (p = 0.001). The increase appears in all three spending subcategories: medicines, hospitalisation and outpatient care. It is statistically strongest for medicines and largest in pesos for outpatient care. The result is sensitive to how the ambiguous transition year is coded (see the robustness checks).

## Empirical strategy

| | |
|---|---|
| **Unit** | Household (uninsured target population: Seguro Popular / INSABI / IMSS-Bienestar or no affiliation) |
| **Data** | ENIGH 2016, 2018, 2020, 2022, 2024 (pooled cross-sections) |
| **Outcome** | Quarterly OOP health spending, in constant 2024 pesos (deflated with the INPC), plus its subcategories |
| **Treatment** | `treated_x_post` = state transferred to IMSS-Bienestar × year ≥ 2020 |
| **Estimator** | Survey-weighted Poisson pseudo-maximum likelihood (PPML), two-way fixed effects (state + year) |
| **Inference** | Standard errors clustered by state |
| **Controls** | Household: log income, sex/age/education of the household head, household size, economic dependency ratio, rural locality. State: % in poverty, hospital beds, doctors and outpatient consultations per 100k inhabitants |

PPML is the main specification because about 39% of households report zero OOP spending in a quarter. Log-OLS and WLS on `log(1+y)` are reported only for comparison. Robustness checks include an event study (reference year 2020), alternative treatment cutoffs (2018, 2022) and dropping the 2020 wave.

## Repository structure

```
.
├── data_prep.py                          # Builds the household panel from ENIGH microdata
├── utils/
│   ├── states_covariates.py              # Builds the state-year covariate panel
│   └── id_map_mxstates.py                # Mexican state name / abbreviation / INEGI code helpers
├── regression_results_oophe.qmd          # Main analysis: total OOP spending (+ rendered .html)
├── regression_results_subcategories.qmd  # Same model per subcategory (+ rendered .html)
├── thesis_figures.qmd                    # Produces every figure in the dissertation (+ rendered .html)
├── input/                                # Raw auxiliary data (see below)
├── resultados/                           # Processed datasets and figures
│   ├── access_analysis_panel.csv         # Household-level analysis panel
│   ├── population_coverage.csv           # Pre-filter household snapshot (descriptive coverage table)
│   ├── state_covariates.csv              # State-year covariates
│   └── figures/                          # Thesis figures (.pdf and .svg)
└── mexico_health_recentralisation_my498_73197.pdf   # Dissertation
```

## Data sources

| Source | Files | Used for |
|---|---|---|
| **ENIGH** (INEGI), household income and expenditure survey microdata, 2016–2024 | *Not included*: `concentradohogar.dbf`, `poblacion.dbf` for each year | Household OOP spending, insurance status, demographics |
| **INPC** (national consumer price index) | `input/INPC_0326.csv` | Deflating to constant 2024 pesos |
| **SICUENTAS** (Secretaría de Salud), health accounts | `input/sicuentas/` | State health spending and uninsured population |
| **Multidimensional poverty measurement** by state (INEGI) | `input/pobreza-inegi/pm_ef_2024.xlsx` | % of population in poverty |
| **DGIS / SINAIS** (Secretaría de Salud), health statistics | `input/siss-dgis/` | Doctors, hospital beds, consultations, discharges, deaths |

The ENIGH microdata are too large to include in the repository. Download them from [INEGI](https://www.inegi.org.mx/programas/enigh/nc/) in DBF format and arrange them as:

```
<ENIGH_DIR>/
├── 2016/{concentradohogar.dbf, poblacion.dbf}
├── 2018/...
├── 2020/...
├── 2022/...
└── 2024/...
```

## Replication

### Requirements

- Python 3.11 or later (developed on 3.13)
- [Quarto](https://quarto.org) to render the `.qmd` notebooks
- Python packages:

```bash
pip install pandas numpy statsmodels matplotlib seaborn dbfread openpyxl jupyter
```

### Steps

All commands are run from the repository root. The processed datasets are already in `resultados/`, so to reproduce only the estimates and figures you can skip to step 3.

1. **Build the household panel.** First set `DATA_DIR` at the top of `data_prep.py` to your ENIGH directory.

   ```bash
   python data_prep.py
   ```

   This writes `resultados/access_analysis_panel.csv` and `resultados/population_coverage.csv`.

2. **Build the state covariates.**

   ```bash
   python -m utils.states_covariates
   ```

   This writes `resultados/state_covariates.csv`.

3. **Run the analysis and render the reports.**

   ```bash
   quarto render regression_results_oophe.qmd
   quarto render regression_results_subcategories.qmd
   quarto render thesis_figures.qmd
   ```

   `thesis_figures.qmd` refits the main model and prints a check against the reported estimate (+23.0%, p = 0.001). It then saves Figures 1–3 and A1–A5 to `resultados/figures/`.

## Citation

> Candidate 73197 (2026). *The (Re)centralisation of Health Services in Mexico: A Difference-in-Differences Analysis of Household Out-of-Pocket Spending*. MSc Applied Social Data Science dissertation, Department of Methodology, London School of Economics and Political Science. Supervisor: Dr. Linda Li.
