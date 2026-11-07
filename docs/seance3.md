# Séance 3 : dossier d'architecture (7 novembre 2026)

Projet : AntibioSentinelle. Ce dossier reprend le projet des séances 1 et 2 et décrit comment il évoluerait sous une nouvelle contrainte. Les valeurs viennent du projet réel (rapports d'exécution, code, mesure du 7 novembre).

## 1. Diagnostic, scénario et exigences

### 1.1 Diagnostic de l'existant (architecture actuelle, version 1)

| Élément | État actuel | Limite observée | Conséquence |
|---|---|---|---|
| Source | Deux CSV statiques publiés sur Zenodo (ECDC/TESSy) : résistance 1998-2019, consommation 1997-2016. Version unique, aucune mise à jour. | Pas de licence explicite sur la page. Le sens de la voie `All` n'est pas documenté. | La collecte est rejouable mais aucune fraîcheur n'est à gagner. Les règles de lecture sont écrites dans les contrats. |
| Collecteur | `collect.py` : URL configurable, 3 tentatives, fichier raw horodaté. | Dépend de la disponibilité de Zenodo (un `Read timed out` a eu lieu le 5 novembre). | Le pipeline s'arrête si les 3 tentatives échouent. Pas d'alerte automatique. |
| Zone raw | CSV bruts horodatés dans `data/raw/`, copie non modifiée de la source. | Pas de politique de rétention écrite. Le raw de la résistance est versionné dans un dépôt public. | Le rejeu est possible, mais les fichiers restent dans l'historique du dépôt. |
| Validation | `validate.py` et `validate_amc.py` : règles automatiques, trois sorties (acceptées, invalides, hors périmètre), rapport JSON. Statut : `FAIL` si aucune ligne n'est acceptée, `PASS_WITH_WARNINGS` s'il y a au moins une ligne invalide, sinon `PASS`. | Le statut ne dépend pas d'un taux de rejet et ne bloque pas lui-même le pipeline. Les anomalies de sens ne sont pas détectées (saut ACISPP de l'Autriche en 2019). La règle sur `All` est écrite dans trois requêtes SQL. | Des KPI peuvent rester trompeurs. C'est signalé dans les contrats. |
| Zone curated | Fichiers `*_final.csv` typés et base SQLite (8 tables) reconstruite à chaque exécution. Pour la résistance, `resistance_curated_consolidated.csv` accumule les lignes acceptées et sert à dédupliquer entre exécutions. | À chaque relance, le rapport A affiche `duplicates_removed` = 9 425 : ce sont les lignes déjà présentes dans le fichier consolidé (preuve d'idempotence). Ce chiffre se lit facilement comme un défaut. | Rejeu sans duplication. Pas d'historique des versions des données. |
| Application | Requêtes SQL lancées à la main (`run_sql.py`). | Pas d'interface ni de tableau de bord. | L'utilisateur doit lire du SQL. |

### 1.2 Scénario d'évolution retenu

**Scénario A, reporting sobre** : mise à jour quotidienne, équipe réduite (une personne). Question d'architecture : une base SQL suffit-elle ? Les sources actuelles sont annuelles. Le scénario est donc une hypothèse : le pipeline serait relancé chaque jour pour un rapport.

### 1.3 Exigences mesurables

| Exigence | Valeur cible | Pourquoi |
|---|---|---|
| Fraîcheur | Base reconstruite et rapport disponibles avant 07 h 00, après un lancement quotidien. | Le scénario A impose un reporting quotidien. |
| Volume quotidien | Aucun nouveau volume (snapshot figé). Aujourd'hui 16 454 lignes chargées (9 425 + 7 029). Dimensionné pour 100 000 lignes au plus. | Une marge de 6 fois suffit à un projet de cette taille. |
| Disponibilité | Pas de haute disponibilité. Base reconstructible en moins de 2 minutes (mesuré : 17,5 secondes, collecte réseau comprise). | Un seul utilisateur : une reconstruction rapide coûte moins qu'un système redondant. |
| Rétention | Raw et rejets conservés pendant le module. Curated et base : reconstructibles, donc sans durée propre. | Les données se rejouent depuis le raw. |
| Utilisateurs | 1 auteur en écriture (aucun autre collaborateur), lecture publique du dépôt. | Pas d'accès concurrent en écriture. |
| Sensibilité | Aucune donnée personnelle (voir `docs/grille_rgpd.md`). | Les données sont agrégées par pays et par année. |

**Question de contrôle : quelle exigence supprimer pour simplifier le plus ?** La mise à jour quotidienne. Sans elle, les sources étant annuelles, un script lancé à la main suffirait : plus besoin de planification ni de supervision de l'exécution.

## 2. Lake, Warehouse, Mart

| Couche | Mission | Contenu de votre projet | Consommateur |
|---|---|---|---|
| Zone raw (pas un vrai Data Lake) | Conserver et rejouer | `data/raw/` (CSV horodatés non modifiés) et `data/rejected/` | Auteur (data engineer) |
| Data Warehouse | Intégrer et historiser | `data/curated/*_final.csv` et base SQLite : 6 dimensions, 2 tables de mesures | Auteur, analyste |
| Data Mart | Servir un usage métier | Requêtes KPI 1, 2 et 3 de `sql/queries.sql` | Utilisateur final |

**Classement des datasets.** Fichiers Zenodo bruts en zone raw. Fichiers validés et typés (`*_final.csv`) et base SQLite en warehouse. Résultats des 3 KPI en mart.

**Transformations entre couches.** Raw vers curated : validation (4 règles de qualité pour la résistance, 6 pour la consommation, rejets conservés), renommage, typage. Curated vers warehouse : chargement dans le schéma, avec contraintes. Warehouse vers mart : jointure sur pays, année et classe, KPI pondéré.

**Produit Gold utile à l'application.**
```
mart_resistance_consommation
- pays, annee, code_atc (classe)
- ddd_community
- n_tested, n_resistant
- taux_resistance_pondere
```
Il serait défini comme une vue SQL (et non une table copiée), pour que tous les KPI partent de la même source.

**Décision.** Notre projet retient la zone raw et le warehouse, et un mart sous forme de vue SQL, parce que les données sont petites et que chaque couche a une fonction distincte. Il n'a pas de Data Lake au sens complet : `data/raw/` est un dossier de fichiers, avec les contrats YAML pour seul catalogue. Une base séparée pour le mart serait inutile à cette échelle et risquerait de produire des KPI contradictoires.

## 3. SQL ou NoSQL

| Critère | Votre besoin |
|---|---|
| Schéma | Stable et explicite : deux sources avec des contrats versionnés. |
| Jointures | Nécessaires : on croise résistance et consommation sur pays, année et classe. |
| Transactions | Peu utiles (chargement unique, lecture ensuite), mais les contraintes d'intégrité sont indispensables. |
| Accès | Requêtes variées : agrégats par pays, par classe, par bactérie. |
| Évolution | Rare : snapshot figé. Migrations acceptables. |
| Distribution | Inutile à 16 454 lignes. |

### Patterns d'accès

| Priorité | Requête métier | Données lues ensemble | Fréquence |
|---|---|---|---|
| 1 | KPI 1 : taux de résistance pondéré par pays, bactérie, année | résultats de résistance, pays, bactérie | À chaque rapport (quotidienne dans le scénario A) |
| 2 | KPI 2 : DDD du secteur Community par pays, année, classe J01 | consommation, pays, classe, voie | À chaque rapport |
| 3 | KPI 3 : croisement consommation et résistance par pays, année, classe | les deux tables de mesures, jointes | À chaque rapport |

### Deux esquisses

**Relationnel** : 8 tables (voir `sql/schema.sql`), clés primaires et étrangères, `UNIQUE` sur la clé métier, `CHECK` sur les bornes.

**Document JSON**, pour la lecture la plus fréquente (KPI 3) :
```json
{
  "pays": "France", "annee": 2010, "classe": "J01M",
  "consommation": {"secteur": "Community", "ddd": 2.1},
  "resistance": [{"bacterie": "ESCCOL", "antibiotique": "CIP", "n_tested": 200, "n_resistant": 50}]
}
```

**Comparaison.** Duplication : le document répète pays, année et classe pour chaque combinaison. Cohérence : le relationnel la garantit par les contraintes. Évolution : le document s'adapte mieux à un schéma qui change, le relationnel demande une migration. Coût des requêtes : le KPI 1 (par bactérie) obligerait à parcourir tous les documents. En SQL, un `GROUP BY` suffit.

```
Choix retenu : SQL
Justification : données tabulaires, jointures nécessaires entre les deux sources, intégrité garantie par la base, 3 requêtes d'agrégation.
Compromis accepté : schéma rigide, une migration est nécessaire si une source change de structure.
Condition de réexamen : si les schémas des sources changent chaque mois (scénario C) ou si la source principale devient une API JSON.
```

## 4. Batch, streaming ou hybride

| Question | Réponse |
|---|---|
| La décision doit-elle être prise en quelques secondes ? | Non : les décisions concernent des campagnes de bon usage, au rythme de l'année. |
| Existe-t-il de vrais événements continus ? | Non : les sources sont des fichiers annuels figés. |
| Le rejeu et l'ordre sont-ils définis ? | Oui : rejeu par fichier horodaté, clé métier unique, déduplication entre exécutions. |
| L'équipe peut-elle superviser un système événementiel ? | Non : une seule personne. |

**Mode retenu : batch.** Le streaming n'apporterait rien, puisqu'il n'y a aucun événement continu ni besoin de faible latence. Kafka n'est pas retenu, donc le tableau Kafka du sujet ne s'applique pas. L'architecture hybride est écartée pour la même raison.

## 5. Orchestration et observabilité

### 5.1 DAG

```
collect_A -> validate_A -> transform_A \
                                        -> load_sqlite -> [contrôle final, manuel] -> queries (KPI)
collect_B -> validate_B -> transform_B /
```

L'orchestrateur est `src/pipeline.py` : il lance les 7 scripts l'un après l'autre (`subprocess.run(..., check=True)`). Il n'y a ni planificateur ni exécution parallèle. Un script qui se termine en erreur arrête tout le pipeline.

| Tâche | Entrée | Sortie | Retry | Échec bloquant |
|---|---|---|---|---|
| Collecte A / B | URL Zenodo configurée | CSV raw horodaté | 3 tentatives (timeout 60 s, attente croissante) | Oui, si les 3 échouent (le script s'arrête en erreur) |
| Validation A / B | CSV raw | acceptées, invalides, hors périmètre, rapport JSON | Aucun (déterministe) | Seulement si le script plante (par exemple, aucun fichier raw trouvé). Le statut `FAIL` (aucune ligne acceptée) est écrit dans le rapport mais n'arrête pas le pipeline. |
| Transformation A / B | CSV acceptées | `*_final.csv` | Aucun | Oui, si le script plante |
| Publication (`load_sqlite`) | les deux `*_final.csv` | base SQLite reconstruite | Aucun (la base est recréée) | Oui : une contrainte `CHECK` ou une clé étrangère violée arrête le chargement |
| Contrôle final | base SQLite | `PRAGMA integrity_check`, `foreign_key_check`, `sql/controle.sql`, `tests/test_schema.py` | Aucun | Non : ces contrôles sont lancés à la main, hors pipeline |

### 5.2 Observabilité minimale

| Signal | Mesure | Seuil ou objectif | Action |
|---|---|---|---|
| Fraîcheur | Retard de disponibilité de la base | Prête en moins de 2 minutes après le lancement (mesuré : 17,5 s) | Relancer le pipeline |
| Volume | Nombre de lignes chargées | 9 425 (A) et 7 029 (B) ; écart de plus de 5 % à enquêter | Lire le rapport, vérifier la source |
| Qualité | Taux de rejet (lignes invalides sur lignes en entrée) | Objectif : moins de 2 %. Mesuré : 0 sur 11 876 (A) et 2 sur 14 084 (B, soit 0,014 %). | Lire `cause_rejet`, ajuster les règles |
| Fiabilité | Taux d'échec du pipeline | 0 échec non repris (1 incident réel observé : timeout Zenodo, repris par les tentatives) | Relancer, puis vérifier la source |
| Performance | Durée d'exécution | Moins de 2 minutes. Mesuré : 17,5 s au total ; validation A 0,49 s et validation B 0,16 s. | Chercher l'étape lente |

**Limite.** Le seuil de 2 % est un objectif, pas encore une règle du code : aujourd'hui, une seule ligne invalide donne `PASS_WITH_WARNINGS`, et `FAIL` n'apparaît que si aucune ligne n'est acceptée. Amélioration prévue : passer en `FAIL` au-dessus de 2 % et faire arrêter le pipeline.

### 5.3 Objectif de service

Après chaque exécution quotidienne, la base est prête en moins de 2 minutes, respecte toutes ses contraintes d'intégrité, moins de 2 % des lignes sont rejetées et un rapport d'exécution est archivé.

### 5.4 Test d'incident : source indisponible

- **Détection** : `collect.py` lève un `Read timed out` (incident réel du 5 novembre).
- **Reprise** : 3 tentatives avec attente croissante, puis arrêt du pipeline.
- **Alerte** : le pipeline s'arrête avec un message. Il n'y a pas d'alerte automatique : c'est une limite.
- **Preuve de résolution** : test avec une URL volontairement erronée : 3 tentatives puis arrêt. Après correction, relance complète et rapport régénéré.

## 6. Gouvernance et sécurité

| Objet | Réponse du projet |
|---|---|
| Owner | L'auteur (Gareth Tchoula) pour le pipeline et les contrats ; l'ECDC pour les données d'origine. |
| Catalogue | README, contrats `config/data_contract*.yaml`, dossier `docs/`. |
| Lineage | Voir ci-dessous. |
| Accès | Lecture : publique (dépôt GitHub public). Écriture : l'auteur seul, aucun autre collaborateur. La base SQLite est locale et non versionnée. |
| Rétention | Raw et rejets : durée du module. Curated et base : reconstructibles, base supprimée à chaque exécution. |
| Évolution | Contrats versionnés (A en 1.1, B en 1.1) avec changelog. |

**Lineage**
```
[Zenodo / ECDC] -> [data/raw/*.csv] -> [Validation] -> [data/curated + data/rejected]
-> [Transformation] -> [*_final.csv] -> [load_sqlite] -> [SQLite] -> [sql/queries.sql] -> [KPI]
```

### Minimisation

Aucun champ n'est personnel ni sensible : les données sont des agrégats par pays et par année (n_tested ≥ 30). Rien à agréger, pseudonymiser ou supprimer. La seule donnée personnelle du dépôt est l'identité de l'auteur dans les commits Git, visible de tous puisque le dépôt est public (voir `docs/grille_rgpd.md`).

### Sobriété

Une seule base fichier, pas de serveur ni de service distribué. Le pipeline est relancé à la demande. La base est reconstruite plutôt que mise à jour.

### Revue de risque

| Risque | Probabilité | Impact | Mesure |
|---|---|---|---|
| Source indisponible | Moyenne (1 incident observé) | Moyen : collecte bloquée, données déjà conservées en raw | 3 tentatives, arrêt propre, raw conservé |
| Schéma cassé | Faible (snapshot figé) | Élevé : chargement impossible | Contrats YAML, règles de validation, contraintes SQL |
| Donnée sensible exposée | Très faible (aucune donnée personnelle) | Faible : seule l'identité de l'auteur est visible dans les commits | Grille RGPD, `.gitignore`, aucun secret dans le dépôt |
| KPI erroné | Moyenne (voie `All` ambiguë, effet de composition) | Élevé : conclusion trompeuse | Règles testées, limites écrites dans les contrats, croisement ciblé |
