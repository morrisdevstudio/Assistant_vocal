# Alfred — hébergement et interfaces Home Assistant

Décisions corrigées le 29 octobre : nouvelle liste familiale dans HA ; calendriers
personnels HA pour les rappels ; minuteurs stockés et programmés par Alfred.
Les autres choix de ce document sont des propositions de préparation ; aucun
service distant, compte, VM ou liste n'a été créé ou modifié pendant l'inspection.

## Constats en lecture seule

Sources : inventaire du projet Serveur et MCP Home Assistant.

- Serveur : Pentium Gold G7400, 32 Go déclarés, Proxmox.
- À 18:46 Europe/Paris, capteurs HA du nœud : CPU environ 7 %, mémoire libre
  environ 6,83 GB, mémoire utilisée environ 77 %. Mesure ponctuelle, pas une
  réservation ni une observation de charge maximale ; cache et mémoire récupérable
  non détaillés par cette lecture.
- VM Docker 103 : environ 0,71 GB libre selon HA. Ne pas y ajouter les moteurs
  vocaux sans lecture système et réévaluation.
- Le capteur disque de 103 annonce 0 % utilisé : ne pas en déduire qu'il est vide.
  Vérifier les systèmes de fichiers, le stockage Proxmox et les instantanés avant
  de choisir la destination d'un nouveau disque.
- Music Assistant est chargé dans HA.
- Deux listes existent déjà : `todo.super_u` et `todo.google_keep_liste_de_course`.
  Leurs noms et capacités ont été lus, pas leurs articles. Elles ne seront ni
  fusionnées ni modifiées : l'utilisateur choisit une nouvelle liste familiale.

## Hébergement proposé le 27 novembre 2026

La cible validée reste la VM Debian dédiée sur l’AuBox sous Proxmox. Point de
départ proposé pour cette VM : **4 vCPU, 8 Gio de RAM et 64 Gio de disque**,
avec les moteurs vocaux sur CPU. Vérifier l’espace physique disponible et la
charge habituelle de l’AuBox avant allocation. Les relevés ci-dessus concernent
le serveur historique. Valider le dimensionnement au cours des essais vocaux.

### Installation directe dans Debian

Le constructeur et l’installeur Debian sont dans `deploy/debian/`. Voir
`deploy/debian/README.md` pour produire un paquet depuis une révision Git,
configurer la voix une fois sur chaque hôte et effectuer les mises à jour.
L’installation et les mises à jour peuvent passer par le paquet APT
`alfred-home`. Le dépôt GitHub est public à la demande de l’utilisateur du
27 novembre. L’index APT signé est servi directement par GitHub Releases
depuis `v0.6.0`, avec un tag précis en dev et l’URL Latest en prod. Installer
une fois l’asset `alfred-home.sources` sur la VM après sa création. Le miroir
LAN reste disponible.

Proposition pour commencer : un service `systemd` sous un compte dédié et un
script d’installation commun au dev et à la prod. Vérifier que le serveur de
dev offre une cible Debian 13 `amd64` comparable. Construire une archive
versionnée avec le code, le worker Parakeet Linux et la PWA compilée si elle
est utilisée. Tester la même archive en dev avant la promotion en prod.
Verrouiller les dépendances Linux et recréer les environnements Python sur
chaque cible. Installer les modèles versionnés séparément de l’archive.

Préparer la nouvelle version à côté de la version active. Conserver les
données SQLite, les réglages et les secrets propres à chaque hôte hors des
répertoires de version. Avant la mise à jour en prod, sauvegarder les données,
activer la nouvelle version et vérifier l’API puis la transcription et la
synthèse. Conserver la version précédente et vérifier la compatibilité des
données avant tout retour arrière. Pour l’ESP32, `media_host` peut rester l’IP
LAN réservée de la VM, comme le prévoit la configuration actuelle.

### Variante Docker Compose

Docker Compose est une proposition pour les deux instances demandées, sur le
serveur de dev et dans la VM de prod. Construire une image Linux `amd64` par
révision, la tester en dev, puis promouvoir exactement son digest en prod.
Un registre privé, par exemple GHCR, permettrait le transfert entre hôtes.
Prévoir un Compose commun avec une configuration par environnement et une
promotion explicite de la version testée. Utiliser le digest précédent en cas
de retour arrière et vérifier la compatibilité des données avant de relancer.

Un conteneur Alfred par instance suffit au départ. Il embarque l’API,
l’ordonnanceur, le binaire Linux Parakeet et le runtime Phonon. Alfred garde
ses workers vocaux existants et leur préchargement. La construction multiétape
compile le Rust et, si la PWA est retenue, produit les fichiers statiques avec
Node. Le service final s’exécute avec un compte sans privilèges. Mettre en
cache les téléchargements et dépendances de build entre les révisions.
Traiter openWakeWord en option et recetter d’abord le réveil Parakeet sur Linux.

