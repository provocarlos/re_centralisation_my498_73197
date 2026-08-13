import os
import pandas as pd
import numpy as np
from pathlib import Path
import re
from utils.id_map_mxstates import abr_to_state_code, state_name_to_abr
import warnings

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "resultados"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def clean_column_names(df):
    new_cols = []
    for col in df.columns:
        name = col

        # Drop unnamed columns
        if re.match(r'Unnamed:', name):
            new_cols.append(None)
            continue

        # Remove leading numbers/bullets like "1.", "1.1", "1.A", "I.", "10 ", etc.

        # Remove parenthetical references like "(1+2+3)", "(1.1+1.2)", "(Ramo 12)", etc.
        name = re.sub(r'\(.*?\)', '', name)

        # Normalize accented characters
        name = name.replace('á','a').replace('é','e').replace('í','i') \
                   .replace('ó','o').replace('ú','u').replace('ñ','n') \
                   .replace('Á','A').replace('É','E').replace('Í','I') \
                   .replace('Ó','O').replace('Ú','U').replace('Ñ','N')

        # Lowercase
        name = name.lower()

        # Replace spaces and special chars with underscores
        name = re.sub(r'[^a-z0-9]+', '_', name)

        # Strip leading/trailing underscores
        name = name.strip('_')

        new_cols.append(name)

    # Drop unnamed columns entirely
    df = df[[col for col, new in zip(df.columns, new_cols) if new is not None]]
    df.columns = [new for new in new_cols if new is not None]

    # Handle any duplicate column names by appending a suffix
    seen = {}
    final_cols = []
    for col in df.columns:
        if col in seen:
            seen[col] += 1
            final_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            final_cols.append(col)
    df.columns = final_cols

    return df


def load_sicuentas():
    sicuentas_path = Path(INPUT_DIR / "sicuentas/DA-SICUENTAS_17012024_Corrientes.csv")
    if not sicuentas_path.exists():
        print(f"Warning: {sicuentas_path} not found. Skipping health expenditure.")
        return None

    # Read CSV file
    df_sicuentas_raw = pd.read_csv(sicuentas_path, encoding="latin1")
    df_sicuentas = clean_column_names(df_sicuentas_raw)
    df_sicuentas = df_sicuentas.dropna(how='all')
    variables_of_interest = [
        'cve_ent', 'entidad_federativa', 'ano',
        '1_1_gasto_publico_en_salud_para_la_poblacion_sin_seguridad_social',
        '1_1_3_fondo_de_aportaciones_para_los_servicios_de_salud_ramo_33',
        '10_gasto_en_la_poblacion_sin_seguridad_social_como_del_gto_pub_en_salud',
        '14_gasto_per_capita_para_la_poblacion_sin_seguridad_social',
        '22_poblacion_total', '24_poblacion_sin_seguridad_social']
    df_sicuentas = df_sicuentas[variables_of_interest]
    # Create a new variable for the percentage of people without social security in the total population
    df_sicuentas['pct_uninsured'] = df_sicuentas['24_poblacion_sin_seguridad_social'] / df_sicuentas['22_poblacion_total'] * 100
    # Rename columns to English
    df_sicuentas = df_sicuentas.rename(columns={
        'cve_ent': 'state_code',
        'entidad_federativa': 'state_name',
        'ano': 'year',
        '10_gasto_en_la_poblacion_sin_seguridad_social_como_del_gto_pub_en_salud': 'pct_healthexp_uninsured',
        '14_gasto_per_capita_para_la_poblacion_sin_seguridad_social': 'healthexp_percapita_uninsured',
        '22_poblacion_total': 'total_pop',
        '24_poblacion_sin_seguridad_social': 'total_uninsured_pop'}
        )

    # Drop variables that are no longer needed
    df_sicuentas = df_sicuentas.drop(
        columns=['1_1_3_fondo_de_aportaciones_para_los_servicios_de_salud_ramo_33',
                  '1_1_gasto_publico_en_salud_para_la_poblacion_sin_seguridad_social',
                  'state_name'])

    # Add padding to state_code to ensure it's 2 digits
    df_sicuentas['state_code'] = df_sicuentas['state_code'].apply(lambda x: str(x).zfill(2))
    # Exclude national totals and unknowns (code greater than 32)
    df_sicuentas = df_sicuentas[df_sicuentas['state_code'].astype(int) <= 32]

    return df_sicuentas

# ── configuration ────────────────────────────────────────────────────────────
INPUT_FILE  = Path(INPUT_DIR / "pobreza-inegi/pm_ef_2024.xlsx")

YEARS     = [2016, 2018, 2020, 2022, 2024]
PCT_COLS  = [10, 11, 12, 13, 14]   # percentage block, row 9
STATE_ROW = 3                       # row with the full state name
DATA_ROW  = 9                       # row with poverty indicator values

warnings.filterwarnings(
    "ignore",
    message="Conditional Formatting extension is not supported",
    category=UserWarning,
)

