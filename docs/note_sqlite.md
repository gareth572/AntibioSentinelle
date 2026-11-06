# Note SQLite : performance, logs, sécurité, RGPD

## Performance
- Volume : 9 425 lignes de résistance et 7 029 de consommation. Sur ce volume,
  aucune requête ne se mesure comme lente, donc aucun temps n'est annoncé.
- Index : `idx_antibiotique_classe` (jointure résistance / consommation par la
  classe) et `idx_resultat_bacterie_antibiotique` (filtre sur la bactérie et
  l'antibiotique sans pays).
- Mesure avec `EXPLAIN QUERY PLAN` (`sql/explain.sql`) : le filtre sur la
  bactérie et l'antibiotique passait de `SCAN resultat_resistance` à
  `SEARCH ... USING INDEX idx_resultat_bacterie_antibiotique`. La clé unique
  `(id_pays, annee, id_bacterie, id_antibiotique)` ne servait pas ce filtre,
  car `id_pays` n'y figure pas en tête.
- Compromis : un index accélère certaines lectures, ralentit les écritures et
  occupe de l'espace. Ici la base est reconstruite à chaque exécution, donc le
  coût d'écriture est faible.

## Logs
- Présents : un rapport JSON par source (`reports/run_report.json` et
  `run_report_amc.json`) avec les comptes, les échecs par règle, le statut et la
  durée ; les lignes invalides sont conservées avec leur `cause_rejet` ; la
  sortie du pipeline indique chaque étape.
- Absents : aucune table `audit_log` ni trigger, et aucun module de logs. La
  base est reconstruite entièrement à chaque exécution et personne ne la
  modifie à la main, donc un audit des modifications apporterait peu. Si elle
  devenait modifiable par des utilisateurs, il faudrait journaliser les
  suppressions et les mises à jour.

## Sécurité
- Les valeurs sont toujours passées en paramètres (`?`) dans le chargement, jamais
  concaténées dans le texte SQL. Les fichiers SQL exécutés par `run_sql.py` sont
  écrits par le développeur : aucune saisie d'utilisateur n'entre dans une requête.
- Les clés étrangères sont activées (`PRAGMA foreign_keys = ON`) à chaque
  connexion, et les contraintes `CHECK`, `UNIQUE` et `NOT NULL` sont testées
  (`tests/test_schema.py`, 10 cas).
- La base n'est pas versionnée (`data/*.db` dans `.gitignore`), ni les données
  brutes. Aucun secret n'est stocké.
- SQLite n'a pas de comptes ni de droits par utilisateur : la protection repose
  sur les droits du fichier sur le poste. Il n'y a ni API ni accès réseau.
- Sauvegarde : aucune sauvegarde chiffrée. La base se reconstruit avec
  `python src\pipeline.py`, à condition que Zenodo soit joignable. Les copies
  brutes horodatées restent en local.

## RGPD
- Les deux sources sont agrégées par pays et par année : aucune donnée
  personnelle, aucun identifiant de patient.
- Conséquence : pas de durée de conservation individuelle, de droit d'accès ni
  de suppression à gérer. La grille RGPD détaillée est dans un document séparé.
- Source : Zenodo, DOI 10.5281/zenodo.14224680, à citer.