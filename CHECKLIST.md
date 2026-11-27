# Alfred — checklist de mise en place

- [x] **A34 — Créer le dépôt GitHub privé et vide d’Alfred.**
  Dépôt morrisdevstudio/Assistant_vocal créé le 23 novembre 2026.
  Lecture des issues vérifiée, conservation par défaut de sept jours confirmée
  et politique inscrite dans AGENTS.md local.
- [ ] **A35 — Préparer la première publication et la vérification des pull requests.**
  Première publication effectuée le 23 novembre 2026 sur main, commit bb7070d.
  Visibilité privée et 225 fichiers vérifiés sur GitHub. Adresses locales retirées,
  installation locale du modèle documentée. 957 tests Python et 65 tests JavaScript
  réussis, deux tests Python ignorés, compilation de l'interface réussie.
  La création d'une pull request reste à vérifier lors d'une vraie modification.
  **Dépend de A34.**

- [x] **A33 — Ajouter les effets LED du satellite par état.**
  Fixe, Rotation, Comète, Respiration et Balayage selon les capacités
  annoncées par la carte. Palettes existantes conservées en Fixe.
  Build, 18 tests UI, 63 tests Python ciblés. Chromium à 1 366 et 390 px :
  Rotation enregistrée en veille éteinte, activée et confirmée par la
  carte après allumage, puis retour au réglage précédent et à l’extinction.
  **Dépend de : A32.**

- [x] **A32 — Éteindre les LED en veille et choisir leurs couleurs par état.**
  Veille, Écoute, Traitement, Réponse parlée et Erreur dans les paramètres
  vocaux de la PWA. Palette serveur, anneau éteint par défaut au repos,
  priorité aux indications natives. Aucun flashage. Chromium à 1 366 px
  et 390 px : couleur enregistrée, allumage confirmé par la vraie carte,
  puis extinction restaurée. Vérification visuelle d’un dialogue complet
  sur place à suivre en A04. **Dépend de : A11, A31, T04.**

- [x] **A31 — Activer le mode dialogue sur demande de réponse.**
  PWA, laboratoire et ESP32. Huit secondes à la fin de la lecture pour les
  confirmations et précisions. Après une réponse complète, fermeture de la prise
  et retour du satellite à sa veille si elle est active. Le silence ne crée
  aucun nouvel appel. PWA vérifiée dans Chromium avec micro et API simulés
  pour une commande terminée, une attente silencieuse et une réponse parlée.
  Build PWA, 50 tests JS et 923 tests Python réussis, deux ignorés. Après
  redémarrage, PWA et API HTTP 200, ESP32 reconnecté et micro/détecteur sains.
  Recette acoustique sur le satellite à suivre en A04. **Dépend de : A11, T04.**

- [x] **A30 — Simplifier les types d’éclairage.** Deux choix, Principal et
  Secondaire. Principal par défaut. Relire les anciens réglages Ambiance
  en Secondaire. Build, 18 tests UI et 316 tests backend ciblés réussis.
  PWA et laboratoire vérifiés dans Chromium à 1 366 et 390 px. Après relance,
  les 14 lumières du catalogue réel étaient de type Principal.
  **Dépend de : A29.**

- [x] **A29 — Distinguer les lumières principales et d’ambiance.**
  Type par lumière et groupe dans la PWA et le laboratoire. Allumage par
  défaut des principales, extinction et lecture des deux, commandes explicites
  par type ou nom. Héritage, sauvegarde et ciblage vérifiés avec Home Assistant
  simulé. Chromium à 1 366 et 390 px dans les deux interfaces, édition et
  persistance sur API simulée. Build, 18 tests UI, 922 tests backend réussis,
  deux ignorés. Service relancé et catalogue réel contrôlé en lecture.
  **Dépend de : A14, F01, F34.**

- [x] **A28 — Proposer les pièces locales dans le sélecteur des appareils.**
  Afficher les pièces de ce navigateur comme « Toilettes du haut » et
  enregistrer l’affectation dans Alfred. Build, 18 tests UI et 57 tests backend
  réussis. Chromium à 1 366 et 390 px avec affectation simulée. Serveur relancé
  et schéma de l’API confirmé. **Dépend de : A25, A27.**

- [x] **A27 — Actualiser le sélecteur de pièces dans la fiche d’appareil.**
  Reprendre les libellés personnalisés dans Alfred et relire le registre à
  l’ouverture. Conserver la référence Home Assistant pour l’enregistrement.
  Build et 18 tests UI réussis. Chromium à 1 366 et 390 px : renommage dans
  Alfred, nouvelle entrée du registre et affectation API simulée vérifiés.
  **Dépend de : A19, A25.**

- [x] **A26 — Afficher l’étage des pièces Home Assistant.** Réutiliser le registre
  déjà lu, afficher le nom de l’étage, préremplir un étage compatible au premier
  réglage et conserver les choix locaux. Build, 18 tests UI et 16 tests du
  catalogue réussis. Service relancé. Vérifié dans Chromium à 1 366 et 390 px :
  10 pièces avec étage sur 12 dans le registre réel, préremplissage,
  étage absent et priorité locale. **Dépend de : A24, A25.**

- [x] **A25 — Personnaliser dans Alfred les pièces issues de Home Assistant.**
  Crayon, nom et étage locaux, pièce affectable au navigateur et aux satellites,
  conservation de la référence d’origine après renommage. Build et 17 tests UI
  réussis. Édition, annulation, rechargement, affectation du navigateur, retrait
  et rétablissement vérifiés dans Chromium à 1 366 et 390 px sur le registre
  réel en lecture. **Dépend de : A24.**

- [x] **A24 — Afficher les pièces Home Assistant dans le bloc Pièces.**
  Réutiliser le registre déjà lu par le catalogue. Afficher les pièces sans
  entité exposée, rapprocher les noms communs et conserver les réglages locaux.
  Build et 16 tests UI réussis. Les 12 pièces du registre réel et la fusion
  avec Bureau ont été vérifiées dans Chromium à 1 366 et 390 px.
  Indisponibilité et actualisation vérifiées sur réponses simulées.
  **Dépend de : A17, A22.**

- [x] **A23 — Améliorer la présentation des pièces de la PWA.** Cartes espacées,
  icône, compteur et état déplié visible. Recherche et filtres dans un même
  panneau. Build et 16 tests UI réussis. Catalogue réel vérifié dans Chromium
  à 1366 et 390 px dans les deux thèmes. Recherche, tri, clavier et édition
  simulée vérifiés après la remise en forme.
  Les cinq panneaux sont alignés sur la largeur du catalogue, vérifié
  dans Chromium à 1 366, 1 920 et 390 px.
  **Dépend de : A22.**

- [x] **A22 — Regrouper les entités de la PWA par pièce repliable.**
  Pièce effective pour Alfred, groupe « Sans pièce », recherche et filtres,
  tri dans les groupes et déplacement après édition. Build et 16 tests UI
  réussis. Chromium à 1366 × 768 et 390 px, édition simulée. Sur le LAN,
  41 entités réelles réparties en 11 groupes vérifiées dans Chromium.
  **Dépend de : A14, A17, A21.**

- [x] **A21 — Afficher les rubriques des paramètres dans le volet desktop.**
  Navigation principale remplacée dans Paramètres, rubrique active indiquée,
  ouverture sur Apparence et retour à l’écran d’origine. Build et 16 tests UI
  réussis. Les huit rubriques, le clavier, l’historique et le redimensionnement
  ont été vérifiés dans Chromium à 1366 × 768 et 1920 × 1080, avec réponses API
  simulées. Accueil des réglages et Retour vérifiés à 360 et 390 px.
  **Dépend de : A20.**

- [x] **A20 — Adapter la PWA aux ordinateurs 16:9.** Volet fixe dès 1 024 px,
  chat centré, lecteur et bibliothèque côte à côte selon l’espace disponible,
  catalogue élargi et volet des paramètres suivi dans A21. Build et 16 tests UI
  réussis. Chromium à 1366 × 768 et 1920 × 1080 : clavier, thèmes, défilement,
  seuils de mise en page, conservation du brouillon et de la sous-page.
  À 360 et 390 px : Retour, Échap, restitution du focus et fiche d’appareil.
  Recette Chromium avec réponses API simulées. **Dépend de : A11, A14, A19.**

Suivi A11 du 21 novembre — retour « Connexion à Alfred indisponible » dans
Maison et appareils. Le serveur Alfred répondait sur 8765 et la PWA ne servait
plus le port 5173. Prévisualisation du build existant relancée. Page et API
vérifiées en HTTPS avec l’autorité locale ; 41 entités renvoyées. Rechargement
dans le navigateur de l’utilisateur à confirmer.

- [x] **A19 — Présélectionner la pièce Home Assistant dans la fiche.**
  Nom de la pièce seul, petite maison quand l’affectation d’origine est
  sélectionnée, une seule entrée par pièce. Présélection, changement et retour
  à « Bureau » vérifiés dans Chromium avec écritures simulées, sur la PWA à
  1280 et 360 px et dans Domotique à 360 px. **Dépend de : A18.**

- [x] **A18 — Éditer les réglages d’un appareil dans une fenêtre dédiée.**
  Récapitulatif en lecture seule, crayon, sélection des pièces Home Assistant,
  validation groupée et reprise des réglages historiques. Vérifié dans
  Chromium à 1280 et 360 px dans les deux interfaces : annulation, reprise
  après erreur, actualisation et retour du focus. Écritures simulées et
  ciblage par pièce vérifié avec Home Assistant simulé. Catalogue réel
  consulté sur le LAN : 41 entités, 12 pièces, réponse avec « Imprimante ».
  Build PWA, 16 tests UI, 46 tests JS et suite Python complète
  (914 réussis, 2 ignorés). **Dépend de : A14, A16, A17.**

- [x] **A17 — Personnaliser la pièce des appareils pour Alfred.**
  Affectation et déplacement dans Domotique et dans le tableau ou la fiche
  mobile de la PWA. Effacer le champ rétablit l’affectation Home Assistant.
  Vérifié avec Home Assistant simulé : changement de pièce, affectation d’une
  entité sans pièce, réinitialisation et ciblage par pièce, y compris lorsqu’une
  lumière ou un sous-groupe déplacé appartenait à un groupe de l’ancienne pièce.
  Build PWA, 16 tests UI et 267 tests Python ciblés réussis. Affectation et
  réinitialisation vérifiées dans Chromium sur ordinateur, à 360 px et dans
  Domotique, avec écritures simulées. Service relancé et catalogue réel
  consulté depuis le LAN.
  **Dépend de : A14, A16, F01.**

- [x] **A16 — Personnaliser le nom des appareils pour Alfred.**
  Champ éditable dans Domotique et dans le tableau ou la fiche mobile de la
  PWA. Nom utilisé pour reconnaître la cible, répondre et demander confirmation.
  Effacer le champ rétablit le nom Home Assistant. Les alias, l’accès et le
  mode confirmation restent gérés par les réglages existants.
  Vérifié avec Home Assistant simulé, y compris pour le commutateur de
  l’imprimante. Build PWA, 16 tests UI, 46 tests JS et suite Python complète
  (913 réussis, 2 ignorés). Édition sur ordinateur et réinitialisation sur mobile vérifiées
  dans Chromium avec écritures simulées. Sur le LAN, « Imprimante » est
  enregistré pour le commutateur réel et utilisé dans la réponse à une
  consultation d’état écrite depuis la PWA. **Dépend de : A14, F01.**

- [ ] **A15 — Intégrer les améliorations ergonomiques de la PWA. Recette Android ouverte.**
  Les cinq points sont validés et implémentés : grand bouton rond avec icône
  de micro au-dessus du logo, forme d’onde liée au micro avec affichage fixe en animations réduites,
  envoi et annulation libellés et retour à la saisie après refus. Deux exemples
  préremplissent le champ. Focus visible et cibles plus grandes. Modes partagé
  et local harmonisés, minuteries actives avant le formulaire et destination
  de la sonnerie indiquée. Fiche d’appareil sur mobile et tableau sur ordinateur.
  Build et 20 tests JS réussis. Chrome à 320 et 360 px avec audio et serveur
  simulés : onde, annulation, WAV, saisie en viewport réduit, modes de rappels
  et minuteries, édition d’un appareil et cohérence avec le tableau vérifiés.
  Téléphone, micro réel et TalkBack à essayer. **Dépend de : A11, A14 ; recette liée à A13.**

  Suivi A15 du 19 novembre : lecture et pause depuis l’icône sous chaque
  réponse accompagnée d’un audio. Barre audio retirée de la zone de saisie.
  Build et 16 tests UI réussis. Chrome à 360 px avec WAV simulés : lecture
  automatique, pause, reprise, relecture d’une réponse précédente, lecture
  unique et réinitialisation vérifiées. Recette Android ouverte.

- [x] **A14 — Reprendre le tableau domotique du laboratoire dans la PWA.**
  Six colonnes, tri et filtres, défilement horizontal avec nom fixe.
  Confirmation, accès et alias modifiables par ligne sur les réglages
  partagés d’Alfred ; alias Home Assistant affichés. Build et 16 tests UI,
  236 tests backend ciblés, test du tableau historique et recette sous
  Chromium à 360 px réussis. Catalogue réel de 41 entités vérifié, écritures
  vérifiées dans des données isolées et simulées dans l’interface.
  **Dépend de : A12, F01.**

- [ ] **A13 — Fluidifier la PWA et corriger le Retour Android.**
  Correction livrée sur le LAN. Retour Android vérifié sur l’application ouverte
  depuis l’accueil de l’émulateur, pour le menu, les listes, les minuteries,
  leurs vues locales et les paramètres. Migration du worker Vite vers le build
  compilé testée avec conservation du stockage. Médianes HTTPS via 5173 :
  courses 259 → 36 ms, rappels 265 → 38 ms, état musical 255 → 34 ms et
  favoris 305 → 59 ms. Build, 16 tests UI, 46 tests JS du laboratoire et
  883 tests Python réussis, 2 tests Python ignorés. Recette sur le téléphone
  de l’utilisateur ouverte. Contrôle serveur : planificateur et lectures HA/MA
  disponibles, terminal ESP32 déconnecté faute de résolution de son nom local.
  **Dépend de : A11 ; contribue à O02 et O04.**

- [x] **A12 — Afficher les appareils Home Assistant dans les paramètres.**
  Catalogue Assist en lecture seule, recherche et états d’exclusion et
  d’indisponibilité. Projection des métadonnées vérifiée et écritures rejetées
  par le proxy. Service relancé. Chromium à 360 px : 41 entités réelles,
  recherche, repli, erreur et reprise vérifiés. Build PWA, 16 tests UI et
  44 tests backend ciblés réussis. Recette Android ouverte. **Dépend de : A11, F01.**

Complément A11 du 18 novembre — le dessous du champ de saisie est libéré.
Les états du micro et les alertes sont placés avant le champ. Une erreur de
synthèse conserve l’avertissement sans recopier la réponse déjà dans le fil.
Build et 16 tests UI réussis. Chromium à 360 px : échange texte, micro simulé,
échec de synthèse et erreur serveur vérifiés. Affichage confirmé par l’utilisateur
sur Android.

- [x] **F34 — Résumer les lumières allumées.**
  Annoncer explicitement qu’aucune lumière n’est allumée si elles sont toutes
  éteintes. Nommer directement toutes les lumières allumées, même pour une
  question de comptage. La lecture vise la maison entière par défaut, la pièce
  du terminal pour « ici » et le lieu explicite en priorité. Les états inconnus
  sont signalés. Vérification LAN via l’API de la PWA et Home Assistant réel :
  phrase de la capture, comptage global et bureau, sans commande envoyée.
  Rendu des lampes allumées et états indisponibles vérifié avec des données
  simulées. Suite backend : 896 tests réussis et 2 ignorés.
  **Dépend de : F01, F21.**
- [ ] **F35 — Définir le style des réponses d’Alfred pour la maison. Proposition.**
  Discuter de la forme des réponses, des clarifications et des résultats
  indisponibles ou non confirmés. Évaluer le partage entre les formulations
  issues du code et les consignes du prompt. Partir de la consultation des
  lumières. Autres réponses composées par le code à examiner : minuteurs,
  température et appareils, musique, courses, rappels et annonces. Examiner
  aussi les confirmations locales et l’arrêt de sonnerie, qui passent sans
  appel au modèle. Pour chaque famille, relever les phrases nominales, les
  questions de précision et les résultats partiels ou non vérifiables.
  **Dépend de : F34 pour le premier cas de recette.**

- [x] **F36 — Réponses des minuteurs et modèles nommés.** Numéros retirés des
  réponses. Consultation et annulation par nom sur le même étage. Les modèles
  sont enregistrés par navigateur et les minuteurs lancés sont partagés sur
  Alfred. Recette API en environnement isolé et Chromium à 360 px avec lancement
  simulé : sauvegarde, persistance, préremplissage, lancement et suppression.
  Recette Android et écoute réelle ouvertes. **Dépend de : F07, F26, A11.**
- [x] **F37 — Annoncer le morceau en cours et la température.** Titre et artiste
  si disponibles pour le lecteur conversationnel, phrase directe pour la mesure
  de température. Piste en cours, pause, lecteur inactif et mesure indisponible
  couverts sur services simulés. Vérification en conversation réelle ouverte.
  Build PWA, 16 tests UI, 882 tests Python réussis et 2 ignorés. Le premier
  redémarrage avait laissé l’ancien Python en écoute. Nouveau processus et
  santé du planificateur vérifiés après relance du service local.
  **Dépend de : F03, F25, F31.**

Complément A11/F03 du 18 novembre — choix du lecteur et pochette raccordés.
Trois sorties Music Assistant détectées. Choix mémorisé par navigateur,
commandes ciblées et image relayée en HTTPS via Alfred. Service relancé
et recettes LAN réussies. À 360 px, sélection, changement de pochette,
repli sur le disque générique, persistance et commande ciblée simulée vérifiés.
Build PWA, 16 tests UI et 880 tests backend réussis, 2 ignorés.
Diffusion physique sur une autre sortie et recette Android encore ouvertes.

Complément A11 du 18 novembre — raccordement du backend et de la PWA.
Proxy HTTPS de même origine, validation du certificat et liste des méthodes
et routes acceptées. Chat texte/micro, recherche par échange, lecture audio,
courses et rappels familiaux, minuteries par étage, favoris et commandes
musicales, diagnostic et états des services intégrés. Les données historiques
restent accessibles en mode « Sur cet appareil ».
Service relancé. Origine étrangère refusée (403) et routes d’administration
exclues (404). Réponse Command Code réelle, transcription et synthèse du
serveur vérifiées avec une phrase de synthèse, lectures et recherche musicale
réelles. Chrome à 360 px : capture WAV simulée et chargement des données
des écrans raccordés. Build PWA, seize tests UI et suite backend complète :
879 réussis, deux ignorés. Recette acoustique et Android, actions avancées sur
échéances partagées, veille vocale,
notifications navigateur et accès par comptes HA restent ouverts.
**Dépend de : A11, F03, P06, I03.**

Complément A11 du 18 novembre — les cinq rubriques restantes sont développées :
IA et recherche, Musique, Notifications et sonneries, Données et confidentialité,
À propos et diagnostic. Choix locaux persistés pour la recherche, la catégorie
de favoris et la sonnerie ; écoute de la sonnerie et réutilisation par les
minuteries, export JSON des cinq ensembles de données enregistrés, état local de
la PWA actualisable. Préférence de recherche préparée pour le raccordement.
Compilation TypeScript/build PWA et seize tests réussis. Recette Chrome à
350 px : huit accès, catégorie appliquée avant et après rechargement, carillon
prévisualisé puis déclenché à échéance, JSON exporté et diagnostic actualisé.
Composant servi en HTTPS 200 sur le port 5173.
Recette Android et raccordements IA, Internet, Music Assistant, notifications
de rappel et diagnostic serveur à poursuivre dans A11.

Complément A11/F03 du 18 novembre — interface Musique réalisée et entrée de menu
activée. Agencement du croquis, thèmes existants, pochette neutre, commandes
désactivées et indication de raccordement manquant. Recherche/effacement et
catégories de favoris utilisables, zone résultats pendant la recherche ; état en
mémoire lors de la navigation. Aucun appel HA/MA ni login ajouté. Compilation
TypeScript/build PWA et quinze tests existants réussis ; composant servi en HTTPS
200 avec autorité locale. Vérification visuelle automatique bloquée (aucun navigateur
disponible). Recette réelle mobile, clavier et thèmes ouverte ; raccordement,
favoris MA et comptes HA restent à réaliser selon F03/P06/I03.

Complément A11/F03 du 18 novembre — page Musique demandée à partir du croquis :
lecteur cible, pochette et métadonnées, progression, commandes de lecture/volume,
recherche, favoris artistes/albums/titres/playlists remplacés par les résultats
pendant la recherche, dans le style Alfred. Étude de l'intégration Music Assistant
effectuée : pont HA déjà présent et API officielle adaptée aux interfaces propres.
Solution 2 validée : page React Alfred ; première étape interface seule, favoris
issus de Music Assistant. Réutilisation du pont HA et API MA si nécessaire à étudier.
Restent à vérifier les capacités de la version
installée (favoris, recherche détaillée, images, progression/déplacement),
raccorder la page, gérer les indisponibilités et réaliser la recette réelle.
Aucun changement de Music Assistant ni lancement audio réalisé pour cette étude.
**Dépend de : A11, F03 ; accès API direct éventuel selon P06.**

Complément A11 du 18 novembre : Maison et appareils accessible. Formulaire
d’adresse HA sans secret, pièces par étage, affectation du navigateur et satellites
locaux, édition et suppression annulable avec contrôle des références. Aucun état
réel de connexion simulé, aucun changement HA/ESP32. Compilation/build PWA et quinze
tests réussis ; page diffusée en HTTPS 200. Recette humaine ouverte, synchronisation
au serveur toujours distincte.

Complément A11 du 18 novembre : retour des paramètres déplacé à gauche du titre,
sur la même ligne, flèche seule ; ancienne ligne textuelle supprimée. Compilation
TypeScript et build PWA réussis.

Complément A11 du 17 novembre : sous-titres des rubriques de paramètres supprimés,
titres/icônes conservés. Compilation TypeScript et build PWA réussis.
Complément A11 : sélection de personnage = preset voix + réveil, sauvegardés en
une seule opération locale et affichés ensemble. « Avancé » supprimé, durée
d’écoute directement accessible. Couples personnalisés existants conservés.
Compilation TypeScript/build PWA et onze tests réussis ; raccordement serveur et
recette humaine ouverts.

- [ ] **A11 — Développer progressivement la nouvelle interface.** Après rejet de
  la refonte précédente, nouvelle instruction du 17 novembre : première étape
  limitée à une page de chat style ChatGPT et icônes Lucide React. Socle séparé
  React/TypeScript/Vite sous `ui/`, port 5173. Saisie et affichage en mémoire de
  page, nouvelle conversation, adaptation mobile ; raccordement Alfred, voix,
  autres écrans restent à faire lors des étapes suivantes.
  Compilation initiale réussie ; recette visuelle bloquée par l’outil navigateur
  Windows, retour humain ouvert. Accès LAN HTTPS demandé ensuite sur
  `https://192.168.1.23:5173` : configuré avec le certificat existant ; compilation
  et accès HTTPS à la page et au code React vérifiés (HTTP 200, certificat validé).
  Serveur relancé hors du bac à sable, dont l’accès LAN expirait ; écoute sur
  `.23:5173`, autorisations Node.js existantes du pare-feu conservées. Certificat
  valable jusqu’au 13 novembre 2027. Essai depuis un autre appareil restant ouvert.
  Dépend de A01 et A07. Les choix de la refonte rejetée restent non validés.
  Bouton micro Lucide ajouté à gauche de l’envoi ; le clic signale le raccordement
  vocal restant, sans capture audio ni appel serveur. Compilation TypeScript et
  build Vite réussis après cet ajout ; usage vocal réel encore ouvert.
  Navigation actualisée : burger Lucide à la place de l’engrenage ; volet plein
  écran glissant depuis la gauche. Conversation, Musique, Listes, Rappels et
  Minuteries ; Paramètres en bas. Conversation, Listes, Rappels, Minuteries et Paramètres
  actifs ; Musique accessible depuis le 18 novembre (interface seule). Fermeture/cycle du focus et mouvement réduit
  pris en charge, chat conservé. Compilation TypeScript et build PWA réussis ;
  menu validé par retour utilisateur ; recette clavier distincte toujours ouverte.
  Page Listes/courses demandée ensuite : ajout, compteur, grandes cases à cocher,
  articles achetés regroupés et repliables, édition du texte, suppression avec
  annulation, sauvegarde navigateur sur cet appareil et erreurs de stockage visibles.
  Liste HA existante non modifiée ; synchronisation/partage entre appareils restant
  à raccorder, pas de données fictives. Chat et brouillon conservés entre pages.
  Compilation TypeScript/build PWA réussis ; ergonomie et persistance sur le
  téléphone réel restant à valider.
  Pages Rappels et Minuteries ajoutées ensuite à la demande : formulaires simples,
  édition/état fait/suppression annulable des rappels ; durées rapides et détaillées,
  pause/reprise/réinitialisation/relance, décompte absolu et son de session facultatif
  pour les minuteries. Sauvegarde locale distincte de HA/serveur, limites d’alertes
  explicites ; notifications des rappels non raccordées. Compilation TypeScript et
  build PWA réussis, six tests de logique réussis (suspension, pause/reprise,
  échéance/relance, format et validation). Synchronisation et recette humaine
  restant ouvertes.
  Paramètres demandés ensuite : accueil des huit rubriques, avec Apparence et Voix/
  conversation réalisées en premier. Thèmes sombre/clair/système
  appliqués globalement et sauvegardés. Retour annoté : bandeau principal masqué
  dans les paramètres, retour vers la page précédente depuis leur accueil ;
  surtitre/phrases décoratives et options de taille du texte/animations supprimés.
  Anciennes valeurs retirées ignorées, accessibilité système conservée.
  Préférences vocales enregistrées sur l’appareil uniquement, limitation visible :
  pas de changement du serveur/ESP32. Compilation TypeScript/build PWA et dix tests
  réussis (préférences et minuteries) ; recette
  visuelle et raccordement des réglages vocaux restent ouverts.
  Installation PWA Android demandée ensuite : manifeste, icônes, service worker
  et bouton Installer implémentés. UI avec certificat dédié signé par une autorité
  locale téléchargeable ; confiance à installer manuellement sur Android si requise.
  Certificat backend conservé. Build TypeScript/Vite et génération du service
  worker réussis ; HTTPS avec validation de l’autorité, manifeste au bon type MIME,
  trois icônes PNG et service worker de développement vérifiés HTTP 200. Audit npm :
  zéro vulnérabilité après surcharge de glob pour Workbox. Serveur 5173 relancé.
  Installation et lancement autonome sur téléphone confirmés par l’utilisateur
  après les indications concernant la confiance du certificat.
  Retour Android : barre d’adresse/menu encore visibles et indicateur rouge de
  certificat sur la capture. Critère de recette : ouverture depuis l’icône sans
  barre navigateur ; vérifier confiance de l’autorité sur Android, puis relancer
  et si nécessaire réinstaller. Manifeste déjà en standalone ; cause exacte
  initialement non confirmée ; problème ensuite déclaré résolu par l’utilisateur.
  Nouvelle demande : bandeau toujours visible quand le clavier Android se déplie.
  En-tête maintenu en haut, défilement limité à la conversation et viewport
  redimensionné avec le clavier. Compilation TypeScript et build PWA réussis ;
  Première correction rejetée par capture Android : bandeau encore hors écran.
  Nouveau correctif : cadre fixe synchronisé avec hauteur/décalage du viewport
  visuel ; défilement automatique limité à la conversation, focus sans déplacement
  du document. Compilation TypeScript/build PWA et simulations ouverture/déplacement/
  fermeture du clavier, zoom et nettoyage réussis. Recette sur Android toujours ouverte.

