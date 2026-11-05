# AntibioSentinelle

Suivi de l'antibiorésistance en Europe : croiser, par pays et par
bactérie/antibiotique, le taux de résistance bactérienne avec le niveau de
consommation d'antibiotiques (données ECDC/EARS-Net, 1998-2019).

## Statut

Séances 1 et 2 terminées pour les deux sources : cadrage, collecte (3
tentatives), validation, séparation acceptées / invalides / hors périmètre,
transformation vers un curated typé, idempotence et rapports d'exécution.
Source A (résistance) : contrat 1.1. Source B (consommation) : contrat 1.0.

Non réalisé : la jointure des deux sources et le calcul des KPI. Voir
« Limites connues » et `docs/cadrage.md`.

## Installation

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Exécution

Pipeline complet (six étapes) :

```
python src\pipeline.py
```

Ou étape par étape :

```
python src\collect.py
python src\collect.py amc
python src\validate.py
python src\transform.py
python src\validate_amc.py
python src\transform_amc.py
```

- `collect.py` récupère une copie brute et horodatée d'un fichier du dépôt
  Zenodo (DOI 10.5281/zenodo.14224680) dans `data/raw/` : `summary_AMR_filtered.csv`
  par défaut, `summary_AMC_byclass.csv` avec l'argument `amc`. En cas d'échec, il
  réessaie 3 fois (attente de 5 s, 10 s puis 15 s) avant d'abandonner.
- `validate.py` et `validate_amc.py` appliquent les règles de qualité sur le
  fichier brut et répartissent les lignes en trois groupes : acceptées
  (`data/curated/`), invalides (`data/rejected/`) et hors périmètre
  (`data/out_of_scope/`). Chacun génère un rapport dans `reports/`.
- `transform.py` et `transform_amc.py` renomment et typent les colonnes,
  contrôlent la cohérence et publient le jeu final.

Résultats à utiliser :
- `data/curated/resistance_curated_final.csv` (contrat `config/data_contract.yaml`, v1.1) ;
- `data/curated/consumption_curated_final.csv` (contrat `config/data_contract_consumption.yaml`, v1.0).

Les autres fichiers de `data/curated/` sont des étapes intermédiaires.

Si la collecte échoue, le pipeline s'arrête et rien d'autre n'est lancé. Si un
contrôle de cohérence échoue, rien n'est publié pour la source concernée.

## Source et licence

- Producteur : ECDC (European Centre for Disease Prevention and Control),
  via TESSy, compilé par Emons, Blanquart & Lehtinen (2024)
- URL : https://zenodo.org/records/14224680 (deux fichiers : résistance et
  consommation)
- Licence : Zenodo Open Access, à citer via le DOI
- Date d'accès : 24/09/2026 (dernière collecte : 05/11/2026)
- Aucune donnée personnelle : agrégation au niveau pays/année

## Règles de qualité

### Source A (résistance)

Appliquées par `validate.py` sur le fichier brut. Une ligne qui échoue à une
règle est **invalide** :

| Règle | Condition | Action | Échecs (dernière exécution) |
|---|---|---|---|
| completude | Country, Pathogen et Antibiotic renseignés | Rejeter | 0 |
| annee_valide | Year entre 1998 et 2019 | Rejeter | 0 |
| taux_valide | p (part de souches résistantes ou intermédiaires) entre 0 et 1 | Rejeter | 0 |
| echantillon_suffisant | N (souches testées) supérieur ou égal à 30 | Rejeter | 0 |

Contrôle de `transform.py` : `n_resistant` entre 0 et `n_tested`, et
`n_resistant / n_tested` égal à `resistance_rate` (tolérance 1e-6). En cas
d'échec, la publication s'arrête (0 échec).

### Source B (consommation)

Appliquées par `validate_amc.py` sur le fichier brut :

| Règle | Condition | Action | Échecs (dernière exécution) |
|---|---|---|---|
| completude | pays, année, secteur, voie, classe et DDD renseignés | Rejeter | 0 |
| annee_valide | Year entre 1997 et 2016 | Rejeter | 0 |
| secteur_connu | Community, Hospital Sector ou Total Care | Rejeter | 0 |
| voie_connue | l'une des 7 voies observées | Rejeter | 0 |
| ddd_positif | DDD supérieur ou égal à 0 | Rejeter | 2 |
| cle_unique | clé (pays, année, secteur, voie, classe) non dupliquée | Rejeter | 0 |

