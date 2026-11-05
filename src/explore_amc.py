from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
amc = pd.read_csv(sorted(RAW.glob("amc_consumption_*.csv"))[-1])
amr = pd.read_csv(sorted(RAW.glob("amr_resistance_*.csv"))[-1])

PAYS = [
    "France", "Netherlands", "Greece", "Hungary", "Spain", "Czech Republic",
    "Austria", "Belgium", "Germany", "Slovenia", "Italy", "Portugal",
    "Croatia", "Slovakia", "United Kingdom",
]
KEY = ["Country", "Year", "Sector", "Antimicrobial.Type", "class"]

print("--- 1. Cle candidate unique ? ---")
dups = amc.duplicated(subset=KEY, keep=False)
print(f"lignes en doublon sur {KEY} : {dups.sum()}")
if dups.any():
    print(amc[dups].sort_values(KEY).head(10).to_string())

print("\n--- 2. DDD negatives ---")
neg = amc[amc["DDD"] < 0]
print(f"nombre : {len(neg)}")
print(neg.sort_values("DDD").head(10).to_string())

print("\n--- 3. Plus grandes valeurs de DDD ---")
print(amc.nlargest(8, "DDD").to_string())

print("\n--- 4. 'All' = somme des autres voies ? ---")
is_all = amc["Antimicrobial.Type"].eq("All")
grp = ["Country", "Year", "Sector", "class"]
tot = amc[is_all].groupby(grp)["DDD"].sum().rename("all_ddd")
oth = amc[~is_all].groupby(grp)["DDD"].sum().rename("others_ddd")
print(f"groupes avec All seulement : {len(tot.index.difference(oth.index))}")
print(f"groupes sans All : {len(oth.index.difference(tot.index))}")
cmp = pd.concat([tot, oth], axis=1).dropna()
cmp["ecart"] = (cmp["all_ddd"] - cmp["others_ddd"]).abs()
print(f"groupes comparables : {len(cmp)}, ecart > 0.01 : {(cmp['ecart'] > 0.01).sum()}")
print(cmp.sort_values("ecart", ascending=False).head(5).to_string())

print("\n--- 5. 'Total Care' = Community + Hospital ? ---")
p = amc.pivot_table(
    index=["Country", "Year", "class", "Antimicrobial.Type"],
    columns="Sector", values="DDD", aggfunc="sum",
).dropna(subset=["Total Care", "Community", "Hospital Sector"])
p["ecart"] = (p["Total Care"] - p["Community"] - p["Hospital Sector"]).abs()
print(f"groupes comparables : {len(p)}, ecart > 0.01 : {(p['ecart'] > 0.01).sum()}")
print(p.sort_values("ecart", ascending=False).head(5).to_string())

print("\n--- 6. Couverture des 15 pays ---")
print(amc[amc["Country"].isin(PAYS)].groupby("Country")["Year"].agg(["min", "max", "nunique"]))

print("\n--- 7. Classes : A contre B ---")
a_cls, b_cls = set(amr["Antibiotic_class"]), set(amc["Antibiotic_class"])
print("dans A, absentes de B :", sorted(a_cls - b_cls))
print("dans B, absentes de A :", sorted(b_cls - a_cls))

print("\n--- 8. Pays : A contre B ---")
print("dans A, absents de B :", sorted(set(amr["Country"]) - set(amc["Country"])))
print("dans B, absents de A :", sorted(set(amc["Country"]) - set(amr["Country"])))