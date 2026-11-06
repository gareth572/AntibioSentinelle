# AntibioSentinelle

Suivi de l'antibiorésistance en Europe : croiser, par pays et par
bactérie/antibiotique, le taux de résistance bactérienne avec le niveau de
consommation d'antibiotiques (données ECDC/EARS-Net, 1998-2019).

## Statut

Séances 1 et 2 terminées pour les deux sources : cadrage, collecte (3
tentatives), validation, séparation acceptées / invalides / hors périmètre,
transformation vers un curated typé, idempotence et rapports d'exécution.
Source A (résistance) : contrat 1.1. Source B (consommation) : contrat 1.0.

Base SQLite terminée : modèle (MCD, MLD), schéma avec contraintes, chargement
des deux sources, 11 requêtes commentées, index et plan d'exécution. Les trois
KPI sont calculés par des requêtes SQL, à la demande : le pipeline Python ne les
produit pas.

Voir « Limites connues » et `docs/cadrage.md`.

## Installation

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Exécution

Pipeline complet (sept étapes) :

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
python src\load_sqlite.py
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
- `load_sqlite.py` recrée `data/antibiosentinelle.db` à partir des deux jeux
  finaux (voir « Base SQLite et requêtes »).

Résultats à utiliser :
- `data/curated/resistance_curated_final.csv` (contrat `config/data_contract.yaml`, v1.1) ;
- `data/curated/consumption_curated_final.csv` (contrat `config/data_contract_consumption.yaml`, v1.0) ;
- `data/antibiosentinelle.db` (base SQLite, non versionnée, reconstruite à chaque exécution).

Les autres fichiers de `data/curated/` sont des étapes intermédiaires.

Si la collecte échoue, le pipeline s'arrête et rien d'autre n'est lancé.

Si un contrôle de cohérence échoue, rien n'est publié pour la source concernée.

## Source et licence

- Producteur : ECDC (European Centre for Disease Prevention and Control),
  via TESSy, compilé par Emons, Blanquart & Lehtinen (2024)
- URL : https://zenodo.org/records/14224680 (deux fichiers : résistance et
  consommation)
- Licence : Zenodo Open Access, à citer via le DOI
- Date d'accès : 24/09/2026 (dernière collecte : 06/11/2026)
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

## Base SQLite et requêtes

`load_sqlite.py` supprime puis recrée la base à chaque exécution : schéma
(`sql/schema.sql`), six dimensions (pays, bacterie, classe, antibiotique,
secteur, voie), puis les deux tables de mesures `resultat_resistance`
(9 425 lignes) et `consommation` (7 029 lignes). Les clés étrangères sont
activées ; le schéma impose clés primaires, clés étrangères, `UNIQUE` et
`CHECK`, avec les mêmes bornes que les règles de qualité.

Modèle : `docs/besoin_metier.md` (besoin, cardinalités, MLD) et
`docs/mcd.png`. Note performance, logs, sécurité et RGPD : `docs/note_sqlite.md`.

| Fichier | Rôle |
|---|---|
| `sql/schema.sql` | schéma complet, contraintes et index |
| `sql/seed.sql` | petit jeu de test fictif (pas de résultats réels) |
| `sql/queries.sql` | 11 requêtes commentées : KPI 1, 2 et 3, exploration, contrôles |
| `sql/controle.sql` | 3 contrôles de rapprochement des requêtes |
| `sql/explain.sql` | plan d'exécution avant et après l'index |

Exécuter les requêtes : `python src\run_sql.py sql\queries.sql`. Tester le
schéma : `python tests\test_schema.py` (1 ligne valide acceptée, 9 refusées).

### Règles de calcul des KPI (appliquées dans les requêtes)

- **KPI 1** : taux pondéré `somme(n_resistant) / somme(n_tested)`, jamais une
  moyenne de taux. Sur `ESCCOL` et `CIP`, la moyenne simple s'écarte du taux
  pondéré jusqu'à 6,5 points (Slovaquie : 0,4102 contre 0,3457).
