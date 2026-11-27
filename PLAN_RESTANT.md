# Alfred — plan du travail restant

État documentaire au 11 novembre 2026, établi depuis CADRAGE.md et CHECKLIST.md.
Ce plan ne constitue pas une nouvelle recette du service ou du matériel.
L'ordre proposé ci-dessous reste une proposition ; les décisions déjà validées
et les travaux différés dans le cadrage continuent de s'appliquer.
Les identifiants renvoient aux tâches existantes : aucun chantier n'est déclaré
terminé par la seule rédaction de ce document.

Complément du 13 novembre : le [plan des optimisations](docs/PLAN_OPTIMISATIONS.md)
décrit les lots de réalisation issus de l'audit global, leurs dépendances et leurs
critères de validation. L'ordre transversal ci-dessous reste la proposition du
11 novembre ; le nouveau plan détaille le chantier d'amélioration demandé ensuite,
sans clore les tâches fonctionnelles ni lever les reports utilisateur.

## 1. Domotique — F01, F02, P01, P03, I03

Acquis : connexion HA, commandes de lumière et extinction réelle confirmées.
Alfred reste autonome ; HA fournit les appareils et leur organisation.

Travail restant :
- Définir les entités autorisées et les exclusions, indépendamment des permissions
  par personne. Vérifier que chaque chemin de commande respecte cette sélection.
- Arbitrer la liaison domotique REST / MCP / réutilisation d'Assist. MCP est une
  proposition, pas une décision. Vérifier la documentation officielle et la
  couverture de la version installée avant de choisir.
- Compléter les associations terminal → pièce → étage et les noms usuels.
- Préciser la clarification lorsque plusieurs appareils peuvent correspondre.
- Recenser les autres équipements réellement présents et les usages souhaités :
  prises, volets, chauffage, scènes, etc. Ce sont des extensions à sélectionner,
  pas des fonctions toutes commandées par défaut.
- Étendre les commandes retenues : action simple, consultation d'état, paramètres
  disponibles, puis demandes composées avec résultats partiels explicites.
- Vérifier les échecs HA, les appareils indisponibles et les délais ; ne pas
  annoncer une exécution réussie sur la seule décision du modèle.
- Appliquer les permissions et confirmations configurées avant mise en production.

Recette : commande locale sans pièce, commande vers une autre pièce, toutes les
lumières de la maison, cible exclue, ambiguïté et coupure HA.

## 2. Musique — F03, F04, T05, T07

Acquis : lecteur de l'ampli sélectionné, lancement Airbourne constaté dans HA,
pause/reprise/arrêt/suivant/précédent et outils conversationnels. Atténuation et
restauration du volume vérifiées pour le navigateur.

Travail restant :
- Valider à l'écoute la recherche Qobuz par artiste, album et titre.
- Traiter les homonymes et demandes ambiguës par une clarification utile.
- Compléter et recetter les playlists selon les usages retenus.
- Définir le lecteur par défaut de chaque pièce et le choix explicite d'un lecteur.
- Préciser les commandes de volume souhaitées et leur interaction avec les
  changements manuels et l'atténuation automatique.
- Raccorder et vérifier l'atténuation sur tout le cycle ESP32 : réveil, prise de
  parole, réponse, reprise de huit secondes, arrêt et erreur.
- Arbitrer les conflits avec sonneries, annonces et rappels ; restaurer le volume
  sans écraser une modification manuelle.
- Tester ampli éteint/indisponible, erreur de recherche, Qobuz indisponible,
  perte réseau et plusieurs terminaux utilisant le même lecteur.

Recette : « Mets Airbourne sur l'ampli », un album, un titre ambigu, une playlist,
puis conversation avec musique et retour au volume précédent. L'essai musical
acoustique différé doit être repris lorsque l'utilisateur le choisit.

## 3. Rappels — F06, F09, P02, P03

Acquis : calendriers HA personnel et familial comme sources de référence ;
création/consultation, récurrence hebdomadaire, modification et suppression ciblées
déjà raccordées. Retour utilisateur global positif ; recette exhaustive ouverte.

Travail restant :
- Raccorder la diffusion au TTS Phonon et au haut-parleur du terminal direct.
  Actuellement les annonces et rappels n'ont plus de cible audio HA.
- Conserver le terminal de création comme destination personnelle par défaut,
  avec autre pièce choisissable. Décider du défaut pour une création web/HA.
- Vérifier les formulations de date, l'heure manquante demandée, les rappels
  personnels/familiaux et l'identification du destinataire.
- Compléter la modification d'une série entière, actuellement refusée.
- Vérifier l'annulation d'une occurrence ou de toute la série ; demander la portée
  lorsqu'elle manque.