Les instances ont des données SQLite, des réglages et des secrets distincts.
Les poids des modèles peuvent être montés en lecture seule depuis un dossier
versionné, avec une référence exacte à vérifier lors du démarrage. Conserver
les profils de voix privés dans le stockage local de chaque environnement.
Monter `.local/data` et `.local/models` séparément pour préserver `.local/bin`
dans l’image, à l’emplacement attendu par le lanceur Parakeet. Exclure `.local`
du contexte de construction. La configuration actuelle de Vite lit les fichiers
TLS dès le chargement : séparer cette configuration de la compilation statique
pour éviter de fournir des clés privées au build.
Utiliser en dev un environnement Home Assistant de test ou des services
simulés et laisser le satellite de production à la prod. La qualification de
la PWA inclut HTTPS et le routage de ses API autorisées.

Le champ `media_host` de l’ESP32 sert à la fois d’adresse d’écoute du serveur
audio et d’adresse annoncée à la carte. Sur Docker Engine Linux, le mode réseau
`host` est la première option à recetter avec l’adresse LAN réservée de la VM,
en limitant les accès par pare-feu. Pour garder un réseau Docker `bridge`,
prévoir une adresse d’écoute distincte de l’adresse LAN annoncée, puis vérifier
le flux de lecture ESP32 de bout en bout. Avant la bascule, mesurer le temps
jusqu’au premier son, la mémoire et la CPU avec les autres charges de l’AuBox.

## Propriété des données proposée

| Donnée ou fonction | Référence proposée | Consommation par l'autre système |
|---|---|---|
| Appareils, pièces, étages, états | HA | Alfred lit les registres et états autorisés |
| Courses familiales | HA — choix validé | Alfred consulte et modifie cette même liste |
| Musique et catalogue Qobuz | Music Assistant | Alfred appelle les commandes adaptées |
| Profils, permissions, souvenirs | Alfred | Aucun souvenir privé exporté dans les états HA |
| Rappels personnels | Calendriers HA — choix corrigé | Alfred lit et modifie ; mécanisme de déclenchement à concevoir |
| Rappels familiaux | `calendar.familial` dans HA | Alfred lit et modifie ; déclenchement à concevoir pour les seuls rappels identifiés |
| Minuteurs | Alfred — choix validé | Consultation et commandes dans HA ; mécanisme à concevoir |
| Annonces et sessions vocales | Alfred | Déclenchement depuis HA à concevoir |

Liste créée le 29 octobre : intégration native **Local to-do**, nom affiché
« Courses Alfred », identifiant vérifié `todo.courses_alfred`. HA est l'unique stockage de référence,
pas une copie synchronisée avec une seconde liste SQLite.

## Interfaces proposées

- Connexion applicative Alfred → HA par API authentifiée, distincte du MCP utilisé
  par l'agent de développement. Ne pas réutiliser implicitement ses identifiants.
- WebSocket HA pour états et appels d'actions ; `subscribe_entities` pour suivre
  les entités choisies, `call_service` pour les actions. Relecture après reconnexion.
  Références de pièces/étages issues des registres, pas de noms dupliqués à la main.
- Courses : API `todo.get_items`, `todo.add_item`, `todo.update_item` et
  `todo.remove_item`, en fonction des opérations validées et des capacités de la
  liste. Utiliser les UID des articles existants ; distinguer articles homonymes.
  Une réponse perdue ne doit pas provoquer un ajout rejoué aveuglément.
- Ne pas annoncer un succès sur simple envoi de requête : examiner son résultat
  et, si approprié, relire l'état ou les articles. En cas de déconnexion HA, signaler
  l'échec sans inventer l'état ni mettre en cache une écriture comme accomplie.
- Tous les outils passent par les permissions d'Alfred avant exécution. Les jetons
  restent côté serveur, hors navigateur, prompts, dépôt et journaux.
- Un compte HA dédié est une proposition ; ne pas promettre une restriction fine
  par entité avec un simple jeton HA. Vérifier les droits réellement nécessaires
  pour les registres et actions avant de fixer le compte.
- Les appels Music Assistant, l'atténuation/restauration de l'ampli et le retour
  HA → Alfred pour rappels/annonces demandent encore une inspection spécifique.
  Ne pas installer une intégration personnalisée ou MQTT par défaut.

## Critères pour clore cette préparation

- Hôte, stockage et ressources mesurés puis cible choisie ; pas seulement les
  valeurs ponctuelles HA.
- Calendriers HA des rappels à choisir ; méthode de déclenchement et exposition des
  minuteurs Alfred dans HA encore à choisir.
- Liste Courses Alfred créée et identifiant vérifié ; ajout et lecture réels d'un
  article temporaire réussis depuis Alfred, puis retrait et contrôle de la liste vide.
  Test de modification et parcours interface/micro encore à réaliser.
- Client applicatif testé avec reconnexion, erreur HA et refus de permissions,
  sans fuite de secrets. Tests réels distincts des mocks locaux.

Sources officielles consultées :
<https://contributors.home-assistant.io/core/internals/websocket-api/>,
<https://www.home-assistant.io/integrations/todo/>,
<https://www.home-assistant.io/integrations/shopping_list/>.