Dernière mise à jour : 17 novembre 2026 (Europe/Paris).

Document vivant à compléter pendant les échanges et les essais. `CADRAGE.md`
reste la référence des exigences ; `PROPOSITION_TECHNIQUE.md` décrit les candidats
techniques. Une tâche dans cette liste ne vaut pas validation de ses choix ouverts.

## Lecture et entretien

- [x] **F32 — Éviter l'erreur terminal pour une température introuvable.**
  Signalement du 16 novembre : question sur le salon suivie d'un clignotement rouge.
  Catalogue réel contrôlé : aucune sonde de température exposée associée au salon.
  Absence, ambiguïté et mesure indisponible deviennent des réponses de clarification
  normales de l'outil ; les erreurs techniques restent signalées. Les noms et pièces
  des sondes sont désormais transmis au modèle même si le relais appareils est désactivé.
  Recette : 100 tests ciblés réussis, dont conversation complète avec sonde absente
  ou indisponible terminée normalement. Essai humain sur ESP32 restant à confirmer.
  Service redémarré ; phrase exacte du signalement vérifiée avec le modèle réel :
  réponse puis fin normale, statut clarification, aucun événement d'erreur.
  **Dépend de : F31 ; contribue à F15.**

- [ ] **T11 — Recetter le satellite Wi-Fi sur prise USB et sa maintenance OTA.**
  Choix validé le 15 novembre : serveur Alfred conservé, réveil configurable dans
  l'interface sans flashage. Prise USB confirmée par l'utilisateur ; identité,
  firmware v2.0.0/ESPHome 2026.9.0 et négociation OTA vérifiés sur la carte.
  Reprise persistante de la veille livrée ; arrêt et transfert navigateur
  désactivent la reprise. Tests réels : redémarrage serveur puis carte,
  reconnexion et flux micro restaurés ; lecture Phonon téléchargée et fin confirmée.
  Lanceur Windows suivi par la tâche, trois reprises sur échec espacées d'une
  minute ; démarrage à l'ouverture de session conservé. Sources de maintenance,
  environnement ESPHome isolé, binaires officiels de récupération et SHA-256
  préparés ; configuration et compilation complètes réussies, binaires OTA/factory
  produits sans transfert. Suite serveur : **810 tests Python réussis/deux ignorés,
  43 JavaScript réussis**. Voir `docs/ESP32_WIFI_OTA.md`.
  Restent : coupure réelle du point d'accès Wi-Fi, écoute humaine/conversation
  après déplacement et transfert OTA lors d'une mise à jour utile. Aucun flashage
  effectué ; ne pas fermer ce point sur la seule négociation OTA.
  **Dépend de : T02, T04 ; contribue à A02/A03.**

- [ ] **F30 — Diagnostiquer et prévenir le gel de la veille STT ESP32.** Incident
  **Récidive :** détecteur libre, non verrouillé, sans analyse en attente ; la
  première correction ne traite pas la cause de ce nouveau cas. Niveaux du
  signal et score VAD exposés sans audio enregistré. Relance et cycle réel
  réveil/commande/lecture/reprise observés ; 92 tests ciblés réussis. Diagnostic
  non clos, observation en situation de panne encore nécessaire.
  Deuxième complément : secours de détection par énergie soutenue (>490 RMS
  PCM16 pendant 180 ms), sans supprimer Silero ni la validation du mot par le
  STT. Un VAD qui refuse tout ne bloque plus à lui seul la veille. Compteur
  `energy_fallbacks` exposé pour mesurer l'utilisation et le bruit induit ; cause
  exacte et efficacité contre la récidive toujours à confirmer sur carte.
  Suite complète après ce complément : 806 réussis, deux ignorés. Service relancé,
  Alfredo en veille STT, signal micro non nul, micro/détecteur `ok` au contrôle.
  terrain du 14 novembre : audio reçu mais deux inférences de veille seulement,
  aucun appel IA actif, phase `waking`. Réarmement immédiat effectué. Détection
  refusée : remise à zéro du verrou ; supervision des verrous orphelins en veille,
  sans interrompre une capture/commande active. Diagnostic enrichi sans contenu
  privé. Tests de refus puis nouvelle détection et récupération avec micro vivant.
  Suite complète : 803 réussis, deux ignorés. Service redémarré, Alfredo/STT
  restauré en écoute, réception micro et détecteur `ok`, verrou absent au contrôle.
  Cause exacte de l'incident encore non prouvée ; recette longue réelle ouverte.

- [ ] **F29 — Recetter les commandes de lumières avec exceptions.** Demande du
  14 novembre : toutes les lumières sauf les pièces/lampes citées. Paramètres
  `exclude_rooms` et `exclude_entities` ajoutés à l'outil LLM, résolution par
  feuilles même avec groupes, états déjà conformes ignorés, exclusions inconnues
  ou pièces omises refusées. Tests automatisés et essai réel DeepSeek contre un
  HA simulé : seule Cuisine éteinte, Bureau et Salon préservés. Aucun appel sur
  des lumières réelles. Suite complète : 800 réussis, deux ignorés ; 56 tests
  d'intentions réussis après ajout du cas d'exclusion par alias. Service relancé.
  Essai vocal humain restant à faire.
  20 novembre : l'extinction globale explicite accepte « toutes les lumière ».
  Si un nom de lampe est inconnu dans une pièce, la question porte sur la lampe
  à préserver. Le choix est rattaché à la commande globale dans la même session
  et le même profil, avec expiration après trente secondes. Dialogue reproduit
  sur Home Assistant simulé via l'API de conversation, y compris interruption,
  expiration et isolation de session. Service relancé et ESP32 reconnecté.
  Dialogue vocal sur l'ESP32 réel restant à vérifier.

- [ ] **F28 — Utiliser le modèle configuré comme interprète principal.** Accord
  du 14 novembre : demandes usuelles transmises au modèle, fonctions locales
  validées pour exécution ; arrêt de sonnerie et interruptions immédiates conservés.
  Contexte des minuteurs actifs fourni par étage. Implémentation livrée ; suite
  complète : 795 réussis, deux ignorés. Essai réel en lecture seule avec le modèle
  configuré : outil minuteur appelé, réponse et audio produits (1730 ms modèle,
  298 ms synthèse sur cet essai). Correction associée : transmettre la réponse
  finale à la synthèse anticipée lorsqu'un outil répond sans delta texte.
  Service redémarré, ESP32 connecté, veille/micro/détecteur `ok`. Recette vocale
  humaine et mesures représentatives de latence restent à faire.

- `[x]` : terminé avec une décision ou une preuve ; `[ ]` : travail restant.
- **À décider** : choix utilisateur ou comparaison encore nécessaire.
- **À tester** : comportement ou performance non démontrés.
- **Différé** : remis à plus tard à la demande de l'utilisateur.
- **Dépend de** désigne les prérequis pour terminer le point. On peut préparer
  les interfaces ou utiliser des simulations avant leur disponibilité ; cela ne
  valide pas le fonctionnement réel.
- Les identifiants sont stables. Ajouter les nouveaux points et leurs dépendances,
  mettre à jour les points existants et ne cocher qu'après vérification.

## 1. Bases acquises

- [x] **B01 — Architecture** : Alfred autonome intégré à HA ; Assist n'est pas le
  socle du dialogue. Décision consignée dans le cadrage.
- [x] **B02 — Périmètre** : domotique, musique/Qobuz, conversation/recherche,
  minuteurs, rappels, courses et annonces ; plusieurs terminaux à terme.
- [x] **B03 — Contraintes** : français, nom Alfred/Fred, conversation de 8 s,
  interruption, profils, permissions et mémoires, budget supplémentaire visé ≤ 5 €/mois.
- [x] **B04 — Candidats du prototype** : faster-whisper, Piper, SpeechBrain ECAPA,
  service Python, premier accès navigateur. Adoption définitive après essais.
- [x] **B05 — Premier banc matériel** : carte reliée à HA, lumières commandées ;
  firmware jyoushiki v2.0.0 constaté via MCP. Cela ne valide pas le firmware Alfred.
- [x] **B06 — Réglage de référence relevé** : Alexa, sensibilité `Moderately sensitive`,
  gain post-AFE 13 ; réveil jugé meilleur par l'utilisateur. Aucun résultat chiffré.

## 2. Décisions et préparation sans attendre la carte

- [ ] **P01 — Fixer les règles encore ouvertes.** À décider : actions à confirmer,
  informations sensibles, accès entre mémoires familiales, commandes de consultation/
  effacement. Contrainte : préserver les permissions invités déjà validées.
  **Dépend de : B03.**
- [ ] **P02 — Définir rappels, minuteurs et annonces.** À décider : annulation et
  destination par défaut des rappels créés sans terminal (web/HA).
  Garder minuteurs par étage et annonces
  maison/étage/pièce. **Dépend de : B02.**
  Validé : « Stop » arrête les sonneries de l'étage courant ; échéances conservées
  après redémarrage ; rappels personnels non délivrés visibles dans l'interface,
  sans annonce à toute la maison. Ces décisions ne valent pas implémentation.
  Rappel personnel : terminal de création par défaut, autre pièce choisissable
  à la voix. Le défaut web/HA sans terminal reste à déterminer.
  Clarification du 29 octobre : rappel daté de type calendrier, ponctuel ou récurrent ;
  heure manquante demandée à l'utilisateur. Minuterie = durée puis sonnerie à l'étage ;
  annonce = diffusion immédiate avec choix du lieu. Exemples : poubelles chaque jeudi
  à 19 h, facture demain, minuterie 7 min 40, annonce « le repas est prêt ».
  L'utilisateur précise ensuite : annonce sans destination explicite diffusée dans
  toute la maison ; toute la maison, étage ou pièce restent ciblables explicitement.
  En cas d'arrêt au moment d'un rappel récurrent : signaler le rappel manqué et
  programmer l'occurrence future suivante, sans annonce tardive.
  Si la portée d'une annulation de rappel récurrent n'est pas précisée, demander
  si elle concerne la prochaine occurrence ou toute la série.
  Reprise validée : rappel manqué signalé dans l'interface ; minuteur expiré marqué
  terminé ; aucune sonnerie tardive. Les échéances futures sont conservées.
- [ ] **P03 — Fixer la propriété des données et les interfaces HA.** Choisir une
  seule source de référence pour courses et rappels, puis préciser affichage et
  commandes HA des fonctions Alfred. Courses obligatoirement disponibles dans HA.
  **Dépend de : B01, P02.**
  Avancement : HA référence pour courses et calendriers personnels ; Alfred référence
  des minuteurs. Correction utilisateur du 29 octobre : ne pas faire du calendrier
  local Alfred la référence des rappels. Choisir les calendriers personnels et le
  calendrier familial, puis concevoir le déclenchement sans double source.
- [ ] **P04 — Mesurer les ressources et dimensionner la VM Debian sur le nouvel AuBox.** Lire CPU/RAM/disque
  disponibles et charge habituelle ; choisir VM/conteneurs et enveloppe de ressources.
  Ne pas supposer les 32 Go libres ni installer sur HA par défaut.
  **Dépend de : B04.**
  8 novembre : matériel cible choisi par l’utilisateur et en attente de réception :
  Chuwi AuBox Ryzen 7 8745HS / 32 Go DDR5 / SSD 512 Go / Radeon 780M. Proxmox pour
  le homelab, Alfred dans une VM Debian. Remplace la proposition d’hébergement sur
  G7400 ; aucune migration réalisée. À réception : vérifier ressources, RAM réelle
  par canal, noyau/CPU visible, allocations et concurrence homelab. Accélération AMD
  non présumée disponible dans la VM. P04 reste ouvert pour ces mesures.
  Avancement : relevé MCP ponctuel à 18:46, environ 6,83 GB libres sur le nœud et
  0,71 GB sur 103. VM dédiée 2 vCPU/4 Gio/32 Gio proposée, non validée ; lectures
  système, charge habituelle et stockage restent nécessaires.
  27 novembre, proposition pour l’AuBox : VM Debian 13 amd64 minimale, 4 vCPU
  de type `host`, 8 Gio fixes et 64 Gio de disque VirtIO, traitement vocal sur
  CPU, réseau bridgé avec réservation DHCP. Confirmer la marge de l’hôte et
  mesurer la latence et la mémoire en conversation sous charge avant d’ajuster.
  Piste GPU examinée le 27 novembre : la Radeon 780M peut faire l’objet d’un
  essai de passthrough PCI dans une VM isolée après vérification du BIOS, des
  groupes IOMMU et de l’accès à la console Proxmox. Parakeet/Silero sont câblés
  sur CPU ; Phonon 0.7.0 Q8 est CPU uniquement. Un essai Phonon GPU demande
  un build Vulkan et des poids f32. Établir d’abord la référence CPU de l’AuBox,
  puis comparer délai au premier son, stabilité et mémoire si un essai GPU
  est retenu. Compatibilité de cet AuBox et gain non vérifiés.
  27 novembre, VM de dev créée et mesurée : Debian 13.8 amd64, 4 vCPU, 7,8 Gio
  de RAM, disque de 75 Gio dont 64 Gio libres, IP 192.168.1.71, fuseau Europe/Paris.
  Le processeur invité est encore exposé comme « QEMU Virtual CPU 2.5+ » sans AVX ;
  `ptts` 0.7.0 a été reconstruit localement pour cette VM et Phonon fonctionne.
  Passer le type de CPU Proxmox à `host` reste recommandé pour le wheel officiel
  et la performance.
  Le reste du dimensionnement et les mesures de latence restent ouverts.
- [ ] **P05 — Définir les critères d'acceptation.** Fixer latence, succès des commandes,
  faux réveils, reconnaissance des personnes et concurrence entre terminaux ; séparer
  objectifs et mesures. Inclure l'enfant de 4 ans et Fred. **Dépend de : B03.**
- [ ] **P06 — Préparer les accès applicatifs.** HA, Music Assistant et Command Code ;
  clés hors documentation/Git/logs, périmètre d'accès à préciser et authentification
  web via HA retenue.
  **Dépend de : B01, P03.**
  18 novembre : login de l'app via les comptes HA dédiés confirmé, Music Assistant
  compris dans le parcours souhaité. Vérifier liaison des identités/sessions et
  droits HA/MA, ainsi que favoris personnels ou partagés ; ne pas présumer une
  transmission automatique de l'identité ou des permissions. Aucun login livré ;
  première étape UI Musique seule, sans bloquer sa réalisation sur P06.
  30 octobre : l'utilisateur choisit les comptes Home Assistant pour
  l'administration si possible. Flux OAuth 2 avec PKCE documenté par HA ;
  intégration et essais réels à faire. Vérifier rôle administrateur, session,
  expiration/révocation, protection côté serveur des routes et contenus personnels,
  et compatibilité de l'accès LAN/HTTPS. Distinguer cette protection des restrictions
  vocales et conserver l'accès invité déjà validé ; périmètre exact à préciser.
  Authentification et droits différés par l'utilisateur jusqu'avant la mise en
  production ; ne pas bloquer les travaux fonctionnels du prototype sur ce point.
  Command Code : formulaire de clé local implémenté, secret protégé DPAPI Windows
  (0600 Linux), aucune reprise de clé d'une autre app. L'utilisateur valide ensuite
  le fonctionnement réel de Command Code. Music Assistant est désormais raccordé à
  un lecteur explicitement choisi ; son accès réel et son arrêt ont été vérifiés.

## 3. Service Alfred et prototype navigateur

- [x] **S01 — Créer le socle exécutable.** Service Python, configuration, données
  locales, démarrage/arrêt, état de santé et dépendances reproductibles.
  **Dépend de : B04.**
  Réalisé le 26 octobre : FastAPI, lanceur `python -m alfred`, configuration par
  dossier de données, SQLite versionné et verrou mono-ordonnanceur. Versions dans
  `requirements.lock.txt`, instructions dans `README.md`. Vérifié sous Python 3.14
  sur Windows : 28 tests passent, contrôle syntaxique JS réussi, service démarré
  sur 127.0.0.1:8765 et minuteur créé/arrêté depuis le navigateur.
- [x] **S02 — Créer la capture et la lecture dans le navigateur.** Micro, envoi audio,
  réponse audible, arrêt, affichage du texte et des durées ; accès micro sur une
  origine compatible. Ne pas confondre avec la validation acoustique ESP32.
  **Dépend de : S01.**
  v0.2 implémentée : capture AudioWorklet mono PCM16, permission au clic, arrêt/
  annulation/limite 30 s, lecture Piper et retour de transcription Whisper. Lecture
  testée dans le navigateur et chaîne synthétique réelle testée. L'utilisateur
  confirme ensuite le 26 octobre : « ça fonctionne très bien » après invitation
  à essayer le vrai micro. Banc vocal navigateur validé qualitativement ; cela ne
  valide ni l'acoustique ESP32 ni les performances du serveur cible.
- [ ] **S03 — Finaliser la recette du STT local retenu.** Choix et intégration
  terminés : Parakeet TDT 0.6B v3 INT8, stack Murmure 1.11.3 autonome sur CPU,
  dictionnaire, nettoyage et formatage locaux. Aucun LLM de réécriture.
  **Dépend de : S02, P04, P05.**
  Retours humains favorables sur téléphone et ESP32, puis « vraiment très bien »
  après intégration. Parité de texte 28/28 avec Murmure sur le corpus synthétique
  d’intégration ; aucun score de précision humaine déduit de ces essais.
  Le 11 novembre, nettoyage demandé : un seul backend et préparation conservés,
  options de bascule, moteur antérieur, routes/scripts/UI de comparaison retirés.
  Anciens modèles, bancs et sources d’étude redondantes placés dans la Corbeille.
  Paquets devenus inutiles désinstallés du venv et résidus retirés. Configuration
  de dictionnaire/formatage et modèle Parakeet conservés, données privées hors Git.
  Silero VAD v6 extrait en ressource autonome vérifiée, même modèle et options
  ONNX, mêmes états/hystérésis et fin de parole ESP32, aucun téléchargement en prise.
  Validation après retrait des paquets : **480 tests Python réussis, 2 optionnels
  ignorés ; 17 tests JS ciblés réussis**. Sources du worker Rust inchangées depuis
  leurs 96 tests réussis. Question témoin correctement transcrite en 217 ms via
  VoiceService sans les paquets supprimés, silence Silero correctement rejeté.
  Service relancé : Parakeet prêt, ESP32 connecté, veille du mot d’appel rétablie
  et réception confirmée. API/page sans comparaison ; voix Dumby conservée.
  Diagnostic sans action maintenu : armement 60 s, expiration sûre, résultat
  en mémoire/affichage deux minutes, aucun IA/TTS/HA ni audio enregistré.
  Restent : débit naturel sous charge sur la VM Debian cible, mémoire/latence,
  musique, noms propres dont Airbourne, voix enfant, distance et bruit. Retour
  positif courant consigné sans généraliser à ces conditions. S03 reste ouvert
  pour cette recette approfondie ; le nettoyage logiciel est terminé.
- [ ] **S04 — Choisir la voix française.** Écoutes Piper, intelligibilité, diction,
  délai de première parole et consommation. Référence d'ambiance Alfred, voix finale
  non choisie ; ne pas promettre une reproduction exacte. **Dépend de : S01, P05.**
  30 octobre : l'utilisateur rejette Tom et Pierre, qui prononcent mal « Alfred » ;
  Pierre dit aussi « majordoum ». Piper n'est plus le moteur actif. Supertonic 3
  local (99 M paramètres, ONNX, licence OpenRAIL-M) est installé avec les cinq voix
  masculines M1 à M5 ; M3 sert de secours. Pocket TTS cloné est désormais la voix
  active par défaut. Le profil nettoyé améliore la similarité ECAPA moyenne de
  0,426 à 0,475 et la reconnaissance de 81 % à 86,6 % sur trois phrases et
  plusieurs graines ; médiane 600 ms et p95 655 ms sur cinq réponses courtes,
  sans repli. « Alfred » est reconnu correctement ;
  « majordome » reste rapproché de « majeur d'homme » par Whisper. Le timbre et la
  diction doivent encore être acceptés par l'utilisateur à l'écoute. Mesures sous
  charge, lecture ESP32 et choix définitif encore ouverts.
  2 novembre : la base synthétique 2 propre au débit 1,242 est acceptée par
  l'utilisateur et conservée en banque (S17). Essais « noble » et intégration
  de cette référence au service restent ouverts ; le clone précédent n'est pas
  validé par cette acceptation.
- [ ] **S05 — Connecter Command Code.** Tester accès GOAT, modèle rapide inclus,
  français, streaming et appels d'outils. Mesurer quotas partagés avec les autres
  usages ; aucune recherche Internet présumée native. **Dépend de : S01, P06.**
  Le 29 octobre : outils IA limités à la lecture et à l'ajout de courses, arguments
  vérifiés côté Alfred ; test fournisseur réel avec liste simulée : lecture naturelle
  et ajout explicite réussis, ajout indirect instable. Essai avec liste réelle refusé
  par l'examen automatique en raison du risque de transmission du contenu à l'IA.
  L'utilisateur autorise ensuite cette transmission éventuelle ; lecture réelle par
  l'outil et réponse vocale vérifiées avec « Que devons-nous acheter ? ». Le contexte
  peut transmettre une réponse contenant des articles au fournisseur. L'ajout indirect
  et les autres outils restent à améliorer et valider.
  Essais supplémentaires avec fournisseur réel et liste simulée : ajout indirect,
  relance « et du café aussi », lecture et question générale réussis ; une réponse
  vide sur une relance avant ajustement de la limite de sortie. Limite portée à
  1024 tokens ; 33 tests ciblés réussis, contexte isolé par session. Fiabilité à
  confirmer par l'utilisateur ; consommation supplémentaire à mesurer en S08.
  v0.3 : connecteur et flux texte/voix implémentés, contexte temporaire par onglet,
  gestion des erreurs et formulaire de clé. Tests simulés réussis puis fonctionnement
  réel validé qualitativement par l'utilisateur (« ça fonctionne bien »). Les outils
  courses ont été ajoutés ensuite ; latence, consommation et comparaison de modèles restent à mesurer.
  Modèle proposé modifiable : exemple officiel `deepseek/deepseek-v4-flash`.
  20 novembre : gestion des modèles depuis « IA et recherche » dans la PWA.
  Bouton Modifier, liste persistante initialisée avec le modèle actif, ajout
  sans activation, test indépendant avec délai de réponse, et sélection explicite.
  La liste reste dans la configuration protégée existante et aucun outil ou
  contexte de conversation n’est transmis par le test. Ajout, échec de test,
  sélection, retour et relecture vérifiés en tests ; 118 Python et 16 JS réussis,
  build PWA réussi. Serveur et UI relancés ; test réel via le proxy PWA en
  1 395 ms sur le modèle actif. Recette des clics et choix d’un autre modèle
  réel restent à faire par l’utilisateur.
  Vérification des modèles gratuits du catalogue le 20 novembre via la PWA,
  un test court chacun sans activation : Glyph Cluster 2 322 ms, Flint
  3 591 ms, Inkling 2 Small échec fournisseur au contrôle. Réponses vocales,
  appels d’outils et stabilité des latences restent à comparer avant adoption.
  Correction de l’interface le 20 novembre : « Modifier » ouvre une fenêtre
  modale, modèle actif précoché, choix unique, validation ou annulation.
  Ajout et test chronométré disponibles dans la fenêtre. Annulation et
  validation vérifiées dans Chromium sur une API simulée, build et 16 tests
  UI réussis, nouvelle version servie sur le port 5173.
- [ ] **S06 — Gérer les sessions conversationnelles.** Fenêtre de 8 s après réponse,
  silence, arrêt, annulation des réponses dépassées et changement de personne.
  Définir précisément renouvellement et fin de session. **Dépend de : S02, S05, I02.**
  v0.4 : boucle navigateur implémentée et testée artificiellement en S12. La fenêtre
  part de la fin réelle de lecture ; envoi après pause, phrase commencée avant
  échéance acceptée, silence sans appel IA. Essai humain et changement de locuteur
  (I02) restent à faire.