- Concevoir le marquage d'un événement créé directement dans HA si l'utilisateur
  veut en faire un rappel Alfred. Les autres événements doivent rester silencieux.
- Tester coupure, redémarrage, indisponibilité du terminal, changement d'heure et
  prévention des doubles annonces ; afficher les rappels manqués sans lecture tardive.
- Finaliser l'isolation des rappels personnels et les permissions avant production.

Recette : rappel ponctuel, rappel familial, jeudi à 19 h récurrent, modification,
annulation, terminal absent et redémarrage pendant une échéance.

## 4. Minuteurs — F07, F09, T07

Acquis : création/consultation/annulation/Stop testés sur téléphone ; persistance
locale Alfred ; sonnerie native raccordée au pont ESP32 le 11 novembre, commandes
acceptées par la carte. Écoute humaine de cette dernière intégration à confirmer.

Travail restant :
- Confirmer à l'oreille sonnerie et arrêt sur le terminal réel.
- Tester plusieurs minuteurs, durées naturelles et arrêt des sonneries de l'étage.
- Exposer consultation et commandes dans HA sans second échéancier de référence.
- Étendre la diffusion à tous les terminaux du même étage.
- Valider les priorités avec conversation et musique, les déconnexions et la reprise.
- Confirmer qu'un minuteur dépassé pendant l'arrêt reste terminé sans sonnerie tardive.

## 5. Annonces — F08, T07

Acquis : demandes conversationnelles et interface de ciblage maison/étage/pièce.
La diffusion physique via le terminal direct reste à construire.

Travail restant :
- Réutiliser la synthèse Phonon et la lecture directe déjà employées par Alfred.
- Diffuser à toute la maison sans lieu explicite, ou à la destination demandée.
- Définir priorité, interruption ou attente lorsqu'une conversation/sonnerie est active.
- Gérer musique, plusieurs destinations et demandes simultanées.
- Signaler une destination indisponible ou un envoi partiellement réussi ; distinguer
  commande acceptée et audition humaine.

## 6. Courses — F05

Acquis : liste familiale HA, ajout/lecture, plusieurs articles, doublons actifs,
cocher/décocher, renommer, modifier quantité, suppression et purge. Plusieurs retours
humains positifs existent ; certains scénarios restent seulement testés en simulation.

Travail restant :
- Recetter toute la chaîne voix/web/HA avec plusieurs articles et relances naturelles.
- Vérifier qu'ajouter un article acheté le remet en liste sans le dupliquer.
- Traiter quantités, variantes, synonymes et ambiguïtés sans fusion abusive.
- Tester les changements simultanés depuis HA et Alfred ainsi que les échecs partiels.
- Finaliser l'écran de courses et les permissions ; garder HA comme seule référence.

## 7. Interface web — A01, A07, A08, A09, P06

Acquis : banc fonctionnel en huit vues, formulaires et dernier échange ESP32 affiché.
Ce banc reste à faire évoluer en interface quotidienne.

Écrans proposés, à valider :
- Accueil : état des services/terminaux, minuteurs actifs, rappels à venir ou manqués,
  accès aux fonctions et conversation texte/voix.
- Maison : pièces, étages, appareils autorisés, exclusions et essais ciblés.
- Musique : recherche, lecteur, morceau courant, transport et atténuation.
- Rappels et minuteurs : listes lisibles, formulaires, récurrences, destination,
  modification/annulation et Stop ; conserver leurs sources de données distinctes.
- Courses : actifs/achetés, ajout multiple, édition, remise en liste et suppression.
- Annonces : texte, destination et retour de diffusion.
- Profils : enrôlement, calibration, rôles et permissions configurables.
- Mémoires : consulter/corriger/effacer avec séparation commune/personnelle.
- Terminaux : connexion, pièce/étage, test de son et diagnostic.
- Réglages/diagnostic : quatre voix Phonon uniquement, connecteurs, erreurs,
  durées, usage et budget ; secrets jamais renvoyés par l'API.

Travaux transverses : adaptation téléphone/ordinateur, navigation lisible, états
de chargement/erreur, synchronisation avec HA, confirmations utiles et accès depuis HA.
Vérifier/renouveler le certificat de développement signalé expiré ; choisir l'accès
HTTPS durable pour la VM. Authentification via comptes HA à étudier et protection
des routes côté serveur avant production, conformément au report utilisateur.

## 8. Voix et conversation — S03, S04, S05, S06, S19, S21, S28, T03, T05

