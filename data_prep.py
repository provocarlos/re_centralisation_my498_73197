import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from dbfread import DBF

warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR = Path("/Users/CarlosMora/Documents/GitHub/Conjuntos de datos/ENIGH/microdatos")
OUTPUT_DIR = Path("resultados")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2016, 2018, 2020, 2022, 2024]

# ---------------------------------------------------------------------------
# Inflation Adjustment (IPC)
# ---------------------------------------------------------------------------

def load_ipc_mapping():
    ipc_path = Path("input/INPC_0326.csv")
    if not ipc_path.exists():
        print(f"Warning: {ipc_path} not found. Skipping inflation adjustment.")
        return None

    # Read IPC, skipping metadata rows. Row 18 (index 17) has headers.
    df_ipc = pd.read_csv(ipc_path, skiprows=18, encoding="latin1")
    df_ipc['Fecha'] = pd.to_datetime(df_ipc['Fecha'], format='%d/%m/%Y', errors='coerce')
    df_ipc = df_ipc.dropna(subset=['Fecha'])
    df_ipc['year'] = df_ipc['Fecha'].dt.year

    # Aggregate by average index per year
    annual_ipc = df_ipc.groupby('year')['SP1'].mean().reset_index()

    # Use 2024 as base year for constant prices
    base_ipc = annual_ipc.loc[annual_ipc['year'] == 2024, 'SP1'].values[0]
    annual_ipc['deflator'] = base_ipc / annual_ipc['SP1']

    return annual_ipc.set_index('year')['deflator'].to_dict()

DEFLATORS = load_ipc_mapping()

# States that remained decentralized (Control Group)
NO_IMSSB = ["01", # Aguascalientes
            "05", # Coahuila
            "08", # Chihuahua
            "10", # Durango
            "11", # Guanajuato
            "14", # Jalisco
            "19", # Nuevo Leon
            "22"] # Queretaro

# # Health Expenditure Codes
# HEALTH_CODES = {
#     "medicines": [f"J{i:03d}" for i in range(20, 38)] + [f"J{i:03d}" for i in range(44, 59)] + \
#                  ["J035", "061118", "061119", "06111A", "06111B", "06111C", "06111D", "06111E",
#                   "06111G", "06111H", "06111I", "061111", "061112", "061113", "061114", "061115",
#                   "061116", "061117", "06111K", "06111L", "011994", "06111F"],
#     "consultations": [f"J{i:03d}" for i in range(16, 19)] + ["062193", "062191", "062210", "062291", "062292", "064101", "064102", "064201"],
#     "hospital": [f"J{i:03d}" for i in range(39, 43)] + ["063101", "063105", "063200", "063102"],
#     "pregnancy": [f"J{i:03d}" for i in range(1, 15)]  + ["062194", "062192", "064103", "064202", "063103", "063104", "062198", "063106"],
#     "other": [f"J{i:03d}" for i in range(60, 72)] +["061f11J", "131209", "061211", "061212", "061221", "061222", "061223", "061230", "061120", "062195", "062196", "062197",
#               "061311", "061312", "061320", "061332", "061333", "061331", "061334", "061335", "061336", "061337", "061338", "061401",
#               "061402", "062110", "062311", "062312", "062313", "062321", "062322", "062323", "133021", "133022", "121202"]
# }
# ALL_HEALTH_CODES = [code for codes in HEALTH_CODES.values() for code in codes]

SERVMED_MAPPING = {
    "servmed_1": "Health Center",
    "servmed_2": "Hospital",
    "servmed_3": "IMSS",
    "servmed_4": "IMSS-Bienestar/INSABI",
    "servmed_5": "Other",
    "servmed_6": "Other",
    "servmed_7": "Other",
    "servmed_8": "Private Office/Pharmacy",
    "servmed_9": "Private Office/Pharmacy",
    "servmed_10": "Other",
    "servmed_11": "Other",
    "servmed_12": "IMSS-Bienestar/INSABI"
}

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def read_dbf_cols(path: Path, cols: list) -> pd.DataFrame:
    """Reads specific columns from a DBF file using dbfread."""
    try:
        table = DBF(path, load=True)
        df = pd.DataFrame(table.records)
        existing_cols = [c for c in cols if c in df.columns]
        return df[existing_cols]
    except:  # noqa: E722
        print(f"Error reading {path}: {e}")
        return pd.DataFrame()

