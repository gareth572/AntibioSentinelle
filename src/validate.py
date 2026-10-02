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