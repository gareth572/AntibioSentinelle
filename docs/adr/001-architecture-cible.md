# ADR 001 : Architecture cible du projet

Date : 7 novembre 2026
Statut : accepté (mise en œuvre : à faire, voir Conséquences)

## Contexte

AntibioSentinelle compare la résistance aux antibiotiques (9 425 lignes chargées) et la consommation (7 029 lignes chargées) pour 15 pays européens. Les deux sources sont des CSV annuels figés publiés sur Zenodo. Le pipeline actuel tourne en 17,5 secondes, en 7 étapes lancées à la main, avec une base SQLite reconstruite à chaque exécution.

Scénario d'évolution (A, reporting sobre) : mise à jour quotidienne, une personne pour exploiter le système. Exigences mesurables : base prête avant 07 h 00, reconstruction en moins de 2 minutes, moins de 2 % de lignes invalides, aucune donnée personnelle, un seul utilisateur en écriture, volume au plus 100 000 lignes.

Limites observées sur l'existant : pas de planification, un statut qualité qui ne bloque rien (`FAIL` seulement si aucune ligne n'est acceptée), contrôles d'intégrité lancés à la main, rapports écrasés à chaque exécution, aucun KPI défini une seule fois.

## Décision

Conserver une architecture batch, un seul poste et une base SQL (SQLite, voir ADR 002), et y ajouter cinq éléments :
1. un planificateur du système (un lancement par jour avant 07 h) ;
2. une porte qualité : `FAIL` et arrêt du pipeline si plus de 2 % de lignes sont invalides ;
3. un contrôle final automatique (`integrity_check`, `foreign_key_check`) ;
4. un mart sous forme de vue SQL ;
5. des rapports archivés avec leur date et une alerte simple.

## Options comparées

- **Simple** : le pipeline actuel, lancé chaque jour par un planificateur.
- **Cible** : Simple plus les cinq ajouts ci-dessus.
- **Évolutive** : orchestrateur, base serveur, stockage Parquet, tableau de bord de métriques.

Le tableau détaillé (description, bénéfice, coût) est dans `docs/architecture_v2.md`.

## Arguments

- L'option Simple ne permet pas de tenir l'objectif de service : sans porte qualité ni contrôle automatique, une dégradation des données passe inaperçue.
- L'option Évolutive répond à des besoins que le projet n'a pas : volume (16 454 lignes), plusieurs utilisateurs, faible latence. Elle demande un serveur à exploiter, ce qu'une personne ne peut pas assurer raisonnablement.
- L'option Cible traite chaque limite observée par un ajout de taille proportionnée.
- Le mode batch convient parce que les sources sont annuelles : aucune décision n'est prise en quelques secondes et il n'y a pas d'événements continus.

## Conséquences positives

- Les six exigences et l'objectif de service sont vérifiables.
- Une donnée dégradée arrête le pipeline au lieu de produire des KPI trompeurs.
- Les KPI partent d'une définition unique.
- Le système reste exploitable par une personne, sans serveur.

## Conséquences négatives

- Les cinq ajouts ne sont pas encore codés : l'architecture décrite est une cible.
- Le seuil de 2 % est choisi sans étude préalable : il faudra l'ajuster après quelques exécutions.
- Pas de parallélisme, pas de tableau de bord, une alerte limitée.
- Les limites sur le sens des données restent entières (voie `All` ambiguë, effet de composition, valeurs `anomalie_valeur` non exclues des KPI) : cette architecture améliore le contrôle des données, pas leur interprétation.

## Condition de réexamen

Réexaminer cette décision si l'un des cas suivants se produit :
- le volume dépasse 100 000 lignes ou le pipeline dépasse 2 minutes ;
- plusieurs personnes doivent écrire ou publier ;
- les sources deviennent fréquentes ou continues (nécessité de streaming) ;
- les sources changent de schéma régulièrement (scénario C).
