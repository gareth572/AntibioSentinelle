-- Plan d'execution avant index : filtre sur bacterie et antibiotique sans pays
EXPLAIN QUERY PLAN
SELECT SUM(n_tested) FROM resultat_resistance WHERE id_bacterie = 1 AND id_antibiotique = 1;