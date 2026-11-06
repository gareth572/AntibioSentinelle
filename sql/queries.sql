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
