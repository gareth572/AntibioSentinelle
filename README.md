# AntibioSentinelle

Suivi de l'antibiorésistance en Europe : croiser, par pays et par
bactérie/antibiotique, le taux de résistance bactérienne avec le niveau de
consommation d'antibiotiques (données ECDC/EARS-Net, 1998-2019).


## Statut

Séances 1 et 2 terminées : cadrage, collecte (3 tentatives), validation,
séparation accepté/rejeté, transformation vers un curated typé (contrat 1.1),
idempotence et rapport d'exécution. Voir `docs/cadrage.md` pour le détail du
cadrage et le journal des décisions révisées.

Non réalisé : source B (consommation d'antibiotiques) et jointure, voir
« Limites connues ».

## Installation

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Exécution

Pipeline complet (collecte, validation, transformation) :

```
python src\pipeline.py
```

Ou étape par étape :

```
python src\collect.py
python src\validate.py
python src\transform.py
```

- `collect.py` récupère une copie brute et horodatée de
  `summary_AMR_filtered.csv` (ECDC/TESSy via Zenodo,
  DOI 10.5281/zenodo.14224680) dans `data/raw/`. En cas d'échec, il réessaie
  3 fois (attente de 5 s, 10 s puis 15 s) avant d'abandonner.
- `validate.py` applique les règles de qualité sur le fichier brut, écrit les
  lignes valides et les lignes écartées, puis génère `reports/run_report.json`.
- `transform.py` renomme et type les colonnes, contrôle la cohérence
  (`n_resistant / n_tested = resistance_rate`) et publie le jeu final.

Résultat à utiliser : `data/curated/resistance_curated_final.csv`, conforme à
`config/data_contract.yaml` (version 1.1). Les autres fichiers de
`data/curated/` sont des étapes intermédiaires.

Si la collecte échoue, le pipeline s'arrête et `validate.py` n'est pas lancé.

Si le contrôle de cohérence échoue, rien n'est publié.

## Règles de qualité

Appliquées par `validate.py` sur le fichier brut :

| Règle | Condition | Action | Échecs (dernière exécution) |
|---|---|---|---|
| completude | Country, Pathogen et Antibiotic renseignés | Rejeter | 0 |
| annee_valide | Year entre 1998 et 2019 | Rejeter | 0 |
| taux_valide | p (taux de résistance) entre 0 et 1 | Rejeter | 0 |
| echantillon_suffisant | N (souches testées) supérieur ou égal à 30 | Rejeter | 0 |
| pays_dans_perimetre | Pays parmi les 15 retenus après profilage | Écarter | 2451 |

Appliquée par `transform.py` sur les lignes validées :

| Règle | Condition | Action | Échecs (dernière exécution) |
|---|---|---|---|
| coherence | `n_resistant` entre 0 et `n_tested`, et `n_resistant / n_tested` égal à `resistance_rate` (tolérance 1e-6) | Arrêter la publication | 0 |

Les lignes écartées sont conservées dans `data/rejected/` avec une colonne
`cause_rejet`. Note : la règle `pays_dans_perimetre` est un filtre de
périmètre, pas un défaut de qualité. Aujourd'hui, ces lignes valides sont
comptées avec les rejets, et le rapport affiche `PASS_WITH_WARNINGS` à cause
d'elles. La séparation est prévue (voir « Limites connues »).

Idempotence : `transform.py` met à jour
`data/curated/resistance_curated_final.csv` par UPSERT sur la clé
(year, country, pathogen, antibiotic, patient_type). Relancer le pipeline ne
crée aucun doublon.

## Limites connues

- Seule la source de résistance est traitée. Le fichier de consommation
  (`summary_AMC_byclass.csv`) et la jointure sur (pays, année) ne sont pas
  implémentés : le croisement résistance / consommation de la question
  centrale reste à faire, et les KPI 2 et 3 ne sont donc pas calculables.
- Le KPI 1 (taux pondéré) est défini dans `docs/cadrage.md` mais n'est pas
  encore calculé : il n'y a pas de couche de restitution.
- Les lignes hors périmètre pays (2 451) sont comptées avec les rejets, et
  le rapport affiche `PASS_WITH_WARNINGS` alors qu'aucune ligne n'est
  invalide.
- `resistance_curated_consolidated.csv` (colonnes brutes) fait doublon avec
  `resistance_curated_final.csv`. Seul le second respecte le contrat.
- Le contrat `config/data_contract.yaml` décrit les règles mais n'est pas
  lu par le code : il peut diverger des scripts.
- Les règles `completude`, `annee_valide`, `taux_valide` et
  `echantillon_suffisant` ne rejettent aucune ligne sur ce fichier, déjà
  nettoyé par le producteur.
- Les intervalles de confiance (`p_min`, `p_max`) ne sont pas conservés.
- La source est un instantané figé (1998-2019), sans mise à jour continue.
- Si les noms de colonnes du fichier source changent, la validation échoue.
- La collecte réessaie aussi sur les erreurs définitives (404), ce qui
  retarde inutilement l'échec.
- Les fichiers horodatés de `data/raw/`, `curated/` et `rejected/`
  s'accumulent en local (ignorés par Git).
- Le dossier `tests/` est vide : aucun test automatisé.

## Arborescence

```
AntibioSentinelle/
  README.md
  requirements.txt
  .gitignore
  config/
    data_contract.yaml        contrat de donnees v1.1
  data/
    raw/                      copies brutes horodatees
    curated/                  valides (horodates), consolide, final
    rejected/                 lignes ecartees + cause_rejet
  docs/
    architecture.png
    cadrage.md                cadrage et journal des decisions
  reports/
    run_report.json
  src/
    collect.py
    profile.py
    validate.py
    transform.py
    pipeline.py
  tests/                      vide
```