- Conserver Parakeet autonome comme seul STT et Phonon comme seul TTS, avec Dumby,
  Alfred cloné, Arnaud et Lucien. Ne pas relancer les anciens moteurs par défaut.
- Valider la diction et le timbre du profil choisi : nombres, heures, négations,
  noms propres, phrases courtes/longues ; corriger la préparation textuelle si besoin.
- Mesurer le délai complet fin de parole → premier son et identifier les étapes
  coûteuses sur l'hôte final. Le streaming natif est une piste à mesurer.
- Recetter phrases naturelles, bruit, musique et reprises ; fin de session et silence
  sans appel IA ; annulation des réponses devenues obsolètes.
- Construire/valider l'interruption vocale : arrêt du son, écho et nouvelle demande.
- Mesurer fiabilité et consommation des outils IA et comparer les modèles si utile.
- Conserver Jarvis pour avancer. Réveil « Hé Alfred » différé par l'utilisateur ;
  sa reprise éventuelle exige des essais humains, dont Fred et bruit réel.

## 9. Profils, permissions et mémoire — I02, I03, I04, I05, P01, P06

- Enrôler/calibrer avec une seconde voix réelle ; tester adultes, enfant, inconnus,
  phrases courtes et bruit ; refuser les identifications incertaines.
- Gérer le changement de personne pendant une conversation sans mélange de contexte.
- Définir puis appliquer restrictions et confirmations à chaque accès et outil.
  Respecter la règle validée : invité autorisé aux fonctions, sans mémoire personnelle
  ni accès aux souvenirs privés ; restrictions propres au profil limité reconnu.
- Construire mémoires commune et personnelles, mémorisation utile, confirmation du
  sensible, provenance, consultation, correction et effacement.
- Ajouter le diagnostic textuel borné à sept jours ET 100 Mo, purge automatique,
  sans audio brut ni secret, distinct des souvenirs persistants.
- Finaliser authentification web et protection des données avant production.

## 10. Installation durable et plusieurs pièces — P04, A02–A05, T02, T06, T07

- À réception et disponibilité de l'AuBox : mesurer les ressources réellement libres,
  créer/dimensionner la VM Debian et vérifier la compatibilité de la pile CPU.
- Installer modèles/workers/services, données persistantes, configuration privée,
  préchargement, redémarrage automatique et état de santé.
- Reconfigurer les secrets sur Debian : les fichiers DPAPI Windows ne sont pas portables.
- Prévoir puis tester sauvegarde/restauration et mise à jour/retour arrière.
- Tester reconnexion ESP32, perte Wi-Fi et redémarrage serveur sans second client audio.
- Ajouter plusieurs terminaux, éviter les réponses en double, permettre les conversations
  distinctes et valider routage par pièce/étage et priorités audio.
- Réaliser la recette bureau puis salon avant extension aux autres pièces.
- Echo Show et autres transports restent des pistes différées, pas des prérequis
  pour finir les fonctions sur l'ESP32 actuel.

## 11. Recherche web et coûts — S07, S08

- Choisir une recherche web après vérification actuelle du fournisseur, de ses tarifs,
  sources et délais. Aucun fournisseur ni abonnement supplémentaire choisi ici.
- Ajouter des réponses sourcées et traiter une page consultée comme une source,
  jamais comme une autorisation d'action domestique.
- Mesurer quotas Command Code partagés et consommation par usage ; afficher compteurs,
  alertes, limites et comportement à épuisement sans bascule payante implicite.
- Respecter l'objectif supplémentaire de 5 €/mois, à confirmer par mesures.

## Ordre de réalisation proposé

1. Achever la sortie audio : sonnerie humaine confirmée, annonces puis rappels sur ESP32,
   règles de priorité et reprise sans double diffusion (F06–F09, T07).
2. Finaliser le périmètre domotique et les commandes retenues (F01–F02).
3. Recetter musique/Qobuz, atténuation ESP32 et courses (F03–F05).
4. Faire évoluer l'interface au fil de ces modules, puis recette mobile/ordinateur (A01).
5. Profils réels, mémoires, droits et authentification avant production (I02–I05, P06).
6. Installation Debian dès que l'hôte est disponible, sauvegardes, recette bureau/salon
   puis plusieurs pièces (P04, A02–A05, T06–T07).
7. Recherche web et suivi budgétaire ; le suivi d'usage peut commencer dès les lots précédents.

La qualité vocale et les mesures de latence se vérifient dans chaque lot. Les essais
musicaux, le réveil personnalisé et les autres pistes différées restent soumis à la
reprise choisie par l'utilisateur. Aucun délai calendaire n'est engagé sans connaître
la disponibilité du matériel et des personnes nécessaires aux essais.
