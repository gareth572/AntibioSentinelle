# Pitch de 3 minutes : AntibioSentinelle

Structure du sujet : 30 s (besoin et contrainte), 60 s (trajet de la donnée), 45 s (choix structurants), 30 s (qualité, sécurité, observabilité), 15 s (limite principale). Le texte compte environ 390 mots : à chronométrer à voix haute.

## 1. Besoin et nouvelle contrainte (30 secondes)

AntibioSentinelle aide à décider quels pays et quelles classes d'antibiotiques cibler pour une campagne de bon usage. Elle compare la résistance bactérienne à l'hôpital et la consommation d'antibiotiques en ville, pour 15 pays européens. La nouvelle contrainte : un rapport mis à jour chaque jour, par une seule personne, sans serveur à surveiller. La question est donc : quelle architecture, avec le niveau de complexité le plus juste ?

## 2. Le trajet de la donnée (60 secondes)

Deux fichiers CSV publiés par l'ECDC sur Zenodo : la résistance, 11 876 lignes, et la consommation, 14 084. Un collecteur les télécharge, avec trois tentatives en cas de panne, et garde une copie brute horodatée. La validation applique des règles de qualité écrites dans des contrats de données : les lignes invalides sont rejetées avec leur cause, les lignes hors périmètre sont mises à part. Il reste 9 425 lignes de résistance et 7 029 de consommation. Elles sont transformées, puis chargées dans une base SQLite qui impose des contraintes d'intégrité. Trois indicateurs sont calculés en SQL, dont le croisement consommation et résistance par pays, année et classe. Un rapport JSON est produit à chaque exécution. Le tout prend moins de vingt secondes.

## 3. Les choix structurants (45 secondes)

Je retiens le batch : les sources sont annuelles et personne n'a besoin d'une réponse en quelques secondes, donc ni streaming ni Kafka. Je retiens SQL plutôt que NoSQL : les données sont tabulaires, il faut croiser deux sources, un GROUP BY suffit et la base garantit l'intégrité. Pour les couches : une zone raw, un warehouse et un mart sous forme de vue SQL. J'ai comparé trois options : simple, cible et évolutive. La cible ajoute à la version simple une porte qualité, un contrôle final automatique et un planificateur. L'évolutive, avec orchestrateur et serveur, serait disproportionnée pour 16 000 lignes et une personne.

## 4. Qualité, sécurité, observabilité (30 secondes)

Qualité : l'objectif est moins de 2 % de lignes invalides ; aujourd'hui, zéro pour la résistance et 0,01 % pour la consommation. Observabilité : un rapport par exécution avec les lignes, les rejets, la durée et le statut, et un incident réel, une panne de la source, repris par les tentatives. Sécurité : aucune donnée personnelle, dépôt public en lecture, écriture par moi seul, contrats versionnés.

## 5. La limite principale (15 secondes)

Ma limite principale : le sens des données. La voie d'administration « All » est ambiguë, et le croisement hôpital et ville est descriptif, pas causal. Et les ajouts de l'architecture cible ne sont pas encore codés.

---

# Réponses aux questions possibles

**Pourquoi ne pas garder l'architecture de la séance 2 ?** Elle n'a pas de planification, son statut qualité ne bloque rien (`FAIL` seulement si aucune ligne n'est acceptée), les contrôles d'intégrité sont lancés à la main et les rapports sont écrasés à chaque exécution.

**Pourquoi SQL ou NoSQL ?** Les données sont tabulaires, avec des jointures entre deux sources et des contraintes d'intégrité. Un document JSON répéterait pays, année et classe, et le KPI par bactérie obligerait à parcourir tous les documents.

**Votre projet a-t-il vraiment besoin d'un Data Lake ?** Non. Ma zone raw est un dossier de fichiers horodatés avec des contrats pour seul catalogue : je ne l'appelle pas Data Lake. Je garde la zone raw et le warehouse.

**Quelle donnée alimente le Data Mart ?** Les deux tables de mesures du warehouse (consommation et résistance), jointes sur pays, année et classe, dans une vue SQL qui donne les KPI.

**Que se passe-t-il si la source est indisponible ?** Le collecteur fait trois tentatives, puis le pipeline s'arrête. Les fichiers raw précédents restent intacts. Le cas s'est produit le 5 novembre (timeout de Zenodo).

**Comment évitez-vous les doublons ?** Clé métier unique ; déduplication entre exécutions avec le fichier consolidé (le rapport affiche `duplicates_removed` = 9 425 : ce sont les lignes déjà vues, donc la preuve que le rejeu n'ajoute rien) ; contrainte `UNIQUE` en SQL ; base reconstruite à chaque exécution.

**Quelle brique supprimeriez-vous en premier pour réduire le coût ?** Le planificateur : si les sources restent annuelles, un lancement manuel suffit. C'est l'exigence de mise à jour quotidienne qui le justifie.
