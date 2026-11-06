# Grille RGPD d'AntibioSentinelle

## 1. Quelles données ?
Les données sont des chiffres agrégés par pays et par année : le nombre de souches testées et résistantes (resultat_resistance) et les DDD pour 1 000 habitants (consommation). Des tables de référence s'y ajoutent (pays, bactérie, antibiotique, classe, secteur, voie). Aucune colonne ne renvoie à une personne physique identifiée ou identifiable. Ce sont des données agrégées et anonymes, donc hors du champ du RGPD : ce ne sont pas des données personnelles.

Ce ne sont pas non plus des données de santé au sens du RGPD. Une donnée de santé doit concerner la santé d'une personne. Ici, une souche ou un DDD se fond dans le total d'un pays entier.

## 2. Quelle finalité ?
L'étude compare 15 pays européens entre 1999 et 2016. Elle met en regard deux séries : la consommation d'antibiotiques en ville (Community), mesurée en doses définies journalières par classe ATC, et le taux de résistance des bactéries testées à l'hôpital, pondéré. L'objectif est de décrire le lien entre ces deux variables, pays par pays et année par année. La comparaison est descriptive et non causale : elle ne prouve pas que la consommation provoque la résistance. Le cadre est pédagogique (cours ESEO).

## 3. Quelle base légale ?
Aucune base légale n'est requise : le projet ne traite pas de données personnelles, donc l'article 6 du RGPD ne s'applique pas. Les données viennent d'un jeu publié en accès ouvert sur Zenodo (« The Evolution of Antibiotic Resistance in Europe, 1998-2019 », issu de l'ECDC). La page Zenodo n'indique pas de licence précise. La réutilisation dépend donc des conditions du jeu, pas du RGPD. Le jeu est cité avec son DOI (10.5281/zenodo.14224680).

## 4. Quelle durée ?
La base SQLite est supprimée puis reconstruite à chaque exécution. Elle n'est pas versionnée (`data/*.db` est dans .gitignore).

Les CSV (raw, curated, rejected) et les rapports JSON (`reports/`) sont versionnés dans Git. Ils restent donc dans l'historique du dépôt même si on les supprime plus tard.

Aucune durée limite ne s'impose, puisque ces fichiers ne visent aucune personne. À la fin du module, le dépôt peut être archivé ou supprimé, sauf le livrable rendu.

## 5. Quels droits ?
Le jeu de données ne contient aucune personne. Aucun droit d'accès, de rectification, d'opposition, d'effacement ou de portabilité n'est donc à ouvrir.

La seule personne concernée par le projet est l'auteur. Il garde la maîtrise de ses propres traces (voir 6). Si des données individuelles étaient ajoutées un jour, il faudrait pouvoir retrouver, corriger et supprimer les lignes d'une personne, et le schéma devrait être revu.

## 6. Quels risques ?
La ré-identification par croisement n'est pas réaliste ici. Le plus petit agrégat compte au moins 30 souches (`n_tested >= 30`), à l'échelle d'un pays, sans âge, sans sexe, sans ville ni date précise à croiser.

Les seules données personnelles du dépôt sont le nom et l'adresse e-mail personnelle de l'auteur, inscrits dans chaque commit Git (Gareth Tchoula, garethtchoula@gmail.com).

Le dépôt est public : cette adresse est donc visible de tous. Une réponse possible serait d'utiliser l'adresse `noreply` de GitHub pour les prochains commits. Les anciens commits la gardent tant que l'historique n'est pas réécrit.

Hébergement : le code est sur GitHub (Microsoft, États-Unis), dont les garanties de transfert sont à vérifier dans ses conditions. La copie de travail est sur OneDrive (Microsoft). Les sources sont sur Zenodo (CERN, Genève). Aucun de ces services ne contient de données sur des personnes, en dehors de l'identité de l'auteur.

Accès : seul l'auteur modifie le dépôt.