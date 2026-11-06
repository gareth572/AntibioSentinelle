import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path("data/antibiosentinelle.db")
SCHEMA_PATH = Path("sql/schema.sql")
A_PATH = Path("data/curated/resistance_curated_final.csv")
B_PATH = Path("data/curated/consumption_curated_final.csv")

def creer_base() -> sqlite3.Connection:
    # schema.sql fait des CREATE TABLE sans IF NOT EXISTS : on repart d'une base vide
    DB_PATH.unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn

def charger_dimensions(conn, a, b) -> None:
    pays = sorted(set(a["country"].dropna()) | set(b["country"].dropna()))
    conn.executemany("INSERT OR IGNORE INTO pays (nom) VALUES (?)",
                     [(p,) for p in pays])

    bacteries = a[["pathogen", "pathogen_long"]].drop_duplicates("pathogen")
    conn.executemany("INSERT OR IGNORE INTO bacterie (code, nom_long) VALUES (?, ?)",
                     bacteries.itertuples(index=False, name=None))

    # classe : libelle connu cote consommation, code seul cote resistance
    libelles = (b[["antibiotic_class", "antibiotic_class_label"]]
                .drop_duplicates("antibiotic_class")
                .set_index("antibiotic_class")["antibiotic_class_label"])
    codes_classe = sorted(set(a["antibiotic_class"].dropna()) | set(b["antibiotic_class"].dropna()))
    conn.executemany("INSERT OR IGNORE INTO classe (code_atc, libelle) VALUES (?, ?)",
                     [(c, libelles.get(c)) for c in codes_classe])

    antibiotiques = a[["antibiotic", "antibiotic_long", "antibiotic_class"]].drop_duplicates("antibiotic")
    conn.executemany(
        """INSERT OR IGNORE INTO antibiotique (code, nom_long, id_classe)
           VALUES (?, ?, (SELECT id_classe FROM classe WHERE code_atc = ?))""",
        antibiotiques.itertuples(index=False, name=None))

    conn.executemany("INSERT OR IGNORE INTO secteur (nom) VALUES (?)",
                     [(s,) for s in sorted(b["sector"].dropna().unique())])

    conn.executemany("INSERT OR IGNORE INTO voie (nom) VALUES (?)",
                     [(v,) for v in sorted(b["administration_route"].dropna().unique())])

def charger_resistance(conn, a) -> None:
    colonnes = ["country", "pathogen", "antibiotic", "year",
                "n_tested", "n_resistant", "resistance_rate"]
    conn.executemany(
        """INSERT OR REPLACE INTO resultat_resistance
           (id_pays, id_bacterie, id_antibiotique, annee,
            n_tested, n_resistant, resistance_rate)
           VALUES (
             (SELECT id_pays FROM pays WHERE nom = ?),
             (SELECT id_bacterie FROM bacterie WHERE code = ?),
             (SELECT id_antibiotique FROM antibiotique WHERE code = ?),
             ?, ?, ?, ?)""",
        a[colonnes].itertuples(index=False, name=None),
    )


def charger_consommation(conn, b) -> None:
    colonnes = ["country", "antibiotic_class", "sector", "administration_route",
                "year", "ddd", "anomalie_valeur"]
    lignes = b[colonnes].copy()
    lignes["anomalie_valeur"] = lignes["anomalie_valeur"].astype(int)
    conn.executemany(
        """INSERT OR REPLACE INTO consommation
           (id_pays, id_classe, id_secteur, id_voie,
            annee, ddd, anomalie_valeur)
           VALUES (
             (SELECT id_pays FROM pays WHERE nom = ?),
             (SELECT id_classe FROM classe WHERE code_atc = ?),
             (SELECT id_secteur FROM secteur WHERE nom = ?),
             (SELECT id_voie FROM voie WHERE nom = ?),
             ?, ?, ?)""",
        lignes.itertuples(index=False, name=None),
    )

if __name__ == "__main__":
    a = pd.read_csv(A_PATH)
    b = pd.read_csv(B_PATH)
    conn = creer_base()
    charger_dimensions(conn, a, b)
    charger_resistance(conn, a)
    charger_consommation(conn, b)
    conn.commit()
    n_r = conn.execute("SELECT COUNT(*) FROM resultat_resistance").fetchone()[0]
    n_c = conn.execute("SELECT COUNT(*) FROM consommation").fetchone()[0]
    conn.close()
    print(f"Base chargee : {n_r} resultats de resistance, {n_c} lignes de consommation.")