- **KPI 2** : DDD du secteur `Community`, classes `J01*`. Par pays, année et
  classe : `All` seule, on prend `All` ; pas de `All`, on additionne les voies ;
  `All` avec d'autres voies, le groupe est exclu (150 groupes sur 2 714).
- **KPI 3** : jointure résistance / consommation sur pays, année et classe, après
  agrégation de chaque côté au même grain. Version par classe (1 133 lignes) et
  version ciblée, quinolones `J01M` et `ESCCOL` à `CIP` (199 lignes).

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

- **Les KPI ne sont pas produits par le pipeline.** Ils sont calculés à la demande
  par des requêtes SQL. La règle sur la voie `All` est recopiée dans trois
  requêtes (4, 5 et 6 de `sql/queries.sql`) : une modification doit être faite
  aux trois endroits.
- **Résistance hospitalière contre consommation en ville.** La résistance (A)
  vient uniquement de patients hospitalisés (`INPAT`). Les KPI de consommation
  retenus portent sur le secteur `Community`, seul présent dans les 15 pays.
  Le croisement est donc descriptif, pas une preuve d'effet.
- **Voie `All` : sens non documenté, et ce n'est pas un total.** Sur les 150
  groupes où `All` coexiste avec d'autres voies, `All` ne vaut la somme des autres
  voies (à 5 % près) que dans 7 cas ; elle est inférieure dans 100, supérieure
  dans 33, et la somme est nulle dans 10. Comparer un pays qui ne déclare que
  `All` à un pays qui déclare des voies séparées n'est donc pas garanti
  équivalent. Le secteur `Total Care` n'est pas documenté non plus.
- **Effet de composition au niveau de la classe.** Le taux d'une classe mélange
  les bactéries et les antibiotiques testés l'année donnée : si le panel change,
  le taux change sans que la résistance ait changé. Le croisement ciblé (une
  bactérie, un antibiotique) l'évite.
- **Couverture inégale.** France 2 417 153 souches testées (2001-2019),
  Allemagne 1 213 930 (1999-2019) ; certains pays commencent en 1999, d'autres
  en 2001, et un taux calculé sur toute la période n'a pas le même sens d'un
  pays à l'autre.
- **Valeur à vérifier** : Autriche, `ACISPP` et `CIP`, 0,0875 en 2018 puis 0,7297
  en 2019 (74 souches). Aucune règle de validation ne la détecte.
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
- La base SQLite est reconstruite à chaque exécution et dépend de Zenodo :
  aucune sauvegarde chiffrée, pas de journal d'audit des modifications.
- Les fichiers horodatés de `data/raw/`, `curated/`, `rejected/` et
  `out_of_scope/` s'accumulent en local (ignorés par Git).
- Tests : `tests/test_schema.py` vérifie les contraintes du schéma avec
  assertions. Les règles de validation de A ne sont testées que par
  `make_invalid_copy.py`, à lancer à la main.
- `docs/mcd.png` est une image générée par un script qui n'est pas versionné.

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
    antibiosentinelle.db      base SQLite (non versionnee)
  docs/
    architecture.png
    cadrage.md                cadrage et journal des decisions
    besoin_metier.md          besoin, cardinalites, MLD
    mcd.png                   modele conceptuel
    note_sqlite.md            performance, logs, securite, RGPD
  reports/
    run_report.json           rapport source A
    run_report_amc.json       rapport source B
  sql/
    schema.sql                schema, contraintes, index
    seed.sql                  jeu de test fictif
    queries.sql               11 requetes commentees
    controle.sql              controles de rapprochement
    explain.sql               plan d'execution
  src/
    collect.py
    validate.py
    transform.py
    validate_amc.py
    transform_amc.py
    load_sqlite.py            chargement dans SQLite
    run_sql.py                execute un fichier de requetes
    pipeline.py               sept etapes
    profile.py                profilage source A
    profile_amc.py            profilage source B
    explore_amc*.py           explorations de la source B
  tests/
    make_invalid_copy.py      prepare une copie de A avec 3 lignes invalides
    test_schema.py            test des contraintes du schema
```