# AntibioSentinelle

Suivi de l'antibiorésistance en Europe : croiser, par pays et par
bactérie/antibiotique, le taux de résistance bactérienne avec le niveau de
consommation d'antibiotiques (données ECDC/EARS-Net, 1998-2019).


## Statut

Séances 1 et 2 terminées : cadrage, collecte, validation, séparation
accepté/rejeté, idempotence et rapport d'exécution. Voir `docs/cadrage.md`
pour le détail du cadrage.

Source B (consommation d'antibiotiques) et jointure : non réalisées, « voir Limites connues ».

## Installation

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Exécution

Pipeline complet (collecte, puis validation) :

```
python src\pipeline.py
```

Ou étape par étape :

```
python src\collect.py
python src\validate.py
```

- `collect.py` récupère une copie brute et horodatée de
  `summary_AMR_filtered.csv` (ECDC/TESSy via Zenodo,
  DOI 10.5281/zenodo.14224680) dans `data/raw/`.
- `validate.py` applique les règles de qualité, écrit les fichiers dans
  `data/curated/` et `data/rejected/`, puis génère `reports/run_report.json`.

Si la collecte échoue (source indisponible), le pipeline s'arrête et
`validate.py` n'est pas lancé.

## Source et licence

- Producteur : ECDC (European Centre for Disease Prevention and Control),
  via TESSy, compilé par Emons, Blanquart & Lehtinen (2024)
- URL : https://zenodo.org/records/14224680
- Licence : Zenodo Open Access — à citer via le DOI
- Date d'accès : 24/09/2026
- Aucune donnée personnelle : agrégation au niveau pays/année


## Règles de qualité

| Règle | Condition | Action | Échecs (dernière exécution) |
|---|---|---|---|
| completude | Country, Pathogen et Antibiotic renseignés | Rejeter | 0 |
| annee_valide | Year entre 1998 et 2019 | Rejeter | 0 |
| taux_valide | p (taux de résistance) entre 0 et 1 | Rejeter | 0 |
| echantillon_suffisant | N (souches testées) supérieur ou égal à 30 | Rejeter | 0 |
| pays_dans_perimetre | Pays parmi les 15 retenus après profilage | Rejeter | 2451 |

Les lignes rejetées ne sont pas supprimées : elles sont écrites dans
`data/rejected/` avec une colonne `cause_rejet`.

Idempotence : le fichier `data/curated/resistance_curated_consolidated.csv`
est dédupliqué sur la clé (Year, Country, Pathogen, Antibiotic, patientType).
Relancer le pipeline ne crée donc aucun doublon.

## Limites connues

- Seule la source de résistance est traitée. Le fichier de consommation
  (`summary_AMC_byclass.csv`) et la jointure sur (pays, année) ne sont pas
  implémentés : le croisement résistance / consommation de la question
  centrale reste donc à faire.
- Les règles completude, annee_valide, taux_valide et echantillon_suffisant
  ne rejettent aucune ligne sur ce fichier, déjà nettoyé par le producteur.
  Seul le périmètre pays filtre des données.
- Les colonnes d'intervalle de confiance (p_min, p_max) ne sont pas conservées
  dans le jeu curated.
- La source est un instantané figé (1998-2019), sans mise à jour continue.
- Si les noms de colonnes du fichier source changent, la validation échoue.
- Les fichiers curated et rejected horodatés s'accumulent en local
  (ignorés par Git) ; seul le fichier consolidé est versionné.

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
    run_report.json
  src/
    collect.py
    profile.py
    validate.py
    pipeline.py
  tests/
```