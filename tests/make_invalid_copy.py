from pathlib import Path

RAW_DIR = Path("data/raw")

# derniere vraie collecte
source = sorted(RAW_DIR.glob("amr_resistance_2026*.csv"))[-1]

# nom a horodatage lointain : validate.py prend toujours le dernier par ordre alphabetique
target = RAW_DIR / "amr_resistance_29991231T235959Z.csv"

content = source.read_text(encoding="utf-8")
if not content.endswith("\n"):
    content += "\n"

bad_lines = [
    # annee 1850 -> annee_valide
    '1850,"France","ESCCOL","CIP","INPAT",100,"1850|FR|ESCCOL|CIP|INPAT",NA,120,0.1,0.05,0.05,0.15,"Ciprofloxacin","J01M","E. coli","ESCCOL|France|CIP",20',
    # taux 1.5 -> taux_valide
    '2015,"France","ESCCOL","CIP","INPAT",100,"2015|FR|ESCCOL|CIP|INPAT",NA,120,1.5,0.05,1.45,1.55,"Ciprofloxacin","J01M","E. coli","ESCCOL|France|CIP",20',
    # N = 12 -> echantillon_suffisant
    '2015,"Germany","STAAUR","OXA","INPAT",5,"2015|DE|STAAUR|OXA|INPAT",NA,12,0.4,0.05,0.35,0.45,"Oxacillin","J01C","S. aureus","STAAUR|Germany|OXA",7',
]

target.write_text(content + "\n".join(bad_lines) + "\n", encoding="utf-8")
print(f"Copie piegee ecrite : {target}")