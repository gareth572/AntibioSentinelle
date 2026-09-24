# AntibioSentinelle

Suivi de l'antibiorésistance en Europe : croiser, par pays et par
bactérie/antibiotique, le taux de résistance bactérienne avec le niveau de
consommation d'antibiotiques (données ECDC/EARS-Net, 1998-2019).

## Statut

Cadrage (séance 1) terminé. Voir `docs/cadrage.md` pour le détail complet
(question, cas d'usage, sources, schéma, architecture, contrat de données).

Pipeline complet (collecte automatisée, validation, curated, rapport) à
construire en séance 2.

## Installation

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Exécution de la collecte


Récupère une copie brute et horodatée de `summary_AMR_filtered.csv`
(ECDC/TESSy via Zenodo, DOI 10.5281/zenodo.14224680) dans `data/raw/`.

## Source et licence

- Producteur : ECDC (European Centre for Disease Prevention and Control),
  via TESSy, compilé par Emons, Blanquart & Lehtinen (2024)
- URL : https://zenodo.org/records/14224680
- Licence : Zenodo Open Access — à citer via le DOI
- Date d'accès : 24/09/2026
- Aucune donnée personnelle : agrégation au niveau pays/année

## Arborescence

```
AntibioSentinelle/
  README.md
  requirements.txt
  .gitignore
  config/
    data_contract.yaml
  data/
    raw/
    curated/
    rejected/
  docs/
    architecture.png
    cadrage.md
  reports/
  src/
    collect.py
  tests/
```