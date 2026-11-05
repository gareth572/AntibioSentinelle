from pathlib import Path
import pandas as pd

INPUT_DIR = Path("data/curated")

def latest_validated_file() -> Path:
    files = sorted(INPUT_DIR.glob("resistance_curated_2*.csv"))
    if not files:
        raise FileNotFoundError("Aucun fichier valide trouve. Lancez d'abord validate.py")
    return files[-1]

COLUMN_MAP = {
    "Year": "year",
    "Country": "country",
    "Pathogen": "pathogen",
    "Pathogen_long": "pathogen_long",
    "Antibiotic": "antibiotic",
    "Antibiotic_long": "antibiotic_long",
    "Antibiotic_class": "antibiotic_class",
    "patientType": "patient_type",
    "N": "n_tested",
    "p": "resistance_rate",
    "N_I_R": "n_resistant",
}

df = pd.read_csv(latest_validated_file())
df = df[list(COLUMN_MAP.keys())].rename(columns=COLUMN_MAP)

print(f"Fichier transforme : {latest_validated_file().name}")
print(df.shape)
print(df.dtypes)
print(df.head(3))

# Controle de coherence
borne_ok = (df["n_resistant"] >= 0) & (df["n_resistant"] <= df["n_tested"])
taux_calcule = df["n_resistant"] / df["n_tested"]
taux_ok = (taux_calcule - df["resistance_rate"]).abs() < 1e-6

print("\n--- Controle de coherence ---")
print(f"n_resistant hors bornes : {(~borne_ok).sum()}")
print(f"taux incoherent avec n_resistant / n_tested : {(~taux_ok).sum()}")

# arreter si une incoherence est detectee
if (~borne_ok).any() or (~taux_ok).any():
    raise ValueError("Incoherence detectee : transformation arretee, rien n'est publie.")

# typage explicite des colonnes
df = df.astype({
    "year": "int64",
    "n_tested": "int64",
    "n_resistant": "int64",
    "resistance_rate": "float64",
})

# publication avec upsert sur la cle metier
CLE_METIER = ["year", "country", "pathogen", "antibiotic", "patient_type"]
FINAL_PATH = INPUT_DIR / "resistance_curated_final.csv"

if FINAL_PATH.exists():
    existing = pd.read_csv(FINAL_PATH)
    combined = pd.concat([existing, df], ignore_index=True)
else:
    combined = df

rows_before = len(combined)
combined = combined.drop_duplicates(subset=CLE_METIER, keep="last")
duplicates_removed = rows_before - len(combined)
combined = combined.sort_values(CLE_METIER).reset_index(drop=True)
combined.to_csv(FINAL_PATH, index=False)

print(f"\nFichier final : {FINAL_PATH} ({len(combined)} lignes, {duplicates_removed} doublons ecartes)")