Contrôle de `transform_amc.py` : le code de classe du libellé doit égaler
`antibiotic_class` (0 désaccord). Signalement, sans rejet : `anomalie_valeur`
marque une valeur de plus de 5 fois la médiane de sa série (série d'au moins
5 points, médiane d'au moins 0,5). Dernière exécution : 6 valeurs, toutes
Italie 2007.

### Filtre de périmètre et idempotence

Le filtre de périmètre n'est pas une règle de qualité : seules les lignes des
15 pays retenus sont acceptées. Les autres, valides, sont écrites dans
`data/out_of_scope/` (2 451 lignes pour A et 7 053 pour B à la dernière
exécution). Les lignes invalides sont conservées dans `data/rejected/` avec une
colonne `cause_rejet`. Le statut de chaque rapport (`PASS`,
`PASS_WITH_WARNINGS`, `FAIL`) ne dépend que des lignes invalides.

Idempotence : chaque `transform` met à jour son fichier final par UPSERT sur la
clé métier. Relancer le pipeline ne crée aucun doublon.

## Vérification des rejets

Source B : les deux `DDD` négatives du fichier réel (République tchèque 2012,
Royaume-Uni 2009) sont rejetées avec la cause `ddd_positif`.

Source A : `tests/make_invalid_copy.py` crée une copie du dernier fichier brut
avec trois lignes volontairement invalides (année 1850, taux 1,5, N = 12).
Après `python src\validate.py`, ces trois lignes doivent apparaître dans
`data/rejected/` avec la bonne `cause_rejet`. La copie doit ensuite être
supprimée (`data/raw/amr_resistance_29991231T235959Z.csv`), sinon `validate.py`
la prendra toujours comme fichier le plus récent.

## Limites connues

- **La jointure et les KPI ne sont pas réalisés.** Les deux curated existent
  séparément ; le croisement résistance / consommation de la question
  centrale reste à faire.
- **Résistance hospitalière contre consommation en ville.** La résistance (A)
  vient uniquement de patients hospitalisés (`INPAT`). Les KPI de consommation
  retenus portent sur le secteur `Community`, seul présent dans les 15 pays.
  Le croisement est donc descriptif, pas une preuve d'effet.
- **Voie `All` non documentée.** Le producteur n'explique pas son sens ; elle
  n'est pas un total des autres voies. La règle prévue (ne pas additionner
  `All` et les voies, exclure les groupes ambigus des KPI) n'est appliquée par
  aucun code. Le secteur `Total Care` n'est pas non plus documenté.
- **Secteur hospitalier incomplet.** Absent pour l'Autriche, la Tchéquie,
  l'Allemagne et l'Espagne, et intermittent ailleurs.
- **Style de déclaration variable.** Avant 2010 environ, plusieurs pays
  déclarent un total (`All`), puis le détail par voie. Le test réalisé n'a pas
  montré de rupture, mais il ne porte que sur 11 transitions.
- **Règle `anomalie_valeur`** : elle ne voit ni les séries courtes ni les
  classes de faible consommation. L'hôpital italien de 2007 n'est pas signalé
  (non vérifié).
- Le champ `n_resistant` compte les souches intermédiaires et résistantes
  (colonne source `N_I_R`) : son nom est trompeur, renommage en attente.
- L'unité du DDD (par 1 000 habitants) est confirmée par la page Zenodo ; la
  période de la consommation (1997-2016) ne l'est pas.
- `resistance_curated_consolidated.csv` (colonnes brutes) fait doublon avec
  `resistance_curated_final.csv`. Seul le second respecte le contrat.
- Les contrats décrivent les règles mais ne sont lus par aucun code : ils
  peuvent diverger des scripts.
- La mise à jour par clé ne retire jamais une ligne qui disparaîtrait de la
  source ou deviendrait invalide plus tard.
- Les règles de qualité de A ne rejettent aucune ligne sur le fichier réel,
  déjà nettoyé par le producteur ; leur fonctionnement n'est vérifié que par
  la copie piégée.
- Les intervalles de confiance (`p_min`, `p_max`) ne sont pas conservés.
- Les sources sont des instantanés figés, sans mise à jour continue.
- Si les noms de colonnes d'un fichier source changent, la validation échoue.
- La collecte réessaie aussi sur les erreurs définitives (404).
- Les fichiers horodatés de `data/raw/`, `curated/`, `rejected/` et
  `out_of_scope/` s'accumulent en local (ignorés par Git).
- Aucun test automatisé avec assertions : `tests/` contient seulement
  `make_invalid_copy.py`, qui prépare un test manuel pour la source A.

## Arborescence

```
AntibioSentinelle/
  README.md
  requirements.txt
  .gitignore
  config/
    data_contract.yaml              contrat A (resistance) v1.1
    data_contract_consumption.yaml  contrat B (consommation) v1.0
  data/
    raw/                      copies brutes horodatees
    curated/                  valides (horodates), consolide A, finals A et B
    rejected/                 lignes invalides + cause_rejet
    out_of_scope/             lignes valides hors des 15 pays retenus
  docs/
    architecture.png
    cadrage.md                cadrage et journal des decisions
  reports/
    run_report.json           rapport source A
    run_report_amc.json       rapport source B
  src/
    collect.py
    validate.py
    transform.py
    validate_amc.py
    transform_amc.py
    pipeline.py
    profile.py                profilage source A
    profile_amc.py            profilage source B
    explore_amc*.py           explorations de la source B
  tests/
    make_invalid_copy.py      prepare une copie de A avec 3 lignes invalides
```