# ADR 002 : Choix de la base d'analyse

Date : 6 novembre 2026
Statut : accepté
Lié à : ADR 001 (architecture cible)

## Contexte
Le projet compare la résistance aux antibiotiques (9 425 lignes) et la consommation (7 029 lignes) pour 15 pays européens. Les volumes sont petits, les données sont annuelles, il y a un seul utilisateur et les usages sont surtout des lectures (agrégations, jointures). Les règles d'intégrité doivent être garanties par la base (clés étrangères, CHECK, UNIQUE).

## Décision
Utiliser SQLite, avec un schéma relationnel (6 dimensions, 2 tables de mesures), reconstruit à chaque exécution du pipeline.

## Alternatives étudiées
- **CSV + pandas** : aucune contrainte d'intégrité garantie, requêtes difficiles à relire et à commenter. Écarté.
- **PostgreSQL** : accès concurrents, droits par utilisateur, gros volumes. Mais il demande un serveur à installer et à administrer, ce qui est disproportionné pour ~16 000 lignes et un seul utilisateur. Écarté.
- **DuckDB** : moteur en colonnes, adapté à l'analytique sur gros volumes. Un bon candidat si les volumes grandissent, mais inutile à cette échelle. Écarté pour l'instant.

## Conséquences
Positives : zéro serveur, un seul fichier, contraintes vérifiées (tests de refus dans `tests/test_schema.py`), EXPLAIN QUERY PLAN disponible, reproductible sur n'importe quelle machine.
Négatives : peu d'accès concurrents, pas de gestion de droits par utilisateur, performances limitées si les volumes devenaient grands. Les clés étrangères ne sont actives que si `PRAGMA foreign_keys=ON` est envoyé à chaque connexion.
À revoir si les données dépassent quelques millions de lignes ou si plusieurs utilisateurs doivent écrire.
