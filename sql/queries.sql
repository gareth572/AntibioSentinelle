-- KPI 1 : taux de resistance pondere par pays, bacterie et annee (antibiotique CIP)
-- pondere = somme des resistants / somme des testes (et non moyenne des taux)
SELECT
    p.nom                                       AS pays,
    b.code                                      AS bacterie,
    r.annee,
    SUM(r.n_tested)                             AS n_tested,
    SUM(r.n_resistant)                          AS n_resistant,
    ROUND(1.0 * SUM(r.n_resistant) / SUM(r.n_tested), 4) AS taux_resistance_pondere
FROM resultat_resistance r
JOIN pays         p  ON p.id_pays = r.id_pays
JOIN bacterie     b  ON b.id_bacterie = r.id_bacterie
JOIN antibiotique ab ON ab.id_antibiotique = r.id_antibiotique
WHERE ab.code = 'CIP'
GROUP BY p.nom, b.code, r.annee
ORDER BY p.nom, b.code, r.annee;

-- Requete 2 - KPI 1 : taux de resistance pondere par pays, toutes annees confondues (ESCCOL, CIP)
-- Compare SUM(n_resistant)/SUM(n_tested) a la moyenne simple des taux, qui serait faussee par les petits effectifs
SELECT
    p.nom                                                AS pays,
    COUNT(*)                                             AS nb_annees,
    SUM(r.n_tested)                                      AS n_tested,
    SUM(r.n_resistant)                                   AS n_resistant,
    ROUND(1.0 * SUM(r.n_resistant) / SUM(r.n_tested), 4) AS taux_pondere,
    ROUND(AVG(r.resistance_rate), 4)                     AS taux_moyenne_simple,
    ROUND(1.0 * SUM(r.n_resistant) / SUM(r.n_tested)
          - AVG(r.resistance_rate), 4)                   AS ecart
FROM resultat_resistance r
JOIN pays         p  ON p.id_pays = r.id_pays
JOIN bacterie     b  ON b.id_bacterie = r.id_bacterie
JOIN antibiotique ab ON ab.id_antibiotique = r.id_antibiotique
WHERE b.code = 'ESCCOL'
  AND ab.code = 'CIP'
GROUP BY p.nom
ORDER BY taux_pondere DESC;

-- Requete 3 - Exploration : combien de voies distinctes par pays, annee et classe (secteur Community)
-- Sert a choisir la regle de calcul du DDD, car la voie All n'est pas un total des autres voies
SELECT
    p.nom                                         AS pays,
    c.annee,
    cl.code_atc                                   AS classe,
    COUNT(DISTINCT c.id_voie)                     AS nb_voies,
    GROUP_CONCAT(v.nom, ', ')                     AS voies,
    MAX(CASE WHEN v.nom = 'All' THEN 1 ELSE 0 END) AS a_voie_all
FROM consommation c
JOIN pays    p  ON p.id_pays = c.id_pays
JOIN classe  cl ON cl.id_classe = c.id_classe
JOIN secteur s  ON s.id_secteur = c.id_secteur
JOIN voie    v  ON v.id_voie = c.id_voie
WHERE s.nom = 'Community'
GROUP BY p.nom, c.annee, cl.code_atc
ORDER BY nb_voies DESC, p.nom, c.annee, cl.code_atc;

-- Requete 3b - Resume : nombre de groupes par situation de voie (All seule, All et autres, sans All)
-- Chiffre la part de chaque cas pour decider de la regle de calcul du DDD
SELECT
    CASE
        WHEN a_voie_all = 1 AND nb_voies = 1 THEN 'All seule'
        WHEN a_voie_all = 1 AND nb_voies > 1 THEN 'All et autres voies'
        WHEN a_voie_all = 0 THEN 'sans All'
        
    END AS situation,
    COUNT(*) AS nb_groupes
FROM (
        SELECT
        p.nom                                         AS pays,
        c.annee,
        cl.code_atc                                   AS classe,
        COUNT(DISTINCT c.id_voie)                     AS nb_voies,
        GROUP_CONCAT(v.nom, ', ')                     AS voies,
        MAX(CASE WHEN v.nom = 'All' THEN 1 ELSE 0 END) AS a_voie_all
    FROM consommation c
    JOIN pays    p  ON p.id_pays = c.id_pays
    JOIN classe  cl ON cl.id_classe = c.id_classe
    JOIN secteur s  ON s.id_secteur = c.id_secteur
    JOIN voie    v  ON v.id_voie = c.id_voie
    WHERE s.nom = 'Community'
    GROUP BY p.nom, c.annee, cl.code_atc
)
GROUP BY situation;

-- Requete 3c - Controle : dans les groupes avec All et d'autres voies, All egale-t-elle la somme des autres voies ?
-- Compte les groupes selon l'ecart entre All et la somme des autres voies (tolerance de 5 %)
SELECT
    CASE
        WHEN ddd_autres IS NULL OR ddd_autres = 0 THEN 'somme des autres voies nulle'
        WHEN ABS(ddd_all - ddd_autres) <= 0.05 * ddd_autres THEN 'All egale a la somme'
        WHEN ddd_all > ddd_autres THEN 'All superieure a la somme'
        ELSE 'All inferieure a la somme'
    END AS comparaison,
    COUNT(*) AS nb_groupes
FROM (
    SELECT
        SUM(CASE WHEN v.nom = 'All' THEN c.ddd END)  AS ddd_all,
        SUM(CASE WHEN v.nom <> 'All' THEN c.ddd END) AS ddd_autres
    FROM consommation c
    JOIN secteur s ON s.id_secteur = c.id_secteur
    JOIN voie    v ON v.id_voie = c.id_voie
    WHERE s.nom = 'Community'
    GROUP BY c.id_pays, c.annee, c.id_classe
    HAVING COUNT(DISTINCT c.id_voie) > 1
       AND SUM(v.nom = 'All') > 0
)
GROUP BY comparaison;

-- Requete 4 - KPI 2 : DDD par pays, annee et classe (secteur Community)
-- Regle : All seule, ou somme des voies si All absente, groupes avec All et autres voies exclus
SELECT
    p.nom AS pays,
    g.annee,
    cl.code_atc AS classe,
    CASE
        WHEN g.a_all > 0 AND g.nb_voies = 1 THEN g.ddd_all
        WHEN g.a_all = 0 THEN g.ddd_autres
        -- All et autres voies : pas de ELSE, donc NULL (groupe exclu)
    END AS ddd
FROM (
    SELECT
        c.id_pays, c.annee, c.id_classe,
        COUNT(DISTINCT c.id_voie)                    AS nb_voies,
        SUM(v.nom = 'All')                           AS a_all,
        SUM(CASE WHEN v.nom = 'All' THEN c.ddd END)  AS ddd_all,
        SUM(CASE WHEN v.nom <> 'All' THEN c.ddd END) AS ddd_autres
    FROM consommation c
    JOIN secteur s ON s.id_secteur = c.id_secteur
    JOIN voie    v ON v.id_voie = c.id_voie
    WHERE s.nom = 'Community'
    GROUP BY c.id_pays, c.annee, c.id_classe
) g
JOIN pays   p  ON p.id_pays = g.id_pays
JOIN classe cl ON cl.id_classe = g.id_classe
WHERE cl.code_atc LIKE 'J01%'
  -- groupes exclus = ceux ou ddd vaut NULL (All et autres voies)
  AND (g.a_all = 0 OR g.nb_voies = 1)
ORDER BY p.nom, g.annee, cl.code_atc;