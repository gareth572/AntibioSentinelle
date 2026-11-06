-- Modele physique SQLite d'AntibioSentinelle.
-- A activer a chaque connexion : PRAGMA foreign_keys = ON;

CREATE TABLE pays (
    id_pays INTEGER PRIMARY KEY,
    nom TEXT NOT NULL UNIQUE
);

CREATE TABLE bacterie (
    id_bacterie INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    nom_long TEXT
);

CREATE TABLE classe (
    id_classe INTEGER PRIMARY KEY,
    code_atc TEXT NOT NULL UNIQUE,
    libelle TEXT
);

CREATE TABLE antibiotique (
    id_antibiotique INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    nom_long TEXT,
    id_classe INTEGER NOT NULL,
    FOREIGN KEY (id_classe) REFERENCES classe(id_classe) ON DELETE RESTRICT
);

CREATE TABLE secteur (
    id_secteur INTEGER PRIMARY KEY,
    nom TEXT NOT NULL UNIQUE
);

CREATE TABLE voie (
    id_voie INTEGER PRIMARY KEY,
    nom TEXT NOT NULL UNIQUE
);

CREATE TABLE resultat_resistance (
    id_resultat INTEGER PRIMARY KEY,
    id_pays INTEGER NOT NULL,
    id_bacterie INTEGER NOT NULL,
    id_antibiotique INTEGER NOT NULL,
    annee INTEGER NOT NULL CHECK (annee BETWEEN 1998 AND 2019),
    n_tested INTEGER NOT NULL CHECK (n_tested >= 30),
    n_resistant INTEGER NOT NULL CHECK (n_resistant >= 0),
    resistance_rate REAL NOT NULL CHECK (resistance_rate BETWEEN 0 AND 1),
    CHECK (n_resistant <= n_tested),
    CHECK (abs(resistance_rate - 1.0 * n_resistant / n_tested) < 0.000001),
    UNIQUE (id_pays, annee, id_bacterie, id_antibiotique),
    FOREIGN KEY (id_pays) REFERENCES pays(id_pays) ON DELETE RESTRICT,
    FOREIGN KEY (id_bacterie) REFERENCES bacterie(id_bacterie) ON DELETE RESTRICT,
    FOREIGN KEY (id_antibiotique) REFERENCES antibiotique(id_antibiotique) ON DELETE RESTRICT
);

CREATE TABLE consommation (
    id_conso INTEGER PRIMARY KEY,
    id_pays INTEGER NOT NULL,
    id_classe INTEGER NOT NULL,
    id_secteur INTEGER NOT NULL,
    id_voie INTEGER NOT NULL,
    annee INTEGER NOT NULL CHECK (annee BETWEEN 1997 AND 2016),
    ddd REAL NOT NULL CHECK (ddd >= 0),
    anomalie_valeur INTEGER NOT NULL DEFAULT 0 CHECK (anomalie_valeur IN (0, 1)),
    UNIQUE (id_pays, annee, id_secteur, id_voie, id_classe),
    FOREIGN KEY (id_pays) REFERENCES pays(id_pays) ON DELETE RESTRICT,
    FOREIGN KEY (id_classe) REFERENCES classe(id_classe) ON DELETE RESTRICT,
    FOREIGN KEY (id_secteur) REFERENCES secteur(id_secteur) ON DELETE RESTRICT,
    FOREIGN KEY (id_voie) REFERENCES voie(id_voie) ON DELETE RESTRICT
);

-- index de jointure : classe d'un antibiotique (jointure resistance / consommation)
CREATE INDEX idx_antibiotique_classe ON antibiotique(id_classe);

-- index de filtre : resistance par bacterie et antibiotique, hors pays (requete 6)
CREATE INDEX idx_resultat_bacterie_antibiotique ON resultat_resistance(id_bacterie, id_antibiotique);