# ── extraction ───────────────────────────────────────────────────────────────
def extract_poverty_pct() -> pd.DataFrame:
    xl      = pd.ExcelFile(INPUT_FILE)
    records = []

    for sheet in xl.sheet_names:
        # Skip non-state sheets: index, precision indicators, chart sheets
        if sheet in ["Índice", "EUM"] or sheet.startswith("IP") or sheet.startswith("Gráf"):
            continue

        df = pd.read_excel(INPUT_FILE, sheet_name=sheet, header=None)

        # state_name = df.iloc[STATE_ROW, 0]
        pct_values = df.iloc[DATA_ROW, PCT_COLS].tolist()

        for year, pct in zip(YEARS, pct_values):
            records.append({
                "year":        year,
                "state_code":  abr_to_state_code(sheet),
                "pct_poverty": round(float(pct), 6) if pd.notna(pct) else None,
            })

        df_poverty = pd.DataFrame(records)
        # Change state_code to string and pad with leading zeros to ensure 2 digits
        df_poverty['state_code'] = df_poverty['state_code'].astype(str).str.zfill(2)

    return df_poverty

# ── extraction ───────────────────────────────────────────────────────────────
def extract_outcomes() -> pd.DataFrame:

    file_list = {"total_hospital_discharges": "2017-2026_Egresos_Totales_porEntidad.xlsx",
                 "total_outpatient_consultations": "2000-2024_consultasporconsultanominal_totales_poranio.xlsx",
                 "total_deaths": "1998-2024_defunciones_totales.xlsx"}

    records = pd.DataFrame()

    for name, file in file_list.items():
        filepath = Path(INPUT_DIR / f"siss-dgis/{file}")
        df = pd.read_excel(filepath)
        df = df.rename(columns={df.columns[0]: 'state_name'})
        # Gather year columns into a single year column
        df = df.melt(id_vars=['state_name'], var_name='year', value_name=name)
        records = pd.merge(records, df, on=['state_name', 'year'], how='outer') if not records.empty else df

    records = records[records['state_name'] != 'Nacional'].reset_index(drop=True)
    # Add state_code column using abr_to_state_code mapping and convert the integer to a string with leading zeros (2 digits)
    records['state_code'] = records['state_name'].apply(lambda x: str(abr_to_state_code(x)).zfill(2))
    records = records.drop(columns=['state_name'])
    return records

# ── extraction ───────────────────────────────────────────────────────────────
def extract_resources() -> pd.DataFrame:
    file_list = ["2012-2024_personalDeSalud_Entidad.xlsx",
                 "2012-2024_recursosFisicos_Entidad.xlsx"]

    records = pd.DataFrame()

    for file in file_list:
        filepath = Path(INPUT_DIR / f"siss-dgis/{file}")

        df = pd.read_excel(filepath, sheet_name=0)
        df = clean_column_names(df)
        df = df.rename(columns={df.columns[1]: 'state_name', 'ano': 'year'})
        if file is file_list[0]:
            df = df[['year', 'state_name', 'medicos_generales_especialistas_y_odontologos', 'enfermeras_generales_y_especialistas']]
            df = df.rename(columns={'medicos_generales_especialistas_y_odontologos': 'total_doctors',
                                    'enfermeras_generales_y_especialistas': 'total_nurses'})
        if file is file_list[1]:
            df = df[['year', 'state_name', 'consultorios', 'camas_hospitalarias', 'camas_no_hospitalarias', 'quirofanos']]
            df = df.rename(columns={'consultorios': 'total_clinics',
                                    'camas_hospitalarias': 'total_hospital_beds',
                                    'camas_no_hospitalarias': 'total_nonhospital_beds',
                                    'quirofanos': 'total_operating_rooms'})
        # Gather into records, keyed on state_name/year
        records = pd.merge(records, df, on=['state_name', 'year'], how='outer') if not records.empty else df
    records = records[records['state_name'] != 'Nacional'].reset_index(drop=True)
    # Add state_code column using abr_to_state_code mapping and convert the integer to a string with leading zeros (2 digits)
    records['state_code'] = records['state_name'].apply(lambda x: str(abr_to_state_code(state_name_to_abr(x))).zfill(2))
    records = records.drop(columns=['state_name'])
    return records

df_sicuentas = load_sicuentas()
df_poverty = extract_poverty_pct()
df_attention = extract_outcomes()
df_resources = extract_resources()

# Merge all dataframes on 'state_code' and 'year'
df_final = df_sicuentas.merge(df_poverty, on=['state_code', 'year'], how='outer') \
    .merge(df_attention, on=['state_code', 'year'], how='outer') \
    .merge(df_resources, on=['state_code', 'year'], how='outer') \


# Convert all columns that contains "totals" into ratio per 100,000 population (total_pop)
for col in df_final.columns:
    if col.startswith("total_") and col not in ["total_pop", "total_uninsured_pop"]:
        df_final[col + "_per100k"] = (df_final[col] / df_final['total_pop']) * 100000
        # Drop the original total column
        df_final = df_final.drop(columns=[col])


# Filter for the years of interest
# df_final = df_final[df_final['year'].isin(YEARS)].reset_index(drop=True)

# Ensure year is integer type for consistent merging
df_final['year'] = df_final['year'].astype(int)

# Drop total_pop and total_uninsured_pop as they are not needed for the final dataset
df_final = df_final.drop(columns=['total_pop', 'total_uninsured_pop'])

# Keep only the columns that are needed for the final dataset
columns_to_keep = ['state_code', 'year', 'pct_poverty', 'total_hospital_beds_per100k', 'total_doctors_per100k', 'total_outpatient_consultations_per100k']
df_final = df_final[columns_to_keep]

# save as csv
OUTPUT_FILE = Path(OUTPUT_DIR / "state_covariates.csv")
df_final.to_csv(OUTPUT_FILE, index=False)
