# Cadrage du projet — AntibioSentinelle

## Étape 1 — Définir l'application

| Question | Réponse |
|---|---|
| Nom provisoire | AntibioSentinelle |
| Utilisateur | Toute personne souhaitant explorer l'évolution de l'antibiorésistance en Europe |
| Problème | On ne voit pas facilement si la hausse de la consommation d'antibiotiques dans un pays s'accompagne d'une hausse de la résistance bactérienne |
| Décision | Prioriser les couples pays / classe d'antibiotique à cibler pour une campagne de bon usage |
| Question centrale | Comment le taux de résistance bactérienne évolue-t-il par pays, bactérie et antibiotique en Europe, et comment se compare-t-il au niveau de consommation d'antibiotiques du même pays ? |
| Périmètre | Inclus : pays UE/EEE couverts par EARS-Net/ESAC-Net, bactéries/antibiotiques du panel de surveillance, 1998-2019. Liste précise des pays à confirmer par profilage réel (séance 2). Exclu : données patients individuelles, santé animale, hors Europe, temps réel |
| Fréquence utile | Annuelle |

> **Mise à jour (séance 2, après profilage) :** le périmètre pays est
> maintenant confirmé par les vrais volumes de données. Les 15 pays retenus
> sont ceux avec le plus de lignes et une couverture continue 1999/2001-2019 :
> France, Netherlands, Greece, Hungary, Spain, Czech Republic, Austria,
> Belgium, Germany, Slovenia, Italy, Portugal, Croatia, Slovakia,
> United Kingdom. Les 14 pays restants (ex. Luxembourg avec seulement
> 12 lignes, Romania avec 57) sont exclus car trop peu représentés pour une
> analyse fiable. Cette décision, prévue comme "à confirmer" dès l'étape 1,
> s'appuie maintenant sur des chiffres réels plutôt qu'une estimation.

## Étape 2 — Cas d'usage et KPI

| Cas d'usage | KPI | Données nécessaires | Fréquence |
|---|---|---|---|
| Comparer le taux de résistance entre pays | Taux de résistance moyen par pays et par bactérie (%) | pays, année, pathogène, antibiotique, % résistant | Annuelle |
| Suivre l'évolution de la consommation | DDD pour 1000 habitants, par pays et par an | pays, année, classe ATC, secteur, DDD | Annuelle |
| Croiser consommation et résistance | Corrélation consommation ↔ % résistance par pays | pays, année (jointure des deux fichiers) | Annuelle |

## Étape 3 — Sources

| Critère | Source A — résistance | Source B — consommation |
|---|---|---|
| Producteur et URL | ECDC/TESSy via Zenodo — zenodo.org/records/14224680 | Idem, même dépôt |
| Mode d'accès | Téléchargement HTTP direct, sans authentification | Idem |
| Format | CSV, UTF-8 (2,5 Mo) | CSV, UTF-8 (1,4 Mo) |
| Fréquence de mise à jour | Version unique (v1, 26/11/2024), snapshot figé 1998-2019 | Idem |
| Clé | (year, country, pathogen, antibiotic, patientType) | (year, country, class, sector) |
| Licence | Zenodo Open Access (DOI 10.5281/zenodo.14224680) | Idem |
| Risque technique | Fichier statique volumineux, pas de panne de service | Idem, plus léger |
| Données personnelles | Aucune, agrégé pays/année | Aucune |

Fichier utilisé en priorité (séance 1-2) : `summary_AMR_filtered.csv` (résistance).
Fichier secondaire (jointure ultérieure) : `summary_AMC_byclass.csv` (consommation).

## Étape 4 — Grain et schéma

Une ligne représente le taux de résistance observé pour une combinaison unique
{année, pays, bactérie, antibiotique testé, type de patient} en Europe,
entre 1998 et 2019.

Clé métier : `(year, country, pathogen, antibiotic, patient_type)`

| Champ | Type | Obligatoire |
|---|---|---|
| year | integer | Oui |
| country | string | Oui |
| pathogen | string | Oui |
| antibiotic | string | Oui |
| patient_type | string | Oui |
| resistance_rate | number | Oui |
| n_tested | integer | Oui |
| pathogen_long | string | Non |
| antibiotic_long | string | Non |
| antibiotic_class | string | Non |

## Étape 5 — Architecture

```
[Source A: Zenodo/ECDC-TESSy]        [Source B: Zenodo/ECDC-TESSy]
 summary_AMR_filtered.csv             summary_AMC_byclass.csv
        |                                     |
        v                                     v
 [Collecteur A]                        [Collecteur B]
        |                                     |
        v                                     v
 [Zone RAW]                             [Zone RAW]
        |                                     |
        v                                     v
 [Validation A]                        [Validation B]
    |      |                              |      |
    v      v                              v      v
[Rejetés][Curated A]               [Rejetés][Curated B]
              \                          /
               \________________________/
                          v
                    [Jointure (country, year)]
                          v
                  [Curated finale]
                          v
              [Application / restitution]
```

Ordre d'implémentation retenu : pipeline A (résistance) complet de bout en
bout d'abord, jointure avec B ensuite si le temps le permet.

## Étape 6 — Contrat de données

Voir `config/data_contract.yaml`.

## Étape 7 — Première collecte brute

Voir `src/collect.py` et `data/raw/`. Premier fichier brut obtenu :
`amr_resistance_20260924T091940Z.csv` (2 459 135 octets, 11 877 lignes),
collecté le 24/09/2026 via le collecteur configurable, sans intervention
manuelle sur le contenu.

**Note (séance 2, profilage) :** la colonne source `N_tested` est vide à 100%
sur l'ensemble du fichier. Le nombre réel de souches testées est contenu dans
la colonne `N`. Le mapping vers notre champ `n_tested` a été corrigé en
conséquence.