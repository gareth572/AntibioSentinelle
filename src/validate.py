# charger le fichier raw le plus recent
from datetime import datetime, timezone
from pathlib import Path
import json
import time

import pandas as pd

start = time.perf_counter()  # chronometre precis

RAW_DIR = Path("data/raw")
CURATED_DIR = Path("data/curated")
REJECTED_DIR = Path("data/rejected")
OUT_OF_SCOPE_DIR = Path("data/out_of_scope")
REPORTS_DIR = Path("reports")
for d in (CURATED_DIR, REJECTED_DIR, OUT_OF_SCOPE_DIR, REPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)


def latest_raw_file() -> Path:
    files = sorted(RAW_DIR.glob("amr_resistance_*.csv"))
    if not files:
        raise FileNotFoundError("Aucun fichier raw trouve. Lancez d'abord collect.py")
    return files[-1]


raw_file = latest_raw_file()
df = pd.read_csv(raw_file)
print(f"Fichier charge : {raw_file.name} ({len(df)} lignes)")

# perimetre : pays retenus apres profilage
PAYS_RETENUS = [
    "France", "Netherlands", "Greece", "Hungary", "Spain", "Czech Republic",
    "Austria", "Belgium", "Germany", "Slovenia", "Italy", "Portugal",
    "Croatia", "Slovakia", "United Kingdom",
]


# ---- regles de QUALITE : un echec = ligne invalide ----

# est-ce que pays/bacterie/antibiotique sont bien remplis ?
def regle_completude(df):
    return df["Country"].notna() & df["Pathogen"].notna() & df["Antibiotic"].notna()


# est-ce que l'annee est comprise entre 1998 et 2019 ?
def regle_annee_valide(df):
    return df["Year"].between(1998, 2019)


# est-ce que le taux de resistance est compris entre 0 et 1 ?
def regle_taux_valide(df):
    return df["p"].between(0, 1)


# est-ce que le nombre de souches testees est suffisant (au moins 30) ?
def regle_echantillon_suffisant(df):
    return df["N"] >= 30


# ---- filtre de PERIMETRE : un echec = ligne valide mais hors perimetre ----

# est-ce que le pays est dans la liste des pays retenus ?
def filtre_pays_dans_perimetre(df):
    return df["Country"].isin(PAYS_RETENUS)


rules = {
    "completude": regle_completude,
    "annee_valide": regle_annee_valide,
    "taux_valide": regle_taux_valide,
    "echantillon_suffisant": regle_echantillon_suffisant,
}

print("\n--- Resultat de chaque regle de qualite ---")
masks = {}
for nom, fonction in rules.items():
    mask = fonction(df)
    masks[nom] = mask
    print(f"{nom} : {(~mask).sum()} lignes en echec sur {len(df)}")

# une ligne est valide seulement si elle passe TOUTES les regles de qualite
mask_valide = pd.Series(True, index=df.index)
for mask in masks.values():
    mask_valide = mask_valide & mask

mask_perimetre = filtre_pays_dans_perimetre(df)

# trois tas qui ne se chevauchent pas
invalid = df[~mask_valide].copy()
out_of_scope = df[mask_valide & ~mask_perimetre].copy()
accepted = df[mask_valide & mask_perimetre].copy()

print("\n--- Resultat final ---")
print(f"Lignes acceptees : {len(accepted)}")
print(f"Lignes invalides : {len(invalid)}")
print(f"Lignes hors perimetre : {len(out_of_scope)}")


# cause du rejet pour chaque ligne invalide
def causes_rejet(row, masks):
    causes = [nom for nom, mask in masks.items() if not mask.loc[row.name]]
    return ", ".join(causes)


if len(invalid) > 0:
    invalid["cause_rejet"] = invalid.apply(lambda row: causes_rejet(row, masks), axis=1)
else:
    invalid["cause_rejet"] = pd.Series(dtype="object")

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
accepted_path = CURATED_DIR / f"resistance_curated_{stamp}.csv"
rejected_path = REJECTED_DIR / f"resistance_rejected_{stamp}.csv"
out_of_scope_path = OUT_OF_SCOPE_DIR / f"resistance_out_of_scope_{stamp}.csv"

accepted.to_csv(accepted_path, index=False)
invalid.to_csv(rejected_path, index=False)
out_of_scope.to_csv(out_of_scope_path, index=False)

print(f"\nFichier curated ecrit : {accepted_path} ({len(accepted)} lignes)")
print(f"Fichier rejected ecrit : {rejected_path} ({len(invalid)} lignes)")
print(f"Fichier hors perimetre ecrit : {out_of_scope_path} ({len(out_of_scope)} lignes)")

# fichier curated consolide, deduplique sur la cle primaire (idempotence)
CONSOLIDATED_PATH = CURATED_DIR / "resistance_curated_consolidated.csv"
CLE_PRIMAIRE = ["Year", "Country", "Pathogen", "Antibiotic", "patientType"]

if CONSOLIDATED_PATH.exists():
    existing = pd.read_csv(CONSOLIDATED_PATH)
    combined = pd.concat([existing, accepted], ignore_index=True)
else:
    combined = accepted

rows_before_dedup = len(combined)
combined = combined.drop_duplicates(subset=CLE_PRIMAIRE, keep="last")
duplicates_removed = rows_before_dedup - len(combined)
combined.to_csv(CONSOLIDATED_PATH, index=False)

print(f"\nFichier consolide (deduplique) : {CONSOLIDATED_PATH} ({len(combined)} lignes)")

# rapport d'execution : le statut ne depend que des lignes INVALIDES
if len(accepted) == 0:
    quality_status = "FAIL"
elif len(invalid) > 0:
    quality_status = "PASS_WITH_WARNINGS"
else:
    quality_status = "PASS"

report = {
    "pipeline": "AntibioSentinelle",
    "executed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "source_file": raw_file.name,
    "input_rows": int(len(df)),
    "accepted_rows": int(len(accepted)),
    "invalid_rows": int(len(invalid)),
    "out_of_scope_rows": int(len(out_of_scope)),
    "duplicates_removed": int(duplicates_removed),
    "rule_failures": {nom: int((~mask).sum()) for nom, mask in masks.items()},
    "quality_status": quality_status,
    "duration_seconds": round(time.perf_counter() - start, 2),
}

report_path = REPORTS_DIR / "run_report.json"
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nRapport ecrit : {report_path}")