def find_col_list(available_cols: list, candidates: list) -> str:
    for c in candidates:
        if c in available_cols:
            return c
    return None


def process_year(year: int):
    # year = 2016
    print(f"--- Processing {year} ---")
    year_dir = DATA_DIR / str(year)

    # 0. Load Concentradohogar
    c_path = year_dir / "concentradohogar.dbf"
    if not c_path.exists(): return None

    c_table = DBF(c_path)
    c_cols_avail = c_table.field_names

    v_col = find_col_list(c_cols_avail, ["folioviv"])
    h_col = find_col_list(c_cols_avail, ["foliohog"])
    g_col = find_col_list(c_cols_avail, ["ubica_geo", "entidad"])
    f_col = find_col_list(c_cols_avail, ["factor", "factor_hog"])
    i_col = find_col_list(c_cols_avail, ["ing_cor"])
    h_a_col = find_col_list(c_cols_avail, ["sexo_jefe"])
    h_b_col = find_col_list(c_cols_avail, ["edad_jefe"])
    h_c_col = find_col_list(c_cols_avail, ["educa_jefe"])
    h_d_col = find_col_list(c_cols_avail, ["tot_integ"])
    h_e_col = find_col_list(c_cols_avail, ["menores"])
    h_f_col = find_col_list(c_cols_avail, ["p65mas"])
    h_g_col = find_col_list(c_cols_avail, ["atenc_ambu", "ambul_serv"])
    h_h_col = find_col_list(c_cols_avail, ["aten_hosp", "hospital"])
    h_i_col = find_col_list(c_cols_avail, ["medicinas", "medic_prod"])
    h_j_col = find_col_list(c_cols_avail, ["salud"])

    household_cols = [
        h_a_col, h_b_col, h_c_col, h_d_col, h_e_col,
        h_f_col, h_g_col, h_h_col, h_i_col, h_j_col
    ]

    df_c = read_dbf_cols(c_path, [v_col, h_col, g_col, f_col, i_col] + household_cols)

    df_c = df_c.rename(columns={
        f_col: "factor",
        i_col: "income",
        h_a_col: "head_sex",
        h_b_col: "head_age",
        h_c_col: "head_education",
        h_d_col: "household_size",
        h_e_col: "minors_count",
        h_f_col: "elderly_count",
        h_j_col: "oop_expenditure",
    })
    df_c = df_c.rename(columns={
        "ambul_serv": "outpatient_care", "atenc_ambu": "outpatient_care",
        "aten_hosp": "hospital",
        "medic_prod": "medicines", "medicinas": "medicines",
    })

    df_c["locality_rural"] = (pd.to_numeric(df_c[g_col].astype(str).str.zfill(10).str[2], errors="coerce").fillna(0) == 6).astype(int)

    df_c["household_id"] = df_c[v_col].astype(str).str.strip() + "_" + df_c[h_col].astype(str).str.strip()

    if g_col == "entidad":
        df_c["state_code"] = df_c[g_col].astype(str).str.zfill(2)
    else:
        df_c["state_code"] = df_c[g_col].astype(str).str.zfill(5).str[:2]

    df_c["head_education"] = pd.to_numeric(df_c["head_education"], errors="coerce").fillna(0).astype(int)
    df_c["economic_dependency_ratio"] = (df_c["minors_count"].fillna(0) + df_c["elderly_count"].fillna(0)) / df_c["household_size"].replace(0, np.nan)

    df_c = df_c[[
        "household_id", "locality_rural", "state_code", "factor", "income",
        "economic_dependency_ratio", "head_sex", "head_age", "head_education", 
        "household_size", "outpatient_care", "hospital", "medicines", "oop_expenditure",
    ]]

    # 1. Load Personas
    p_path = year_dir / "poblacion.dbf"
    p_table = DBF(p_path)
    p_cols_avail = p_table.field_names

    vp_col = find_col_list(p_cols_avail, ["folioviv"])
    hp_col = find_col_list(p_cols_avail, ["foliohog"])
    numren_col = find_col_list(p_cols_avail, ["numren"])

    # Health columns
    prob_sal_col = "prob_sal"
    aten_sal_col = "aten_sal"
    prob_anio_col = "prob_anio"
    prob_mes_col = "prob_mes"
    hh_esp_col = "hh_esp"
    mm_esp_col = "mm_esp"
    servmed_cols = [f"servmed_{i}" for i in range(1, 13) if f"servmed_{i}" in p_cols_avail]

    insurance_candidates = ["segpop", "pop_insabi", "atemed", "inst_1", "inst_2", "inst_3", "inst_4", "inst_5", "inst_6", "inst_9"]

    p_cols_to_read = [vp_col, hp_col, numren_col, prob_sal_col, aten_sal_col, prob_anio_col, prob_mes_col, hh_esp_col, mm_esp_col] + servmed_cols
    for c in insurance_candidates:
        if c in p_cols_avail: p_cols_to_read.append(c)

    df_p = read_dbf_cols(p_path, p_cols_to_read)
    df_p["household_id"] = df_p[vp_col].astype(str).str.strip() + "_" + df_p[hp_col].astype(str).str.strip()

    df_p["had_problem"] = (pd.to_numeric(df_p[prob_sal_col], errors="coerce").fillna(0) == 1).astype(int)
    df_p["effective_access"] = (pd.to_numeric(df_p[aten_sal_col], errors="coerce").fillna(0) == 1).astype(int)

    # Institution Identification
    def get_institution(row):
        for col in servmed_cols:
            val = str(row[col]).strip()
            # Extract numeric index from column name (e.g., '1' from 'servmed_1')
            idx = col.split("_")[1]
            # Valid 'Yes' values: '1', the index itself (e.g., '1'), or padded index ('01')
            if val in ["1", idx, idx.zfill(2)]:
                return SERVMED_MAPPING.get(col, "Other")
        return "None/No Attention"

    # Get dummies for institutions
    df_p["institution"] = df_p.apply(get_institution, axis=1)
    df_p["institution"] = df_p["institution"].str.lower().str.replace(" ", "_").str.replace("/", "_").str.replace("-", "_")
    df_p = pd.get_dummies(df_p, columns=["institution"], prefix="inst", dtype=int, prefix_sep="_")

    # Create target variable for public attention
    df_p["public_attention"] = (df_p["inst_imss_bienestar_insabi"] == 1).astype(int)

    # Demand date
    df_p["demand_year"] = pd.to_numeric(df_p[prob_anio_col], errors="coerce")
    # df_p["demand_month"] = pd.to_numeric(df_p[prob_mes_col], errors="coerce")

    # Insurance logic
    df_p["is_imss"] = (pd.to_numeric(df_p.get("inst_1"), errors="coerce").fillna(0) == 1).astype(int)
    df_p["is_issste"] = ((pd.to_numeric(df_p.get("inst_2"), errors="coerce").fillna(0) == 2) |
                            (pd.to_numeric(df_p.get("inst_3"), errors="coerce").fillna(0) == 3)).astype(int)
    df_p["is_private"] = (pd.to_numeric(df_p.get("inst_4"), errors="coerce").fillna(0) == 4).astype(int)

    if year <= 2018:
        sp_col = find_col_list(p_cols_avail, ["segpop"])
        df_p["is_uninsured_target"] = ((pd.to_numeric(df_p.get(sp_col), errors="coerce").fillna(0) == 1) |
                                        (pd.to_numeric(df_p.get("atemed"), errors="coerce").fillna(0) == 2)).astype(int)
    elif year <= 2022:
        insabi_col = find_col_list(p_cols_avail, ["pop_insabi"])
        df_p["is_uninsured_target"] = ((pd.to_numeric(df_p.get(insabi_col), errors="coerce").fillna(0) == 1)|
                                        (pd.to_numeric(df_p.get("atemed"), errors="coerce").fillna(0) == 2)).astype(int)
    else:
        df_p["is_uninsured_target"] = ((pd.to_numeric(df_p.get("inst_5"), errors="coerce").fillna(0) == 5) |
                                        (pd.to_numeric(df_p.get("inst_6"), errors="coerce").fillna(0) == 6) |
                                        (pd.to_numeric(df_p.get("inst_9"), errors="coerce").fillna(0) == 9)).astype(int)

    # Accumulate household-level health problem indicators
    agg_cols = {
        "had_problem": "max",
        "demand_year": "max",
        "effective_access": "max",
        "is_uninsured_target": "max",
        "public_attention": "max",
        "is_imss": "max",
        "is_issste": "max",
        "is_private": "max",
        "inst_health_center": "max",
        "inst_hospital": "max",
        "inst_imss": "max",
        "inst_imss_bienestar_insabi": "max",
        "inst_private_office_pharmacy": "max",
        "inst_other": "max",
        "inst_none_no_attention": "max",
    }
    # Only aggregate columns that exist in df_p
    agg_cols = {k: v for k, v in agg_cols.items() if k in df_p.columns}
    health_agg = df_p.groupby("household_id").agg(agg_cols).reset_index()

    # 3. Final Merge
    df_final = health_agg.merge(df_c, on="household_id", how="left")

    # Apply deflation if mapping is available
    for var in ["income", "oop_expenditure", "outpatient_care", "hospital", "medicines"]:
        if DEFLATORS and year in DEFLATORS:
            df_final[var] = df_final[var] * DEFLATORS[year]
        else:
            df_final[var] = df_final[var]

    # Snapshot of the full (pre-filter) household population, used only to compute the
    # uninsured-target population's share of the national total for the descriptive table
    # in the thesis (Section 2.1) -- not used anywhere in the regression pipeline.
    coverage_snapshot = df_final[["household_id", "state_code", "factor", "is_uninsured_target"]].copy()
    coverage_snapshot["year"] = year

    # Filter for uninsured target population
    df_final = df_final[df_final['is_uninsured_target'] == 1].copy()

    # ── Feature engineering
    df_final["year"] = year
    df_final["post"] = int(year >= 2020)
    df_final["treated"]             = (~df_final["state_code"].isin(NO_IMSSB)).astype(int)
    df_final['post_treatment']      = (df_final['year'] >= 2020).astype(int)
    df_final['treated_x_post']      = df_final['treated'] * df_final['post_treatment']
    df_final['log_oop_expenditure'] = np.log1p(df_final['oop_expenditure'])
    df_final["log_income"]          = np.log1p(df_final["income"])


    return df_final, coverage_snapshot

# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------

all_years = []
all_coverage = []
for year in YEARS:
    result = process_year(year)
    if result is not None:
        df_year, coverage_year = result
        all_years.append(df_year)
        all_coverage.append(coverage_year)

if all_years:
    panel = pd.concat(all_years, ignore_index=True)
    panel.to_csv(OUTPUT_DIR / "access_analysis_panel.csv", index=False)
    print(f"Panel saved to {OUTPUT_DIR / 'access_analysis_panel.csv'}")
    print(f"Total rows (people with health problems): {len(panel):,}")

if all_coverage:
    coverage = pd.concat(all_coverage, ignore_index=True)
    coverage.to_csv(OUTPUT_DIR / "population_coverage.csv", index=False)
    print(f"Coverage snapshot saved to {OUTPUT_DIR / 'population_coverage.csv'}")
else:
    print("No data processed.")
