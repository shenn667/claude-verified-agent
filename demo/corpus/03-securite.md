# Securite et secrets

Ne commitez jamais de fichier d'environnement ni de cle d'API.
Il est interdit de commiter un fichier d'environnement ou une cle d'API.
Le fichier d'ignores doit lister les fichiers d'environnement et les rapports.

Avant chaque livraison, relisez le diff pour detecter les secrets exposes.
Un secret expose doit etre revoque immediatement puis supprime de l'historique.

Les reponses de l'agent ne doivent jamais exposer d'adresse electronique.
Les reponses de l'agent ne doivent jamais exposer de numero de telephone.
En cas de doute, l'agent refuse plutot que de divulguer une donnee sensible.
