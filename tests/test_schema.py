import sqlite3
from pathlib import Path

SCHEMA = Path("sql/schema.sql").read_text(encoding="utf-8")


def new_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.execute("INSERT INTO pays(nom) VALUES ('France')")
    conn.execute("INSERT INTO bacterie(code, nom_long) VALUES ('ESCCOL', 'E. coli')")
    conn.execute("INSERT INTO classe(code_atc) VALUES ('J01M')")
    conn.execute("INSERT INTO antibiotique(code, nom_long, id_classe) VALUES ('CIP', 'Ciprofloxacin', 1)")
    conn.execute("INSERT INTO secteur(nom) VALUES ('Community')")
    conn.execute("INSERT INTO voie(nom) VALUES ('Oral')")
    return conn


RESULTAT = ("INSERT INTO resultat_resistance(id_pays, id_bacterie, id_antibiotique, "
            "annee, n_tested, n_resistant, resistance_rate) VALUES (?, ?, ?, ?, ?, ?, ?)")
CONSO = ("INSERT INTO consommation(id_pays, id_classe, id_secteur, id_voie, annee, ddd) "
         "VALUES (?, ?, ?, ?, ?, ?)")


def doit_echouer(nom, sql, params, conn=None):
    conn = conn or new_db()
    try:
        conn.execute(sql, params)
    except sqlite3.IntegrityError as exc:
        print(f"OK  refuse : {nom} ({exc})")
        return
    raise AssertionError(f"La base a accepte : {nom}")


# une ligne valide doit passer
conn = new_db()
conn.execute(RESULTAT, (1, 1, 1, 2015, 120, 24, 0.2))
conn.execute(CONSO, (1, 1, 1, 1, 2015, 3.5))
print("OK  ligne valide acceptee")

doit_echouer("annee 1850", RESULTAT, (1, 1, 1, 1850, 120, 24, 0.2))
doit_echouer("taux 1.5", RESULTAT, (1, 1, 1, 2015, 120, 24, 1.5))
doit_echouer("n_tested 12", RESULTAT, (1, 1, 1, 2015, 12, 2, 0.1667))
doit_echouer("n_resistant > n_tested", RESULTAT, (1, 1, 1, 2015, 120, 130, 0.5))
doit_echouer("taux incoherent", RESULTAT, (1, 1, 1, 2015, 120, 24, 0.5))
doit_echouer("pays inexistant", RESULTAT, (999, 1, 1, 2015, 120, 24, 0.2))
doit_echouer("ddd negatif", CONSO, (1, 1, 1, 1, 2015, -0.5))

doublon = new_db()
doublon.execute(RESULTAT, (1, 1, 1, 2015, 120, 24, 0.2))
doit_echouer("cle dupliquee", RESULTAT, (1, 1, 1, 2015, 120, 24, 0.2), doublon)

utilise = new_db()
utilise.execute(RESULTAT, (1, 1, 1, 2015, 120, 24, 0.2))
doit_echouer("suppression d'un pays utilise", "DELETE FROM pays WHERE id_pays = ?", (1,), utilise)

print("\nTous les tests sont passes.")