from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
amc = pd.read_csv(sorted(RAW.glob("amc_consumption_*.csv"))[-1])
amc["is_all"] = amc["Antimicrobial.Type"].eq("All")

print("--- 1. 'All' et voies d'administration (pays, annee, secteur, classe) ---")
key = ["Country", "Year", "Sector", "class"]
all_rows = amc[amc["is_all"]].groupby(key)["DDD"].sum().rename("all_ddd")
route_rows = amc[~amc["is_all"]].groupby(key)["DDD"].sum().rename("routes_ddd")
both = pd.concat([all_rows, route_rows], axis=1)
both["cas"] = "les deux"
both.loc[both["all_ddd"].isna(), "cas"] = "voies seulement"
both.loc[both["routes_ddd"].isna(), "cas"] = "All seulement"
print(both["cas"].value_counts().to_string())

mix = both[both["cas"] == "les deux"]
print(f"\nGroupes 'les deux' : All = 0 dans {(mix['all_ddd'] == 0).sum()} cas sur {len(mix)}")
print(mix[mix["all_ddd"] > 0].head(10).to_string())

only_all = both[both["cas"] == "All seulement"]
print(f"\nGroupes 'All seulement' : DDD = 0 dans {(only_all['all_ddd'] == 0).sum()} cas sur {len(only_all)}")
print(only_all["all_ddd"].describe().to_string())

print("\n--- 2. Secteurs presents ensemble (pays, annee, classe) ---")
sect = amc.groupby(["Country", "Year", "class"])["Sector"].agg(lambda s: " + ".join(sorted(set(s))))
print(sect.value_counts().to_string())
print("\nPays ayant des lignes 'Total Care' :")
print(amc[amc["Sector"] == "Total Care"].groupby("Country").size().to_string())

print("\n--- 3. Italie ---")
it = amc[amc["Country"] == "Italy"].groupby(["Year", "Sector"])["DDD"].sum().unstack()
print(it.round(2).to_string())
it_c = amc[
    (amc["Country"] == "Italy") & (amc["class"] == "J01C Penicillins")
    & (amc["Sector"] == "Community") & (amc["Antimicrobial.Type"] == "Oral")
]
print("\nItalie, J01C, Community, Oral :")
print(it_c.sort_values("Year")[["Year", "DDD"]].to_string(index=False))

print("\n--- 4. Voisinage des deux DDD negatives ---")
cas = [("Czech Republic", 2012, "J01C Penicillins"), ("United Kingdom", 2009, "J01G Aminoglycosides")]
for country, year, cls in cas:
    sub = amc[
        (amc["Country"] == country) & (amc["class"] == cls)
        & (amc["Sector"] == "Community") & (amc["Antimicrobial.Type"] == "Parenteral")
        & (amc["Year"].between(year - 2, year + 2))
    ]
    print(f"\n{country}, {cls} :")
    print(sub[["Year", "DDD"]].sort_values("Year").to_string(index=False))