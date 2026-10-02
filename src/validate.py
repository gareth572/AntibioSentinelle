#charger le fichier raw le plus recent
from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")

def latest_raw_file() -> Path:
    files = sorted(RAW_DIR.glob("amr_resistance_*.csv")) 
    if not files:
        raise FileNotFoundError("Aucun fichier raw trouvé. Lancez d'abord collect.py")
    return files[-1]

df=pd.read_csv(latest_raw_file())
print(f"Fichier charge : {latest_raw_file().name} ({len(df)} lignes)")

# Les 5 regles de validation
PAYS_RETENUS = [
    "France", "Netherlands", "Greece", "Hungary", "Spain", "Czech Republic",
    "Austria", "Belgium", "Germany", "Slovenia", "Italy", "Portugal",
    "Croatia", "Slovakia", "United Kingdom",
]

# est-ce que pays/bacterie/antibiotique sont bien remplis ?
def regle_completude(df):
    """Les champs cles ne doivent pas etre vides."""
    mask = df["Country"].notna() & df["Pathogen"].notna() & df["Antibiotic"].notna()
    return mask

# est-ce que l'annee est comprise entre 1998 et 2019 ?
def regle_annee_valide(df):
    """L'annee doit etre comprise entre 1998 et 2019."""
    mask = df["Year"].between(1998, 2019)
    return mask

# est-ce que le taux de resistance est compris entre 0 et 1 ?
def regle_taux_valide(df):
    """Le taux de resistance doit etre compris entre 0 et 1."""
    mask = df["p"].between(0, 1)
    return mask

# est-ce que le nombre de souches testees est suffisant (au moins 30 souches) ?
def regle_echantillon_suffisant(df):
    """Le nombre de souches testees (N) doit etre au moins 30 pour etre fiable."""
    mask = df["N"] >= 30
    return mask

# est-ce que le pays est dans la liste des pays retenus ?
def regle_pays_dans_perimetre(df):
    """Le pays doit etre dans la liste des pays retenus."""
    mask = df["Country"].isin(PAYS_RETENUS)
    return mask

# appliquer les règles et afficher un résumé
rules = {
    "completude": regle_completude,
    "annee_valide": regle_annee_valide,
    "taux_valide": regle_taux_valide,
    "echantillon_suffisant": regle_echantillon_suffisant,
    "pays_dans_perimetre": regle_pays_dans_perimetre,
}

print("\n--- Resultat de chaque regle ---")
masks = {}
for nom, fonction in rules.items():
    mask = fonction(df)
    masks[nom] = mask
    nb_echecs = (~mask).sum()
    print(f"{nom} : {nb_echecs} lignes en echec sur {len(df)}")

# combiner toutes les regles : une ligne est valide seulement si elle passe TOUTES les regles
mask_global = pd.Series(True, index=df.index)
for nom, mask in masks.items():
    mask_global = mask_global & mask

accepted = df[mask_global].copy()
rejected = df[~mask_global].copy()

print(f"\n--- Resultat final ---")
print(f"Lignes acceptees : {len(accepted)}")
print(f"Lignes rejetees : {len(rejected)}")

from datetime import datetime, timezone

CURATED_DIR = Path("data/curated")
REJECTED_DIR = Path("data/rejected")
CURATED_DIR.mkdir(parents=True, exist_ok=True)
REJECTED_DIR.mkdir(parents=True, exist_ok=True)

# ajouter la cause du rejet pour chaque ligne rejetee
def causes_rejet(row, masks):
    causes = [nom for nom, mask in masks.items() if not mask.loc[row.name]]
    return ", ".join(causes)

rejected = rejected.copy()
rejected["cause_rejet"] = rejected.apply(lambda row: causes_rejet(row, masks), axis=1)

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
accepted_path = CURATED_DIR / f"resistance_curated_{stamp}.csv"
rejected_path = REJECTED_DIR / f"resistance_rejected_{stamp}.csv"

accepted.to_csv(accepted_path, index=False)
rejected.to_csv(rejected_path, index=False)

print(f"\nFichier curated ecrit : {accepted_path} ({len(accepted)} lignes)")
print(f"Fichier rejected ecrit : {rejected_path} ({len(rejected)} lignes)")