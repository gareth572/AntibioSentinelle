from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
amc = pd.read_csv(sorted(RAW.glob("amc_consumption_*.csv"))[-1])

PAYS = [
    "France", "Netherlands", "Greece", "Hungary", "Spain", "Czech Republic",
    "Austria", "Belgium", "Germany", "Slovenia", "Italy", "Portugal",
    "Croatia", "Slovakia", "United Kingdom",
]
CLASSES = ["J01A", "J01C", "J01D", "J01F", "J01G", "J01M", "J01X"]

d = amc[
    amc["Country"].isin(PAYS)
    & amc["Year"].between(1999, 2016)
    & amc["Sector"].eq("Community")
    & amc["Antibiotic_class"].isin(CLASSES)
].copy()
d["is_all"] = d["Antimicrobial.Type"].eq("All")

key = ["Country", "Year", "Antibiotic_class"]
a = d[d["is_all"]].groupby(key)["DDD"].sum().rename("all_ddd")
r = d[~d["is_all"]].groupby(key)["DDD"].sum().rename("routes_ddd")
g = pd.concat([a, r], axis=1).reset_index()


def conso(row):
    all_ddd, routes = row["all_ddd"], row["routes_ddd"]
    if pd.isna(all_ddd):
        return routes
    if pd.isna(routes):
        return all_ddd
    if all_ddd == 0:
        return routes
    if routes == 0:
        return all_ddd
    return float("nan")  # ambigu


g["conso"] = g.apply(conso, axis=1)
g["kind"] = "mix"
g.loc[g["routes_ddd"].isna(), "kind"] = "all"
g.loc[g["all_ddd"].isna(), "kind"] = "voies"

t = g.groupby(["Country", "Year"]).agg(total=("conso", "sum"), n=("conso", "count"))
t.loc[t["n"] < len(CLASSES), "total"] = float("nan")
t["style"] = g.groupby(["Country", "Year"])["kind"].agg(
    lambda s: "A" if set(s) == {"all"} else ("V" if set(s) == {"voies"} else "M")
)

print("--- 1. Total Community (7 classes), par pays et annee ---")
print(t["total"].unstack("Year").round(1).to_string())

t = t.reset_index().sort_values(["Country", "Year"])
t["prev_total"] = t.groupby("Country")["total"].shift()
t["prev_year"] = t.groupby("Country")["Year"].shift()
t["prev_style"] = t.groupby("Country")["style"].shift()
t["ratio"] = t["total"] / t["prev_total"]
ok = t[(t["Year"] - t["prev_year"] == 1) & t["ratio"].notna()].copy()
ok["ecart"] = (ok["ratio"] - 1).abs()
ok["changement_style"] = ok["prev_style"] != ok["style"]

print("\n--- 2. Les 12 plus grands sauts d'une annee a la suivante ---")
cols = ["Country", "Year", "prev_style", "style", "prev_total", "total", "ratio"]
print(ok.nlargest(12, "ecart")[cols].round(2).to_string(index=False))

print("\n--- 3. Ecart typique : annees avec changement de style ou non ---")
print(ok.groupby("changement_style")["ecart"].describe().round(3).to_string())