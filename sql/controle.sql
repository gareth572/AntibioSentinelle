-- Controle A : lignes sources d'un groupe, pour verifier une valeur de la requete 6 a la main
-- Autriche 1998 classe J01A, secteur Community : toutes les voies et leur DDD
SELECT v.nom AS voie, c.ddd
FROM consommation c
JOIN pays p ON p.id_pays = c.id_pays
JOIN classe cl ON cl.id_classe = c.id_classe
JOIN secteur s ON s.id_secteur = c.id_secteur
JOIN voie v ON v.id_voie = c.id_voie
WHERE p.nom = 'Austria' AND c.annee = 1998 AND cl.code_atc = 'J01A' AND s.nom = 'Community';

-- Controle B : rapprochement des effectifs entre la requete 6 et les groupes de la requete 3b
-- groupes_j01 moins j01_exclus doit donner 2325, et groupes_j01 plus groupes_hors_j01 doit donner 2714
SELECT
    SUM(cl.code_atc LIKE 'J01%')                                  AS groupes_j01,
    SUM(cl.code_atc NOT LIKE 'J01%')                              AS groupes_hors_j01,
    SUM(cl.code_atc LIKE 'J01%' AND g.a_all > 0 AND g.nb_voies > 1) AS j01_exclus
FROM (
    SELECT
        c.id_classe,
        COUNT(DISTINCT c.id_voie) AS nb_voies,
        SUM(v.nom = 'All')        AS a_all
    FROM consommation c
    JOIN secteur s ON s.id_secteur = c.id_secteur
    JOIN voie    v ON v.id_voie = c.id_voie
    WHERE s.nom = 'Community'
    GROUP BY c.id_pays, c.annee, c.id_classe
) g
JOIN classe cl ON cl.id_classe = g.id_classe;

-- Controle C : effectifs et taux de resistance de l'Autriche 2001, classe J01C, calcules directement
-- Doit donner n_tested 655 et un taux de 0.1786 comme la requete 5
SELECT SUM(r.n_tested) AS n_tested,
       SUM(r.n_resistant) AS n_resistant,
       ROUND(1.0 * SUM(r.n_resistant) / SUM(r.n_tested), 4) AS taux
FROM resultat_resistance r
JOIN pays p ON p.id_pays = r.id_pays
JOIN antibiotique ab ON ab.id_antibiotique = r.id_antibiotique
JOIN classe cl ON cl.id_classe = ab.id_classe
WHERE p.nom = 'Austria' AND r.annee = 2001 AND cl.code_atc = 'J01C';