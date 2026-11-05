from pathlib import Path
import pandas as pd

CURATED_DIR = Path("data/curated")


def latest_validated_file() -> Path:
    # "2*" retient les fichiers horodates et laisse de cote consumption_curated_final.csv
    files = sorted(CURATED_DIR.glob("consumption_curated_2*.csv"))
    if not files:
        raise FileNotFoundError("Aucun fichier valide trouve. Lancez d'abord validate_amc.py")
    return files[-1]


COLUMN_MAP = {
    "Country": "country",
    "Year": "year",
    "Sector": "sector",
    "Antimicrobial.Type": "administration_route",
    "Antibiotic_class": "antibiotic_class",
    "class": "antibiotic_class_label",
    "DDD": "ddd",
}

source_file = latest_validated_file()
df = pd.read_csv(source_file)
df = df[list(COLUMN_MAP.keys())].rename(columns=COLUMN_MAP)
print(f"Fichier transforme : {source_file.name}")
print(df.shape)

# controle : le code de classe contenu dans le libelle doit egaler antibiotic_class
code = df["antibiotic_class_label"].str.split().str[0]
ecart = df["antibiotic_class_label"].notna() & (code != df["antibiotic_class"])
print("\n--- Controle de coherence ---")
print(f"classe et libelle en desaccord : {ecart.sum()}")
if ecart.any():
    raise ValueError("Incoherence detectee : transformation arretee, rien n'est publie.")

# signalement des valeurs anormales (aucune ligne n'est supprimee)
SERIE = ["country", "antibiotic_class", "sector", "administration_route"]
positif = df["ddd"] > 0
df["_med"] = df[positif].groupby(SERIE)["ddd"].transform("median")
df["_n"] = df[positif].groupby(SERIE)["ddd"].transform("size")
df["anomalie_valeur"] = (
    positif & (df["_n"] >= 5) & (df["_med"] >= 0.5) & (df["ddd"] > 5 * df["_med"])
)
df = df.drop(columns=["_med", "_n"])

print("\n--- Valeurs signalees (anomalie_valeur) ---")
print(f"nombre : {df['anomalie_valeur'].sum()}")
print(df[df["anomalie_valeur"]][["country", "year", "antibiotic_class", "sector", "ddd"]]
      .sort_values(["country", "year"]).to_string(index=False))

df = df.astype({"year": "int64", "ddd": "float64", "anomalie_valeur": "bool"})

# publication avec upsert sur la cle metier
CLE_METIER = ["country", "year", "sector", "administration_route", "antibiotic_class"]
FINAL_PATH = CURATED_DIR / "consumption_curated_final.csv"

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