# Projet AWS - Notre Console Cloud Autonome (Parties 1 & 2 unifiées)

L'objectif ici était de créer un outil d'administration complet et autonome. Au lieu d'utiliser un framework tout fait, tout le site est propulsé par un **serveur web natif en Python** (`http.server`) qui communique en temps réel avec Amazon grâce au SDK `boto3`. 

Une seule page, aucun rechargement inutile, et une interconnexion totale entre la partie Réseau et la partie Machines Virtuelles.

---

## Ce que fait l'application

Pour rendre la démonstration propre et éviter de polluer l'écran avec les ressources par défaut du Learner Lab AWS, **l'application démarre sur une "Page Blanche"**. Elle filtre le bruit de fond d'AWS pour n'afficher **que ce que vous créez** via l'interface.

### Partie 1 : EC2
* **Déploiement propre :** Lancement d'instances adaptées aux quotas du Lab.
* **Aiguillage automatique :** Vous choisissez l'OS (Amazon Linux, Ubuntu, Debian) et le script s'occupe de trouver le bon ID d'image (AMI) correspondant.
* **Le lien avec le réseau (Variabilisation) :** Impossible de lancer une machine dans le vide. Le formulaire vous force à sélectionner l'un des sous-réseaux que vous avez créés dans la Partie 2.
* **Contrôle total :** Des boutons pour Arrêter, Redémarrer et Supprimer (`terminate`) chaque machine.

### Partie 2 : Le coin Réseau (VPC & Sous-réseaux)
* **Réseau sur-mesure :** Création de VPC personnalisés en tapant une plage IP (ex: `10.0.0.0/16`).
* **Découpe des sous-réseaux :** Création de Subnets rattachés au VPC de votre choix (ex: `10.0.1.0/24`).
* **Le Bonus :** Un bouton pour générer des passerelles Internet (IGW).
* **La suppression en cascade :** AWS refuse d'effacer un VPC s'il reste des choses dedans. Notre bouton "Supprimer VPC" intègre un script intelligent : il va d'abord scanner le VPC, supprimer proprement les sous-réseaux et les tables de routage cachées, puis détruire le VPC d'un coup. Plus de blocages !

---

## Comment lancer la démo en 3 étapes

### 1. Les clés d'accès
Avoir ses identifiants AWS Académie à jour dans le fichier local habituel (`~/.aws/credentials`). *Sécurité oblige : ce dossier est protégé par notre `.gitignore` et ne sera jamais publié sur ce dépôt public.*

### 2. Allumer le moteur
Ouvrez votre terminal dans ce dossier et lancez le script :
```bash
python app.py
