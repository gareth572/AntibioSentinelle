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
amc15 = amc[amc["Country"].isin(PAYS) & amc["Year"].between(1999, 2016)].copy()
amc15["is_all"] = amc15["Antimicrobial.Type"].eq("All")

print("--- 1. All / voies, par pays (15 pays, 1999-2016) ---")
key = ["Country", "Year", "Sector", "class"]
all_rows = amc15[amc15["is_all"]].groupby(key)["DDD"].sum().rename("all_ddd")
route_rows = amc15[~amc15["is_all"]].groupby(key)["DDD"].sum().rename("routes_ddd")
both = pd.concat([all_rows, route_rows], axis=1).reset_index()
both["cas"] = "les deux"
both.loc[both["all_ddd"].isna(), "cas"] = "voies seulement"
both.loc[both["routes_ddd"].isna(), "cas"] = "All seulement"
print(pd.crosstab(both["Country"], both["cas"]).to_string())

print("\n--- 2. Secteurs presents (pays, annee, classe), par pays ---")
sect = (amc15.groupby(["Country", "Year", "class"])["Sector"]
        .agg(lambda s: " + ".join(sorted(set(s)))).reset_index())
print(pd.crosstab(sect["Country"], sect["Sector"]).to_string())

print("\n--- 3. Couverture des classes communes A / B ---")
common = sorted(set(amr["Antibiotic_class"]) & set(amc["Antibiotic_class"]))
print("classes communes :", common)
cov = (amc15[amc15["Antibiotic_class"].isin(common)]
       .drop_duplicates(["Country", "Year", "Antibiotic_class"])
       .groupby("Country").size())
print((cov.astype(str) + " / " + str(18 * len(common))).to_string())

print("\n--- 4. Valeurs tres superieures a la mediane de leur serie ---")
ser = ["Country", "class", "Sector", "Antimicrobial.Type"]
d = amc[amc["DDD"] > 0].copy()
d["med"] = d.groupby(ser)["DDD"].transform("median")
d["n"] = d.groupby(ser)["DDD"].transform("size")
d = d[(d["n"] >= 5) & (d["med"] >= 0.5)]
d["ratio"] = d["DDD"] / d["med"]
print(f"observations comparees (serie >= 5 points, mediane >= 0.5) : {len(d)}")
for seuil in (2, 3, 5):
    print(f"ratio > {seuil} : {(d['ratio'] > seuil).sum()}")
cols = ["Country", "Year", "class", "Sector", "Antimicrobial.Type", "DDD", "med", "ratio"]
print(d.nlargest(15, "ratio")[cols].round(2).to_string())