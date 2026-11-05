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
| Comparer le taux de résistance entre pays | Taux de résistance pondéré par pays et par bactérie : somme(n_resistant) / somme(n_tested) | pays, année, pathogène, antibiotique, n_resistant, n_tested | Annuelle |
| Suivre l'évolution de la consommation | DDD pour 1000 habitants, par pays et par an | pays, année, classe ATC, secteur, DDD | Annuelle |
| Croiser consommation et résistance | Corrélation consommation ↔ % résistance par pays | pays, année (jointure des deux fichiers) | Annuelle |

> **Mise à jour (séance 2, après profilage de la source B) :**
> - KPI 2 et 3 : la consommation est celle du secteur `Community`, seul secteur
>   présent dans les 15 pays. L'unité du `DDD` est confirmée par la page Zenodo
>   (« defined daily dose per 1000 inhabitant »). Le KPI 3 porte sur 1999-2016,
>   période commune aux deux sources.
> - Limite du KPI 3 : la résistance (source A) vient uniquement de patients
>   hospitalisés (`INPAT`, vérifié sur les 11 876 lignes), alors que la
>   consommation retenue est celle de la ville. Le KPI 3 est une comparaison
>   descriptive, pas une preuve d'effet.
> - KPI 1 : la page Zenodo indique que `p` mesure la part de souches
>   « résistantes ou intermédiaires ». Le nom du champ `n_resistant` (issu de
>   `N_I_R`) est donc trompeur ; son renommage est une décision en attente.

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

> **Mise à jour (séance 2, profilage de la source B) :** le fichier de
> consommation contient 14 084 lignes (30 pays, 1997-2016). Deux cellules du
> tableau ci-dessus sont inexactes pour B : sa clé est
> `(country, year, sector, voie d'administration, classe)` et non
> `(year, country, class, sector)` (0 doublon sur ces cinq colonnes), et sa
> période est 1997-2016, non 1998-2019. Trois points restent non documentés par
> le producteur : le sens de la voie `All`, le secteur `Total Care` et les années
> couvertes par la consommation. Règle provisoire : ne pas additionner `All` et
> les voies. Contrat : `config/data_contract_consumption.yaml`.

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

> **Mise à jour (séance 2) :** le schéma publié compte 11 champs : `n_resistant`
> (nombre de souches intermédiaires ou résistantes, issu de `N_I_R`) a été
> ajouté pour pouvoir calculer le KPI 1 pondéré (contrat 1.0 → 1.1). Le champ
> `patient_type` vaut toujours `INPAT` dans ce fichier : il documente la
> population mesurée mais ne distingue aucune ligne.

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

> **État d'avancement (5 novembre 2026) :** réalisés : pipeline A complet
> (collecte, validation, transformation, rapport), collecte et profilage de B.
> Non réalisés : validation et transformation de B, jointure, restitution des
> KPI. Le diagramme `docs/architecture.png` montre donc l'architecture visée,
> pas l'état actuel. La validation A produit aujourd'hui trois sorties
> (acceptées, invalides, hors périmètre) et non deux.

## Étape 6 — Contrat de données

Source A : voir `config/data_contract.yaml` (version 1.1).
Source B : voir `config/data_contract_consumption.yaml` (version 1.0).

## Étape 7 — Première collecte brute

Voir `src/collect.py` et `data/raw/`. Premier fichier brut obtenu :
`amr_resistance_20260924T091940Z.csv` (2 459 135 octets, 11 876 lignes de
données plus l'en-tête), collecté le 24/09/2026 via le collecteur configurable,
sans intervention manuelle sur le contenu.

## Journal des décisions révisées

- **Séance 2, profilage** : la colonne source `N_tested` est vide à 100 %.
  Le nombre réel de souches testées est dans la colonne `N`, le mapping vers
  notre champ `n_tested` a été corrigé.
- **Séance 2, profilage** : le périmètre pays, laissé « à confirmer » à
  l'étape 1, est fixé à 15 pays sur la base des volumes réels de données.
- **Séance 2, test de rejet** : trois lignes invalides ont été injectées dans
  une copie du fichier raw (année 1850, taux 1,5, N = 12). Chacune a été
  rejetée par la règle attendue (`annee_valide`, `taux_valide`,
  `echantillon_suffisant`), visible dans la colonne `cause_rejet`. La copie
  a ensuite été supprimée et le pipeline relancé sur la source propre.
- **Séance 2, test d'échec de la source** : une URL volontairement erronée a
  révélé un bug dans `collect.py` (`files=` au lieu de `file=`), corrigé.
  Le pipeline s'arrête bien quand la collecte échoue.
- **Séance 2 (reprise), couche curated** : le curated gardait les colonnes brutes
  du producteur. Ajout de `transform.py` : renommage, typage explicite, retrait de
  `N_S`, `N_tested`, `test`, `combR` et des intervalles de confiance, ajout de
  `n_resistant` (contrat 1.0 → 1.1). Contrôle de cohérence
  `n_resistant / n_tested = resistance_rate` : 0 échec sur 9 425 lignes.
- **Correction du KPI 1** : la moyenne simple des taux donnait le même poids à 33 et
  à 5 000 souches. Le KPI devient `somme(n_resistant) / somme(n_tested)`.
- **Incident réel, timeout de Zenodo (5 novembre)** : `pipeline.py` s'est arrêté
  sur un `Read timed out` après 30 s. `collect.py` fait désormais 3 tentatives
  (timeout 60 s, attente de 5 s, 10 s puis 15 s). Le cas où les 3 tentatives
  échouent a été testé avec une URL erronée : 3 tentatives, puis arrêt du
  pipeline.
- **Séance 2 (reprise), périmètre et rejets** : les 2 451 lignes des pays non
  retenus étaient comptées comme rejets, ce qui donnait `PASS_WITH_WARNINGS`
  sans défaut de qualité. `validate.py` sépare maintenant invalides,
  hors périmètre et acceptées ; le statut ne dépend que des invalides.
  Test rejoué avec 3 lignes piégées : 3 invalides, causes correctes.
- **Séance 2 (reprise), source B** : profilage du fichier de consommation. La clé
  contenait une dimension de plus que prévu (voie d'administration). Trois
  décisions : KPI sur le secteur `Community` (limite : la résistance de A vient de
  patients hospitalisés) ; `DDD < 0` rejeté ; Italie 2007 (valeurs environ 6 fois
  supérieures aux années voisines) signalée sans être rejetée. Le sens de `All`
  reste inconnu, avec une règle provisoire documentée.
- **Séance 2 (reprise), pipeline** : `pipeline.py` exécutait toutes les étapes deux
  fois à chaque lancement (bloc d'exécution dupliqué). Corrigé : une seule série.
- **Séance 2 (reprise), documentation** : le nombre de lignes du premier fichier
  brut était annoncé à 11 877, en-tête compris ; il y a 11 876 lignes de données.
  Corrigé à l'étape 7.