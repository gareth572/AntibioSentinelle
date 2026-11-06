import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("data/antibiosentinelle.db")

def main(fichier: str, nb_lignes: int = 10) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    texte = Path(fichier).read_text(encoding="utf-8")
    requetes = [q.strip() for q in texte.split(";") if q.strip()]
    for i, requete in enumerate(requetes, start=1):
        print(f"\n=== Requete {i} ===")
        cur = conn.execute(requete)
        print([c[0] for c in cur.description])
        for ligne in cur.fetchmany(nb_lignes):
            print(ligne)

if __name__ == "__main__":
    main(sys.argv[1])