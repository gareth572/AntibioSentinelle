-- Jeu de donnees de test : valeurs FICTIVES pour montrer le schema, pas des resultats reels.
-- Les vraies donnees sont chargees par src/load_sqlite.py.

-- Dimensions
INSERT INTO pays (nom) VALUES ('France'), ('Italy');
INSERT INTO bacterie (code, nom_long) VALUES ('ESCCOL', 'E. coli');
INSERT INTO classe (code_atc, libelle) VALUES
    ('J01M', 'J01M Quinolones'),
    ('J01C', 'J01C Penicillins');
INSERT INTO antibiotique (code, nom_long, id_classe) VALUES
    ('CIP', 'Ciprofloxacin', (SELECT id_classe FROM classe WHERE code_atc = 'J01M'));
INSERT INTO secteur (nom) VALUES ('Community'), ('Hospital Sector');
INSERT INTO voie (nom) VALUES ('All'), ('Oral');

-- Resistance : n_resistant / n_tested doit egaler resistance_rate
INSERT INTO resultat_resistance
    (id_pays, id_bacterie, id_antibiotique, annee, n_tested, n_resistant, resistance_rate)
VALUES
    ((SELECT id_pays FROM pays WHERE nom = 'France'),
     (SELECT id_bacterie FROM bacterie WHERE code = 'ESCCOL'),
     (SELECT id_antibiotique FROM antibiotique WHERE code = 'CIP'), 2010, 200, 50, 0.25),
    ((SELECT id_pays FROM pays WHERE nom = 'France'),
     (SELECT id_bacterie FROM bacterie WHERE code = 'ESCCOL'),
     (SELECT id_antibiotique FROM antibiotique WHERE code = 'CIP'), 2011, 200, 60, 0.3),
    ((SELECT id_pays FROM pays WHERE nom = 'Italy'),
     (SELECT id_bacterie FROM bacterie WHERE code = 'ESCCOL'),
     (SELECT id_antibiotique FROM antibiotique WHERE code = 'CIP'), 2010, 100, 40, 0.4);

-- Consommation : DDD pour 1000 habitants, secteur Community
INSERT INTO consommation
    (id_pays, id_classe, id_secteur, id_voie, annee, ddd, anomalie_valeur)
VALUES
    ((SELECT id_pays FROM pays WHERE nom = 'France'),
     (SELECT id_classe FROM classe WHERE code_atc = 'J01M'),
     (SELECT id_secteur FROM secteur WHERE nom = 'Community'),
     (SELECT id_voie FROM voie WHERE nom = 'All'), 2010, 1.5, 0),
    ((SELECT id_pays FROM pays WHERE nom = 'France'),
     (SELECT id_classe FROM classe WHERE code_atc = 'J01M'),
     (SELECT id_secteur FROM secteur WHERE nom = 'Community'),
     (SELECT id_voie FROM voie WHERE nom = 'All'), 2011, 1.6, 0),
    ((SELECT id_pays FROM pays WHERE nom = 'Italy'),
     (SELECT id_classe FROM classe WHERE code_atc = 'J01M'),
     (SELECT id_secteur FROM secteur WHERE nom = 'Community'),
     (SELECT id_voie FROM voie WHERE nom = 'Oral'), 2010, 2.0, 0),
    ((SELECT id_pays FROM pays WHERE nom = 'Italy'),
     (SELECT id_classe FROM classe WHERE code_atc = 'J01C'),
     (SELECT id_secteur FROM secteur WHERE nom = 'Community'),
     (SELECT id_voie FROM voie WHERE nom = 'Oral'), 2010, 12.0, 0);