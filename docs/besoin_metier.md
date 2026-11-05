# Besoin métier et modèle de données

## Besoin métier

1. Un pays publie, pour une année donnée, des résultats de tests de résistance.
2. Chaque résultat porte sur une bactérie testée contre un antibiotique, chez des patients hospitalisés. Il donne le nombre de souches testées et, parmi elles, le nombre de souches résistantes ou intermédiaires.
3. Un antibiotique relève d'une seule classe thérapeutique, identifiée par un code ATC. Une classe regroupe plusieurs antibiotiques.
4. Un pays publie aussi, pour une année donnée, la consommation d'une classe d'antibiotiques, pour un secteur et une voie d'administration donnés, exprimée en doses journalières pour 1 000 habitants.
5. Résistance et consommation se rejoignent sur trois clés : le pays, l'année et la classe d'antibiotiques.

## MCD : associations et cardinalités

| Association | Côté dimension | Côté mesure |
|---|---|---|
| PAYS déclare RESULTAT_RESISTANCE | 0,n | 1,1 |
| BACTERIE concerne RESULTAT_RESISTANCE | 0,n | 1,1 |
| ANTIBIOTIQUE est testé dans RESULTAT_RESISTANCE | 0,n | 1,1 |
| CLASSE regroupe ANTIBIOTIQUE | 0,n | 1,1 |
| PAYS déclare CONSOMMATION | 0,n | 1,1 |
| CLASSE concerne CONSOMMATION | 0,n | 1,1 |
| SECTEUR qualifie CONSOMMATION | 0,n | 1,1 |
| VOIE qualifie CONSOMMATION | 0,n | 1,1 |

`CLASSE regroupe ANTIBIOTIQUE` est en 0,n : cinq classes n'existent que dans la
source B et n'ont aucun antibiotique dans la source A. Il n'y a aucune
association directe entre les deux mesures.

## Décisions de modélisation

- L'année est un attribut des deux mesures, pas une entité.
- `patient_type` n'est pas modélisé : il vaut `INPAT` sur les 11 876 lignes.
- La voie `All` est une valeur ordinaire de `VOIE` ; son sens n'est pas documenté.
- Seuls les 15 pays retenus sont chargés.
- Le libellé d'une classe peut être vide : la source A ne donne que le code.

## MLD

```
PAYS(id_pays PK, nom UNIQUE NOT NULL)
BACTERIE(id_bacterie PK, code UNIQUE NOT NULL, nom_long)
CLASSE(id_classe PK, code_atc UNIQUE NOT NULL, libelle NULL)
ANTIBIOTIQUE(id_antibiotique PK, code UNIQUE NOT NULL, nom_long,
             id_classe FK NOT NULL)
SECTEUR(id_secteur PK, nom UNIQUE NOT NULL)
VOIE(id_voie PK, nom UNIQUE NOT NULL)
RESULTAT_RESISTANCE(id_resultat PK, id_pays FK, id_bacterie FK,
             id_antibiotique FK, annee, n_tested, n_resistant, resistance_rate,
             UNIQUE(id_pays, annee, id_bacterie, id_antibiotique))
CONSOMMATION(id_conso PK, id_pays FK, id_classe FK, id_secteur FK, id_voie FK,
             annee, ddd, anomalie_valeur,
             UNIQUE(id_pays, annee, id_secteur, id_voie, id_classe))
```