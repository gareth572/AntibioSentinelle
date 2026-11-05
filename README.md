# AntibioSentinelle

Suivi de l'antibiorésistance en Europe : croiser, par pays et par
bactérie/antibiotique, le taux de résistance bactérienne avec le niveau de
consommation d'antibiotiques (données ECDC/EARS-Net, 1998-2019).

## Statut

Séances 1 et 2 terminées : cadrage, collecte (3 tentatives), validation,
séparation acceptées / invalides / hors périmètre, transformation vers un
curated typé (contrat 1.1), idempotence et rapport d'exécution. Voir
`docs/cadrage.md` pour le détail du cadrage et le journal des décisions
révisées.

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
- `validate.py` applique les règles de qualité sur le fichier brut et répartit
  les lignes en trois groupes : acceptées (`data/curated/`), invalides
  (`data/rejected/`) et hors périmètre (`data/out_of_scope/`). Il génère aussi
  `reports/run_report.json`.
- `transform.py` renomme et type les colonnes, contrôle la cohérence
  (`n_resistant / n_tested = resistance_rate`) et publie le jeu final.

Résultat à utiliser : `data/curated/resistance_curated_final.csv`, conforme à
`config/data_contract.yaml` (version 1.1). Les autres fichiers de
`data/curated/` sont des étapes intermédiaires.

Si la collecte échoue, le pipeline s'arrête et `validate.py` n'est pas lancé.

Si le contrôle de cohérence échoue, rien n'est publié.

## Source et licence

- Producteur : ECDC (European Centre for Disease Prevention and Control),
  via TESSy, compilé par Emons, Blanquart & Lehtinen (2024)
- URL : https://zenodo.org/records/14224680
- Licence : Zenodo Open Access, à citer via le DOI
- Date d'accès : 24/09/2026 (dernière collecte : 05/11/2026)
- Aucune donnée personnelle : agrégation au niveau pays/année

## Règles de qualité

Appliquées par `validate.py` sur le fichier brut. Une ligne qui échoue à une
règle est **invalide** :

| Règle | Condition | Action | Échecs (dernière exécution) |
|---|---|---|---|
| completude | Country, Pathogen et Antibiotic renseignés | Rejeter | 0 |
| annee_valide | Year entre 1998 et 2019 | Rejeter | 0 |
| taux_valide | p (taux de résistance) entre 0 et 1 | Rejeter | 0 |
| echantillon_suffisant | N (souches testées) supérieur ou égal à 30 | Rejeter | 0 |

Filtre de périmètre (ce n'est pas une règle de qualité) : seules les lignes
des 15 pays retenus sont acceptées. Les autres, valides, sont écrites dans
`data/out_of_scope/` (2 451 lignes à la dernière exécution).

Appliquée par `transform.py` sur les lignes acceptées :

| Règle | Condition | Action | Échecs (dernière exécution) |
|---|---|---|---|
| coherence | `n_resistant` entre 0 et `n_tested`, et `n_resistant / n_tested` égal à `resistance_rate` (tolérance 1e-6) | Arrêter la publication | 0 |

Les lignes invalides sont conservées dans `data/rejected/` avec une colonne
`cause_rejet`. Le statut du rapport (`PASS`, `PASS_WITH_WARNINGS`, `FAIL`) ne
dépend que des lignes invalides.

Idempotence : `transform.py` met à jour
`data/curated/resistance_curated_final.csv` par UPSERT sur la clé
(year, country, pathogen, antibiotic, patient_type). Relancer le pipeline ne
crée aucun doublon.

## Vérification des rejets

`tests/make_invalid_copy.py` crée une copie du dernier fichier brut avec trois
lignes volontairement invalides (année 1850, taux 1,5, N = 12). Après
`python src\validate.py`, ces trois lignes doivent apparaître dans
`data/rejected/` avec la bonne `cause_rejet`. La copie doit ensuite être
supprimée (`data/raw/amr_resistance_29991231T235959Z.csv`), sinon `validate.py`
la prendra toujours comme fichier le plus récent.

## Limites connues

- Seule la source de résistance est traitée. Le fichier de consommation
  (`summary_AMC_byclass.csv`) et la jointure sur (pays, année) ne sont pas
  implémentés : le croisement résistance / consommation de la question
  centrale reste à faire, et les KPI 2 et 3 ne sont donc pas calculables.
- Le KPI 1 (taux pondéré) est défini dans `docs/cadrage.md` mais n'est pas
  encore calculé : il n'y a pas de couche de restitution.
- `resistance_curated_consolidated.csv` (colonnes brutes) fait doublon avec
  `resistance_curated_final.csv`. Seul le second respecte le contrat.
- Le contrat `config/data_contract.yaml` décrit les règles mais n'est pas
  lu par le code : il peut diverger des scripts.
- Les 4 règles de qualité ne rejettent aucune ligne sur le fichier réel,
  déjà nettoyé par le producteur. Leur fonctionnement est vérifié
  uniquement avec la copie piégée.
- Les intervalles de confiance (`p_min`, `p_max`) ne sont pas conservés.
- La source est un instantané figé (1998-2019), sans mise à jour continue.
- Si les noms de colonnes du fichier source changent, la validation échoue.
- La collecte réessaie aussi sur les erreurs définitives (404), ce qui
  retarde inutilement l'échec.
- Les fichiers horodatés de `data/raw/`, `curated/`, `rejected/` et
  `out_of_scope/` s'accumulent en local (ignorés par Git).
- Aucun test automatisé avec assertions : `tests/` contient seulement
  `make_invalid_copy.py`, qui prépare un test manuel.

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
    rejected/                 lignes invalides + cause_rejet
    out_of_scope/             lignes valides hors des 15 pays retenus
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
  tests/
    make_invalid_copy.py      prepare une copie avec 3 lignes invalides
```