- [ ] **S07 — Ajouter la recherche Internet.** Choisir le fournisseur selon tarifs
  actuels, sources et délais ; distinguer contenu web et instructions utilisateur.
  **Dépend de : S05, P05.**
  Décision du 16 novembre : actualités à la demande, météo courante et prévisions
  sur sept jours, culture générale avec recherche selon besoin. Open-Meteo et
  Tavily gratuits retenus ; commune dans les réglages Alfred, sources à l'écran.
  Socle implémenté : trois outils typés, synthèse sans outils d'action, clé
  protégée, plafond gratuit persistant et conservation des sources texte/voix/ESP32.
  Réservations conservatrices, mois UTC et blocage sur quota ; aucune bascule payante.
  Vérification réelle publique Open-Meteo réussie (géocodage, sélection et prévisions
  Paris), sans utiliser la position du domicile. Tests logiciels dans
  `tests/test_internet.py` et `tests/internet-panel.test.mjs`.
  Recette du 16 novembre : **867 tests Python réussis, deux ignorés ; 46 tests
  JavaScript réussis**. Service relancé, santé et réglages HTTP 200 ; panneau
  présent, ESP32 reconnecté en veille. Aucun appel Tavily réel sans clé locale.
  Après retour utilisateur « C'est bon » : configuration locale contrôlée,
  clé présente sans lecture ni affichage, accès Tavily vérifié par le service,
  commune enregistrée et quota non bloqué. Configuration et accès réel validés.
  **Reste à faire :** mesurer qualité/latence avec Command Code et faire l'écoute
  navigateur/ESP32 ; ce retour ne valide pas à lui seul la recette conversationnelle.
  17 novembre : premiers essais positifs rapportés, puis défaut de synthèse
  reproduit sur les grèves. Budget de génération épuisé par la réflexion DeepSeek.
  Corrigé : `reasoning_effort=off` pour le seul résumé DeepSeek V4 via Command Code,
  aucun changement aux autres modèles ni au premier appel de compréhension.
  Résumé tronqué toujours rejeté avec erreur distincte, aucune relance ni nouvelle
  recherche automatique. Trois résumés réels consécutifs réussis, sans réflexion,
  environ deux secondes par synthèse. Suite complète : **875 tests Python réussis,
  deux ignorés** ; **82 tests ciblés** revérifiés après adaptation à la passerelle.
  Service relancé ; même question vérifiée via `/api/conversation/text` avec
  fournisseurs et TTS réels : réponse complète, cinq sources, environ 8,7 secondes
  au total (IA/recherche 7,1 s, synthèse vocale 1,4 s), sans lecture physique.
  Santé HTTP 200, ESP32 connecté au repos. Écoute après correction à confirmer.
  Bulletins automatiques et vigilances exclus de cette première version.
  20 novembre : prévisions limitées au temps en clair, aux températures minimale
  et maximale et au risque de pluie. La météo actuelle donne la température et
  la pluie dans l’heure d’après les créneaux de quinze minutes. Phrase « Il fait
  beau » si les données complètes sont sèches. Format produit localement, source
  séparée du texte. 122 tests ciblés réussis. Après redémarrage, demandes « demain »
  et « en ce moment » vérifiées via l’API de la PWA avec les fournisseurs réels.
  Écoute sur ESP32 à confirmer.
  20 novembre : délai dépassé dans la synthèse des résultats de Formule 1 sur
  GLM-5.3 Flash. Le journal ESP32 confirme le délai et le pont signalait une
  erreur au firmware. Les échecs attendus du service de conversation ferment
  désormais la prise, affichent le motif et réarment la veille sans signal
  d’erreur matériel. Délai nominal de synthèse porté de 10 à 20 secondes sans
  relance. 151 tests ciblés réussis, dont délai simulé à travers le pont ESP32.
  Après redémarrage, veille et micro vérifiés ; demande EL2 via l’API PWA et
  GLM réel terminée avec cinq sources et synthèse vocale. Voyant à confirmer
  sur la carte au prochain échec fournisseur.
- [ ] **S08 — Appliquer le budget.** Compteurs de consommation, alertes, plafonds et
  comportement à quota épuisé ; aucune bascule payante implicite. Objectif de départ :
  aucune nouvelle API vocale payante, sans garantie avant mesures.
  **Dépend de : S03, S04, S05, S07.**
- [x] **S09 — Vérifier le socle des échéances en local.** Test sans profils ni
  diffusion physique : création, annulation et transitions réelles dans SQLite ;
  « Stop » isolé par étage, persistance, reprise sans sonnerie tardive, concurrence
  et verrou d'instance. Tests automatisés et minuteur de deux secondes dans le
  navigateur vérifiés le 26 octobre. **Dépend de : S01.**
  Ne clôture pas F06/F07/F09 : rappels récurrents, profils, HA et haut-parleurs
  ne sont pas encore raccordés.
- [x] **S10 — Vérifier la chaîne vocale locale sur audio synthétique.** Moteurs
  et modèles publics préparés séparément ; exécution sans téléchargement ni
  enregistrement audio à l'inférence. API STT/TTS et boucle réelle Piper → Whisper
  vérifiées le 26 octobre : 42 tests Python passent avec l'intégration activée,
  plus 2 tests JavaScript PCM/WAV. Lecture du sample Piper vérifiée dans le
  navigateur. **Dépend de : S01.** Ne valide pas les voix humaines ni le serveur cible.
- [x] **S11 — Développer et tester le connecteur conversationnel.** Streaming
  Command Code → texte progressif → voix locale, absence d'action domotique,
  contexte éphémère isolé, clé jamais retournée et configuration protégée.
  Recette v0.3 : 61 tests Python réussis (dont voix réelle locale, fournisseur IA
  simulé) et 5 tests JS. **Dépend de : S01, S02.** Accès réel validé ensuite par
  retour utilisateur. Ne clôture pas S05 : modèle, latence et outils restent à vérifier.
- [x] **S12 — Implémenter la reprise de parole navigateur.** Première capture au
  clic, envoi après pause, huit secondes après la fin réelle de lecture et
  renouvellement après chaque réponse ; arrêt, absence de reprise après erreur,
  réécoute ou onglet caché. Recette v0.4 : 61 tests Python et 25 tests JS, dont le
  contrôleur d'interface avec micro et audio artificiels. **Dépend de : S02, S11.**
  Ne clôture pas S06 : aucune validation du vrai micro, des profils ou de l'ESP32.

- [x] **S13 — Commander les minuteurs depuis le dialogue du banc navigateur.**
  Choisi par l'utilisateur le 27 octobre ; v0.6 implémentée : création sur durée,
  consultation et temps restant, annulation de l'unique actif ou précision par
  numéro, Stop des sonneries de l'étage. Commandes directes sans IA/HA, étage
  explicite transmis par texte ou en-tête audio ; mêmes échéances SQLite.
  **Dépend de : S01, S09, S11.**
  Vérifié : 133 tests Python réussis (1 test vocal réel optionnel non activé),
  26 tests JS réussis. Tests HTTP hors bac à sable Windows pour contourner le
  blocage asyncio ; voix/IA/HA simulés et données isolées. Inclut durée française,
  demandes mixtes sans action, ambiguïté sans annulation, isolation des étages,
  persistance et échec de synthèse après création sans nouvelle tentative.
  Retour utilisateur : création vocale, consultation, annulation et Stop
  confirmés sur Android. Ne clôture
  pas F07 : permissions, exposition HA et diffusion physique restent à faire.
  Les règles de consultation/annulation restent à confirmer en P02.

- [x] **S14 — Raccorder les sonneries du banc à un terminal ESPHome.**
  Le 27 octobre, à la demande de l'utilisateur : Home Assistant voit la carte
  Waveshare `eb05fc` au repos, dans Bureau / RDC, firmware jyoushiki v2.0.0.
  Ses actions natives `start_ringing` et `stop_ringing` sont disponibles avec
  le compte HA propre à Alfred. La carte est configurée sur le RDC dans
  `.local/data/bell-targets.json` ; aucune action de sonnerie réelle n'a été
  envoyée pendant la recette, l'utilisateur étant à distance.
  **Dépend de : S09, S13, F01.**
  Implémenté : déclenchement par étage, arrêt après Stop/annulation du dernier
  minuteur, journal d'appel avant envoi, pas de nouveau départ après réponse réseau
  incertaine ni de sonnerie tardive au redémarrage ; arrêt retenté si nécessaire.
  Coupure native du firmware après 15 minutes, possibilité de sonner pour une
  nouvelle échéance ultérieure. État de demande ou d'erreur affiché, sans déclarer
  le son entendu sur simple réponse HA. Aucun proxy ou modification firmware.
  Recette : 142 tests Python réussis, 1 optionnel non activé, 26 tests JS réussis ;
  neuvième test ciblé supplémentaire sur échéance après 15 minutes réussi.
  Sonnerie réelle, arrêt physique ou par la voix et comportement multi-terminaux
  restent à vérifier en F07/T07. Les minuteurs Assist partagent la sonnerie native ;
  un arrêt local Assist n'est pas encore remonté à Alfred.
- [ ] **S15 — Expérimenter le clonage de voix.** Créer, à partir d'un échantillon
  français de 10 à 20 secondes avec accord explicite de la personne, un profil de
  voix local rapide sur CPU ; conserver la référence dans les données
  privées, jamais dans Git, et ne pas produire d'imitation trompeuse. **Dépend de : S04.**
  30 octobre : l'utilisateur fournit un échantillon de 30 s. Qwen3-TTS GGUF 0.6B
  Q8 est écarté sur CPU (5,4 à 9,1 s pour 2,2 à 4,4 s d'audio). Pocket TTS 4.0.1
  est retenu, avec 0,39 à 0,86 s de génération pour 2 à 3,3 s sur deux threads.
  L'échantillon complet est préparé en privé sous `.local` (meilleure similarité
  de timbre que les extraits courts), le choix Pocket est
  intégré avec repli Supertonic M3 et le profil `.safetensors` est exporté et actif.
  Mesures du clone livré par l'API : 600 ms de médiane et 655 ms au p95 ;
  similarité ECAPA moyenne 0,475 avec la référence nettoyée, contre 0,426 avant
  nettoyage et une valeur négative pour M3.
  « Alfred » est reconnu correctement, « majordome » reste transcrit « majeur
  d'homme » par Whisper. Restent l'écoute subjective du timbre et de la diction,
  puis la validation de la qualité sur les futurs appels réels. Le profil n'est
  pas encore déclaré final.
  Retour utilisateur du 30 octobre : seul le sample semblait utiliser le clone,
  les autres réponses reprenaient la voix standard. Défaut reproduit : le délai
  de 2,5 s portait sur toute la synthèse, provoquant le repli des phrases longues.
  Corrigé : 2,5 s entre blocs, limite totale de 60 s ; secours conservé en cas
  d'erreur ou de dépassement. 22 tests ciblés réussis. Après relance, quatre
  synthèses réelles successives de 40 à 253 caractères utilisent Pocket sans
  repli, dont une génération de 2 835 ms. Écoute humaine encore à valider.
  Conversation réelle Command Code → Pocket également vérifiée : réponse de
  312 caractères, synthèse de 3 809 ms, moteur Pocket et aucun repli.
  Nouveau retour utilisateur : le timbre dérive après quelques mots et la hauteur
  change. Qualité refusée en l'état ; la présence du moteur Pocket ne suffit pas
  à valider la voix. Comparaison locale en cours : température de génération et
  longueur des segments, sans modifier ni publier la référence privée.
  Essai retenu : limite de regroupement abaissée de 50 à 25 tokens, avec copie
  explicite du profil pour chaque génération ; température inchangée à 0,3.
  Sur deux textes longs et deux graines, similarité ECAPA moyenne avec la
  référence de 0,612 à 0,645 ; pour les quatre dernières secondes, de 0,464 à
  0,532. Couverture indicative des mots par Whisper : 78,4 % à 92,7 %.
  La température 0,15 n'a pas aidé et n'est pas appliquée. Ces mesures ne
  prouvent pas la correction des changements de hauteur ; nouvelle écoute
  nécessaire. Audios et scripts de comparaison conservés sous `.local`.
  24 tests ciblés réussis, dont deux essais Pocket → Whisper réels (court et
  long). Service relancé ; réponse de 253 caractères générée par Pocket en
  3 423 ms sans repli, disponible pour écoute privée sous `.local`.
  Retour d'écoute utilisateur : résultat insuffisant, une partie du caractère
  vocal d'Alfred est perdue avec ce réglage. Essai à 25 tokens non validé malgré
  les scores automatiques ; ne pas clôturer S04/S15. Préciser les caractéristiques
  perceptives manquantes avant tout nouveau réglage. Aucun retour automatique à
  l'ancien réglage, qui présentait aussi une dérive audible.
  Précision utilisateur : le timbre et la façon de parler sont les deux aspects
  perdus. Prochain critère de comparaison : ressemblance perceptive sur ces deux
  axes ; aucune variante acceptée sur la seule base des mesures automatiques.
  Comparaison A/B : A (`06-14-out.wav`) préférée par l'utilisateur ; préférence
  relative, sans choix final ni bascule du profil actif. Sert de repère d'écoute.

- [ ] **S16 — Évaluer une voix originale synthétique à identité fixe.** Piste
  proposée par l'utilisateur pour améliorer la constance du timbre et de la
  façon de parler. Distinguer conception d'une voix avec un modèle préentraîné,
  sélection/personnalisation d'une voix fixe et entraînement depuis zéro.
  Vérifier création, réutilisation de l'identité, exécution CPU, coût compatible
  avec 5 €/mois et stabilité sur plusieurs réponses longues. Comparer à A à
  l'écoute ; pas de garantie de stabilité sur la seule origine synthétique,
  ni de dépense ou de remplacement du moteur présumés acceptés.
  **Dépend de : S01, P04, P05.**
  Exploration acceptée par l'utilisateur. Banc privé sous
  `.local/synthetic-voice-bench/` : trois profils fixes Supertonic M2/M1
  interpolés (80/20, 50/50, 20/80), débit 0,96 ; essais courts et longs.
  Interpolation expérimentale, sans garantie constructeur de qualité ; aucun
  clonage ni entraînement depuis zéro. A sert de repère de présélection seulement.
  Écoute comparative à faire ; profil du service inchangé.
  Six synthèses vérifiées : trois courtes et trois longues, profils exportés et
  rechargés avant synthèse. Couverture indicative Whisper : 91,7 % sur les courtes,
  88,9–91,7 % sur les longues. Synthèse 3,5–3,6 s pour environ 6 s d'audio court,
  9,4–9,7 s pour environ 16 s d'audio long. Début/fin évalués automatiquement,
  sans conclusion de constance à l'oreille ; latence interactive non validée.
  2 novembre : l'utilisateur préfère le deuxième prototype (M2/M1 à 50/50,
  débit 0,96). Base retenue pour la suite des essais ; écoute longue, stabilité,
  latence et choix définitif encore ouverts. Aucun changement de voix active.
  Précision du 2 novembre : débit légèrement plus rapide et voix perçue autour
  de 70 ans. Essais `essai-2-rapide-*` et `essai-2-patine-*` sous le même banc :
  vitesse 1,08 au lieu de 0,96 (hausse de 12,5 % du paramètre), profil inchangé.
  Version patinée : coloration spectrale, saturation légère et souffle faible,
  sans changement de pitch. Approximation expérimentale, âge non contrôlable
  directement dans Supertonic ; aucun résultat perceptif validé. WAV courts
  et longs générés et relus par Whisper : 5,36 s et 14,28 s d'audio, produits
  en 1 144 ms et 2 866 ms dans ce banc ; diction toujours à écouter, notamment
  « majordome ». Ne pas attribuer toute la baisse de latence au nouveau débit :
  les conditions de charge diffèrent des premiers essais.
  Retour utilisateur : patine rejetée, impression de saturation/haut-parleur
  cassé ; aucune panne physique démontrée. Demande de 15 % de débit en plus.
  Nouvel essai propre à 1,242 (1,08 × 1,15), sans aucun effet de patine ni
  changement de hauteur, avec gain uniforme seulement. WAV vérifiés finis et
  sans échantillons écrêtés ; audio court 4,67 s, long 12,40 s, synthèse 1 071 ms
  et 2 590 ms. Fichiers `essai-2-propre-1242-*` dans le banc privé. Diction,
  qualité perçue et âge de 70 ans restent ouverts ; service inchangé.
  Retour suivant : « impec », voix propre à 1,242 acceptée comme référence.
  L'utilisateur demande des essais plus nobles sans perdre cette base.
  Deux variantes séparées préparées sous `noble-01/` : cadence seule sur texte
  identique et registre plus soutenu. Même profil et vitesse, pauses explicites,
  aucun effet de patine ou pitch. WAV générés sans écrêtage et contrôlés par
  Whisper ; 13,80 s / 14,01 s d'audio, synthèses 3 209 / 3 459 ms. La variante
  de cadence seule présente une transcription imparfaite de la durée : ne pas
  la confondre avec une recette réussie de diction. Retour utilisateur : essai
  noble abandonné ; conserver explicitement `essai-2-propre-1242-long.wav`,
  profil 2 à 1,242 sans effet. Fin des variantes de cette série ; S16 reste
  ouvert pour la recette technique, S18 pour l'intégration.

