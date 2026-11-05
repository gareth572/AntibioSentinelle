# validation de la source B (consommation) : meme logique que validate.py
from datetime import datetime, timezone
from pathlib import Path
import json
import time

import pandas as pd

start = time.perf_counter()

RAW_DIR = Path("data/raw")
CURATED_DIR = Path("data/curated")
REJECTED_DIR = Path("data/rejected")
OUT_OF_SCOPE_DIR = Path("data/out_of_scope")
REPORTS_DIR = Path("reports")
for d in (CURATED_DIR, REJECTED_DIR, OUT_OF_SCOPE_DIR, REPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)


def latest_raw_file() -> Path:
    files = sorted(RAW_DIR.glob("amc_consumption_*.csv"))
    if not files:
        raise FileNotFoundError("Aucun fichier amc trouve. Lancez : python src\\collect.py amc")
    return files[-1]


raw_file = latest_raw_file()
df = pd.read_csv(raw_file)
print(f"Fichier charge : {raw_file.name} ({len(df)} lignes)")

PAYS_RETENUS = [
    "France", "Netherlands", "Greece", "Hungary", "Spain", "Czech Republic",
    "Austria", "Belgium", "Germany", "Slovenia", "Italy", "Portugal",
    "Croatia", "Slovakia", "United Kingdom",
]
SECTEURS = ["Community", "Hospital Sector", "Total Care"]
VOIES = ["All", "Oral", "Parenteral", "Inhalation", "Rectal", "Other", "Implant"]
CLE = ["Country", "Year", "Sector", "Antimicrobial.Type", "Antibiotic_class"]


# ---- regles de QUALITE : un echec = ligne invalide ----

def regle_completude(df):
    cols = ["Country", "Year", "Sector", "Antimicrobial.Type", "Antibiotic_class", "DDD"]
    return df[cols].notna().all(axis=1)


def regle_annee_valide(df):
    return df["Year"].between(1997, 2016)


def regle_secteur_connu(df):
    return df["Sector"].isin(SECTEURS)


def regle_voie_connue(df):
    return df["Antimicrobial.Type"].isin(VOIES)


def regle_ddd_positif(df):
    # une consommation negative est impossible (NaN donne False)
    return df["DDD"] >= 0


def regle_cle_unique(df):
    # toutes les copies d'une cle dupliquee sont invalides : on ne sait pas laquelle est juste
    return ~df.duplicated(subset=CLE, keep=False)


# ---- filtre de PERIMETRE : un echec = ligne valide mais hors perimetre ----

def filtre_pays_dans_perimetre(df):
    return df["Country"].isin(PAYS_RETENUS)


rules = {
    "completude": regle_completude,
    "annee_valide": regle_annee_valide,
    "secteur_connu": regle_secteur_connu,
    "voie_connue": regle_voie_connue,
    "ddd_positif": regle_ddd_positif,
    "cle_unique": regle_cle_unique,
}

print("\n--- Resultat de chaque regle de qualite ---")
masks = {}
for nom, fonction in rules.items():
    mask = fonction(df)
    masks[nom] = mask
    print(f"{nom} : {(~mask).sum()} lignes en echec sur {len(df)}")

mask_valide = pd.Series(True, index=df.index)
for mask in masks.values():
    mask_valide = mask_valide & mask

mask_perimetre = filtre_pays_dans_perimetre(df)

# trois tas qui ne se chevauchent pas (invalide prioritaire)
invalid = df[~mask_valide].copy()
out_of_scope = df[mask_valide & ~mask_perimetre].copy()
accepted = df[mask_valide & mask_perimetre].copy()

print("\n--- Resultat final ---")
print(f"Lignes acceptees : {len(accepted)}")
print(f"Lignes invalides : {len(invalid)}")
print(f"Lignes hors perimetre : {len(out_of_scope)}")


def causes_rejet(row, masks):
    causes = [nom for nom, mask in masks.items() if not mask.loc[row.name]]
    return ", ".join(causes)


if len(invalid) > 0:
    invalid["cause_rejet"] = invalid.apply(lambda row: causes_rejet(row, masks), axis=1)
else:
    invalid["cause_rejet"] = pd.Series(dtype="object")

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
accepted_path = CURATED_DIR / f"consumption_curated_{stamp}.csv"
rejected_path = REJECTED_DIR / f"consumption_rejected_{stamp}.csv"
out_of_scope_path = OUT_OF_SCOPE_DIR / f"consumption_out_of_scope_{stamp}.csv"

accepted.to_csv(accepted_path, index=False)
invalid.to_csv(rejected_path, index=False)
out_of_scope.to_csv(out_of_scope_path, index=False)

print(f"\nFichier curated ecrit : {accepted_path} ({len(accepted)} lignes)")
print(f"Fichier rejected ecrit : {rejected_path} ({len(invalid)} lignes)")
print(f"Fichier hors perimetre ecrit : {out_of_scope_path} ({len(out_of_scope)} lignes)")

# rapport d'execution : le statut ne depend que des lignes INVALIDES
if len(accepted) == 0:
    quality_status = "FAIL"
elif len(invalid) > 0:
    quality_status = "PASS_WITH_WARNINGS"
else:
    quality_status = "PASS"

report = {
    "pipeline": "AntibioSentinelle-consumption",
    "executed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "source_file": raw_file.name,
    "input_rows": int(len(df)),
    "accepted_rows": int(len(accepted)),
    "invalid_rows": int(len(invalid)),
    "out_of_scope_rows": int(len(out_of_scope)),
    "rule_failures": {nom: int((~mask).sum()) for nom, mask in masks.items()},
    "quality_status": quality_status,
    "duration_seconds": round(time.perf_counter() - start, 2),
}

report_path = REPORTS_DIR / "run_report_amc.json"
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nRapport ecrit : {report_path}")