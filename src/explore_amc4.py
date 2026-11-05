from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
amc = pd.read_csv(sorted(RAW.glob("amc_consumption_*.csv"))[-1])

PAYS = [
    "France", "Netherlands", "Greece", "Hungary", "Spain", "Czech Republic",
    "Austria", "Belgium", "Germany", "Slovenia", "Italy", "Portugal",
    "Croatia", "Slovakia", "United Kingdom",
]
d = amc[amc["Country"].isin(PAYS) & amc["Year"].between(1999, 2016)].copy()
d["is_all"] = d["Antimicrobial.Type"].eq("All")

key = ["Country", "Year", "Sector", "class"]
all_ddd = d[d["is_all"]].groupby(key)["DDD"].sum().rename("all_ddd")
routes = d[~d["is_all"]].groupby(key)["DDD"].sum().rename("routes_ddd")
g = pd.concat([all_ddd, routes], axis=1).reset_index()
g["style"] = "les deux"
g.loc[g["all_ddd"].isna(), "style"] = "voies"
g.loc[g["routes_ddd"].isna(), "style"] = "all"

print("--- 1. Groupes ambigus : All > 0 ET voies > 0 ---")
amb = g[(g["style"] == "les deux") & (g["all_ddd"] > 0) & (g["routes_ddd"] > 0)].copy()
print(f"{len(amb)} groupes ambigus sur {len(g)} ({len(amb) / len(g):.1%})")
print(amb.groupby("Country").size().to_string())

print("\n--- 2. Rapport All / somme des voies dans ces groupes ---")
print((amb["all_ddd"] / amb["routes_ddd"]).describe().round(2).to_string())

print("\n--- 3. Style de declaration par pays et par annee ---")
print("A = All seulement, V = voies seulement, M = melange")
def lab(s):
    u = set(s)
    if len(u) > 1 or "les deux" in u:
        return "M"
    return "A" if u == {"all"} else "V"
tab = g.groupby(["Country", "Year"])["style"].agg(lab).unstack("Year")
print(tab.fillna("-").to_string())