- [x] **S17 — Conserver la voix de référence acceptée dans une banque locale.**
  Demandé le 2 novembre ; « Alfred — référence validée », profil synthétique 2,
  débit 1,242, sans effet. Copie du profil, des deux WAV acceptés/associés,
  du script de génération et du rapport sous
  `.local/data/voice-bank/alfred-reference-20261102/`, avec manifeste et paramètres.
  Identité binaire des cinq copies vérifiée par SHA-256 ; archive exclue de Git.
  Les variantes nobles restent distinctes et ne remplacent pas cette référence.
  **Dépend de : S16 (base acceptée à l'écoute).** Ne vaut pas activation dans
  l'interface ni validation de l'âge vocal de 70 ans.

- [x] **S18 — Raccorder la référence de la banque au service et au sélecteur.**
  Réalisé après le « go » utilisateur : charger le profil
  fixe et son débit depuis la banque, utiliser les mêmes paramètres pour sample
  et conversation, préserver la référence et distinguer les variantes d'essai.
  Vérifier persistance du choix, métadonnées et comportement en cas d'absence
  du profil. **Dépend de : S17.** Voix `alfred-reference` activée et persistée
  sur le service relancé. Profil vérifié par SHA-256, paramètres et gain de la
  référence conservés ; absence/altération signalée sans changement silencieux,
  autres voix toujours sélectionnables. 271 tests Python réussis, 3 réels
  optionnels ignorés ; 29 tests JS réussis. Contrôles réels : sample 2 013 ms,
  texte de 215 caractères 2 940 ms (12,40 s d'audio), conversation de
  253 caractères 3 029 ms de synthèse. Même voix à 1,242, aucun repli, préférence
  persistée et HTML du sélecteur vérifiés. Recette humaine micro et ESP32 ouverte.
  Retour humain suivant : « ça va c'est acceptable ». Appréciation générale
  acquise, sans mesure ni détail de scénarios ; essai ESP32 toujours non réalisé.


- [ ] **S19 — Réduire le délai avant la réponse vocale ESP32.** Retour utilisateur
  du 4 novembre : conversation fonctionnelle mais lente. Mesure initiale :
  STT 2 126 ms, IA 2 584 ms, TTS 7 635 ms. Profil et débit de référence conservés.
  Quatre threads CPU testés (+11 % de vitesse sur petit banc), lancement Windows
  normal et HighQoS ciblé sur Alfred. Sur un même texte de 215 caractères :
  ~6 400 → ~2 330 ms de TTS à chaud ; 3 729 ms à froid après redémarrage.
  74 tests ciblés réussis. Diagnostics de latence sans texte privé ajoutés.
  Demande suivante : produire la voix par blocs et les jouer pendant le calcul
  des suivants. Flux progressif livré et actif : synthèse par phrases/clauses,
  profil verrouillé pour toute la réponse, FLAC continu HTTP chunked. Le texte
  final et les actions restent validés avant la parole. Code : `audio_stream.py`,
  `terminal.py`, voie interne de conversation à TTS différé. Tests d'ordre,
  décodage, envoi avant génération du bloc suivant, arrêt et absence de rejeu
  réussis. Test réel sur quatre blocs : première demande à 2 053 ms, un bloc prêt,
  audio total prêt à 4 480 ms ; lecture de 14,98 s terminée selon la carte.
  Temps de ce diagnostic hors STT/IA ; ce n'est pas une mesure du premier son.
  290 tests Python réussis, 3 optionnels ignorés ; 29 tests JS réussis.
  Option `progressive_tts: false` de retour au mode complet. Retour d'écoute du
  5 novembre : petites pauses audibles, mais voix propre. Rendu vocal confirmé,
  continuité à améliorer sans changer profil ni débit. Mesures suivantes : sur
  les blocs témoins, silence cumulé de 1 035–1 230 ms par jonction, sans besoin
  d'attendre la génération suivante. Correction des seuls bords internes : RMS
  -60 dBFS, garde d'au moins 80 ms en tête / 180 ms en fin, trame de protection,
  raccord sur faible amplitude ; début/fin de l'énoncé et pauses internes conservés.
  Sur les mêmes blocs : jonctions 290 / 291 / 290 ms, 2 575 ms retirées.
  Tests de conservation bit à bit de la parole, consonnes faibles et pauses
  internes à 16 / 44,1 / 48 kHz réussis. Correction déployée, 294 tests Python
  réussis et 3 optionnels ignorés. Extrait rejoué : quatre blocs, fin de lecture
  confirmée, 12,70 s d'audio, 2 276 ms de marges retirées sur cette génération,
  première demande audio à 1 969 ms. Voix et débit vérifiés inchangés.
  Après rejeu corrigé, retour utilisateur du 5 novembre : « c'est très bien ».
  Rendu et continuité de l'extrait validés ; réglage conservé, profil et débit
  inchangés. Gain perceptif global après une demande réelle en conversation
  encore à confirmer : S19 reste ouvert pour cette seule vérification.
  **Dépend de : S18, T04, P05.**

- [x] **S20 — Terminer la prise ESP32 malgré un fond musical.** Retour du
  6 novembre : texte bien reconnu, mais fin seulement quand la musique est coupée.
  Cas : ESP32, musique chantée sur autre appareil. Défaut du seuil de volume
  distinct du décodage STT. Remplacement livré par Silero VAD v6 local déjà
  fourni avec faster-whisper, état réinitialisé à chaque prise ; pause900ms,
  pré-capture et PCM inchangés. Pas de baisse de musique externe, de changement
  de gain/firmware ni de nouvelle capture implicite. Statut `speech_detector`
  et `last_capture.end_reason`, résultat de test lisible dans la page.
  303 tests Python réussis, 4 optionnels ignorés ; test intégré TTS+fond
  instrumental synthétique également réussi. La prise se termine avec le fond
  encore présent et garde la phrase entière. Ce fond n'est pas du chant :
  validation utilisateur sur son morceau ensuite acquise. Le modèle ne sépare
  pas les locuteurs ; voix chantées et TV restent des limites possibles.
  Service relancé, carte connectée, modèle actif vérifié. Retour humain du
  6 novembre après nouvel essai : « très bien ça fonctionne nickel » ; scénario
  musical de l'utilisateur validé, réglage conservé. Statut de reprise :
  `speech_pause`, prise de 5 432 ms, pas d'erreur. Ce succès ne clôture pas les
  recettes de tous les morceaux, TV, distances ou conditions de charge.
  **Dépend de : S03, T04, S06.** Prioritaire avant le réveil et les nouveaux modules.

- [ ] **S21 — Corriger la préparation française pour la synthèse vocale.**
  Retour du 8 novembre : lecture incorrecte des heures et « plus » négatif prononcé
  avec un s (exemple de pâtes). Voix de référence et débit 1,242 conservés.
  Livré : `alfred/tts_text.py`, appliqué à toutes les synthèses, y compris blocs
  progressifs et repli. `20h43`, `20 h 43` et `20:43` deviennent « vingt heures
  quarante-trois » ; heures/minutes valides seulement. Négations d’absence explicites
  reformulées (« il ne reste pas de pâtes », « il n’en reste pas »), sans remplacement
  global de « plus » comparatif/positif ni interprétation d’une phrase ambiguë.
  Consigne conversationnelle : heures en lettres, absence formulée explicitement ;
  ne pas confondre liste de courses et inventaire du stock réel. Texte affiché et
  paramètres d’actions inchangés par la préparation TTS.
  Vérification : 159 tests ciblés réussis ; audio réel de 6,06 s généré avec la
  référence Supertonic, débit 1,242, sans repli, sans diffusion sur la carte.
  Échantillon local `.local/tts-pronunciation/essai-francais.wav` pour écoute.
  Retour humain : diction peu naturelle, liaisons manquantes et s de « plus »
  toujours signalé. Correction insuffisante à l’écoute ; S21 reste ouvert. Les
  tests logiciels ne valident pas la qualité phonétique. Voir comparaison S22.
  **Dépend de : S04, S05.**

- [ ] **S22 — Comparer la diction française des moteurs TTS.** Nouveau besoin du
  8 novembre après retour négatif sur S21 : évaluer liaisons obligatoires/interdites,
  prosodie, homographes « plus », heures et réponses courtes. Isoler d’abord les
  effets du profil, du débit 1,242 et du découpage par rapport au moteur lui-même.
  Comparaison proposée sur les mêmes phrases : Supertonic actuel, autre moteur
  local francophone et éventuellement service distant dans le budget existant.
  Documentation consultée : Chatterbox Multilingual prend en charge le français,
  qualité et délai sur l’hôte cible non mesurés ; Kokoro officiel ne fournit qu’une
  voix française féminine et signale des limites possibles de phonémisation.
  Comparaison autorisée ensuite : voix actuelle à 1,242, même profil à 1,0 puis
  Chatterbox français. Environnement et modèles Chatterbox existants réutilisés
  hors ligne, banc sous `.local/tts-comparison-20261108/`. Aucun moteur alternatif
  adopté ni service payant engagé ; garder la référence active jusqu’au choix
  humain. Banc livré : A référence à 1,242, B même profil à 1,0, C Chatterbox
  Multilingual v2 en français, conditionné sur le sample synthétique d’Alfred.
  Même texte non reformulé en une seule prise ; aucun son envoyé sur la carte.
  Générations de la réponse courte sur l’heure, médianes de trois essais à chaud :
  A 0,530 s, B 0,666 s, C 9,826 s, sur CPU du PC, hors chargement et autres étapes.
  Douze WAV vérifiés ; contrôle Whisper des phrases principales effectué, sans
  validation des liaisons ou de la phonétique. Chatterbox a émis des avertissements
  d’arrêt/répétition ; couverture et naturel restent à écouter. Banc v2 existant,
  pas le checkpoint v3, ni un essai GPU. Rapport `docs/COMPARAISON_TTS.md`.
  Service principal sain, référence active et veille Jarvis reçue au contrôle final.
  Retour humain reçu : C nettement meilleur ; A et B jugés équivalents pour le
  français. Préférence Chatterbox pour la diction de l’extrait acquise ; le simple
  ralentissement de Supertonic ne répond pas au défaut selon cet essai. Reste à
  résoudre la latence sur l’hôte cible et tester les autres phrases, le profil
  et l’intégration éventuelle ; S22 non coché. Aucun remplacement actif réalisé.
  Ne pas reprendre Qwen CPU sans considérer
  les mauvais délais déjà mesurés. **Dépend de : S04, S21, P04, S08.**

- [ ] **S23 — Réduire la latence Chatterbox sur la cible Alfred. Essai CPU rejeté pour l’usage courant.** Travail autorisé
  le 8 novembre après préférence humaine pour C. Cible précisée pendant les essais :
  nouvel AuBox 8745HS/32 Go/780M sous Proxmox, Alfred dans une VM Debian, matériel
  encore attendu. Aucun remplacement actif et aucune opération Proxmox effectués.
  Banc local CPU/GPU séparé livré : GPU RTX FP32 1,842 s de médiane courte contre
  9,826 s initialement sur CPU ; FP16 1,940 s, INT8 CPU 15,049 s. Contrôle CPU
  PyTorch 2.6 : 8,749 s à quatre threads, 7,979 s à huit threads (petit banc,
  chevauchement partiel de charge). Échantillons non identiques entre versions.
  ONNX Q4 CPU : 3,711 s sur phrase courte mais texte long invalide (600 tokens,
  pas de fin normale, 43,254 s, fin de texte omise à la transcription). Variante
  non retenue. Le contrôle CPU PyTorch 2.6 dérive aussi sur texte long : 129,486 s
  pour 36,7 s d’audio. Alertes de nombres/omissions à la transcription GPU ; écoute
  humaine encore requise, pas de validation acoustique par Whisper seul.
  33 WAV vérifiés. `scripts/bench_chatterbox.py` livré, CLI et compilation vérifiées,
  exécuté réellement sur CPU local ; poids/référence locaux, zéro téléchargement
  implicite, WAV/JSON seulement. Rapport `docs/TTS_LATENCE_AUBOX.md`.
  À réception : profil CPU de la VM, ressources et charge homelab, mesures 2/4/8
  threads, robustesse sur plusieurs phrases/graines et premier son de bout en bout.
  Radeon non présumée accessible/compatible en invité Debian ; pas de transposition
  des mesures CUDA vers l’AMD. Pas encore de solution fluide et fiable validée sur
  l’hôte final ; S23 reste ouvert.
  Demande suivante : essai immédiat sur le CPU du PC actuel, sans attendre l’AuBox.
  Livré et activé : voix `chatterbox-cpu`, processus persistant via stdio, dépendances
  isolées dans l’environnement CPU existant, mêmes paramètres que C ; aucun GPU,
  audio en mémoire uniquement. Disponibilité, sélection persistante, statut,
  synthèse simple et progressive, fermeture et délais bornés raccordés. Référence
  Supertonic conservée et sélectionnable pour retour manuel, aucune substitution
  automatique sur panne Chatterbox. Heures développées, « plus » laissé au moteur.
  Test HTTP réel d’abord à 40,115 s ; même réglage HighQoS Windows que le parent
  ajouté à l’enfant pour éviter le ralentissement du service sans fenêtre.
  Après correction : 9,096 s / 2,94 s d’audio sur l’heure, réponse HTTP 200,
  voix Chatterbox et aucun repli. Le worker est conservé entre deux demandes.
  430 tests Python réussis, 4 optionnels ignorés ; 30 tests JS réussis, dont le choix
  Chatterbox ; 5 tests ciblés après HighQoS. Recette humaine avec Jarvis, naturel,
  attentes et réponses longues encore ouverts ; ne pas confondre activation
  fonctionnelle et validation de fluidité. Retour utilisateur suivant : trop lent,
  trouver un autre moyen/outil. Chatterbox CPU arrêté, plus la solution active ;
  privilégier S24. Qualité de C ne vaut pas acceptation de son délai ni validation
  définitive de la voix. **Dépend de : P04, S19, S22, T04.**

- [ ] **S24 — Évaluer une diction française rapide via le TTS Cloud existant.**
  Demande du 8 novembre après rejet de la latence Chatterbox CPU. Piste vérifiée
  dans HA : `tts.home_assistant_cloud` et voix masculine `HenriNeural` déjà configurée.
  Abonnement déjà payé confirmé par l’utilisateur ; aucun nouvel achat ni secret.
  Banc livré : 265/297/295 ms pour trois réponses courtes distinctes ; 1 783 ms pour
  le texte comparatif long / 13,25 s d’audio. Cache permanent désactivé, aucune
  lecture sur les appareils. Les deux étapes API URL/audio et la conversion sont
  incluses dans ces temps ; pas le STT/IA/ESP32 ni la perception de bout en bout.
  Intégration activée `ha-cloud-henri` : voix sélectionnable, métadonnées correctes,
  synthèse normale et progressive, même accès HA protégé. Requêtes restreintes au
  proxy audio du même HA, redirections refusées, réponses et PCM bornés, erreurs
  sans jeton/texte privé. Aucun choix Cloud implicite ni repli silencieux.
  Service redémarré ; contrôle HTTP 200, synthèse inédite en 1 020 ms pour 5,02 s
  d’audio. Veille Jarvis et terminal connecté, flux reçu. 443 tests Python réussis,
  4 optionnels ignorés ; 32 tests JS réussis. Échantillon d’écoute fourni,
  `.local/tts-cloud-comparison-20261108/henri-long.wav`.
  Restent : retour humain sur naturel, liaisons/plus/heures, délai complet en
  conversation, disponibilité réseau et recette sur VM Debian. Aucun choix vocal
  définitif déduit du seul banc. Retour suivant : l’utilisateur trouve Henri bien,
  mais souhaite un réglage plus proche d’Alfred. Appréciation qualitative de la voix
  acquise ; personnalisation et recette générale restent ouvertes en S25.
  **Dépend de : S04, S21, S22, F01, S08.**

- [x] **S25 — Évaluer une personnalisation légère d’Henri. Essais rejetés.** Besoin exprimé le
  8 novembre après appréciation positive de la voix : se rapprocher d’Alfred en
  gardant rapidité et diction. Le TTS Cloud expose le choix de voix/styles et le
  format audio, sans réglage libre de timbre ou clonage. Deux essais d’écoute
  séparés produits avec FFmpeg/rubberband déjà installé : cadence 0,96, puis
  cadence 0,96/hauteur 0,94 avec formants préservés. Aucun effet appliqué au service.
  Échantillons sous `.local/henri-tuning-20261108/`, durées 13,8 s ; traitement
  146/144 ms et PCM mono valides, sans écrêtage. Pas de nouveau coût ni génération
  Cloud : source générique déjà synthétisée réutilisée. Naturel et rapprochement
  perçu évalué ensuite : l’utilisateur rejette les deux variantes (« c’est mauvais »).
  Évaluation terminée avec résultat négatif : aucune variante retenue, aucun effet
  à intégrer ni réglage d’interface à construire pour ces traitements. Conserver
  Henri original actif, référence Supertonic et décisions antérieures d’abandon
  des patines intactes. Le souhait d’une voix plus proche d’Alfred reste ouvert
  en S04 ; ne pas relancer ces variantes sans nouvelle demande.
  **Dépend de : S24, S04.**

- [ ] **S26 — Comparer Sopro et MeloTTS/OpenVoice en local. Henri préféré après écoute.**
  Le 9 novembre, l’utilisateur autorise la mise en œuvre des deux solutions pour
  les tester. Deux environnements CPU isolés préparés, sans modifier les dépendances
  d’Alfred : Sopro 2.2.0/Python 3.11/PyTorch 2.6 et Melo/OpenVoice/Python 3.10/
  PyTorch 2.2.2. Poids français téléchargés explicitement, révisions conservées.
  Référence commune : sample synthétique Alfred archivé de 12,4 s, pas de nouvel
  enregistrement utilisateur. Imports Melo limités au français et BERT local pour
  éviter les dépendances/modèles des autres langues ; paramètres de synthèse et
  phonémisation française conservés. Filigrane OpenVoice conservé (le moteur peut
  signaler qu’un clip est trop court pour le porter).
  Livré : `local_voice_cpu.py`, `local_voice_models.py`, `local_voice_worker.py`,
  voix `sopro-cpu` et `melo-openvoice-cpu` sélectionnables. Processus persistants,
  CPU explicite, hors ligne après préparation, audio mémoire, délai et taille
  bornés ; pas de repli silencieux ni de choix expérimental automatique.
  Banc sur texte commun : Sopro 820 ms court / 3 178 ms long (10,229 s d’audio) ;
  Melo/OpenVoice 4 352 ms premier court / 8 629 ms long (8,824 s d’audio), puis
  1 871 ms sur négation. Le premier son streaming n’est pas mesuré par ce banc.
  Contrôle API service : deux phrases en 1 264/1 244 ms Sopro, 3 373/1 801 ms
  Melo/OpenVoice, sans repli ; les deux sélections répondent 200. Henri rétabli
  après vérification. Sept WAV mono vérifiés. Whisper retrouve les phrases
  principales ; doute « deux amis » / « deux années » sur Melo, à écouter ; aucun
  contrôle automatique ne valide les liaisons, le timbre ou toutes les prononciations.
  460 tests Python réussis, 4 optionnels ignorés ; 36 tests JS réussis. Compatibilité
  du double vocal sans méthode status corrigée dans le banc STT pour la suite complète.
  Rapport `docs/TTS_SOPRO_MELO_ESSAIS.md`, fichiers `.local/local-tts-comparison-20261109/`.
  ESP32 non joignable au contrôle ; l’utilisateur choisit de tester d’abord les
  fichiers et le navigateur. Aucun réarmement matériel prétendu, pas de firmware
  modifié. Restent : retour humain et choix de voix, robustesse des phrases longues,
  vrai streaming éventuel et recette sur la future VM Debian/Ryzen. S26 non coché
  sur la seule intégration ; aucune voix nouvelle déclarée définitive.
  Retour humain : Henri reste nettement meilleur en diction et rapidité. Les deux
  moteurs locaux ne sont pas retenus pour remplacer Henri à ce stade. La question
  de l’identité vocale Alfred reste ouverte ; priorité à S27 pour les nouvelles
  pistes en ligne, pas à un nouveau réglage de hauteur des essais rejetés.
  **Dépend de : S04, S22, P04.**

- [ ] **S27 — Étudier une voix en ligne plus proche d’Alfred. Proposition.**
  Après préférence affirmée pour Henri en diction et rapidité, souhait de retrouver
  le timbre initial. Catalogue Nabu Casa publié : Claude, Maurice et Yves parmi
  les autres voix françaises ; disponibilité sur l’instance et écoute à vérifier.
  Première proposition : comparer ces voix déjà incluses dans l’accès Cloud.
  Autre proposition : création de voix par description, par exemple ElevenLabs
  Voice Design, avec moteur de synthèse rapide. Aucun compte ou achat lancé.
  Starter affiché à 6 $/mois hors taxes, compatibilité au budget de 5 € non acquise.
  Les ~100 ms annoncées pour Flash concernent une médiane serveur en streaming,
  voix chaude ; ce n’est pas un délai de réponse complet garanti chez l’utilisateur.
  Henri conserve sa place active ; aucune voix ni dépense nouvelle validée.
  **Dépend de : S04, S24, S08.**

- [ ] **S28 — Tester Gradium/Phonon en local. Installé et disponible.**
  Mise en œuvre demandée le 11 novembre. Accès au checkpoint français réussi via
  la configuration locale existante, sans afficher de clé ni accepter de nouvelles
  conditions par automatisation. Runtime `ptts` 0.7.0 installé dans un environnement
  Python 3.11 séparé, sans PyTorch. Modèle `gradium/phonon-40m-fr` Q8, révision
  `d91086970206b88efd2c88ca971d0628b5968f0f`, et deux voix masculines du catalogue
  Gradium : Arnaud/Lucien. Aucune référence privée envoyée, pas de clonage en ligne,
  de compte Gradium créé ou de nouvel abonnement.
  Banc CPU quatre threads : court 198/186 ms, texte long 735/755 ms ; premiers
  blocs natifs 62/39 ms. Ces premiers blocs concernent l’API native Phonon, pas
  encore tout le transport applicatif. Synthèse Alfred via worker persistant :
  Arnaud 308/244 ms, Lucien 331/256 ms sur la même phrase de deux propositions,
  WAV de 3,04/3,12 s, HTTP 200, aucun repli. Henri rétabli, Jarvis actif avec trames
  reçues et terminal connecté. Deux choix ajoutés dans le laboratoire vocal.
  Quatre extraits de comparaison et une première prise générés ; PCM mono vérifié,
  pas d’écrêtage. Whisper retrouve les phrases principales des deux textes longs,
  sans valider le timbre, les liaisons ou « plus ». 479 tests Python réussis,
  4 optionnels ignorés ; 38 tests JS réussis. Test du checkpoint anglais refusé
  dans les contrôles pour empêcher une substitution au modèle français.
  Rapport `docs/PHONON_ESSAI.md`, mesures `.local/phonon-trial-20261111/`.
  Retour humain reçu : « vraiment rapide ». Appréciation qualitative positive
  sur la réactivité ; aucune nouvelle mesure de bout en bout ni voix précise
  déduite. Choix Arnaud/Lucien, diction et timbre encore ouverts.
  Restent : retour humain, choix de voix, autres phrases/nombres, éventuel streaming
  natif bout en bout et recette sur l’hôte Debian. Modèle FR sous CC BY-NC 4.0 ;
  voix personnalisée exportable depuis Gradium Studio en option, non créée ici.
  Conseils de remplissage du formulaire de clonage demandés ensuite : fournis
  sans création ou téléversement par l’agent. Référence sonore non évaluée à partir
  de la seule capture ; attributs proposés à faire correspondre au locuteur réel.
  Création, choix de l’extrait, validation humaine et export de voix personnalisée
  restent à confirmer. Aucun profil vocal personnel ajouté aux documents.
  Parcours d’export demandé et vérifié : catalogue Studio, menu de la voix,
  « Download for Phonon », fichier .safetensors à conserver sous .local ;
  fichier ensuite fourni et importé localement. L’export audio WAV/MP3 ne remplace
  pas ce fichier de voix. Ne pas demander de clé API dans le chat.
  Pas de performance ou équivalence à Henri promise avant écoute. S28 non coché
  sur la seule réussite logicielle.
  Profil personnel fourni ensuite dans docs : copie privée vérifiée et original
  conservé, exclusion /docs/*.safetensors de Git, zéro fichier de profil suivi.
  Ajout et activation de `phonon-alfred-cpu` dans le service et le sélecteur.
  Test natif : 369 ms court / 794 ms long (10,32 s d’audio). HTTP réel : 395/330 ms,
  WAV valide, moteur Phonon, aucun repli ; Jarvis actif et flux ESP32 reçu.
  82 tests Python ciblés et 39 tests JS réussis. Aucune nouvelle requête de
  clonage/cloud ni exposition du profil. Henri disponible pour retour manuel.
  Activation d’essai vérifiée, naturel et ressemblance à écouter ; pas de
  validation vocale définitive déduite de la réussite technique.
  Second clonage fourni ensuite et activé à la demande : export différent copié
  en version 2 dans .local, original docs conservé et ignoré par Git ; version 1
  et ancienne configuration conservées. Worker réellement rechargé sur le nouveau
  fichier. Test natif long 849 ms / 10,32 s ; HTTP 391/341 ms / 3,92 s, sans repli.
  Jarvis actif, carte connectée, flux reçu. Pas de changement de code : contrôles
  réels modèle/service adaptés, pas de relance sans motif des suites logicielles.
  Retour : le profil précédent convient moins ; nouvel export fourni, nommé
  Dumby à la demande de l’utilisateur. Profil stocké séparément sous .local,
  choix `phonon-dumby-cpu` ajouté au sélecteur et activé. Profils Alfred 1/2
  conservés, pas de nouveau clonage ou appel Cloud. Test natif : 956 ms / 11,36 s.
  HTTP réel : 323/244 ms pour 3,2 s d’audio, moteur Phonon et aucun repli.
  83 tests Python ciblés et 40 tests JS réussis. Jarvis actif et flux ESP32 reçu.
  Dumby est le choix d’essai actuel ; acceptation du timbre/diction encore ouverte. **Dépend de : S04, S24, P04.**

- [x] **S29 — Ne conserver que les voix Phonon dans Alfred.** Demande du
  11 novembre. Les seuls choix sont Dumby, Alfred cloné, Arnaud et Lucien ; Dumby
  actif et par défaut. Henri, Pocket, Supertonic/référence, Chatterbox, Sopro et
  Melo/OpenVoice retirés de l’interface, du registre et de l’API. Anciennes requêtes
  422, anciens choix persistés ramenés à Dumby ; panne Phonon signalée sans autre
  timbre de secours. Chargements et synthèses des anciens moteurs retirés du
  service ; worker local uniquement Phonon. Dépendances TTS Pocket/Supertonic
  retirées des listes d’installation. Archives d’essai conservées sous .local,
  modèles et références historiques non effacés, intégration HA de la maison
  conservée. Ne pas réintroduire ces anciennes voix à partir des tâches historiques
  sans nouvelle demande. README et tests adaptés au retrait.
  480 tests Python réussis, 2 optionnels ignorés ; 34 tests JS. Service relancé,
  liste réelle de quatre Phonon, anciens choix refusés, synthèse Dumby en 307 ms
  / 3,2 s, sans repli ; Jarvis actif et réception confirmée. La qualité définitive
  de Dumby reste en S28, pas déduite de ce nettoyage. **Dépend de : S28.**

## 4. Identités, permissions et mémoire

- [x] **I01 — Définir l'enrôlement.** Deux adultes et un enfant, échantillons à
  collecter, stockage/suppression et renouvellement ; données privées hors dépôt.
  **Dépend de : P01, S02.**
  Décidé et implémenté le 26 octobre : trois phrases dites deux fois (six passages de
  six secondes au plus), environ vingt secondes par personne ; audio conservé avec les
  empreintes sous `.local/data/profiles`, hors dépôt ; suppression du profil effaçant
  l'audio ; renouvellement par réenrôlement, les passages s'ajoutant aux existants.
  Moteur retenu : ECAPA-TDNN VoxCeleb via SpeechBrain 1.1.2 et PyTorch 2.14.1, modèle
  de 85 Mo dans `.local/models`, sans réseau pendant l'enrôlement, licence Apache 2.0.
  Écran et API livrés : création, enrôlement guidé, réécoute, suppression.
  12 tests réussis (7 stockage, 5 API) ; parcours HTTP réel effectué sur le service
  local avec voix Piper. La reconnaissance en conversation reste hors de ce point.
- [ ] **I02 — Tester l'identification par personne.** ECAPA, phrases courtes, inconnus,
  enfant, bruit et changements de locuteur ; calibrer les seuils et l'incertitude.
  Inconnu = invité autorisé, sans accès aux mémoires privées ; un enfant non reconnu
  peut échapper à ses restrictions, conformément au choix utilisateur.
  **Dépend de : I01, P05.**
  Mesure du 26 octobre sur voix synthétique : 0,84 pour la même voix, 0,93 entre deux
  bruits sans rapport. Le cosinus brut ne sépare pas ; normalisation et calibration par
  personne indispensables avant tout seuil.
  29 octobre : l'utilisateur demande le raccordement de la reconnaissance. Préparer
  une calibration avec essais indépendants, au moins une voix différente et refus
  des scores incertains ; aucune décision d'identité ne doit dépendre d'un seuil
  arbitraire ou d'un simple bruit. Tester le changement de locuteur et l'isolement
  des contextes ; la reconnaissance ne remplace pas les permissions I03.
  30 octobre : calibration expérimentale et reconnaissance en conversation
  implémentées avec au moins deux personnes, six échantillons chacune et deux
  essais indépendants par profil ; les voix trop proches sont refusées et une
  modification des profils invalide la calibration. Un seul profil humain est
  actuellement enrôlé avec six échantillons et aucun fichier de calibration
  validée n'existe. L'essai réel avec une seconde voix reste nécessaire ; le
  mécanisme n'est ni une authentification ni une permission I03.
- [ ] **I03 — Appliquer les permissions avant accès et action.** Règles par profil,
  confirmations par action et contrôle de chaque outil, sans déléguer la décision
  au seul prompt du modèle. Tester invité/enfant/adultes. **Dépend de : I02, P01, S01.**
  30 octobre : cadrage retenu ; restrictions propres à l'enfant et contrôles par
  action à préciser. Reconnaissance non calibrée : ne pas prétendre appliquer les
  restrictions à un locuteur identifié avant validation de I02.
  Différé par l'utilisateur avant la mise en production ; préparation fonctionnelle
  des autres modules possible sans considérer les permissions comme acquises.
- [ ] **I04 — Construire les mémoires commune et personnelles.** Extraction utile,
  confirmation pour le sensible, provenance, consultation/correction/effacement et
  séparation des profils, y compris lors des changements de locuteur. Pas de mémoire
  personnelle invités ni alimentation automatique de la mémoire commune par eux.
  **Dépend de : I03, P01, S05.**
- [x] **I05 — Ajouter l'historique de diagnostic.** Textes/réponses/actions/erreurs/
  durées, invités inclus ; sept jours ET 100 Mo maximum, purge automatique, aucun
  audio brut ni secret. Séparer ce journal des souvenirs persistants et en contrôler
  l'accès. **Dépend de : S01, P06.**
  13 novembre : demande explicite de consulter les essais de lumière ; constat que
  seul le dernier échange ESP32 est accessible, sans historique persistant. Priorité
  à ce journal pour recetter la compréhension ; aucun historique antérieur recréé.
  Livraison : journal SQLite borné et purgé, consultation/export/annotations via
  commande locale, raccordement conversations et API directe, sans nouvelle route
  réseau. Compteurs d'usage conservés, audio et secrets exclus. Tests de rétention,
  taille, annotation et masquage réussis. Purge automatique chaque minute même
  sans conversation, et à la consultation/écriture. Contrôle réel après redémarrage :
  conversation, identifiant d'échange et entrée SQLite vérifiés sans action d'appareil.
  Consultation/export CLI locaux ; aucune nouvelle route réseau d'historique.

## 5. Fonctions de la maison

- [ ] **F22 — Compréhension sémantique et recette quotidienne.** Plan approuvé et
  implémentation autorisée le 13 novembre ; aucun comparatif ni changement de modèle.
  Outil IA et exécuteur commun des lumières : marche/arrêt, état, intensité, couleur,
  blanc en kelvins, contrôles de cibles/capacités/groupes, relecture et statuts distincts.
  Six échanges/cinq minutes par source/session/profil ; propositions de trente secondes,
  reprises locales/IA, lots de quatre préparés avant envoi et arrêt sans répétition.
  Nouveaux outils minuteur/appareil livrés derrière réglages locaux désactivés par
  défaut ; les outils des autres fonctions déjà actives sont conservés. Pas de
  généralisation avant recette. Corpus : cinq cents cas synthétiques, dont cent
  de validation par familles distinctes. Trente cas de développement réels au
  modèle : trente réussites, médiane 1,85 s/p95 2,695 s, appareils simulés.
  Validation indépendante : cent intentions exactes sur cent cas synthétiques,
  médiane 1,8005 s/p95 2,476 s, texte et appareils simulés. Aucun cas de validation
  réutilisé pour retoucher le prompt. Suite complète : 722 tests Python réussis,
  deux ignorés ; 43 tests JavaScript réussis. Derniers contrôles ciblés : 263 tests
  réussis ; après maintenance finale, 92 tests ciblés réussis. Lecture HA réelle
  de la lumière du bureau confirmée avec écriture interdite dans le pilote de recette
  (901 ms, hors STT/IA/TTS). Service relancé, santé et catalogue HTTP 200, treize lumières autorisées,
  modèle configuré conservé, ESP32 connecté et veille réarmée. Contrôle applicatif
  et historique réels sans action d'appareil. Recette humaine/audio, latence vocale,
  coût quotidien et objectif de 99 % restent à établir. Voir `docs/COMPREHENSION_DOMOTIQUE.md`. **Dépend de : F01, F02, S05, I05.**

- [ ] **F24 — Piloter les groupes de lumières exposés.** Validé par l'utilisateur
  après le refus Moodlight. Le groupe autorise ses membres masqués dans son seul
  sous-arbre, sans exposition individuelle supplémentaire ; exclusions de groupe,
  sous-groupe ou lampe prioritaires. Graphe privé séparé du catalogue public,
  cycles/membres manquants refusés, feuilles dédupliquées, références conversationnelles
  conservant l'autorité du groupe. Suite complète : 733 tests réussis, deux ignorés ;
  après ajout de l'attente bornée d'état, 294 tests ciblés réussis. Préparation réelle de
  Moodlight réussie : trois lampes, toutes toujours masquées individuellement, aucun
  appel d'écriture HA. Service redémarré, santé/catalogue HTTP 200, groupe visible
  et membres toujours masqués ; ESP32 reconnecté et veille réarmée. Courte attente
  de confirmation d'état ajoutée sans retry d'écriture. Recette vocale/physique à
  confirmer par l'utilisateur.
  **Dépend de : F01, F22.**

  Retour ESP32 du 20 novembre : les demandes d’allumage du Bureau et du groupe
  Ambiance ont chacune envoyé une commande, puis arrêté la séquence faute de
  confirmation d’état. Le journal ne conserve ni la première lampe effectivement
  commandée ni le détail des relectures. À vérifier lors de la recette physique,
  en distinguant le délai de remontée d’état d’un échec de lecture ou d’allumage.
  L’utilisateur confirme qu’une seule lampe s’est allumée pour le Bureau.
  Attente cumulée entre relectures portée de 300 ms à 2 s par lampe. Le test
  simule trois états obsolètes puis une confirmation et vérifie la poursuite
  du groupe sans renvoi. 105 tests ciblés réussis ; service redémarré, santé
  et API de la PWA vérifiées. Nouvel essai physique à faire.

- [ ] **F25 — Musique et volume en langage naturel.** Plan du 13 novembre mis en œuvre.
  Lecteur `media_player.amp_salon_2` sélectionné dans Alfred, aucune substitution,
  exposition/capacités/exclusions vérifiées. Panneau avec recherche et sélection
  de playlist par URI ; API réelle : dix-huit playlists distinctes (douze locales,
  six Qobuz). Absence de playlist par défaut provoque une clarification, sans
  lecture. « Mets de la musique » lance la sélection enregistrée.
  Exécuteur commun local/IA : lecture explicite, reprise, pause, arrêt, pistes,
  sourdine, volume exact et variation de cinq points ; contexte partagé et lots
  de quatre préparés avant écriture. Recherche précise annoncée envoyée sans
  certitude de piste ; résultats vérifiables relus. Volume normal séparé de
  l'atténuation ; correction manuelle externe respectée. Action incertaine arrête
  la suite sans répétition. Tests : 749 Python réussis/deux ignorés, 43 JS réussis,
  syntaxe panneau valide. Corpus synthétique musical de 104 cas, vingt de validation
  indépendante : développement 20/20, validation 20/20, p95 2,263 s sur modèle
  actuel et appareils simulés. Service redémarré ; santé/musique/playlist/catalogue
  HTTP 200 ; ESP32 connecté et veille réarmée. Aucun son ni appareil actionné dans
  les contrôles réels. Recette humaine après choix de la playlist par défaut à faire ;
  minuteurs après cette recette. **Dépend de : F22, F18.**

- [ ] **F26 — Minuteurs naturels et recette.** Demande du 13 novembre après validation
  qualitative musique (« ça marche au top »). Compréhension locale et outil IA
  bornés partagent `TimerActions` et le `TimerService` existant : création avec
  durées libres, « dans cinq minutes… », ajout annoncé, liste, annulation par
  numéro stable et arrêt de sonnerie. Étages, plafond sept jours, négations, mixte
  minuteur/lampe et paramètres invalides conservent les protections historiques.
  Lots de quatre actions ordonnées ; interruption arrête la suite sans supprimer
  les minuteurs déjà créés. Relais IA actif après les tests, présent dans les outils
  du modèle quand le floor est disponible. Suite complète : 763 tests Python
  réussis/deux ignorés, 43 JS réussis. Corpus synthétique : 104 cas, développement
  20/20 et validation indépendante 20/20, stockage temporaire. Service redémarré,
  santé/musique/playlists/échéances HTTP 200 ; six minuteurs actifs existants conservés,
  ESP32 connecté et veille réarmée. Aucun nouveau minuteur persistant créé pour la
  recette automatisée. Essai micro, sonnerie réelle et reprise après redémarrage
  restent à confirmer. **Dépend de : F07, F22, F25.**

- [ ] **F23 — Généraliser la compréhension après recette des lumières.**
  Diagnostic du 17 novembre, essai imprimante : relais `devices` effectivement
  désactivé, donc outil `controler_appareil` et catalogue des switchs absents du
  contexte IA. « allume-la » aboutit à un refus conversationnel, avant confirmation.
  Après accord utilisateur : relais activé localement et catalogue réel vérifié.
  Modèle réel en texte : demande explicite et « allume-la » conduisent à la
  confirmation ; annulation puis allumage après oui réussis sur l'imprimante.
  État activé relu séparément, santé `ok`, aucun redémarrage nécessaire.
  145 tests ciblés réussis. Recette vocale humaine et autres appareils ouvertes.
  Ordre approuvé : musique/volume, minuteurs, courses, switchs/températures/helpers,
  puis aspirateur/annonces/calendriers. Outils existants conservés ; nouveaux relais
  typés préparés et testés ; appareils désactivés par défaut, activés localement
  le 17 novembre pour résoudre ce défaut. Recette de
  chaque famille avant activation ; chauffage et nouvelles applications TV exclus.
  Lots mixtes entre familles encore refusés avant exécution ; leur généralisation
  doit conserver préparation de toutes les actions et arrêt sans retry après doute.
  **Dépend de : F22 (recette humaine), F19, F15.**

- [ ] **F20 — Étudier les applications TV et formulations naturelles.** Question
  utilisateur du 13 novembre : « mets Canal Plus sur la télé » pour ouvrir l'app,
  et « passe l'aspirateur dans la cuisine ». Faisabilité à expliquer ; aucun
  accord d'implémentation ou de lancement réel déduit de cette question.
  TV : identifier la bonne intégration et la méthode d'ouverture de CANAL+,
  vérifier l'identifiant ou le lien de l'app et lever les homonymes. Aspirateur :
  ajouter la variante de phrase si demandée et associer Cuisine à sa carte HA ;
  mapping encore vide au contrôle en lecture seule. **Dépend de : F18, F19.**

- [x] **F18 — Ajouter les lecteurs multimédias et aspirateurs.** Demande du
  13 novembre. Actions natives par capacités, noms et alias, exposition Assist
  moins exclusions ; homonymes et groupes vérifiés avant toute commande.
  Lecteurs : état, marche/arrêt, lecture/pause, pistes, volume/muet, sources.
  Aspirateurs : état, démarrage/reprise, pause/arrêt, base, localisation, puissance,
  nettoyage d'une pièce déjà associée dans HA, sans repli global. Parcours musical
  existant préservé. Tests simulés des quatre entrées, valeurs, capacités absentes,
  groupes imbriqués et erreurs sans répétition ; 184 tests Python ciblés réussis.
  Capacités réelles du Roborock et des lecteurs relevées en lecture seule ; aucun
  appareil actionné pour la recette. **Dépend de : F14.** Recette réelle en F19.
  Suite complète : 561 tests Python réussis, 2 optionnels ignorés ; 34 tests JS
  réussis et syntaxe du panneau valide. Catalogue réel : 7 lecteurs et 1 aspirateur.
  Aucune pièce associée dans le mapping HA du robot au moment du contrôle :
  nettoyage par pièce conditionné à cette configuration utilisateur, non créée ici.
  Service redémarré ; santé/catalogue/interface HTTP 200. Lectures réelles via
  l'API Alfred réussies : état du robot à sa base et sources de l'ampli. Aucun
  changement de lecture, volume, source ou déplacement du robot pendant la recette.
- [ ] **F21 — Corriger les demandes de lumière conversationnelles.** Le 13 novembre,
  refus IA signalé pour « tu peux m'allumer la lumière du bureau » (orthographié
  « luniere » dans le retour ; transcription exacte non vérifiée). Préfixes
  conversationnels et pronom « me/m' » ajoutés au traitement direct, ponctuation
  interrogative acceptée. Instruction IA obsolète corrigée : proposer une
  reformulation plutôt qu'annoncer une absence de connexion. 166 tests ciblés
  réussis ; service redémarré, santé et catalogue HA HTTP 200, treize lumières
  autorisées. Aucun appareil actionné pendant le diagnostic. Essai vocal humain
  restant. Capture suivante : « On éteint la lumière du bureau. » transcrit par
  l'ESP32 et refusé. Ajout de « on éteint/on allume » et de l'homophone « éteint »
  au parcours lumière uniquement ; négations et questions explicatives non exécutées.
  172 tests ciblés réussis, dont le parcours conversationnel sans appel IA et
  les refus sur négation/question. Service redémarré ; santé et catalogue HA
  HTTP 200. Aucun appareil réel actionné ; nouvel essai vocal restant.
  Nouveau retour : « éteins la lumière du bureau s'il te plaît. » refusé.
  Cause vérifiée : ponctuation retirée après la courtoisie, qui restait dans la
  cible. Nettoyage oral partagé entre lumières et autres commandes domotiques :
  ponctuation avant courtoisie, politesse en tête/fin, répétitions, variantes STT
  bornées de politesse, demandes « est-ce que tu peux », « tu veux bien »,
  « je voudrais que tu » et pronoms « éteins-moi ». Aucun rapprochement approximatif
  de nom de cible. Valeurs texte conservées avec casse, accents et ponctuation.
  Corpus de formulations croisant préfixes/suffixes, parcours sans IA et autres
  appareils testé ; suite complète : 685 tests réussis, deux ignorés. Service
  redémarré, santé et catalogue HA HTTP 200. Aucun appareil réel actionné pendant
  la recette. Essai humain restant. **Dépend de : F02.**

- [ ] **F19 — Recetter lecteurs et aspirateur sur le vrai HA.** Choisir une cible
  et une commande d'essai, vérifier les alias des lecteurs homonymes, le volume,
  les sources et les confirmations ; valider la carte et une pièce avant nettoyage.
  **Dépend de : F18 ; cibles d'essai choisies explicitement.**

- [x] **F17 — Trier et alléger le tableau Domotique.** En-têtes Nom, Pièce et Type
  cliquables, tri français croissant/décroissant avec indicateur et accès clavier.
  Identifiant technique retiré du texte visible et placé dans l'infobulle du nom.
  Critère conservé lors des filtres et de l'actualisation du catalogue.
  Vérification DOM simulé : trois colonnes dans les deux sens, accents et nombres,
  filtre, alias conservés et identifiant uniquement dans title. Syntaxe JavaScript
  valide ; script et styles servis HTTP 200 par le service actif.
  **Dépend de : F14.**

- [x] **F14 — Ajouter les températures, switchs et helpers courants.** Demande du
  13 novembre, avec confirmation utilisateur que les lumières vocales fonctionnent.
  Lecture des températures, switchs/booléens, nombres, sélecteurs, dates/heures,
  textes et boutons implémentés sur le parcours direct texte/navigateur/ESP32.
  Noms/alias, pièce du terminal, exposition Assist moins exclusions, contrôle des
  groupes et des valeurs, textes confidentiels non lus, relecture avant confirmation.
  Interface Domotique et exemples actualisés ; tests Home Assistant simulé et
  routage des quatre entrées vérifiés. Aucun essai réel d'écriture effectué.
  Vérification : suite complète 518 tests Python réussis, 2 optionnels ignorés ;
  34 tests JavaScript réussis. Après le dernier traitement des erreurs TTS,
  158 tests Python ciblés réussis, dont absence de répétition d'un bouton.
  Service Windows redémarré ; santé, page et catalogue réels HTTP 200.
  Catalogue : switchs, capteurs, un input_datetime et un input_button exposés ;
  aucun input_boolean/input_number/input_select/input_text actuellement exposé.
  Lecture seule : aucune commande envoyée à un appareil pour cette vérification.
  **Dépend de : F01, F02.** Livraison logicielle ; recette réelle suivie par F15.
- [x] **F31 — Raccorder la lecture des températures au modèle et aux formules
  usuelles.** Constat du 16 novembre : les capteurs de température exposés étaient
  présents dans le catalogue, mais le relais conversationnel ne proposait aucun
  outil de température ; les formules « au bureau » et « fait-il dans le salon »
  échouaient aussi sur le parcours local. Ajout d'un outil `lire_temperature`
  strictement en lecture, indépendant du relais appareils, avec ciblage par pièce,
  nom de capteur ou « ici » (pièce du terminal). Formules locales élargies ; un nom
  de pièce partiel ambigu demande une précision. Vérification : 818 tests Python
  réussis, 2 ignorés, dont flux conversation → outil → exécuteur sans écriture.
  Lecture réelle de la sonde du bureau via l'outil : 19,1 °C, sans écriture.
  Essai conversationnel réel en texte avec le modèle configuré : outil utilisé,
  réponse 19,1 °C et aucune écriture. Aucun essai vocal humain effectué ; il reste
  couvert par F15.
  **Dépend de : F14 ; recette réelle suivie par F15.**
- [x] **F33 — Confirmer les équipements sensibles.** Demande du 16 novembre :
  ajouter une case Confirmation par entité dans le tableau Domotique, stockée
  localement. Essai humain du 17 novembre initialement non abouti : deux transcriptions incorrectes puis
  « allume-la » reconnu, mais refus IA sans résultat d'action à 09:17:46.
  Alias imprimante et confirmation présents sur le même switch local ; relais
  appareils alors désactivé (F23). Après activation autorisée : 145 tests ciblés
  réussis ; modèle réel et API texte vérifiés avec annulation, reprise
  « allume-la », question puis oui local sans appel IA. HA confirme le switch
  activé ; relecture indépendante réussie. TTS généré sans écoute humaine ;
  recette au micro toujours ouverte. Toute action modificatrice sur une entité marquée, ou sur un membre
  effectivement piloté de son groupe, est bloquée avant Home Assistant et demande
  oui/non dans la session du terminal. Les lectures, températures, options et le
  panneau Musique restent directs. Une commande globale est confirmée en une fois ;
  expiration après trente secondes ; boutons Confirmer/Annuler sur la page.
  Vérification : 867 tests Python réussis, 2 ignorés ; 46 tests JavaScript réussis,
  dont le parcours IA qui exécute « oui » sans second appel au modèle. Aucun
  appareil réel actionné pendant les tests ; recette humaine clavier/micro restante,
  avec une cible d'essai choisie explicitement.
  **Dépend de : F14, F22, F31.**
- [ ] **F15 — Recetter les nouveaux types sur le vrai HA.**
  Le 17 novembre, imprimante choisie par l'utilisateur : parcours texte du modèle
  réel vérifié, confirmation, annulation puis activation après oui et état relu.
  Aucun autre appareil actionné ; recette micro et autres types restant à faire.
  Choisir explicitement une sonde et des switchs/helpers d'essai, vérifier exposition/exclusions, alias,
  valeurs et confirmations au clavier puis au micro. Ne pas activer une routine
  ou modifier un appareil réel sans cible d'essai choisie. **Dépend de : F14.**
- [ ] **F16 — Piloter les climate — différé par l'utilisateur.** Attendre qu'il
  soit chez lui avant de cadrer et tester les thermostats. Aucun appel `climate`
  dans F14 ; ne pas déduire une autorisation de chauffage du support des helpers.
  **Dépend de : F01, F15 ; présence utilisateur au domicile.**

- [ ] **F13 — Reprendre les alias Home Assistant.** Lecture des alias du registre
  HA pour les entités exposées, affichage à côté des alias locaux et résolution des
  lumières par ces alias sans modifier HA ni écraser les alias Alfred. Tests simulés
  et lecture réelle du registre ; recette vocale sur un alias HA reste à confirmer.

- [ ] **F12 — Écrire les nombres en toutes lettres dans les réponses.** Demande
  utilisateur : remplacer les chiffres des réponses d'Alfred par du texte, à l'écran
  et pour la synthèse. Conversion locale dans le flux de réponse et le TTS, sans
  modifier les valeurs utilisées par les actions ; nombres, heures, décimaux et
  ordinaux couverts par tests. Recette vocale réelle et cas particuliers à vérifier.

- [ ] **F11 — Recetter les alias vocaux en conditions réelles.** L'utilisateur
  signale l'échec de « allume la lumière bizarre » pour la lumière du bureau.
  Constat : aucun alias local enregistré ; l'analyse exigeait aussi que l'alias
  inclue le mot « lumière ». Enregistrement automatique à la sortie du champ et
  reconnaissance du nom précédé de « lumière » ou « lampe » ajoutés ; alias
  fourni par l'utilisateur associé localement à l'entité Lumière Bureau. Tests
  automatisés réussis ; essai vocal et réponse physique restent à confirmer.

- [x] **F10 — Formuler naturellement les confirmations de lumière.** Demande
  utilisateur : supprimer les « (s) » prononcés par le TTS. Accords singulier et
  pluriel dans la réponse parlée et le panneau de connexion ; vérification par tests.

Décision du 11 novembre pour F01 : entités exposées à Assist moins exclusions
persistantes dans Alfred ; nouvelles entités autorisées par défaut. Catalogue par
pièce et type, distinction des capacités. Vérifier l'exposition effective avant
chaque commande et empêcher le contournement par groupe. Implémentation et recette
réelle restent à faire.
Demande utilisateur : présenter les entités en tableau et ajouter des alias locaux
pour les noms parlés. Tableau et édition livrés ; résolution des alias raccordée
aux lumières existantes avec refus des homonymes et respect des exclusions. Les
  autres types sont étendus aux températures, switchs et helpers courants en F14 ; recette
visuelle et vocale réelle à effectuer.
Contrôle réel : HA 2026.11.0 ; authentification WebSocket et commandes de lecture
`homeassistant/expose_entity/list` et `homeassistant/expose_new_entities/get`
réussies. Le registre des entités dépasse la limite de 1 Mio du client d'essai ;
prévoir une limite adaptée. Stockage local des exclusions préparé et vérifié
isolément ; il n'est pas encore raccordé aux commandes ni à l'interface.
Suite : catalogue WebSocket et filtre raccordés aux commandes de lumière et à
l'interface Domotique ; exclusions persistantes, contrôle des membres de groupes.
Lecture réelle du catalogue HA réussie. 86 tests Python ciblés et 34 JS réussis ;
la suite complète compte 488 réussites, 2 ignorés et un test de santé intermittent
réussi isolément. Recette réelle de commande/exclusion et vérification visuelle
restent à faire. Par prudence, une entité sans entrée au registre et dont l'exposition
Assist n'est pas explicitement observable n'est pas incluse : parité complète avec
les règles HA de ces entités encore à vérifier. F01 reste ouvert.

- [ ] **F01 — Intégrer HA et les cibles.** Appareils, pièces, étages, états et
  commandes ; toute la maison pour « toutes les lumières », pièce du terminal sinon,
  précision si ambigu. **Dépend de : P03, P06, S01.**
  v0.5 : client REST, jeton protégé DPAPI, test de connexion, compte des lumières,
  résolution d'une pièce par modèle HA et lumière du terminal. 29 tests synchrones
  réussis avec Home Assistant simulé ; aucun essai contre le vrai HA, aucune
  réservation d'entités ni exclusion de lampes particulières.
  Retour utilisateur ensuite : « c'est bon ça fonctionne », puis confirmation
  explicite que les lampes se sont éteintes sur ordre. Connexion réelle,
  exécution réelle et ciblage validés le 26 octobre. Restent : exclusions de
  lampes, permissions par profil, comportement en cas de coupure réseau.
  8 novembre : choix de liaison à cadrer avec l'utilisateur (Assist/MCP/API).
  Proposition non validée : serveur MCP officiel HA, jeu « Device control »
  limité aux entités exposées à Assist. Vérifier version HA, compatibilité client,
  couverture des fonctions et permissions I03 ; les accès REST conservés doivent
  appliquer explicitement les restrictions de cibles. Aucun changement HA effectué.
- [ ] **F02 — Traiter les commandes simples.** Voie directe pour commandes certaines,
  voie LLM pour demandes complexes, résultat vérifié et confirmation d'échec honnête.
  Les commandes restent soumises aux permissions. **Dépend de : F01, I03, S03, S05.**
  v0.5 : analyse stricte des phrases de lumière (accents, politesse, toutes/pièce),
  exécution locale sans appel LLM, réponse courte parlée. Une phrase mixte comme
  « éteins la lumière et raconte une blague » n'est pas exécutée automatiquement.
  Les permissions par profil (I03) ne sont pas encore branchées.
- [ ] **F03 — Intégrer Music Assistant/Qobuz.** Recherche artiste/titre, lecteur cible,
  lecture et ambiguïtés. **Dépend de : P06, I03, S05.**
  Préparation en lecture seule du 29 octobre : intégration Music Assistant chargée ;
  `media_player.amp_salon_2` relève de Music Assistant et est idle, tandis que
  `media_player.salon_amp_salon` relève de SongPal et est off. Les actions HA
  `music_assistant.search` et `music_assistant.play_media` sont disponibles. Aucun
  démarrage de musique, changement de configuration ou accès Qobuz testé ; cible
  et scénario effectif à confirmer avant exécution.
  30 octobre : lecteur `media_player.amp_salon_2` sélectionné dans l'interface et
  configuration locale enregistrée. Commandes directes artiste/album/titre, pause,
  reprise, arrêt, suivant et précédent ; outils bornés équivalents avec Command Code.
  Essai réel Airbourne accepté par `music_assistant.play_media`, état `playing`
  constaté puis lecture arrêtée et volume initial rétabli. Recherche/ambiguïtés,
  Qobuz, playlists, erreurs réseau et écoute physique restent à recetter.
  Retour PWA du 20 novembre : les commandes Suivant et Précédent étaient
  refusées. L’API envoyait `media_next` et `media_previous`, absentes du registre
  réel. Correction vers `media_next_track` et `media_previous_track`, toutes deux
  présentes. 44 tests ciblés réussis, dont les commandes sur le lecteur choisi
  depuis la PWA. Service redémarré et API Musique HTTP 200 via la PWA. Changement
  de piste à vérifier pendant une écoute, les lecteurs étant au repos au contrôle.
- [x] **F04 — Atténuer et restaurer la musique.** Choisir niveau/délais et lecteur(s),
  gérer interruption, erreur et modification manuelle du volume. La baisse après
  réveil ne résout pas un réveil manqué dans la musique. **Dépend de : F03, S06.**
  30 octobre : réalisé pour le navigateur et le lecteur musical configuré. Volume
  par défaut à 25 % du niveau courant (plancher 3 %), réglable de 5 à 80 %. Baisse
  dès le début de l'interaction, maintien pendant les huit secondes de reprise,
  restitution à la fin du son, à l'arrêt ou après erreur. Un volume modifié
  manuellement est conservé. Restauration de secours après 90 secondes et demande
  `keepalive` à la fermeture de page. Essai réel 12 % → 3 % → 12 %, puis volume
  initial 47 % ; intégration au cycle des futurs terminaux ESP32 en T04/T05.
  Retour utilisateur : « c'est éteint » ; HA confirme `idle`, volume 47 %, non muet.
- [ ] **F05 — Gérer les courses.** Ajout, lecture et opérations à définir ; une liste
  familiale cohérente dans HA et Alfred, sans duplication divergente.
  **Dépend de : P03, F01, I03.**
  Décisions complémentaires : permettre de remettre un article coché dans la liste
  active et de supprimer définitivement sur demande explicite. Modification de nom
  et de quantité, remise et suppression implémentées ; distinction entre cocher et
  effacer, validation de la demande explicite et refus des ambiguïtés. Cycle complet
  vérifié avec HA simulé ; formulations vérifiées avec fournisseur réel/liste simulée.
  174 tests réussis, un ignoré ; test réel utilisateur et permissions restent ouverts.
  Correction du 29 octobre : ajouter un article coché le remet en liste ; « supprime
  [article] » efface définitivement, « purge la liste » / « supprime tout » efface
  tous les articles actifs et cochés. Cocher reste une opération distincte. Code et
  interface adaptés ; 177 tests réussis, un ignoré, commandes testées avec le modèle
  réel et HA simulé. L'utilisateur indique ensuite que cela fonctionne, sans détailler
  les scénarios essayés ; permissions et recette exhaustive restent ouvertes.
  Choix validé : nouvelle liste familiale Alfred dans HA ; pas de reprise automatique
  de Super u ou de la liste Google Keep existante.
  27 octobre : préparation logicielle de l'ajout et de la lecture via une entité
  todo explicitement configurée, interface web et commandes texte/voix directes.
  Le 29 octobre, liste réelle « Courses Alfred » créée via Local to-do ; entité
  `todo.courses_alfred` configurée dans Alfred. Ajout et lecture d'un article test
  réussis depuis le code d'Alfred vers HA réel ; article supprimé et liste vide.
  Essai par l'interface et au micro et permissions par profil restent à faire.
  Modification et suppression définitive implémentées ; essai réel à confirmer.
  Serveur de développement relancé le 29 octobre sur `192.168.1.23:8765` en HTTPS ;
  santé 200 et lecture de la liste vide vérifiées via son API avec certificat non
  vérifié pendant ce test local. Essai utilisateur à faire depuis son navigateur.
  Retour du 29 octobre : « il y a quoi dans la liste » partait vers l'IA. Formulation
  corrigée et vérifiée sur le serveur relancé avec la liste HA réelle ; essai vocal
  utilisateur à confirmer. Sept tests ciblés réussis.
  Retour utilisateur : les demandes de plusieurs articles posent problème. Les
  journaux disponibles datent du 27 octobre et ne couvrent pas cet essai ; le code
  limitait effectivement l'IA à un seul appel/produit. Correction : jusqu'à huit
  articles, validés avant écriture, ajoutés séparément ; arrêt et signalement des
  résultats partiels en cas d'erreur. Fournisseur réel avec liste simulée : deux
  demandes multiples réussies. Essai vocal sur liste réelle à confirmer.
  Décision utilisateur : ignorer les articles déjà présents et le signaler.
  Détection implémentée avant ajout, commandes IA/directes et interface, y compris
  répétition dans la même demande ; comparaison normalisée, sans synonymes ni
  garantie atomique contre un ajout simultané externe. Tests simulés réussis ;
  l'utilisateur confirme ensuite que l'essai réel fonctionne.
  Suite proposée et implémentée : cocher un article acheté dans HA, depuis l'interface
  ou une commande vocale/texte, sans suppression définitive. Résolution par UID ;
  refus si aucun ou plusieurs articles correspondent. 169 tests réussis, 1 ignoré ;
  deux formulations validées avec Command Code réel et liste simulée. L'utilisateur
  confirme ensuite que l'essai réel fonctionne ; permissions et gestion des articles
  terminés restent à préciser.
  En cas d'ajout dont la réponse est perdue, vérifier la liste avant de réessayer.
  30 octobre : après les corrections sur les ajouts multiples, les doublons, les
  articles cochés, la modification et la suppression, l'utilisateur confirme que le
  parcours de la liste fonctionne et choisit une autre fonction. Une recette
  exhaustive et les permissions par profil restent ouvertes.
- [ ] **F06 — Gérer les rappels personnels/collectifs et récurrents.** Lecture et
  écriture dans les calendriers HA, gestion des échéances, modification/annulation.
  Décision corrigée : calendriers HA source des rappels personnels ; Alfred interface
  vocale. Droits, recette réelle et gestion des événements HA existants à compléter.
  **Dépend de : P02, P03, I03, S01.**
  Modification/suppression vocales demandées : cibler un événement HA par UID,
  éviter les homonymes et préserver les informations ; sur série récurrente, demander
  si l'annulation concerne la prochaine occurrence ou toute la série. Essais simulés
  et sur événements de test uniquement avant validation sur de vraies données.
  Ancien banc local suspendu le 29 octobre : création et diffusion locales désactivées,
  données conservées et sauvegardées. Aucune migration ni suppression effectuée.
  Inspection HA : calendrier local « Travail » et jours fériés visibles, sans lire
  leurs événements. L'utilisateur choisit ensuite de créer un calendrier personnel :
  « Personnel », entité `calendar.personnel`, intégration Local Calendar chargée.
  Aucun événement créé ni transféré. Son propriétaire est confirmé et associé à son
  profil existant dans la configuration privée locale. L'utilisateur choisit un
  calendrier familial distinct : « Familial », entité `calendar.familial`, créée et
  associée localement. Seuls les événements identifiés comme rappels sont annoncés.
  Client HA préparé en isolation pour consulter une période et créer un événement
  ponctuel sur un calendrier explicitement autorisé, sans répétition en cas de
  réponse perdue ; lecture réelle vérifiée sans afficher son contenu. Création et
  consultation depuis Alfred raccordées ; récurrence hebdomadaire HA vérifiée avec
  un événement de test temporaire retiré ensuite, y compris changement d'heure.
  Les rappels créés par Alfred portent un marqueur dans la description HA ; seuls
  ces événements sont surveillés et annoncés. Les autres événements restent silencieux.
  Reprise : occurrences manquées journalisées sans lecture tardive ; prochaine
  occurrence fournie par HA. Le journal local ne contient ni titre ni texte de rappel.
  Les résultats de consultation ne sont pas renvoyés à Command Code dans l'historique.
  224 tests réussis, un ignoré ; essai vocal physique, reconnaissance du locuteur,
  protection de l'interface et modification/suppression des événements restent à faire.
  Retour utilisateur : « Ça fonctionne le rappel ». Résultat confirmé globalement ;
  étapes exactes essayées, récurrence et écoute sur le terminal restent à préciser.
  Les événements ajoutés directement dans HA ne sont pas automatiquement des rappels
  Alfred ; leur marquage depuis HA reste à concevoir.
  29 octobre : l'utilisateur choisit les rappels comme prochaine fonction. Premier
  socle : rappel personnel associé explicitement à un profil ou familial, pièce
  demandée dans le formulaire web, stockage et échéance persistants. Migration du
  schéma 2 vers 3, contrôle des profils et protection contre suppression d'un profil
  ayant des rappels en attente ou manqués. Tests automatisés réussis avec données
  fictives. Reconnaissance vocale et permissions, exposition HA et choix du défaut
  web restent ouverts. L'interface actuelle
  n'isole pas les rappels par personne et n'est pas authentifiée.
  Ancien banc avant suspension : récurrence hebdomadaire dans le formulaire, heure de Paris préservée,
  création atomique de l'occurrence suivante et reprise après arrêt selon la règle
  validée. Schéma 4 et tzdata ajoutés ; changement d'heure, arrêt/redémarrage et
  annulation de série testés. 192 tests réussis, un ignoré. Pour une heure locale
  inexistante au printemps, premier horaire valide ; en automne, première occurrence
  de l'heure répétée : comportements techniques du banc à confirmer à l'usage.
  Ancien banc avant suspension : outil de création vocale avec contrôles d'heure, jour, profil et pièce ;
  essais avec modèle réel et données fictives réussis. L'utilisateur choisit la voix
  cloud HA existante. Diffusion de rappels sur Bureau/RDC désormais suspendue ; une
  tentative est journalisée et jamais répétée automatiquement, sans prétendre que
  l'écoute est confirmée. 205 tests réussis, un ignoré, dont un test de bout en bout HA
  simulé. Le moteur exact, l'essai physique, les permissions et la
  confidentialité restent à valider. La reconnaissance du locuteur est expérimentale
  et raccordée, mais reste inactive faute d'une seconde voix (voir I02).
  30 octobre : modification et suppression vocales raccordées par UID, avec refus
  des homonymes, vérification des dates explicites et conservation des champs
  existants. Sur le calendrier HA réel, une occurrence d'un événement temporaire a
  été modifiée, une occurrence retirée puis l'événement de test entièrement supprimé.
  La modification d'une série entière est refusée explicitement et reste à faire.
  Permissions, essai physique et recette de toutes les formulations restent ouverts.
  11 novembre : la diffusion des rappels reste sans sortie audio depuis la
  déconnexion de la carte de HA (`announcement-targets.json` vide,
  `delivery_mode: disabled`). Une demande échoue sans rejouer le rappel ; le
  raccordement au TTS du terminal direct est le prochain travail identifié.
- [ ] **F07 — Gérer les minuteurs.** Échéances, opérations validées en P02 et sonnerie
  sur tous les Alfred de l'étage d'origine. **Dépend de : P02, F01, S01.**
  Décision acquise : Alfred stocke et programme ; HA permet consultation et commandes.
  v0.6 : commandes texte/voix locales vérifiées en S13 ; consultation/annulation
  par étage et numéro proposées dans le prototype. Création vocale, consultation,
  annulation et Stop confirmés par l'utilisateur sur Android.
  29 octobre : prise en charge du mot « minuterie » et de durées comme « 7min40 »
  ou « sept minutes quarante » ; 34 tests ciblés réussis, essai vocal réel à faire.
  S14 : sonnerie native de la carte Bureau/RDC raccordée et testée avec HA simulé ;
  son réel et arrêt sur le terminal à vérifier. Commandes HA non raccordées.
  11 novembre : la carte n'étant plus dans HA, sonnerie native raccordée au pont
  direct. Pour l'étage du terminal, Alfred appelle `start_ringing` au premier
  minuteur en état « sonne » et `stop_ringing` après le dernier ; une réponse
  perdue est retentée sans redémarrage en double, et rien n'est rejoué au
  redémarrage. Bouton « Tester la sonnerie » et route dédiée ajoutés. Recette :
  485 tests Python et 34 tests JS réussis ; sonnerie de test acceptée par la
  carte, minuteur de 5 s vu actif puis coupé par Stop. Reste à confirmer à
  l'écoute, puis priorités audio avec musique et diffusion multi-terminaux.
- [ ] **F08 — Gérer les annonces.** Cibler maison/étage/pièce, définir interruption
  et comportement avec musique, indisponibilité et demandes simultanées.
  **Dépend de : P02, F01, I03, S04.**
  Annonces maison/étage/pièce depuis la conversation et l'interface, terminal
  Bureau/RDC explicitement configuré, tests HA simulé et modèle réel avec terminaux
  simulés. L'utilisateur choisit la voix cloud du pipeline HA ; diffusion activée.
  Aucune annonce physique n'a été testée. Musique, pannes, permissions et plusieurs
  terminaux restent à traiter.
  11 novembre : plus aucune cible HA depuis T08 ; la diffusion est désactivée et
  les annonces ne sortent pas sur l'ESP32. Réutiliser le TTS et la lecture du
  terminal direct, avec une règle explicite de priorité et d'interruption.

- [ ] **F09 — Vérifier la reprise des échéances.** Conserver rappels et minuteurs
  après redémarrage ; tester échéances futures et dépassées sans double diffusion.
  Appliquer la règle validée : rappel manqué visible, minuteur expiré terminé,
  aucune sonnerie tardive. Rappels personnels non délivrés
  visibles dans l'interface, sans diffusion générale. **Dépend de : P02, F06, F07.**
  Socle local vérifié en S09 ; recette complète avec profils/HA/terminaux restante.

## 6. Terminal ESP32 et plusieurs pièces

- [ ] **T14 — Évaluer un point d'écoute principal pour le salon bruyant.**
  Besoin précisé le 25 novembre : parole à distance, qualité visée proche
  Echo/Google Home. Pistes proposées, aucun achat validé : ReSpeaker XVF3800
  (USB + hôte local ou ESP32-S3 compatible), Home Assistant Voice Preview Edition.
  Vérifier le transport audio direct vers Alfred et le retour de lecture pour
  l'AEC avant choix. Comparer aux mêmes emplacements la Waveshare et le candidat :
  réveil, transcription, faux réveils, TV/musique et écoute pendant la réponse.
  Les capacités constructeur ne valent pas validation dans le salon.
  Recherche documentaire : essai domestique favorable au XVF3800 face au Voice
  PE et au Satellite1, avec le même STT, une seule voix et des enceintes externes.
  Démonstration avec Echo Dot comme témoin, sans taux vérifié. Ajouter un Echo ou
  Nest d'origine comme témoin d'usage si disponible. Comparer séparément le réveil
  natif et la réussite de la commande. Pistes de réemploi à évaluer : EchoMuse
  sur ancien Echo pour récupérer la captation d'origine, MiciMike pour remplacer
  la carte et les micros d'un Home Mini. Aucune conversion validée.
  Echo Show 5 de première génération (2019, H23K37 / checkers) : piste TECHO5
  avec écran, captation, réveil local et Assist via API ESPHome. Vérifier le
  flux attendu par le pont Alfred et comparer la captation au système d'origine
  avant de retenir ce terminal. Le comportement en présence de la TV et la
  compatibilité avec le réveil « Alfred » restent à valider.
  Retour utilisateur : Alexa d'origine capte partout dans son salon. Préserver
  ce témoin et vérifier la possibilité de restaurer Fire OS et de réactiver
  Alexa sur cette unité avant une conversion. Le retour documenté par le
  portage TECHO5 de test est vers LineageOS. La restauration Fire OS évoquée
  par des projets tiers reste à vérifier pour l'appareil et son état logiciel.
  **Dépend de T13 pour la référence ; contribue à T03 et A04.**

- [ ] **T13 — Améliorer la captation audio de la Waveshare.** Priorité demandée
  Séance humaine du 16 novembre, bureau calme, STT « Alfred » avec variantes
  Alfraide/alfrède/alfrede/alfreide : 5/5 à 0,5 m, 9/10 à 1 m, 4/5 à 2 m,
  4/5 à 3 m, soit 22/25. Aucun déclenchement sur les deux silences de 30 s,
  aucune coupure ni saturation numérique relevée. Le signal maximum pendant
  un essai et la dernière valeur VAD ne prouvent pas la qualité exacte du mot ;
  le compteur STT est cumulatif. Les analyses STT ont augmenté pendant les trois
  essais manqués mais leurs transcriptions n'étaient pas conservées : cause
  indéterminée, ne pas en déduire que chaque mot a été analysé. Pour les prochains
  tests STT uniquement : journaliser au plus cinq transcriptions bornées par essai,
  statut de correspondance, durée et indicateur final ; aucune transcription de
  veille ordinaire ni d'audio brut ajoutée. 86 tests ciblés réussis, service relancé,
  ESP32 connecté, STT Alfred sélectionné et veille au repos. Diagnostic humain à
  poursuivre avant modification des gains, variantes ou seuils.
  Première séance choisie par l'utilisateur : réveil STT avec « Alfred » ;
  réussite annoncée à 100 % sur téléphone, sans comptage ou conditions précisés.
  Tester sur ESP32 avant de conclure ou de changer les réglages acoustiques.
  Carte rebranchée le 16 novembre : identité vérifiée, v2.0.0/ESPHome 2026.9.0,
  gain post-AFE 13, AEC et AFE actifs. Contrôle micro sans transcription :
  63 488 octets soit 1,98 s, signal non nul ; cela ne valide pas l'acoustique.
  Compteur de diagnostic corrigé (octets comptés deux fois en capture) ; 43 tests
  ciblés réussis, service relancé, terminal connecté au repos, veille arrêtée.
  Attendre la séance humaine guidée avant tout réglage acoustique.
  le 16 novembre. Priorité précisée : **fiabiliser Jarvis au calme avant les essais
  avec musique**. L'utilisateur a remis Jarvis et rapporte un très bon résultat
  sur téléphone, mais des problèmes sur ESP32 même au calme. Contrôle du service :
  openWakeWord/Jarvis actif, seuil 0,3, vérification secondaire désactivée ; le
  chemin openWakeWord reçoit directement les trames sans filtre Silero préalable.
  Carte déconnectée, zéro octet reçu, nom mDNS non résolu et dernière IP connue
  injoignable ; l'utilisateur confirme ensuite carte débranchée ou hors réseau.
  Ce constat ne diagnostique pas les ratés acoustiques antérieurs. Reprendre
  les mesures lorsque la carte est disponible, puis compter les détections au
  calme et comparer les scores/flux avec le téléphone avant de régler le gain,
  le seuil ou l'AFE. Commencer par identifier la carte et lire ses réglages réels
  (gain post-AFE, AEC, traitement AFE) ; le gain 13 est un ancien relevé du banc
  Assist, pas une mesure actuelle. Comparer parole naturelle au calme, à plusieurs
  distances, puis avec l'ampli externe et pendant une lecture du satellite.
  Relever niveau, saturation, bruit, mots coupés, transcription et réveils séparément.
  Pistes proposées, non validées : placement, gain/AGC, comparaison AFE actif/bypass,
  puis mode AFE high-performance ou filtrage serveur si bénéfice mesuré. Le YAML
  épinglé prévoit deux micros, AEC/BSS/AGC, mode low_cost et NS dédié désactivé ;
  vérifier l'état réel avant de conclure. L'AEC reçoit le retour du haut-parleur
  de la carte, pas celui de l'ampli externe. Aucun réglage ni flashage effectué
  lors de ce point documentaire. **Dépend de : T02, T04 ; contribue à T03/T11.**
  Comparaison documentaire Kustos Voice demandée le même jour : même matériel,
  même famille ESP-SR AEC/BSS/AGC et sortie micro 16 kHz ; pas de supériorité
  démontrée sur notre firmware. L'auteur annonce environ cinq mètres pendant sa
  musique, sans comparaison contrôlée avec Alfred ni preuve avec ampli externe.
  Examiner comme pistes son gain analogique 33 dB et son VAD microWakeWord 0,03,
  sans recopier ce seuil dans Silero/openWakeWord. Le firmware vise Assist/MA ;
  compatibilité avec le pont direct et modèles ONNX Alfred à développer/vérifier.
  Aucun remplacement décidé. Source : https://github.com/Qorvano/kustos-voice.
  Proposition du 16 novembre après question utilisateur sur les logs : compléter
  le journal de commandes I05 existant par des événements de réveil horodatés,
  pics de score par fenêtre, seuil/modèle, niveaux micro et interruptions de flux,
  avec corrélation vers l'échange. Prévoir un marqueur manuel « appel raté » :
  une absence de détection ne prouve pas qu'un appel a été prononcé. Résumés
  bornés plutôt que trames en continu ; conserver la règle sept jours/100 Mo,
  sans audio brut. Extension demandée ensuite : onglet Logs, test guidé avec
  détection automatique ou bouton d'appel manqué, parcours réveil seul choisi.
  Choix moteur openWakeWord/STT et mot d'appel exigé sur cette page ; reprendre
  les contrôles existants, figer les réglages par séance, adapter les mesures au
  moteur (pas de score openWakeWord inventé pour STT). Proposition de protocole
  au calme : 5/10/5/5 essais à 0,5/1/2/3 m et 30 s de silence avant/après,
  carte fixe dans le bureau. Onglet Logs livré avec choix du moteur et du mot,
  historique et export ; séance guidée avec deux silences, distances 5/10/5/5,
  détection ou échec manuel, distance ignorée et suivi des interruptions. Audio
  non enregistré ; niveaux, saturation et score disponibles par essai. Recette
  humaine sur la carte encore ouverte. L'API expose les échanges aux clients
  ayant accès à l'interface, sans authentification propre ; à traiter sur réseau partagé.
  Vérification logicielle : 812 tests Python réussis, deux ignorés ; syntaxe JS
  validée. Service relancé, route de test HTTP 200 ; carte absente pendant cette
  vérification. Mesures acoustiques et essai humain restent à faire.
  Le 24 novembre, déplacement du satellite signalé. Refaire le test guidé au
  nouvel emplacement, micros dégagés, au calme et avec le réglage existant.
  Connexion et réception du flux confirmées à distance ; STT, mot « Alfred ».
  Séance terminée : 5/5 à 0,5 m, 8/10 à 1 m, 4/5 à 2 m et 3/5 à 3 m.
  Sauvegarde locale des réglages Bureau dans
  `.local/backups/reveil-esp32-bureau-2026-11-24.json`. Variante « Al Fred »
  ajoutée au réglage actif : un raté à 3 m récupéré sur les transcriptions,
  « Fred » seul toujours refusé. Veille et flux vérifiés après l'ajustement.
  Nouveau passage à 3 m : 4/5 contre 3/5, aucune réussite via « Al Fred ».
  Faux réveils en conversation à vérifier.
  Proposition du 24 novembre : parcours « Calibrer cet emplacement » à l'ajout
  ou au déplacement d'un ESP32. Partir du test guidé, mesurer le bruit et la
  parole aux distances d'usage et comparer quelques réglages locaux sur les
  mêmes extraits en mémoire, puis confirmer sur des essais indépendants.
  Évaluer réveils manqués, faux réveils, transcription, saturation et latence.
  Garder le réglage de départ si le bénéfice n'est pas confirmé. Sauvegarder
  le réglage retenu par satellite et emplacement, avec restauration.
  Prérequis : vérifier les réglages accessibles sur le firmware et séparer
  les traitements serveur rejouables des réglages micro nécessitant une
  nouvelle capture. Proposition à valider avant implémentation.
  Précision utilisateur : Bureau = studio traité ; Salon = nouvel emplacement,
  réverbération ou écho flottant suspectés. Priorité aux distances et orientations
  réelles (de face, de côté, dos) ; mesure à 0,5 m comme référence seulement.
  Variante proposée : l'application mobile émet un balayage connu depuis
  plusieurs points d'usage, l'ESP32 capte la réponse et Alfred estime la
  décroissance et les réflexions de la chaîne. Même téléphone, volume et
  orientation pour les comparaisons ; vérifier la répétabilité avec le flux
  prétraité de la carte. Comparer les réglages sur de la parole et confirmer
  avec la voix humaine aux orientations réelles avant de retenir un profil.
  Source méthode : https://aes.org/publications/elibrary/elibrary-page/?id=10211
  Diagnostic matériel proposé : comparer la Waveshare et un micro de référence
  côte à côte dans le salon, sur les mêmes phrases naturelles de côté et de dos
  et avec Parakeet commun. Mesurer les écarts de reconnaissance avant de conclure
  sur la chaîne de captation ou d'envisager un remplacement.
  Protocole préparé dans `docs/PROTOCOLE_CALIBRATION_SALON.md` avec
  `alfred.room_benchmark` (balayage, mesure relative et Parakeet hors ligne).
  Première séance humaine partielle : balayage Salon et deux prises vocales.
  Rapport précoce/tardif indicatif +9,34 dB, aucune saturation. Passe-haut
  120 Hz et gains +6/+12 dB sans amélioration fiable sur ces deux prises.
  Refaire des phrases identiques en captation parallèle avec le micro de
  référence et répéter le balayage avant le choix du profil. Le 25 novembre,
  ajout de la capture WAV
  de 12 secondes dans Logs et du lecteur du balayage. Comparaison hors ligne
  du même PCM avec la référence et avec ou sans passe-haut 120 Hz.
  Vérifié sur l'ESP32 réel : WAV de 12 secondes, mono 16 kHz, téléchargement
  lié à la session, veille et réception du flux après la prise.
  Réduction de réverbération et profil Salon à valider sur des prises réelles.
  Parcours guidé demandé sans micro de studio : deux balayages et deux phrases
  identiques à 50 cm, puis au canapé de face, de côté et de dos. Validation
  ou reprise de chaque étape, export ZIP avec noms et phrases attendues.
  Comparaison avec un autre micro facultative.

- [ ] **T12 — Évaluer l'ATOM Echo si cette piste est retenue. À décider.**
  Candidat évoqué le 15 novembre, aucun achat ni adoption validé. Distinguer le
  classique C008-C des variantes S3R ; vérifier le firmware et le transport direct
  Alfred, puis comparer captation, réveil en bruit et restitution à la Waveshare.
  La compatibilité Assist documentée ne valide pas le raccordement direct Alfred.
  **Dépend de : T02, T03, T04.**

- [ ] **T10 — Diagnostiquer le bip entendu sur « Alexa ».** Retour utilisateur du
  11 novembre : un bip sur l'ESP32 après « Alexa ». Le modèle chargé a été vérifié :
  seul `jarvisse_20260916_004415` est actif, seuil 0,5 ; les compteurs ne permettent
  pas d'attribuer une détection passée. Banc synthétique Phonon sur une seule voix :
  pics Alexa/Alexa avec commande/Hé Alexa 0,001 ; Jarvis isolé 0,991 et avec commande
  0,944. Ces essais ne prouvent pas le comportement des voix humaines ni l'origine
  du bip. Essai humain comparé aux compteurs demandé ; ne pas modifier le seuil ni
  le mot de réveil sans diagnostic et recette de non-régression.
  Retour utilisateur : pas de bip pendant l'essai « Alexa » ; détections Jarvis
  inchangées à une et aucune nouvelle capture, réception micro active. Le symptôme
  initial n'a pas été reproduit ; cause encore inconnue, aucune correction ni
  modification de sensibilité effectuée. À reprendre si le bip revient.

- [ ] **T09 — Évaluer l'Echo Show 5 H23K37 pour Alfred.** Matériel stock confirmé
  le 3 novembre ; flashage acceptable en principe, très bonne détection prioritaire.
  Comparer TECHO5 et echo-dot-assist sur checkers ; ce dernier conserve Fire OS,
  le traitement audio et le moteur Amazon, mais son port n'est essayé que sur une
  unité et sa référence d'annulation d'écho en lecture reste à mesurer. Distinguer
  mots Amazon et réveil personnalisé « Alfred » : aucune équivalence de qualité
  établie. Vérifier version publiée, transport direct vers Alfred, captation avec
  ampli, faux réveils Fred/TV, reprise de huit secondes et écran avant choix.
  Kiosk Satellite : image checkers encore en développement. Aucun firmware choisi,
  aucune manipulation ni installation réalisée. **Dépend de : T02, T03, T04.**

- [x] **T08 — Déconnecter le banc ESP32 de Home Assistant.** Demandé le 2 novembre :
  carte Waveshare `eb05fc` uniquement, utilisée dans HA pour un essai. Entrée
  ESPHome désactivée et déchargée ; appareil relais Music Assistant désactivé
  dans HA, sans désactiver Music Assistant globalement. Réactivation ciblée
  possible, aucun effacement ni flashage. Recherche des consommateurs HA sans
  dépendance trouvée. Trois configurations de routage locales sauvegardées et
  vérifiées sous `.local/backups/esp32-ha-disconnect-20261102/`, puis cibles
  d'annonces/sonneries retirées et lecteur musical de test désélectionné.
  Vérification : entrée `not_loaded`/désactivée par utilisateur, satellite
  `unavailable`, relais MA désactivé, service Alfred sain et référence à 1,242.
  Les connecteurs HA de maison restent en place ; aucune sonnerie physique
  envoyée. T02/T04 restent nécessaires pour l'usage direct avec Alfred.
- [ ] **T01 — Reprendre les mesures audio du banc Assist. Différé par l'utilisateur.**
  Compter réveils/manqués/faux réveils, transcription naturelle et qualité sonore,
  au calme puis avec ampli, en gardant les réglages de référence. Suivre
  `PROTOCOLE_TEST_AUDIO.md`. Ne bloque pas la préparation logicielle.
  **Dépend de : B05, B06, P05.**
- [ ] **T02 — Choisir firmware et transport vers Alfred.** Comparer adaptation de
  l'existant et ESP-IDF/ESP-SR, vérifier les licences et le fonctionnement des codecs,
  duplex audio, reconnexion, mute, LED et mise à jour. Garder un retour au banc Assist.
  **Dépend de : T01, S01.**
  2 novembre : réutilisation du firmware installé v2.0.0 / ESPHome 2026.9.0 pour
  un prototype sans flashage. API native directe via aioesphomeapi 46.25.1
  (MIT), MAC vérifiée ; PCM16 mono 16 kHz en TCP et retour FLAC mono 48 kHz.
  Nouveau port HTTP local 8766 limité à l'IP de la carte et à des jetons de 90 s,
  aucune exposition Internet ni audio écrit. Configuration privée `terminal.json`,
  reconnexion du pont au démarrage du service. Choix durable et recette complète
  (mute/LED/reconnexion en panne réelle/duplex) restent ouverts.
- [ ] **T03 — Réveil configurable STT/openWakeWord livré côté logiciel ; recette acoustique ouverte. Jarvis actif sur ESP32 au 16 novembre.** Prononciation française,
  adultes/enfant, exemples négatifs Fred, conversation et TV/musique ; choisir moteur
  et emplacement d'exécution après mesures. **Dépend de : T02, P05.**
  13 novembre : l'utilisateur choisit `lfpoulain/wakeword-generator` pour
  entraîner lui-même Alfy et Alfredo. Recettes distinctes proposées ; écouter
  les graphies avec les voix du générateur, puis entraîner/importer les ONNX et
  comparer sur Fred, voix humaines, TV/musique et distance. Aucun entraînement
  ni changement du modèle actif réalisé dans cette préparation.
  Retour utilisateur : modèle `alfy_v1.onnx` créé après génération sous WSL,
  extraits synthétiques jugés bons. Test micro demandé ; qualité acoustique et
  import dans Alfred non encore validés lors de ce premier échange.
  Testeur Windows séparé préparé sous `.local/wakeword-tester` avec Python
  3.13 existant et Tkinter ; dépendances du générateur installées. Copie locale
  du modèle, `--check` réussi (25 entrées micro), fenêtre lancée pour essai.
  Résultat acoustique du testeur non encore reçu. Installation Python 3.12 MSI
  bloquée par le service Windows Installer absent ; réparation non réalisée.
  Préparation Alfredo demandée puis réalisée : `training-alfredo.yml` créé dans
  le dépôt WSL du générateur, modèle `alfredo_v1`, graphies Alfredo/Alfrédo,
  négatifs incluant Fred, Alfred et Alfy/Alfi. Recette Alfy sauvegardée dans
  `training-alfy.yml`, `training.yml` inchangé. Chargement par le validateur du
  générateur réussi, paramètres d'entraînement identiques à Alfy. Après écoute,
  l'utilisateur rejette la voyelle de la v1 : prononciation souhaitée al-frè-do.
  `training-alfredo.yml` corrigé en `alfredo_v2`, graphies utilisateur Alfrèdo,
  Alfreido, Alfraido ; ancienne recette conservée dans `training-alfredo-v1.yml`.
  Chargement validé, clips v1 conservés séparément. Nouvelle génération, écoute,
  entraînement et recette humaine v2 restent à faire.
  Nouvelle demande du 13 novembre : `docs/alfy_v1.onnx` importé par l’API,
  validateur isolé réussi et identité SHA-256 de la copie vérifiée. Alfy
  sélectionné en openWakeWord au seuil 0,5 pour ESP32 et navigateur. ESP32
  Bureau connecté, veille armée, flux reçu sans erreur ; navigateur configuré
  mais non activé. Anciennes préférences sauvegardées sous `.local/backups/`.
  Jarvis reste disponible ; recette humaine et faux réveils restent ouverts.
  13 novembre : implémentation demandée et réalisée : moteurs configurables
  pour ESP32 et navigateur, STT Alfy/Alfi par défaut sans Hé, choix des modèles
  openWakeWord et import ONNX validé en processus borné. Préférences locales
  indépendantes, propriétaire unique, annulation des résultats tardifs,
  reprise huit secondes et attente six secondes après mot seul ; pas d'IA
  pour le silence ni les paroles sans appel. Recette humaine restant à faire.
  Recette logicielle : 594 Python réussis/deux ignorés en suite complète,
  puis 127 ciblés après confirmation stricte du préfixe ; 43 JavaScript réussis.
  Modèle Jarvis accepté par le validateur isolé. Canal WSS réel validé sur audio
  synthétique jusqu'à la capture, sans IA/action. Un réveil Parakeet réel ;
  graphie complète « Al fit » à examiner humainement, non ajoutée aux variantes.
  Service relancé, nouvelles routes HTTP 200. Après rebranchement utilisateur :
  ESP32 Bureau reconnecté, identité vérifiée, veille Jarvis et flux actifs sans
  erreur, une détection au compteur ; essai humain STT non réalisé. Tests humains,
  distance/TV/musique et recette VM Debian restent ouverts. Vérification visuelle
  réelle non disponible (aucun navigateur pilotable). Certificat HTTPS local
  expiré à traiter séparément avant une recette navigateur sans avertissement.
  Retour du 20 novembre : ESP32 en veille STT sur « Alfred ». Le journal confirme
  un déclenchement de veille, puis le dernier échange affiche « Fred » en tête
  de la phrase complète et un rejet avant appel IA. Recetter la conservation
  de l’amorce et les écarts entre transcription de veille et de phrase complète.
  « Fred » reste un cas négatif du réveil. Origine acoustique non vérifiable
  sur cet échange, l’audio brut n’étant pas conservé.
  Même échange, clignotement rouge : le pont envoyait une erreur au firmware
  après le rejet du réveil. Le rejet conserve son message dans l’interface,
  termine la séquence sans signal d’erreur et réarme la veille. 100 tests ciblés
  réussis. Après redémarrage, carte connectée et flux micro actif sur « Alfred ».
  Comportement du voyant lors du prochain rejet à vérifier sur la carte.
  Nouveau retour du 20 novembre : écran bloqué sur la transcription alors que
  la carte recevait déjà le micro en veille et que le moteur était libre. Le cas
  mot d’appel seul suivi de silence reproduit cet affichage. L’interface affiche
  désormais l’attente de la demande puis la fin de l’échange si elle expire.
  Un traitement interrompu sans réponse clôt également son affichage. 100 tests
  Python et deux tests JS réussis ; page et veille vérifiées après redémarrage.
  Durcissement demandé ensuite : clôture de secours si le terminal est revenu
  en veille ou déconnecté sans prise ni traitement actif. Si l’échange disparaît
  après un redémarrage, le panneau clôt son attente sans modifier une réponse
  saisie depuis le navigateur. 101 tests Python et deux tests JS réussis ; page
  mise à jour et flux micro confirmés après redémarrage.
  Refaire un essai humain du mot seul et d’une demande prononcée d’une traite.
  Les recherches et le comparatif initial gratuit passent après cette livraison.
  Voicute écarté : export personnalisé payant confirmé par sa documentation,
  malgré entraînement et essai Basic gratuits en ligne. Vérifier encore
  français en acoustique réelle, charge/latence et recette VM Debian.
  Aucun achat, entraînement ni flashage ; Jarvis conservé sur ESP32.
  Alfy choisi comme valeur initiale STT, modifiable ; qualité non validée.
  Piste différée : audit des données/prononciations et un éventuel
  modèle dédié Alfy ; comparer aussi les confusions avec « elle a fini »,
  « ça le fait », Fred et Alfred. Entraînement dédié non lancé ; ne pas mesurer
  Alfy avec le modèle Hé Alfred ni conclure sur les seuls exemples synthétiques.
  8 novembre : nouveau banc temporaire demandé : **Jarvis**, fourni dans
  `docs/jarvisse_20260916_004415.onnx` (415 224 octets). Installé sous
  `.local/models/wake-word/`, seuil initial 0,5, `wake_name=jarvis`, vérification
  Whisper désactivée. Modèle réellement chargé et dix secondes de silence sans
  détection ; 198 tests Python ciblés et 29 tests JS réussis. Interface et commandes
  directes adaptées à Jarvis/Jarvisse. Carte revenue en ligne après vérification
  utilisateur, identité vérifiée par le pont. Service HTTPS redémarré, modèle
  Jarvis actif, veille armée et trames reçues : 95 744 octets en trois secondes,
  sans erreur au contrôle. Retour utilisateur : détection jugée parfaite pendant
  son essai, même à basse voix ; validation qualitative de cet essai acquise.
  Jarvis conservé pour poursuivre les fonctions ; travail sur le réveil différé
  explicitement. Essai musical reporté car il est tard. Taux chiffrés, faux réveils,
  bruit/musique, autres locuteurs et latence restent ouverts ; T03 reste non coché.
  Ancienne configuration sauvegardée localement.
  6 novembre : l'utilisateur choisit de tester d'abord la chaîne complète avec
  un réveil préentraîné avant de revenir au mot personnalisé. Banc temporaire :
  modèle officiel openWakeWord `alexa_v0.1.onnx`, seuil 0,5, pas de vérificateur
  Whisper ; carte inchangée, service PC et modèle « Hé Alfred » conservés. Modèle
  entraîné en anglais : aucune fiabilité en français ni équivalence au moteur
  Amazon ne sont démontrées. Flux actif, modèle chargé et silence sans détection ;
  tests utilisateur au débit naturel, clavier, compréhension et enchaînements à faire.
  6 novembre : l'utilisateur a l'impression que le réveil ne fonctionne pas ;
  diagnostic humain à poursuivre, sans cause encore établie. État consulté :
  terminal connecté, veille active, quatre détections cumulées et aucune erreur ;
  ces compteurs ne prouvent pas la réussite des essais actuels.
  Retour suivant : fonctionne « une fois sur 1000 » (appréciation, pas mesure).
  Diagnostic : veille déclarée armée mais phase idle et aucun octet reçu pendant
  quatre secondes après une interaction. Rechercher et corriger le réarmement et
  l'indication d'état, puis mesurer la reconnaissance sur voix humaine ; ne pas
  attribuer l'ensemble des échecs au modèle sans distinguer ces deux causes.
  L'utilisateur demande un modèle français préentraîné pour comparaison. Piste
  non validée : Porcupine en français sur Windows, clé Picovoice et modèle de mot
  compatibles requis ; vérifier conditions et coût avant adoption. Un modèle
  « Hé Alfred » personnalisé resterait à générer puis à valider, pas présumé éprouvé.
  Prévoir comparaison réversible, contrôle du flux et tests de reprise et Fred.
  Correctifs de veille implémentés : surveillance et relance du flux absent,
  remise en veille après une reprise silencieuse, reprise après reconnexion et
  affichage actif conditionné aux trames récentes. Tests simulés : K2, silence,
  erreur et relance, flux interrompu et reconnexion. Sur carte réelle, veille
  activée puis flux reçu à 32 Ko/s et arrêtée à nouveau ; reprise après réponse,
  déconnexion physique, K2 et précision à la voix restent à valider en réel.
  Retour utilisateur : réveil difficile et retour en écoute très long. Correction :
  réarmement immédiat après fin silencieuse ou arrêt du firmware ; éviter qu'une
  relance amorcée par le délai de reprise annule sa propre tâche. Tests des trois
  fins sur terminal simulé ; délai et efficacité sur carte réelle à mesurer. Les
  huit secondes de reprise sans mot restent inchangées. Ne pas déduire la qualité
  du modèle des seuls tests du cycle de vie.
  Retour utilisateur : bruit entre les tours déclenche écoute et conversation.
  Distinguer reprise libre pendant les huit secondes, faux réveil du modèle et
  activation envoyée par la carte ; mesurer les compteurs d'origine sans conserver
  audio ou transcription avant de changer le seuil ou la sensibilité. Maintenir la
  reprise sans mot et vérifier les bruits réels et les commandes courtes.
  L'utilisateur précise : aussi après les huit secondes. Compteurs d'origine
  ajoutés et testés ; un réveil est observé sur la carte, sans confirmation qu'il
  corresponde au bruit de l'essai demandé. Cause et correction restent ouvertes.
  L'utilisateur confirme l'essai ; des activations ont été attribuées au détecteur.
  Filtre de confirmation local ajouté avant conversation ou action : transcrire
  en mémoire un court extrait et exiger « Alfred ». Un bruit ou une erreur de
  transcription est rejeté ; test simulé positif/négatif, vérification humaine
  et effet sur les ratés/latence restent à mesurer. Reprise et K2 non filtrés.
  Nouveau retour : amélioration partielle, mot encore mal détecté, réveils pendant
  la frappe clavier. Sept détections cumulées observées, sans pouvoir attribuer
  chaque tour à une frappe. Raccourcir à 6 s l'attente de parole après un réveil,
  compter les prises silencieuses et vider les mémoires audio du détecteur lors
  du réarmement ; tests simulés réussis, recette au clavier et voix à refaire.
  La mauvaise reconnaissance du modèle reste ouverte, sans hausse aveugle du seuil.
  Retour utilisateur : le clavier ne déclenche plus lors de son essai ; le réveil
  exige une parole très lente et trop articulée. Statut observé : trois détections
  dont un rejet par la vérification et deux tours, sans attribution par essai ;
  mesurer à débit naturel pour distinguer ratés du modèle et du filtre.
  Essai utilisateur déclaré terminé : entre les deux relevés, +1 détection de
  réveil, +4 captures de reprise, aucun rejet supplémentaire du filtre et +4 tours.
  Les reprises ne mesurent pas le mot de réveil ; succès perçus et délais exacts
  restent à préciser avant d'en déduire un taux de reconnaissance.
  Essai suivant : cinq demandes à débit naturel après retour en veille ; retour
  utilisateur : deux non-détections, deux détections suivies d'une réponse qui ne
  comprend pas la demande, une détection avec bonne réponse. Compteurs concordants :
  +3 détections du mot et +3 tours, aucun rejet de vérification supplémentaire.
  Échantillon limité : analyser séparément les deux manques du détecteur et la
  transcription ou le pré-roll des deux réponses incomprises ; ne pas en déduire
  leur cause sans observations de transcription ni réglage aveugle du seuil.
  Priorité révisée le 6 novembre : traiter S03 et la fin de parole S20 avant ce
  travail de réveil, à la demande de l'utilisateur. Ne pas reprendre avant cela ou
  nouvelle décision explicite.
  6 novembre : mot retenu **« Hé Alfred »** (trois syllabes, protège du risque « Fred »).
  Architecture **A retenue : détection côté serveur**, sans flashage de la carte.
  Constat bloquant vérifié sur la carte réelle : binaire 2026.9.0, projet
  `jyoushiki.waveshare-voice` v2.0.0, `available_wake_words=[]` et
  `max_active_wake_words=0` ; le YAML source v2.0.0 déclare pourtant quatre modèles.
  Aucun modèle n'est donc embarqué. Le générateur `lfpoulain/wakeword-generator`
  produit un modèle **ONNX openWakeWord** (~200 Ko) et sa documentation indique
  explicitement qu'il ne convient pas à microWakeWord sur microcontrôleur : la
  version B (tflite embarqué) aurait exigé un flash OTA et un autre corpus.
  Justification de A : aucun flash, socle d'embedding préentraîné de Google,
  vérificateur Whisper possible ensuite, latence de détection +250 à 350 ms
  seulement sur un tour mesuré d'environ 5,7 s. La carte dépend déjà du PC
  depuis T08, la dépendance n'est donc pas nouvelle.
  Livré : `alfred/wake_word.py` (détecteur, seuil, anti-rebond 2 s, veille avec
  pré-roll 0,6 s), `alfred/setup_wake_word.py` (prétraitement public vérifié par
  SHA-256, installation du modèle privé), intégration dans `alfred/terminal.py`
  (`start_wake_word`, `stop_wake_word`, renouvellement de session, réarmement),
  routes `/api/terminal/wake-word/*`, boutons dans le laboratoire vocal.
  Observabilité : `/api/terminal/status` publie `wake_word` avec détections,
  instant du dernier réveil, seuil, faux réveils déclarés et erreur, sans texte
  ni audio ni empreinte.
  Préfixe parlé corrigé en même temps : `WAKE_PREFIX` partagé retire « hé / eh /
  hey / et / alors / euh » devant « alfred » pour les lumières, minuteurs,
  musique et courses ; auparavant seul l'anglais « hey » était accepté, donc
  « Hé Alfred allume la lumière » partait vers l'IA sans exécuter la commande.
  16 tests dédiés ajoutés, dont la non-régression « he alfred » / « hey alfred ».
  Restent ouverts : essai humain chiffré (≥ 9/10 à 2 m, 0 déclenchement sur
  « Fred » x10, ≤ 0,2 faux réveil/h sur 1 h de TV ou chant), latence p50/p95
  mesurée, et vérificateur Whisper non engagé tant que le détecteur seul n'a pas
  été mesuré.
  Contrainte de faisabilité constatée : le firmware n'accepte **qu'un seul client
  Voice Assistant**. Une session longue depuis un second processus a rendu 0 octet
  en 660 s (`start_va` accepté, aucune trame reçue) ; le composant refuse
  explicitement un arrêt/désabonnement venu d'un autre client. La mesure de tenue
  doit donc passer par la connexion d'Alfred, pas par un harnais séparé.
  Second point vérifié sur la carte : le firmware n'entre en `STREAMING_MICROPHONE`
  qu'après un `VoiceAssistantResponse(port=0)`. `handle_start` doit donc retourner
  0 ; sinon la carte rapporte `failed_to_start` et n'envoie aucune trame. Une
  première version de la veille l'omettait : `phase=waking`, 0 octet, aucune erreur
  visible. Corrigé et couvert par un test.
  Modèle `alfred-he.onnx` entraîné le 6 novembre en WSL Ubuntu (Docker natif,
  RTX 2060 SUPER, CUDA 11.7) : 44 000 clips, 50 000 pas + deux affinages.
  Contrôle sur clips de validation jamais vus : score maximal 0,970, 31/40
  au-dessus de 0,5, négatifs 0/40 déclenché (max 0,002).
  Recette de généralisation sur cinq voix **Supertonic**, moteur et locuteurs
  distincts des voix Piper d'entraînement : **14/15 (93 %) sur la prononciation
  française** « Hé Alfred » / « Et Alfred », contre 2/5 pour la graphie anglaise
  « Hey Alfred » qui n'est pas celle visée. Le seuil 0,25 récupère M3 sur
  « Hé Alfred » (0,301 -> 0,502). 0 faux réveil sur 27 mots proches (« Fred »
  compris), 0 sur 12 phrases continues, et **0 déclenchement sur 60 min de parole
  enchaînée puis 60 min avec fond musical continu** (score max 0,020). Latence
  ajoutée par le détecteur : **0 ms**, la décision tombe avant la fin de l'énoncé.
  Seuil par défaut abaissé de 0,5 à 0,25 : deux détections gagnées, aucun faux
  réveil créé ; médiane des positifs 0,963 contre 0,117 pour le pire négatif.
  Restent ouverts : essai à la voix humaine, « Fred » dit par un membre de la
  famille, et faux réveils sur une TV ou un chant réels plutôt que synthétiques.
- [x] **T04 — Relier un terminal au service.** Captation/lecture, identité terminal,
  pièce/étage, flux audio et reconnexion ; faire fonctionner le prototype bureau.
  **Dépend de : T02, S03, S04, F01.**
  Depuis T08, ne plus utiliser le banc HA pour tester cette carte. Prototype
  direct livré et actif le 2 novembre (`alfred/terminal.py`) : pièce Bureau/RDC,
  MAC vérifiée, activation K2, capture après parole puis pause, pipeline navigateur
  réutilisé en interne, retours avec la référence au débit 1,242. Tests réels :
  lecture FLAC téléchargée et terminée, diagnostic micro 62 976 octets / 1,97 s
  sans transcription ni stockage. Après rejeu demandé, écoute du sample validée
  par l'utilisateur. API de statut et bouton d'essai ajoutés au laboratoire.
  Fenêtre de huit secondes et arrêt implémentés, silence sans appel IA testé.
  4 novembre : l'utilisateur confirme que la conversation fonctionne, avec un
  délai excessif traité en S19 ; prototype bureau validé, acoustique approfondie
  et reconnexion en panne réelle restent à tester en T01/T02/A04.
  Annonces, rappels et sonneries physiques non raccordés à
  cette nouvelle liaison. Voir `TERMINAL_DIRECT.md`. Recette logicielle :
  282 tests Python réussis, 3 optionnels ignorés ; 29 tests JS réussis.
- [ ] **T05 — Valider l'interruption vocale.** Écho du haut-parleur, bruit de l'ampli,
  arrêt effectif du son et des actions non encore exécutées, transition vers la
  nouvelle demande. Une détection de parole seule ne suffit pas.
  **Dépend de : T04, S06, F04.**
- [ ] **T06 — Arbitrer les terminaux simultanés.** Une seule réponse si plusieurs
  appareils entendent, conversations distinctes possibles, affectation pièce/étage
  et comportement si un terminal manque. **Dépend de : T03, T04, S06, I02.**
- [ ] **T07 — Valider les diffusions physiques.** Minuteurs par étage, annonces et
  rappels sur leurs destinataires, arrêt de sonnerie et priorités audio.
  **Dépend de : T06, F06, F07, F08.**

- [ ] **T10 — Corriger et valider le gel de l’écoute ESP32 après plusieurs commandes.**
  Signalement utilisateur du 13 novembre : arrêt forcé puis réactivation nécessaires.
  Carte Bureau réellement connectée et trames reçues au diagnostic ; panne non
  présente au relevé. Défauts identifiés dans le pont : relance par `start_va`
  sans terminer une session encore active (démarrage ignoré par ESPHome), et
  absence de récupération si la notification de fin de lecture est perdue.
  Correction : arrêt de session, pause de trois cents millisecondes puis relance
  bornée ; protection des callbacks pendant cet arrêt, compteur de récupérations
  sans contenu privé ; surveillance de la lecture avec marge sur sa durée et
  préservation des captures et traitements actifs. Aucun rejeu de commande.
  Vérification : suite complète 768 tests réussis/deux ignorés, puis 36 tests
  de réveil réussis après ajout du cas arrêt en échec puis nouvelle tentative.
  Les scénarios couvrent session active ignorant start, fin de lecture perdue,
  silence/flux sain et préservation des opérations actives. Service relancé
  par sa tâche Windows et veille STT Alfredo réarmée ; contrôle réel du flux
  consigné dans le cadrage. Recette humaine sur plusieurs commandes et
  reproduction exacte de la panne restant à faire. Aucun flashage.
  **Dépend de : T03, T04 ; recette prolongée en A04.**

## 7. Administration et mise en service

- [x] **A10 — Préparer le plan de réalisation des optimisations.**
  Demandé le 13 novembre après l'audit global ; livré dans
  `docs/PLAN_OPTIMISATIONS.md` : lot 0 de reprise/référence, puis sept lots avec
  dépendances de démarrage, livrables et critères de sortie. Tests logiciels,
  mesures et recettes humaines distingués ; migration conditionnée à l'hôte,
  objectifs chiffrés et arbitrage audio explicitement proposés. Le plan est livré,
  les développements O01–O06 restent ouverts. **Dépend de : audit global.**

- [x] **O01a — Livrer la supervision et le début de réponse anticipé.**
  Suite demandée le 13 novembre après le plan. Santé par composant, âge de
  progression et raison de récupération sans secret ; renouvellement périodique
  séparé d'un incident ; catalogue partagé et compteurs ; actualisation des
  panneaux masqués arrêtée ; cache des assets versionnés ; calcul du diagnostic
  ESP32 sans requête interrompue ; certificat local
  renouvelé jusqu'au 13 novembre 2027, ancien conservé sous `.local/https`.
  Première liaison synthèse anticipée → navigateur : phrases complètes seulement,
  audio unique progressif, aucun appel d'outil supplémentaire, repli au mode
  standard sur erreur. Suite Python finale **777 réussies/deux ignorés** et
  43 JS réussies ; les tests ciblés du streaming anticipé réussissent.
  Service redémarré, ESP32 identifié, veille réarmée, flux de 255 488 octets en
  huit secondes, transport/micro/détecteur `ok`, aucune erreur. Limites ouvertes : recette acoustique
  du premier son, réponses réelles longues, annulation pendant Phonon, confiance
  du certificat sur les appareils, réseau mobile/latence et mesure p95. Aucun
  réglage de réveil changé. **Complète T10/O01 et contribue à S19.**

- [x] **F10 — Conserver le contexte du minuteur et arrêter sa sonnerie à la voix.**
  Retour utilisateur du 14 novembre : sans numéro, la consultation et l'annulation
  demandaient une clarification ; la sonnerie ESP32 ne pouvait être coupée à la voix.
  Livré par le même service de minuteurs : "quel temps reste-t-il sur le minuteur"
  vise la sonnerie active, sinon la création la plus récente du même étage ;
  "annule le minuteur" retire ce minuteur et le confirme par son numéro. Une demande
  explicitement plurielle conserve le choix par numéro. Pendant la sonnerie, le
  firmware coupe le son dès qu'il reconnaît le mot de réveil, sans attente réseau :
  dire « Alfredo » seule. L'interface explique ce geste. Tests ciblés minuteurs,
  sonnerie, intents et API : **111 réussis** ; suite complète finale **778 réussis/
  deux ignorés** et JavaScript **43 réussis**.
  Reste à confirmer à l'écoute que le mot est reconnu pendant le timbre et que
  l'annulation sans numéro fonctionne depuis l'ESP32. Service relancé ; Bureau
  identifié, veille active, transport/micro/détecteur `ok`, santé HTTP 200.
  **Complète F06/F07 sur le cycle d'un terminal ; la diffusion multiroom reste T07.**

- [x] **F27 — Corriger la consultation du minuteur courant depuis l'ESP32.**
  Orientation corrigée par l'utilisateur : rendre la compréhension résiliente,
  sans accumulation de formulations. Le raccourci local laisse désormais les
  formulations inconnues rejoindre les outils IA typés. Suppression des consignes
  conversationnelles qui exigeaient une reformulation malgré ces outils ; ajout
  de l'opération `remaining` pour consulter le courant via l'interprétation IA.
  106 tests ciblés et suite complète de 787 tests réussis, deux ignorés.
  Service relancé, ESP32 reconnecté, veille et santé micro/détecteur `ok`.
  Compréhension par le
  modèle réel et recette acoustique restent à confirmer ; repli dépendant de l'IA.
  Complément du 14 novembre après retour terrain : acceptation de « On met un
  minuteur de deux minutes » et des questions inversées (« Il reste combien de
  temps sur le minuteur ? »). Le chemin local conserve maintenant la sélection
  du minuteur courant au lieu de transformer la demande en liste complète.
  Tests traversant l'API vocale avec STT simulé et deux minuteurs : création,
  consultation du plus récent, liste complète et annulation isolée ; 102 tests
  ciblés réussis ; suite complète : 783 réussis, deux ignorés. Service redémarré.
  Validation acoustique réelle encore ouverte.
  Retour utilisateur du 14 novembre : l'annulation sans numéro fonctionne, mais
  « quel temps reste-t-il sur le minuteur » est encore rejeté par le raccourci
  vocal avec « Précisez une durée ». Le service de minuteurs connaissait la
  formulation ; le filtre local d'intentions en utilisait une liste incomplète.
  Corrigé en partageant `is_current_timer_query()` entre le service et le chemin
  local. Essai traversant sur la tâche active : « Minuteur onze : encore dix
  minutes. », puis « Minuteur onze annulé. » ; zéro appel IA, plus aucun minuteur
  actif après l'essai. Suite complète : **779 réussis/deux ignorés**. Service
  relancé, santé générale HTTP 200 et transport/micro/détecteur reconnus.
  Recette acoustique depuis l'ESP32 restant à faire.

- [x] **A09 — Rétablir les textes de la conversation ESP32 dans le laboratoire.**
  Demande du 8 novembre : afficher les mots reconnus et la réponse d’Alfred dans
  les deux zones existantes. Flux conversationnel raccordé à un dernier échange
  éphémère, endpoint sans cache et actualisation chaque seconde ; affichage avant
  synthèse vocale et erreurs visibles. Statuts techniques sans texte préservés.
  57 tests Python et 17 tests JavaScript ciblés réussis. Service local relancé,
  page et endpoint vérifiés HTTP 200, ESP32 identifié et reconnecté ; essai
  humain après actualisation restant en A01.
  **Dépend de : T04, A07.**

- [x] **A07 — Réorganiser le banc web par fonction.** Demande du 4 novembre :
  réduire le défilement pour accéder aux essais. Huit vues à accès direct,
  navigation persistante adaptée aux petits écrans, laboratoire vocal à l'ouverture,
  étage commun et aide/réglages secondaires repliables. Champs et contrôleurs
  conservés ; sélecteur d'étage toujours associé au formulaire d'échéance.
  **Dépend de : S01.** 29 tests JS réussis ; structure HTML, identifiants et
  navigation des huit vues vérifiés sans matériel ni commande vers la maison.
  Recette visuelle ordinateur/téléphone et satisfaction utilisateur à confirmer
  dans A01 ; accès navigateur désactivé pour cette session.
- [ ] **A08 — Renouveler le certificat HTTPS de développement expiré.**
  Expiration constatée le 4 novembre pendant un GET avec validation du certificat
  de `.local/https/server.crt`. Le serveur répond à la connexion TLS, mais la
  validation HTTPS échoue. Prévoir le renouvellement local et vérifier les
  accès PC/téléphone ; aucune modification du certificat ou du service réalisée.
  **Dépend de : A06.** Le contrôle HTTP de la nouvelle interface reste à confirmer.

- [ ] **A01 — Construire l'interface dédiée.** Profils/enrôlement, permissions,
  mémoires, rappels, courses, terminaux/pièces/étages, réglages et diagnostic.
  Peut commencer par des écrans simulés ; validation finale avec services réels.
  **Dépend de : P01, P03, P06, I01, I03, I04, I05, F05, F06, T04.**
  Écrans locaux fonctionnels pour échéances, santé et laboratoire vocal ; n'incluent
  pas encore les profils et autres modules. Aperçus dans `.local/screenshots/`.
  4 novembre : navigation par fonction livrée en A07 pour les modules existants,
  dont les profils. Recette visuelle et retour utilisateur attendus ; le travail
  restant sur les permissions/mémoires n'est pas validé par cette réorganisation.
- [ ] **A02 — Installer durablement le service.** Configuration et secrets séparés,
  volumes persistants, redémarrage automatique, état de santé et limites de ressources.
  **Dépend de : P04, P06, S01, S08.**
  27 novembre, procédure proposée : choisir une révision vérifiable, installer
  Alfred dans un venv avec les dépendances nécessaires au réveil STT, compiler
  Parakeet sur Debian et recréer le venv Phonon avec les chemins Linux du profil.
  Le verrou Windows inclut openWakeWord 0.6.0, dont la dépendance Linux
  `tflite-runtime` ne fournit pas de roue pour Python 3.13. Recetter d’abord le
  réveil Parakeet, puis traiter openWakeWord si ce mode doit être utilisé.
  Prévoir un service `systemd` sous un compte dédié, une IP réservée pour le
  retour audio ESP32 et un HTTPS reconnu par les navigateurs. Vérifier la PWA si
  utilisée et terminer la protection d’accès prévue en P06 avant l’ouverture
  à la famille. Compilation, voix et redémarrage restent à vérifier sur Debian.
  Variante demandée pour les deux instances : évaluer Docker Compose commun,
  image `amd64` construite une fois et promue par digest, données et réglages
  propres à chaque hôte. Si retenue, la supervision Compose remplace la recette
  `systemd` directe ci-dessus. Préparer le Dockerfile multiétape et vérifier le
  montage des modèles, le build PWA sans clés privées, le réseau du satellite et
  l’isolement des intégrations dev. Voir `HEBERGEMENT_ET_HA.md`. Proposition à
  confirmer et à recetter sur les deux hôtes.
  L’installation directe en VM dédiée est également envisagée par l’utilisateur.
  Proposition : script commun, dépendances Linux verrouillées et même archive
  versionnée testée en dev puis installée en prod. Vérifier la compatibilité du
  serveur de dev, le démarrage du service et la recette audio sur la VM cible.
  27 novembre : scripts de construction et d’installation livrés dans
  `deploy/debian/`. Paquet Linux avec roues Python, worker Parakeet et build PWA,
  service `systemd` et données persistantes séparées. La PWA est compilable
  sans certificats ; son hébergement HTTPS reste à configurer. Construction,
  SHA-256, installation hors ligne des roues et démarrage de l’API vérifiés
  dans Debian 13 jetable. Transcription Parakeet sur WAV synthétique et
  synthèse Phonon Arnaud vérifiées avec le paquet. Unité contrôlée par
  `systemd-analyze`, avec `systemctl` simulé pour l’installation. Le démarrage
  au boot, la recette ESP32 et la promotion dev/prod restent ouverts.
  À la demande utilisateur, fournir une installation APT native. Le nom
  Debian est `alfred-home` pour éviter le paquet réseau officiel `alfred`.
  Construction `.deb`, dépôt signé avec canaux dev et prod et guide livrés
  dans `deploy/debian/`. Debian 13 jetable : même paquet dans les deux canaux,
  installation APT signée, mise à jour, sauvegarde, rétrogradation, démarrage
  de l’API et retrait du paquet avec conservation des données vérifiés.
  `systemctl` simulé pendant la recette APT. Choisir l’hébergement du dépôt et
  sa clé de signature, puis tester le service réel et l’ESP32 sur la VM.
  Suite utilisateur : versionner la distribution sur GitHub. Dépôt rendu
  public à sa demande et visibilité vérifiée. Préparation des fichiers APT
  signés par release dans `deploy/debian/github-release-assets.sh`. APT testé
  avec index signé et redirections de téléchargement simulant GitHub Releases.
  Scripts versionnés sur `codex/debian-apt-release`. Release publique Latest
  `v0.6.0`, commit `94730975c9a2`, paquet `alfred-home` `0.6.0-1`, index signé
  et `alfred-home.sources` publiés. Clé d’exploitation dédiée conservée dans
  le trousseau local WSL. Installation APT via le tag, validation de l’unité
  et démarrage de l’API vérifiés en Debian 13 jetable avec `systemctl` simulé.
  Source Latest et téléchargement SHA-256 vérifiés depuis GitHub. L’utilisateur
  indique que la VM n’est pas encore créée. Raccordement et démarrage réel
  `systemd` restent ouverts.
  27 novembre, demande utilisateur : gérer les mises à jour dans Alfred.
  Recherche manuelle, installation immédiate d’une version supérieure et
  option automatique quotidienne implémentées dans les deux interfaces.
  Automatique désactivé par défaut, exécution à 4 h (heure du serveur), code
  administrateur et service `systemd` dédié au paquet et à sa source APT.
  Recherche, refus sans code, installation forcée et traitement automatique
  vérifiés entre trois vrais paquets sous Debian 13 jetable avec `systemctl`
  simulé. Publication dans un paquet suivant et déclenchements réels sur la
  VM restent ouverts.
  Skill locale `alfred-release` créée pour le build Debian, la signature APT
  et la promotion GitHub Latest à la demande. Recette sur `v0.6.0` : build
  du commit exact et signature locale vérifiés, installation via le tag et
  téléchargement signé via Latest vérifiés. Recette en lecture seule sur
  GitHub, version courante vérifiée à `v0.6.0`.
  27 novembre, migration vers la VM de dev : dépôt cloné dans
  `/home/morris-dev/Assistant_vocal`, venv Python 3.13, Node 24.22 et Rust 1.100
  installés en espace utilisateur, worker Parakeet Linux compilé, UI construite,
  données et modèles restaurés, certificat HTTPS régénéré pour `192.168.1.71` et
  service utilisateur `alfred-dev.service` démarré. `/health` répond, Parakeet
  transcrit et Phonon synthétise après reconstruction locale de `ptts` 0.7.0
  (le wheel officiel exige AVX). Le terminal ESP32 est hors ligne et les trois
  secrets DPAPI restent à ressaisir.
  Bascule du 27 novembre : instance Windows arrêtée, SQLite finale copiée et
  `integrity_check` ok. Recette Linux : 963 tests Python réussis, 2 ignorés,
  48 tests JavaScript et 18 tests UI réussis ; interface HTTPS 200, STT 2,2 s,
  TTS 1,24 s pour une phrase courte. Secrets et terminal restent à raccorder.
- [ ] **A03 — Prévoir et vérifier sauvegarde/restauration.** Configuration, mémoires,
  profils et échéances ; procédure de mise à jour/retour arrière. Essai de restauration
  distinct de la production. **Dépend de : A02, I04, F06, F07.**
  27 novembre, bascule proposée : préparer et tester la VM en isolant les actions
  réelles, arrêter l’instance Windows avant la copie finale de SQLite et le
  raccordement des intégrations, ressaisir les secrets DPAPI sur Debian et tester
  une restauration depuis une sauvegarde hors de l’AuBox. Garder l’installation
  Windows disponible pour un retour arrière, avec décision sur les données créées
  sur la VM avant toute reprise de l’ancienne instance.
  Avec Compose, conserver aussi le digest d’image précédent et les versions
  des modèles. Vérifier la compatibilité de SQLite et des réglages lors d’un
  retour arrière, ainsi que la restauration du volume de prod en environnement isolé.
  L’installeur Debian sauvegarde l’état avant chaque bascule et réactive la
  version précédente en cas d’échec au démarrage. Ordre arrêt/sauvegarde et
  retour du code avec conservation des données vérifiés en simulation. Essai
  de restauration réelle et copie hors de la VM restent ouverts.
  27 novembre, archive de pré-migration créée et vérifiée par SHA-256 ; la
  restauration réelle et la copie hors de la VM restent à faire.
  Archive `alfred-state-20261127.tar.gz` SHA-256 `4DED5A23…` ; bundle Git
  `Assistant_vocal-9fd1670.bundle` SHA-256 `12AEE568…`.
- [ ] **A04 — Recette bureau puis salon.** Scénarios familiaux, français naturel,
  musique, profils et confidentialité, pannes réseau/services, redémarrage, quota et
  latence ; consigner résultats et écarts. **Dépend de : P05, A01, A02, A03, F09, F02,
  F03, F04, F05, S07, I05, T03, T05, T07.**
- [ ] **A05 — Étendre aux autres pièces.** Documenter ajout/enrôlement d'un appareil,
  coût et ressources par terminal ; revalider simultanéité et couverture des étages.
  **Dépend de : A04.**
- [x] **A06 — Vérifier l'accès au serveur de développement via le VPN existant.**
  Correction explicite utilisateur : accès LAN direct, sans nouvelle passerelle.
  Android WireGuard `10.8.0.2/24` via serveur `.103`, PC Alfred `.23`.
  **Dépend de : S13.** L'authentification et l'accès durable restent ouverts en P06.
  Ajout de `--host 192.168.1.23`, hôte autorisé explicite et refus des origines
  étrangères préservé. Service relancé sur `.23:8765` ; santé et page HTTP 200
  vérifiées. Recette : 134 tests Python réussis, 1 vocal optionnel non activé.
  Passerelle HTTPS arrêtée, code et fichiers temporaires retirés. VPN inchangé ;
  aucune règle de pare-feu ajoutée.
  L'utilisateur demande ensuite HTTPS : option `--https` ajoutée au même serveur,
  certificat auto-signé de sept jours et clé privée sous `.local/https`, protégés
  par ACL. Aucun nouveau proxy/port. Service démarré en HTTPS sur `.23:8765` ;
  santé, page et script vocal vérifiés 200 avec validation du certificat côté PC.
  134 tests Python réussis, 1 vocal optionnel non activé. Avertissement certificat
  possible sur Android. L'utilisateur confirme ensuite que l'accès fonctionne
  sur son téléphone et que l'essai vocal de création d'un minuteur fonctionne.
  Consultation, annulation et Stop également essayés et confirmés par l'utilisateur.
  Ce test ne valide ni les sonneries physiques ni le déploiement durable.
  30 octobre : une tâche Windows utilisateur `Alfred Assistant Vocal` maintient le
  service après la fin des sessions de commande. `/health` et la page répondent 200
  sur `192.168.1.23:8765`. Le lancement passe par le Python système déjà autorisé
  par le pare-feu, avec les dépendances du `.venv` ; la règle dédiée au port
  nécessitait des droits administrateur.

## 8. Optimisations proposées après audit global du 13 novembre

- [ ] **O07 — Évaluer l'intérêt de Jev pour des décisions bornées. Proposition.**
  Avis demandé le 15 novembre ; Jev de TypeSafe confirmé par l'utilisateur,
  aucune intégration autorisée. Candidats : choix d'intention/cible connue et
  classement de résultats. Un essai éventuel doit comparer la chaîne complète
  avec/sans Jev, les appels IA effectivement évités, le coût, les médianes/p95
  et les erreurs sur français, contexte, négations et demandes multiples.
  Prévoir abstention/clarification ; conserver les contrôles d'exécution.
  Aucun appel API ni changement de service réalisé pour cet avis.
  **Dépend de : S05, F22, I05/O01 pour les mesures.**

Rapport : `docs/AUDIT_OPTIMISATIONS_2026-11-13.md`. L'utilisateur demande une
revue et des propositions ; aucune implémentation ni priorité nouvelle validée.
Le plan de réalisation demandé ensuite est livré dans `docs/PLAN_OPTIMISATIONS.md`
(A10). Commencer par le lot 0, puis la supervision/mesure du lot 1 est l'ordre
proposé ; la demande de plan ne lance pas l'implémentation des optimisations.
Audit réalisé : 769 tests Python réussis/deux ignorés, 43 JavaScript réussis,
contrôles locaux en lecture seule. Recette visuelle Firefox bloquée par l'outil.

- [ ] **O01 — Renforcer la supervision et les mesures vocales. Proposition.**
  Distinguer renouvellement prévu, flux absent et fin de lecture perdue ; santé
  des composants, transitions/événements tardifs et cent cycles simulés. Raccorder
  les temps ESP32 au journal existant et mesurer le premier son séparément.
  **Démarrage : lot 0, I05 et correction logicielle T10 disponibles.** P05 est
  précisé par le protocole ; recette humaine T10 et bilan S19/A04 restent des
  critères de validation, sans empêcher le démarrage du lot 1.
  Banc ESP32 de latence d’allumage implémenté pour l’état de référence. Balises
  de fin de parole, réveil, STT, modèle, préparation et envoi HA, confirmation
  d’état, synthèse et demande audio. Réussite, annulation, réponse HA perdue,
  état absent, ambiguïté, négation et cible exclue vérifiés en simulation.
  Armement et fermeture vérifiés sur le service HTTPS et l’ESP32 connecté.
  Référence réelle du 23 novembre terminée : 15/15 réussites au premier énoncé
  sur l’ESP32 et les deux lampes de la cuisine. Médiane de 4,42 s entre la fin
  de parole détectée et le dernier état `on` observé.
  Raccourci local implémenté pour les allumages explicites, avec relais de la
  même transcription pour les demandes libres ou ambiguës. Service relancé
  et ESP32 reconnecté. Avec le catalogue réel, quatre formulations du banc
  résolvent les cibles localement et la formulation libre reste destinée au
  modèle. Comparaison réelle du 23 novembre : sur les 10 essais locaux, de
  4,35 à 2,24 s en médiane sur les cas correspondants. Le banc atteste 14/15
  réussites au premier énoncé, contre 15/15 avant : une pièce mal transcrite
  n'a déclenché aucun envoi tracé. Garder la recette de fiabilité ouverte.
  Omission de « de » sur un nom de lampe unique et clarification locale d’une
  pièce inconnue implémentées. Essai de dictionnaire limité à « cuisine » :
  18/24 reconnaissances du nom sur des audio synthétiques contre 16/24,
  témoins inchangés. Réglage à l’essai sur le service relancé et ESP32
  reconnecté. Diagnostic audio et clarification sans action vérifiés via
  le service actif. Reste le diagnostic micro ESP32 puis les 15 essais.
  Protocole et export local dans `PROTOCOLE_TEST_AUDIO.md`.
- [ ] **O02 — Mutualiser les échanges et le catalogue Home Assistant. En partie.**
  Métadonnées partagées, invalidation, connexions réutilisées ; garder exclusions,
  exposition, groupes et capacités vérifiés avant action. Mesurer les lectures
  par commande et tester modifications entre préparation et exécution.
  **Démarrage : socle F01/F02 existant et mesures O01 disponibles.** Préserver
  les contrôles existants ; lot 2 du plan. Connexions HTTP réutilisées et
  mesures des lectures PWA réalisées en A13. Le catalogue et les mesures par
  commande restent à traiter dans ce lot.
  Proposition du 19 novembre : examiner d’abord les lectures de Musique.
  Le sélecteur récupère tous les états HA puis filtre les lecteurs. Chaque
  recherche ou ouverture de favoris redécouvrait aussi l’intégration Music
  Assistant. Correction livrée : lecture des lecteurs espacée de 15 à 60 s,
  état du lecteur actif toutes les 5 s, découverte conservée une minute
  en mémoire avec invalidation par changement de serveur ou jeton, erreur
  ou expiration. Vérification du lecteur avant commande conservée. Tests
  de réutilisation et d’invalidation réussis. Favoris Titres via 5173 :
  médiane de 37 ms sur huit lectures HTTP 200, dont une à 115 ms. La réduction
  du volume par lecture des états HA reste à étudier.
- [ ] **O03 — Faire progresser le streaming vocal de bout en bout. Proposition.**
  Phrase IA stabilisée vers Phonon pendant la suite du texte, puis éventuelles
  trames natives si gain démontré. Ne confirmer une action qu'après son résultat.
  Voix et moteurs actuels conservés ; valider nombres, coupure et erreurs.
  **Dépend de : O01 stabilisé et socle Phonon S28/S29 disponible.** Complète
  S19, sans attendre sa clôture globale ; lot 4, après comparaison des lots 2/3.
- [ ] **O04 — Réduire actualisations et téléchargements inutiles. En partie.**
  Écrans actifs, arrière-plan, gardes/délais et mutualisation des statuts ; cache
  seulement des assets versionnés, sans cache des données personnelles/audio.
  **Dépend de : A07 ; contribue à A01.** Lot 3 avec A08 ; objectifs proposés
  et comptage réseau réel décrits dans le plan. En A13, la PWA sert le build
  compilé et suspend les lectures périodiques en arrière-plan. La mutualisation
  des statuts et le comptage global des requêtes restent ouverts.
  Suite du 19 novembre livrée : chargement différé de Musique et Paramètres,
  bulles de conversation mémorisées et défilement regroupé par image. Module
  principal 333 → 294 Ko avant compression, 91 Ko transférés en gzip ; les
  modules différés restent précachés pour l’usage hors ligne. Retour et
  brouillon vérifiés dans Chrome Android. Douze échanges simulés dans Chromium :
  texte en flux, sources et défilement vérifiés. Build, 16 tests UI,
  46 tests JS du laboratoire et 884 tests Python réussis, 2 tests Python ignorés.
  Restent les mesures sur le téléphone
  au lancement à froid et au changement de page, en Wi-Fi et via VPN, et le
  profilage des longues conversations.
- [ ] **O05 — Concevoir une vue quotidienne et un diagnostic distinct. Proposition.**
  État utile, dernier échange, parler/arrêter, échéances ; réglages/tests repliés.
  Afficher distinctement enregistrement du rappel et disponibilité de diffusion.
  Recette réelle mobile/ordinateur nécessaire avant validation ergonomique.
  **Démarrage : A09 et états O01 disponibles ; maquette préparable avant les
  sorties audio.** Contribue à A01 ; affichage final selon F06/F07/T07 réellement
  disponibles, lot 6. La finalisation globale A01 n'est pas un préalable.
- [ ] **O06 — Simplifier l'exploitation et la maintenance. Proposition.**
  SQLite bloquant à isoler sans perdre unicité/arrêt transactionnel ; modules et
  protocole worker générique, état documentaire court, historique Git local
  après vérification des exclusions ; bilan d'usage à partir du diagnostic existant.
  Installation supervisée et sauvegarde/restauration selon disponibilité Debian.
  **Démarrage : état de référence du lot 0 et I05 ; contribue à A02/A03/P04/S08.**
  Travaux locaux de reprise au lot 0, extractions ciblées dans chaque lot puis
  finalisation au lot 7. Migration finale conditionnée à l'hôte disponible.
  Authentification/droits restent différés avant production.

## Prochaine progression possible

Plan transversal demandé le 11 novembre : voir `PLAN_RESTANT.md` pour le détail
par domaine, les recettes et l'ordre de réalisation proposé. Cet ordre n'est pas
une nouvelle priorité validée et ne lève pas les reports utilisateur. Les tâches
gardent leurs identifiants et leurs états ; aucun développement supplémentaire
n'est déclaré terminé par cette synthèse.

**11 novembre : Phonon est le seul TTS retenu ; Dumby est actif et par défaut,
Alfred cloné, Arnaud et Lucien restent disponibles.**
Les anciens essais vocaux sont historiques ; ne pas les réactiver à partir des
propositions antérieures sans nouvelle demande. Poursuivre la recette Phonon et
les autres fonctions selon le choix utilisateur.

**11 novembre : sonnerie des minuteurs raccordée au pont direct.** Le minuteur
sonne désormais sur l'ESP32 du bureau sans Home Assistant, et un bouton permet
de tester le son. Le prochain trou fonctionnel identifié est la diffusion des
annonces et rappels sur le même haut-parleur, aujourd'hui sans cible audio.


**Priorité du 8 novembre : approfondir le fonctionnement de l’assistant.**
Jarvis est accepté pour poursuivre après un essai humain très positif, même à
basse voix. Conserver les réglages ; réveil personnalisé et essai musical différés
par l’utilisateur. Le premier défaut fonctionnel choisi ensuite concerne la prononciation française
du TTS (S21) : heures et négations. Correction logicielle jugée insuffisante à
l’écoute ; comparaison de diction proposée en S22, moteur alternatif non choisi.


**Priorité du 6 novembre : S03, qualité de transcription sur navigateur et ESP32.**
Small/beam5 est installé et retenu après retour humain positif. S20 est validé
pour le fond chanté externe de l'utilisateur. Conserver les réglages ; recettes
plus larges et hôte cible encore ouverts. Choisir le prochain chantier au retour :
réveil Alfred proposé, ou diffusions physiques sur le pont direct ; aucun de ces
nouveaux chantiers n'est lancé par la seule note de reprise.

Le 30 octobre, après le raccordement de Music Assistant et de Pocket TTS,
recette complète relancée : **262 tests Python réussis, 2 tests réels optionnels
ignorés ; 28 tests JavaScript réussis**. Le test vocal réel Supertonic → Whisper
avait également réussi, et Pocket TTS a été chargé avec un profil de voix français
préparé localement. La suite Python a été exécutée
hors du bac à sable Windows : elle comprend le test HTTP de calibration qui se
bloquait dans le bac à sable. Cela ne valide ni l'acoustique réelle ni la
calibration avec une seconde personne. Les permissions et la protection de
l'interface (I03, P06 et A01) sont depuis différées par l'utilisateur avant la
mise en production ; priorité actuelle aux fonctions. Service HTTPS relancé sur
`192.168.1.23:8765`, santé `ok` et lecteur Music Assistant vérifié.

Le 29 octobre, l'utilisateur indique ne pouvoir communiquer que par écrit pour
le moment : différer les essais et travaux vocaux, sans abandonner les fonctions
correspondantes. Privilégier les tâches réalisables à l'écrit ; les validations
nécessitant une voix ou un terminal physique restent ouvertes.

Accès smartphone : ouvrir `https://192.168.1.23:8765/` avec le VPN WireGuard
existant activé. Alfred écoute désormais directement sur le LAN à la demande
explicite de l'utilisateur. Accès, création vocale, consultation, annulation et
Stop confirmés par l'utilisateur sur son téléphone (A06).

Diagnostic d'accès du 27 octobre résolu côté service : le navigateur tentait
d'ouvrir `alfred/static/index.html` en `file://`. Utiliser
`http://127.0.0.1:8765/`. Ancien processus v0.5 identifié puis redémarré ;
`/health` confirme v0.6.0 et `/` répond HTTP 200 avec l'interface des minuteurs.
  La création vocale est depuis validée par l'utilisateur en S13.

Le 27 octobre, l'utilisateur est hors domicile et choisit les minuteurs : commandes
du banc livrées et vérifiées en S13, création vocale confirmée sur Android.
Autres pistes proposées sans sélection validée : historique I05, préparation des
permissions I03 avec identités simulées et réglages A01, courses F05 avec HA simulé.
Les prérequis de validation réelle restent applicables ; essais acoustiques et
manipulations ESP32 à son retour.

Préparation hébergement/HA en cours : voir `HEBERGEMENT_ET_HA.md` pour les relevés,
la proposition concrète et les choix restant ouverts. Aucun point P03/P04/F05
n'est coché sur la seule base de cette préparation documentaire.

Les essais audio T01 sont différés, pas le projet. S01 et le banc local S09 sont
terminés. S10 terminé pour le banc synthétique ; S02 validé par l'essai utilisateur.
S11 terminé et conversation réelle validée qualitativement par l'utilisateur ;
S05 reste ouvert pour mesures, comparaison du modèle et outils. Retours STT/TTS S03/S04,
en parallèle
des choix d'accès/hébergement P04/P06.
v0.5 : lumières Home Assistant implémentées, 29 tests synchrones avec HA simulé.
Connexion réelle au HA de la maison et extinction effective des lampes confirmées
par l'utilisateur le 26 octobre ; restent les exclusions de lampes, les permissions
par profil et le comportement en cas de coupure réseau.
S12 terminé côté logiciel ; prochain essai utilisateur : enchaîner deux demandes au
calme, laisser expirer huit secondes, puis tester « Arrêter la conversation ».
Les règles encore ouvertes restent en P01/P02. Cette liste ne déclenche pas à elle
seule les installations ou modifications des services existants.
