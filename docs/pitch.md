# Pitch (3 minutes)

**Le problème.** Les bactéries résistent de plus en plus aux antibiotiques. On dit que c'est lié à la consommation, mais est-ce visible dans les données européennes ?

**Ce que j'ai construit.** AntibioSentinelle prend deux sources ouvertes de l'ECDC, publiées sur Zenodo : la résistance (9 425 lignes) et la consommation (7 029 lignes), pour 15 pays entre 1999 et 2016. Un pipeline en 7 étapes les collecte, les contrôle avec des contrats de données, les nettoie, puis les charge dans une base SQLite.

**Pourquoi SQLite.** Un schéma relationnel avec 6 dimensions et 2 tables de mesures. Les règles sont dans la base : un taux de résistance hors de 0 à 1 est refusé. Je l'ai testé avec 9 cas invalides. Pour ~16 000 lignes et un utilisateur, un serveur serait disproportionné. C'est mon ADR 001.

**Ce que ça produit.** Trois indicateurs : le taux de résistance pondéré, la consommation par classe, et le croisement des deux par pays et par année. Un index a fait passer une requête d'un balayage complet (SCAN) à une recherche (SEARCH), vérifié avec EXPLAIN QUERY PLAN.

**Ce que j'ai appris et corrigé.** La voie d'administration « All » n'est pas un total des autres voies : je l'ai testé sur 150 groupes et j'ai écrit une règle. Mon contrat disait que les valeurs anormales étaient exclues des KPI, alors que le SQL les gardait : j'ai corrigé le contrat plutôt que de cacher l'écart.

**Les limites, dites franchement.** Le lien entre consommation en ville et résistance à l'hôpital est descriptif, pas causal. Un effet de composition peut fausser l'évolution par classe. La couverture varie selon les pays.

**RGPD.** Les données sont agrégées par pays : aucune donnée personnelle, donc pas de base légale à justifier. La seule donnée personnelle du dépôt est mon identité dans les commits.

**La suite.** Si les volumes grandissent, passer à DuckDB ou PostgreSQL ; exclure ou traiter les valeurs anormales ; ajouter de l'observabilité automatique.