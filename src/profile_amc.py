from pathlib import Path
import pandas as pd

files = sorted(Path("data/raw").glob("amc_consumption_*.csv"))
if not files:
    raise FileNotFoundError("Aucun fichier amc trouve. Lancez : python src\\collect.py amc")

df = pd.read_csv(files[-1])
print(f"Fichier analyse : {files[-1].name}")

print("\n--- Dimensions ---")
print(df.shape)

print("\n--- Types ---")
print(df.dtypes)

print("\n--- Valeurs manquantes (taux) ---")
print(df.isna().mean().sort_values(ascending=False))

print("\n--- Doublons (lignes entierement identiques) ---")
print(df.duplicated().sum())

print("\n--- Apercu ---")
print(df.head(5).to_string())

print("\n--- Colonnes texte : valeurs distinctes ---")
for col in df.select_dtypes(include=["object", "string"]).columns:
    n = df[col].nunique()
    print(f"\n{col} : {n} valeurs distinctes")
    if n <= 40:
        print(df[col].value_counts().to_string())

print("\n--- Colonnes numeriques ---")
print(df.describe().T.to_string())