# Deploiement et environnements

Le deploiement de previsualisation se fait avec la commande de previsualisation.
Chaque branche obtient une URL de previsualisation pour valider le build.

La production exige une approbation ecrite explicite avant tout deploiement.
Ne jamais deployer en production sans cette approbation.

Ne jamais merger sur main sans revue.
La revue verifie le build local, les tests et l'absence de secrets.

Un build local reussi est obligatoire avant d'ouvrir une revue.
La commande de build doit passer sans erreur.
