#charger le fichier raw le plus recent
from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")

def latest_raw_file() -> Path:
    files = sorted(RAW_DIR.glob("amr_resistance_*.csv")) 
    if not files:
        raise FileNotFoundError("Aucun fichier raw trouvé dans le répertoire 'data/raw'. Lancez d'abord collect.py")
    return files[-1]

df=pd.read_csv(latest_raw_file())
print(f"Fichier analyse : {latest_raw_file().name}")

#profilage
print("\n-- Dimensions --")
print(df.shape)

print("\n-- Types de données --")
print(df.dtypes)

print("\n-- Taux de valeurs manquantes --")
print(df.isna().mean().sort_values(ascending=False))

print("\n-- Doublons --")
print(df.duplicated().sum())

print("\n-- Statistiques descriptives --")
print(df.describe(include='all'))

print("\n--- Verification colonnes N_tested vs N vs test ---")
print(df[["N_S", "test", "N_tested", "N", "p"]].head(5))

print("\n--- Nombre de lignes par pays ---")
counts_by_country = df["Country"].value_counts()
print(counts_by_country)

print("\n--- Etendue des annees couvertes, par pays ---")
year_range = df.groupby("Country")["Year"].agg(["min", "max", "count"])
print(year_range.sort_values("count", ascending=False))