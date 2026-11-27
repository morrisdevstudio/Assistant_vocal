# Alfred — cadrage du projet

## Dépôt GitHub — décision du 23 novembre 2026

La création du dépôt privé et vide [morrisdevstudio/Assistant_vocal](https://github.com/morrisdevstudio/Assistant_vocal) est validée.
Les issues sont activées et accessibles. La conservation par défaut des données
GitHub Actions est fixée à sept jours. Le code sélectionné est publié sur main
depuis le 23 novembre. Le dépôt doit rester privé pour le moment.

22 novembre — l’anneau du satellite ESP32 est éteint par défaut au repos,
y compris lorsque le détecteur du mot d’appel tourne en arrière-plan. Le
satellite signalait encore l’effet « Wipe » de réponse alors qu’Alfred le
signalait en veille. Alfred resynchronise l’anneau via l’API native existante.
Dans les paramètres de la PWA, les états Veille, Écoute, Traitement, Réponse
parlée et Erreur ont chacun une couleur ou une extinction et un effet enregistré
sur le serveur. Les options prises en charge sont Fixe, Rotation, Comète,
Respiration et Balayage. Les palettes existantes reprennent avec l’effet Fixe.
Les indicateurs natifs de micro coupé, de volume et de minuteur gardent
la priorité. En cas de déconnexion, le firmware reprend la signalisation locale.

22 novembre — le mode dialogue est actif par défaut pour un échange vocal.
Alfred rouvre le micro pendant huit secondes à la fin de la lecture uniquement
si la réponse demande une confirmation ou une précision. Une réponse complète
termine l’échange. Le satellite revient alors à la veille du mot d’appel si
elle est armée. Un silence pendant la reprise ferme la prise sans appel IA.
La PWA et le laboratoire permettent de désactiver la reprise localement.

21 novembre — les lumières et groupes ont un type partagé dans Alfred :
Principal ou Secondaire, avec Principal par défaut. Un groupe classé peut
donner son type à ses membres sans réglage individuel. Secondaire départage
les groupes à distance égale. Les anciens réglages Ambiance deviennent
Secondaire. L’allumage générique vise les
principales ; l’extinction et la lecture génériques couvrent les deux types.
Un type ou un nom prononcé cible les lumières correspondantes. La mention
« y compris l’ambiance » inclut les deux types à l’allumage.

21 novembre — le bloc Pièces affiche toutes les pièces du registre Home
Assistant, y compris celles sans entité exposée à Assist, et les pièces locales
d’Alfred. Un nom commun à une seule pièce locale apparaît sur une ligne avec
son étage local et la mention Home Assistant. Le crayon personnalise le nom
et l’étage d’une pièce Home Assistant pour ce navigateur. L’étage du registre
est affiché et prérempli au premier réglage s’il correspond à un étage géré
par Alfred. Sinon, l’étage local est à choisir. Alfred conserve la référence au nom
d’origine et la pièce personnalisée devient affectable au navigateur et aux
satellites locaux. Retirer la personnalisation rétablit l’entrée du registre.
Le sélecteur « Pièce pour Alfred » affiche le nom personnalisé des pièces
Home Assistant dans ce navigateur. Il relit le registre à l’ouverture de la
fiche et propose aussi les pièces créées dans Alfred dans ce navigateur.
Une affectation transmet au serveur la référence Home Assistant ou le nom
de la pièce locale sélectionnée.

21 novembre — dans Maison et appareils, le catalogue regroupe les entités
par pièce effective pour Alfred, avec « Sans pièce » à la fin. Les groupes
sont repliés à l’ouverture sur ordinateur et mobile. Une recherche ou un
filtre déplie les groupes correspondants. L’édition d’une affectation déplace
l’entité dans son nouveau groupe. Chaque groupe a sa propre carte avec icône,
compteur et état déplié visible. La recherche et les filtres sont réunis dans
un panneau au-dessus du catalogue. Toutes les cartes de Maison et appareils
s’alignent sur la largeur du catalogue.

21 novembre — Alfred conserve une PWA commune. À partir de 1 024 px, un volet
permanent de 240 px à gauche reprend la navigation, avec Paramètres en bas.
Nouvelle conversation reste dans l’en-tête. Sur un écran 16:9, le chat reste
centré et le tableau des appareils s’élargit. Sur ordinateur, Paramètres
remplace les entrées du volet par les huit rubriques de réglages. Apparence
s’ouvre à droite à l’entrée et la rubrique active est indiquée à gauche.
Retour au menu principal retrouve la page d’origine. L’accueil des réglages
reste disponible sur mobile. Musique passe à deux colonnes quand sa zone dispose d’au moins
1 000 px. En dessous de 1 024 px, le menu et la présentation mobiles s’appliquent.

20 novembre — le tableau Domotique et les lignes mobiles affichent le
récapitulatif. Le crayon ouvre une fiche d’édition. Valider enregistre ensemble
les champs modifiés ; Annuler et Échap abandonnent la saisie.
« Pièce pour Alfred » propose les pièces du registre Home Assistant pour déplacer
un appareil ou en affecter un sans pièce. Une ancienne pièce personnalisée peut
être conservée. Le sélecteur affiche directement le nom de la pièce d’origine
et la présélectionne par défaut. Une petite maison identifie cette sélection.
Choisir la pièce d’origine rétablit l’affectation Home Assistant.
Alfred utilise la pièce personnalisée dans son catalogue et dans les demandes
par pièce. L’affectation est enregistrée sur le serveur Alfred et Home Assistant
conserve la sienne.

20 novembre — les réglages Domotique proposent un « Nom pour Alfred » par
entité dans le laboratoire et la PWA. Alfred emploie ce nom dans ses réponses
et ses confirmations. La reconnaissance conserve aussi le nom Home Assistant
et les alias existants. Le nom est enregistré sur le serveur Alfred par
identifiant d’entité. Effacer le champ et enregistrer rétablit le nom d’origine.

19 novembre — retour Android sur la lecture des réponses. Remplacer le
lecteur audio au-dessus de la saisie par une icône de haut-parleur sous
chaque réponse disposant d’un audio. L’icône commande la lecture et la pause.
Chaque audio reste réécoutable pendant la conversation, et la lecture
automatique suit le réglage existant.

19 novembre — correction de la consultation des lumières après le retour Android.
La question de la capture vise toute la maison dès le premier échange. L’outil
de lecture résume les lumières encore allumées par leur nom, y compris les
membres autorisés de groupes exposés, et signale les états indisponibles. La
formulation est produite par le serveur à partir des états relevés. Vérification
sur le LAN par l’API de la PWA avec Home Assistant réel : la phrase de la
capture renvoie « Toutes les lumières sont éteintes. » sans question
intermédiaire. Le comptage global et le ciblage du bureau passent également
en lecture seule.

19 novembre — validation des cinq améliorations de la PWA proposées après
la revue ergonomique. Sur l’écran d’accueil Conversation, un grand bouton
rond avec une icône de micro se place au-dessus du logo existant. Pendant la prise, la forme d’onde
suit le signal du micro dans le navigateur. Les actions d’envoi et d’annulation
sont libellées et le refus de permission propose la saisie. Deux exemples
préremplissent le champ avant le premier échange. Focus visible et commandes
principales de 44 px minimum. Les modes partagé et local des rappels et
minuteries s’affichent comme dans la liste de courses. Les minuteries actives
précèdent le formulaire et la destination de la sonnerie est visible au
lancement. Sur téléphone, une fiche regroupe l’accès, la confirmation et les
alias d’un appareil ; sur ordinateur, l’édition reste disponible en tableau.

19 novembre — précision sur le bouton Parler : forme ronde et icône de
micro seule, avec le nom accessible « Parler ».

19 novembre — l’utilisateur demande de reprendre dans Maison et appareils le
tableau domotique du laboratoire. Colonnes : Nom, Pièce, Type, Mode
confirmation, Activer / désactiver et Alias. Tri et filtres repris. L’accès
règle l’autorisation d’Alfred, et le mode confirmation s’applique aux commandes
qui modifient l’entité. Le 20 novembre, la fiche ouverte par le crayon remplace
les champs et l’enregistrement dans la ligne.

19 novembre — les optimisations proposées pour la PWA et Musique sont
autorisées et livrées sur le LAN. La liste des lecteurs se rafraîchit toutes
les 60 secondes tant que Musique est visible, au lieu de 15. L’état du lecteur
actif reste actualisé toutes les 5 secondes. Alfred garde l’identifiant
d’intégration Music Assistant en mémoire pendant une minute, pour la même
configuration Home Assistant, et l’invalide en cas d’erreur de lecture de
l’intégration. La validation du lecteur avant une commande reste en place.

Musique et Paramètres sont importés à leur première ouverture. Le service
worker précache leurs fichiers compilés pour qu’ils restent disponibles hors
ligne. Le JavaScript principal passe de 333 à 294 Ko avant compression ; le
transfert observé sur le LAN est de 91 Ko en gzip. Les bulles de conversation
inchangées réutilisent leur rendu et le défilement est planifié à la prochaine
image. Les gains perçus sur le téléphone et via VPN restent à mesurer.

18 novembre — optimisation de la PWA et du serveur demandée après un délai
ressenti d’environ une seconde et la fermeture de l’app par le bouton Retour.
Le menu, les pages, les rubriques des paramètres et les vues locales sont
inscrits dans l’historique. Le Retour ferme le menu ou remonte d’un écran.
Le menu se ferme en 140 ms au lieu de 320 ms. Les lectures périodiques se
limitent aux vues visibles et reprennent au retour au premier plan.

Le serveur réutilise les connexions HTTP vers Home Assistant. Sur le LAN via
HTTPS 5173, temps médian jusqu’au premier octet avant/après en millisecondes
(4 relevés avant, 10 après) : courses 259/36, rappels 265/38, état musical
255/34, favoris musicaux 305/59. Le build compilé est servi sur la même origine.
Le passage depuis l’ancien service worker Vite a été vérifié avec conservation
du stockage local. Retour vérifié sur la PWA ouverte depuis l’accueil d’un
émulateur Android. Le délai perçu et le comportement restent à confirmer sur
le téléphone de l’utilisateur. Planificateur, Home Assistant et Music Assistant
répondent. Le nom réseau local de l’ESP32 ne se résout pas lors de ce contrôle.

18 novembre — les appareils Home Assistant sont ajoutés aux paramètres de la
PWA. La première version en lecture seule est remplacée le 19 novembre par le
tableau éditable. Les pièces et les satellites enregistrés dans le navigateur
restent des réglages locaux.

18 novembre — réponses et minuteurs nommés. L’utilisateur demande de retirer
les numéros des réponses sur les minuteurs et d’enregistrer des modèles nommés
dans l’interface. Il valide le titre et l’artiste pour le morceau en cours et
une phrase directe pour la température. Les modèles de minuterie enregistrent
le nom et la durée dans le navigateur. Le lancement reste partagé sur l’étage
choisi. Courses, rappels et annonces restent au stade des exemples.

18 novembre — format des réponses d’Alfred. L’utilisateur confirme sur Android
la correction du dessous du champ de saisie et ouvre la discussion sur les
réponses domotiques. Le prompt contient déjà des consignes de ton et d’oralité.
Avant la correction du 19 novembre, le code transmettait l’inventaire
et appliquait aussi en lecture la demande de précision
« cette pièce ou toute la maison » issue de la règle serveur.
Périmètre validé pour les consultations : sans lieu, Alfred regarde toute la
maison. « Ici » désigne la pièce du terminal et un lieu explicite fixe le
périmètre. Cette règle s’applique aux demandes de lecture. Format validé :
Alfred nomme directement toutes les lumières allumées dans le périmètre,
y compris lorsque la question porte sur leur nombre. Si elles sont toutes
éteintes, il le dit explicitement. Le modèle choisit l’outil et le périmètre
et le serveur compose ce résumé.

18 novembre — retour sur la conversation PWA. Le dessous du champ de saisie
reste libre. La transcription et la réponse figurent dans le fil. Les états du
micro et les erreurs utiles s’affichent au-dessus du champ. Si la synthèse
échoue après l’affichage de la réponse, l’avertissement ne la répète plus.
Le format des réponses sur les lumières est à traiter dans un second temps.

18 novembre — correction de la page Musique après retour utilisateur. Le
sélecteur propose les lecteurs Music Assistant détectés dans Home Assistant.
La PWA mémorise le choix dans les préférences du navigateur et transmet la
cible pour la lecture, les commandes et le déplacement. Le lecteur configuré
sur le serveur sert de valeur par défaut et reste la cible des commandes vocales
existantes. La pochette du morceau vient du proxy d’images Home Assistant via
Alfred. Le disque générique s’affiche lorsque l’image manque ou échoue.
Trois lecteurs ont été détectés sur le LAN. À 360 px, le navigateur a affiché
les pochettes de l’ampli et du PC, puis le disque générique pour le téléviseur.
La sélection a persisté après rechargement. Le ciblage a été vérifié avec
une commande simulée. La diffusion physique sur un autre lecteur reste à essayer.

18 novembre — raccordement de l’interface au backend sur le LAN de développement.
La PWA conserve son origine HTTPS sur 5173 et relaie ses routes vers Alfred
sur 8765 avec validation du certificat. Conversation texte et micro manuel par
le flux NDJSON. Autorisation de recherche par échange, lecture facultative
pour le texte et débit appliqué dans le navigateur. L’étage du navigateur suit
sa pièce enregistrée, lorsque renseignée.

Les vues par défaut utilisent les courses familiales HA, les rappels Alfred
du calendrier familial, les minuteries serveur par étage et le lecteur Music
Assistant sélectionné dans la PWA ou, par défaut, configuré sur le serveur.
Les anciennes données restent accessibles
via « Sur cet appareil », sans migration automatique. Les réglages affichent
les états du serveur et des services ; les secrets restent sur Alfred.
Choix d’étape : création et consultation des rappels familiaux, démarrage et
annulation des minuteries partagées. Les rappels personnels, les actions
avancées des échéances, les notifications du navigateur, le changement de
personnage et la veille vocale restent ouverts. Le login par comptes HA et les
permissions par profil restent à traiter avant la production.

18 novembre — réalisation des cinq pages restantes des paramètres de la PWA.
Les huit rubriques sont accessibles. Choix d’implémentation pour cette étape :
préférence locale de recherche Internet à appliquer au raccordement, catégorie
de favoris par défaut utilisée dans Musique, deux sonneries de minuterie avec
écoute et application dans les minuteries locales. L’activation du son reste
manuelle pour chaque session et dépend de la visibilité de la PWA.
Données et confidentialité indique la durée de conservation des échanges et
permet l’export JSON des préférences, de la maison, des courses, des rappels et
des minuteries de la PWA. À propos et diagnostic affiche la version et contrôle
le stockage, le contexte sécurisé, le réseau selon le navigateur et le service
worker local. Le raccordement de l’IA, de la recherche, de Music Assistant, des
notifications de rappel et du diagnostic serveur reste ouvert.

18 novembre — première étape UI Musique réalisée dans le menu. Page dans les
thèmes existants : lecteur, pochette neutre, métadonnées, progression, commandes
précédent/lecture/suivant puis volume moins/arrêt/plus. Commandes désactivées et
mention « Music Assistant non raccordé ». Recherche saisissable/effaçable,
catégories Artistes/Albums/Titres/Playlists ; zone résultats à la place des favoris
pendant la recherche. Aucun contenu musical fictif, appel HA/MA ou login ajouté.
Recherche et catégorie conservées en mémoire lors de la navigation. Compilation
TypeScript/build PWA et quinze tests existants réussis, composant diffusé en HTTPS
200 avec l'autorité locale. Contrôle visuel automatique indisponible (aucun navigateur
exposé) ; recette téléphone, clavier et thèmes à confirmer par l'utilisateur.

18 novembre — chantier UI Musique demandé. Référence fournie par l'utilisateur :
sélecteur de lecteur, pochette, titre/album/artiste, progression, précédent/lecture/
suivant, volume moins/arrêt/plus, recherche et zone affichant les favoris
(artistes, albums, titres, playlists) ou les résultats. Reprendre le style actuel
d'Alfred. L'utilisateur demande aussi d'évaluer l'intégration de Music Assistant.
Solution 2 validée par l'utilisateur : page React propre à Alfred raccordée à
l'installation Music Assistant existante. Première étape choisie : interface seule,
avant raccordement réel. Les favoris proviendront de Music Assistant. Réutiliser
le pont HA pour les fonctions disponibles et évaluer l'API MA pour les données
manquantes reste une proposition technique. Recherche, favoris, pochettes et déplacement dans le morceau à vérifier
avec la version réellement installée ; raccordement réel toujours à réaliser.
Documentation officielle consultée :
https://www.music-assistant.io/api/ (API pour interfaces personnalisées).

18 novembre — page Maison et appareils demandée et réalisée dans les paramètres.
Étape UI locale : adresse Home Assistant (sans identifiant ni jeton), pièces au
rez-de-chaussée/premier étage, affectation de ce navigateur et répertoire de
satellites affectés aux pièces. Ajout/modification/suppression annulable ; suppression
d’une pièce affectée refusée. Liste vide au départ, aucun appareil réel déclaré
connecté à partir de faits historiques. Configuration persistée sur cet appareil ;
connexion HA, synchronisation serveur, détection et association matérielle à
raccorder ultérieurement, limite explicitement affichée. Aucun secret enregistré.

Retour UI du 18 novembre : dans tous les paramètres, le retour est une flèche
seule placée à gauche du titre, sur la même ligne. La ligne de retour séparée
avec le texte « Paramètres »/« Retour » est supprimée ; destination inchangée.

Instruction UI complémentaire du 17 novembre : supprimer tous les sous-titres
des rubriques/pages des paramètres. L’accueil affiche uniquement les icônes,
titres et indications « À venir » ; les libellés et aides utiles des réglages restent.
Instruction suivante : dans Voix et conversation, sélectionner un personnage,
défini comme un preset de voix et de mot de réveil. Le choix applique les deux
préférences ensemble ; le couple est affiché. Plus de rubrique « Avancé » : durée
d’écoute et lecture des réponses sont directement visibles. Anciens réglages
personnalisés conservés tant qu’aucun preset n’est choisi. Raccordement serveur/
ESP32 toujours distinct de cette étape UI locale.

## Interface — décision du 17 novembre 2026

L’utilisateur rejette la refonte proposée et demande de revenir à l’interface précédente. Les choix de la proposition rejetée ne sont pas considérés comme validés.

Nouvelle instruction du 17 novembre : développer progressivement la véritable
interface sur un port distinct, avec pour cible une web app PWA installable.
La première étape autorisée se limite à une page de chat dans le style d’une
conversation ChatGPT, avec les icônes **Lucide React**. Socle choisi pour cette
page : React, TypeScript et Vite, sous `ui/`, port 5173. L’utilisateur demande
ensuite l’accès réseau sur **https://192.168.1.23:5173** ; écoute LAN en HTTPS
avec un certificat de développement sous `.local/https/`.
Le raccordement
aux services et les autres pages sont des étapes ultérieures,
pas des fonctionnalités livrées par ce premier écran.
Ajout demandé ensuite : bouton micro avec l’icône Lucide `Mic`, immédiatement
à gauche du bouton d’envoi. À ce stade de construction de l’UI, le clic indique
que le raccordement vocal reste à réaliser ; aucune capture audio n’est lancée.
Navigation (instruction actualisée) : remplacer l’engrenage par un menu burger
Lucide ouvrant un volet **plein écran**, animé depuis la gauche vers la droite.
Entrées Conversation, Musique, Listes, Rappels et Minuteries ; Paramètres tout en
bas. Conversation, Listes, Rappels, Minuteries et Paramètres sont maintenant développés ;
Musique est accessible depuis le 18 novembre (interface seule). Fermeture par croix, Échap ou retour à la
conversation ; contenu du chat conservé. Cette instruction remplace la précédente
suppression du volet et l’engrenage sans action.
Instruction suivante : rendre l’application installable sur Android dès maintenant.
Manifeste français, icônes PNG 192/512 et maskable, affichage autonome, service
worker et bouton Installer. Cache limité au shell compilé ; aucun audio ni
message/API mis en cache. En développement, installation activée, sans promesse
de fonctionnement hors réseau. Aucun rechargement forcé des conversations pour
les mises à jour. L’UI utilise désormais un certificat dédié signé par une autorité
locale sous `.local/https/`, sans modifier celui du backend ni installer de confiance
système. L’autorité publique est téléchargeable pour installation manuelle sur
Android ; cette confiance est nécessaire si Chrome refuse le certificat privé.
L’installation et le lancement sans barre navigateur sont confirmés par
l’utilisateur le 17 novembre après les indications de confiance du certificat.
Retour Android : l’utilisateur exige un lancement sans barre d’adresse ni menu
navigateur. Capture reçue : barre navigateur visible et indicateur rouge de
certificat. Le manifeste utilise déjà `display: standalone`, avec portée `/`.
Ce problème est ensuite déclaré résolu par l’utilisateur (« c’est bon ça fonctionne »).
Nouvelle exigence : conserver le bandeau Alfred, paramètres et nouvelle conversation
visible à l’ouverture du clavier Android. Conteneur sans défilement de document,
bandeau maintenu en haut et redimensionnement du contenu avec le clavier ; seule
la conversation défile. Premier essai CSS/viewport rejeté par l’utilisateur :
capture Android avec clavier ouvert et bandeau absent. Correction suivante :
cadre fixé au viewport visuel via `visualViewport.height` et `offsetTop`, suivi
des événements de déplacement/redimensionnement ; suppression du défilement
des ancêtres par `scrollIntoView`, focus sans défilement. Zoom conservé.
Recette du clavier sur téléphone toujours ouverte, aucun succès humain revendiqué.
Retour suivant : menu validé avec enthousiasme par l’utilisateur. Nouvelle demande :
page Listes sobre, pratique pour les courses. Réalisation UI : ajout rapide,
cochage/décochage par grande cible, compteur des articles à acheter, regroupement
des articles cochés repliable, modification du libellé/quantité dans le texte,
suppression individuelle ou des cochés avec annulation. Aucun article fictif.
Choix d’implémentation pour cette étape UI : stockage persistant dans le navigateur
sur cet appareil, explicitement indiqué ; aucune synchronisation Home Assistant,
aucune modification de sa liste existante. Ce choix ne remplace pas l’architecture
des courses HA ; raccordement et éventuel partage entre appareils restent à décider.
Le chat et sa saisie sont conservés pendant la navigation. Recette humaine ouverte.
Demande suivante : réaliser les pages Rappels et Minuteries dans le même style.
Étape UI locale : rappels datés/horodatés, création/modification, état fait,
suppression annulable ; aucune notification ni annonce vocale raccordée.
Minuteries avec heures/minutes/secondes, présélections, nom facultatif, compte
à rebours, pause/reprise, réinitialisation, relance et suppression annulable.
Durées calculées à partir d’une date de fin persistée, recalculées au retour dans
l’application ; son bref activable pour la session quand l’app est visible.
Stockage navigateur sur cet appareil, distinct des calendriers HA et minuteurs
serveur existants, sans modification de ceux-ci. Aucune garantie d’alerte lorsque
la PWA est fermée ou en arrière-plan ; rappel explicite dans les écrans.
Le raccordement aux calendriers, aux sonneries serveur et le partage restent à
réaliser séparément. Recette humaine des deux nouvelles pages ouverte.
Paramètres : proposition de rubriques acceptée, réalisation progressive en
commençant par Apparence et Voix/conversation. Accueil sobre avec icônes et accès
aux huit rubriques depuis le 18 novembre.
Apparence : thème sombre/clair/système appliqué à toute l’interface, choix
persistant sur l’appareil. Retour annoté suivant : le bandeau principal est masqué
dans tous les paramètres ; retour interne conservé et bouton de sortie sur
l’accueil vers la page précédente. Surtitre et phrases décoratives sous le titre
supprimés. Taille du texte, réduction des animations et note d’accessibilité retirées
selon les éléments barrés ; les anciennes préférences associées sont ignorées.
L’accessibilité du système reste respectée. Réglages de voix
préférée Phonon, débit souhaité, lecture des réponses et options avancées de réveil/
écoute enregistrés localement comme préférences futures ; aucune modification
du serveur, des moteurs ou de l’ESP32. Cette limite est affichée sur la page.
Recette visuelle et raccordement des réglages vocaux restent ouverts.

Dernière mise à jour : 17 novembre 2026 (Europe/Paris).

Ce document est la mémoire du cadrage. Il est complété à chaque décision validée.
Les propositions et questions ouvertes ne constituent pas des décisions.
`CHECKLIST.md` suit la mise en place, les contraintes, dépendances et états ; il
est complété au fil de la discussion dès qu'un nouveau travail est identifié.

## Objectif et priorités validés

Construire un assistant vocal domestique appelé **Alfred**, parlant toujours en
français, relié à Home Assistant. La domotique est prioritaire, avec dès la première
version l'ambition de couvrir aussi musique, minuteurs, conversation, questions
générales, recherche sur Internet et fonctions d'assistant personnel : **rappels,
listes de courses et annonces dans la maison**. Notes et agenda général ne sont pas
retenus pour la première version ; les rappels restent liés aux dates du calendrier.

- Priorité à la fluidité, à la rapidité et à l'efficacité, en minimisant les coûts.
- Pas d'exigence de fonctionnement hors Internet : le mode manuel de la maison
  convient à l'utilisateur en cas de panne.
- Budget supplémentaire maximal visé : **5 € par mois**, en plus de l'abonnement
  Command Code GOAT existant, annoncé par l'utilisateur à environ 10 € par mois.
- Décision du 11 novembre : **synthèse exclusivement Phonon local sur CPU**.
  Les seuls profils proposés sont **Dumby** (actif et par défaut), **Alfred cloné**,
  **Arnaud** et **Lucien**. Les autres voix sont retirées du sélecteur, de l’API
  et du service de synthèse ; aucun repli vers un ancien moteur. Les archives
  de recherche et références conservées sous .local ne sont pas des voix actives.
  Le choix du moteur est validé par cette instruction ; le jugement détaillé du
  profil Dumby et la recette sur l’hôte final restent à poursuivre.
- Base de prototype acceptée : faster-whisper pour la transcription, SpeechBrain
  ECAPA pour les profils et service Python avec interface web. Piper avait été
  retenu pour la synthèse ; après écoute le 30 octobre, l'utilisateur le rejette
  (mauvaise prononciation d'« Alfred » et de « majordome »). Supertonic 3 a assuré
  le relais ; Pocket TTS a ensuite été essayé pour le clonage sur CPU. Après
  dérive du timbre à l'écoute, l'utilisateur retient le 2 novembre une voix
  synthétique Supertonic à profil fixe, débit 1,242, sans effet. Cette référence
  a été archivée puis utilisée pour les samples et la conversation. Pocket
  et M1–M5 ont ensuite été retirés des voix disponibles le 11 novembre. L'âge vocal autour de 70 ans n'est pas
  validé séparément ; les essais nobles et la patine sont abandonnés. Conversation,
  rendu ESP32 et scénario de fond chanté validés pour le prototype. Recettes
  acoustiques plus larges, comparaison des modèles de dialogue, réveil et
  hébergement définitifs restent ouverts. Le 8 novembre, comparaison de diction :
  l’utilisateur juge Chatterbox français (C) nettement meilleur que Supertonic
  au débit 1,242 (A) comme à 1,0 (B), jugés équivalents pour le français.
  Chatterbox est préféré pour la diction de cet extrait, mais son essai CPU en
  conversation est ensuite **rejeté par l’utilisateur car trop lent**. Le 8 novembre,
  **Henri via Home Assistant Cloud** est raccordé et activé comme nouvel essai.
  L’utilisateur confirme que son abonnement Cloud est déjà payé ; aucun nouvel
  abonnement ni nouvelle clé. Les réponses à lire passent par le TTS Cloud existant,
  sans déplacer la conversation IA, le réveil ou le transport ESP32 dans Assist.
  Référence Supertonic conservée et sélectionnable pour retour manuel. Retour
  utilisateur après comparaison : **Henri reste nettement meilleur en diction et
  en rapidité de génération**, y compris face à Sopro et Melo/OpenVoice. Henri
  reste une référence comparative de ces essais ; son timbre s’éloigne encore
  de la voix Alfred initialement souhaitée. Identité vocale définitive et recette
  VM Debian restent ouvertes.
  Ne pas relancer Chatterbox CPU comme solution courante.
  Le 11 novembre, profil de voix créé et exporté par l’utilisateur reçu puis
  activé pour essai sous **Alfred · Phonon · voix clonée**, entièrement sur CPU.
  Henri a ensuite été retiré du service avec les autres voix non Phonon ;
  ressemblance, diction et choix définitif du profil restent à valider à l’écoute.
  Après un nouveau retour, la version 2 convient moins ; un autre export fourni
  par l’utilisateur est nommé **Dumby** et activé comme nouveau profil d’essai
  Phonon local. Les anciens profils sont conservés.

- Décision STT du 9 novembre : après préférence humaine pour Murmure sur
  téléphone et ESP32, l'utilisateur autorise son intégration avec la même stack.
  Reprendre Parakeet TDT 0.6B v3 INT8, ONNX Runtime CPU, décodage/dictionnaire,
  nettoyage et formatage de Murmure 1.11.3 dans un worker autonome d'Alfred.
  Import local des modèles et réglages de dictée ; aucune dépendance à Murmure
  ouvert ni appel LLM de réécriture. **Livré et actif après recette** : Parakeet
  sélectionné dans le service réel, préchargé, Henri conservé, ESP32 Bureau
  connecté au repos. Parité de texte 28/28 sur corpus synthétique étendu, silence
  compris ; 96 tests Rust, 473 Python (4 ignorés) et 19 JS ciblés réussis.
  Worker persistant, PCM par pipes et aucun WAV temporaire, erreurs bornées.
  Depuis le nettoyage autorisé du 11 novembre, **seul Parakeet est conservé** :
  anciens moteurs, bascules et comparatifs retirés, paquets inutiles désinstallés,
  modèles/bancs obsolètes mis à la Corbeille. Silero VAD v6 est autonome avec le
  même modèle et les mêmes paramètres. Acoustique approfondie et recette Debian
  restent à vérifier ; retour humain courant positif reçu après intégration.

## Recherche Internet — décision du 16 novembre 2026

- Trois modules validés : actualités à la demande, météo courante/prévisions et
  culture générale. Les connaissances stables restent traitées directement ;
  recherche pour faits récents, incertitudes et vérifications explicites.
- Fournisseurs retenus : Open-Meteo sans clé pour l'usage personnel non commercial,
  Tavily pour actualités et recherche générale, offre gratuite d'abord. Clé saisie
  uniquement dans l'interface locale protégée, jamais dans le chat.
- Commune météo enregistrée dans Alfred, pas reprise automatiquement de HA.
  Une ville explicitement demandée prime ; lieu absent ou ambigu à clarifier.
  Aujourd'hui et les six jours suivants, dates selon le fuseau du lieu.
- Format météo validé le 20 novembre. Pour une journée, donner le temps attendu
  en langage courant, les températures minimale et maximale et le risque de pluie.
  Pour la météo actuelle, donner la température et la pluie prévue dans l’heure.
  Si les données de l’heure sont complètes et sèches, dire « Il fait beau ».
  Les codes numériques, le vent et la mention finale de la provenance sont retirés
  de la réponse. La source reste accessible séparément à l’écran.
- Actualités : par défaut trois informations France/monde sur vingt-quatre heures.
  Réponses brèves à l'oral, médias nommés pour l'actualité et liens à l'écran.
  Bulletins programmés, personnalisation durable et vigilances hors première version.
- Recherche Tavily simple, cinq résultats maximum, un appel documentaire par tour.
  Plafond local persistant de mille crédits par mois UTC, abaissable ; tentatives
  comptées même en cas de réponse perdue. Quota partagé avec les autres usages du
  compte ; arrêt sur refus/quota fournisseur, aucune bascule payante. Synthèse
  supplémentaire décomptée de Command Code. Ne pas activer la facturation Tavily.
- Implémentation : outils typés, réponse météo formatée localement et synthèse
  des autres résultats documentaires sans outils d'action,
  sources transmises dans le dernier échange texte/voix/ESP32 ; réglages locaux.
  Accès réel Tavily vérifié après configuration locale ; qualité de synthèse avec
  le modèle réel, latence et écoute humaine restent à valider.
- Vérification du 16 novembre : 867 tests Python réussis/deux ignorés et 46 tests
  JavaScript réussis. Open-Meteo vérifié en réel sur Paris (lieu de test public) ;
  service relancé, santé et configuration HTTP 200, ESP32 reconnecté en veille.
  Commune personnelle et clé Tavily non configurées au contrôle ; aucun appel
  Tavily réel ni validation du modèle réel ou de l'écoute revendiqués.
- Contrôle suivant après retour utilisateur « C'est bon » : clé Tavily configurée,
  accès vérifié par le service, commune enregistrée et quota non bloqué. Aucun
  secret ni lieu personnel recopié. Cela valide la configuration et l'accès,
  pas encore la qualité conversationnelle ou acoustique des trois modules.
- Retour humain du 17 novembre : premiers essais fonctionnels, puis erreur de
  synthèse sur une question d'appel à la grève. Défaut reproduit : DeepSeek
  consomme parfois les sept cents jetons disponibles en réflexion, termine avec
  `finish_reason=length` et réponse vide ou coupée. Correction : réflexion coupée
  uniquement pour la synthèse documentaire DeepSeek V4 via
  `reasoning_effort=off` sur Command Code (son API refuse `none`). Limites et
  refus des réponses tronquées conservés ; aucune relance automatique.
  Trois synthèses réelles consécutives réussies après correction, sans jetons
  de réflexion, environ deux secondes chacune ; ce n'est pas une mesure de
  latence vocale complète ni une validation factuelle de toutes les réponses.
  Après relance, même question vérifiée via l'API texte avec TTS réel : réponse
  complète et cinq sources, 8,7 s de bout en bout jusqu'à l'audio généré, sans
  lecture physique. Santé HTTP 200, ESP32 connecté au repos. Suite complète :
  875 tests Python réussis/deux ignorés ; 82 tests ciblés revérifiés.
- Références officielles vérifiées : <https://www.tavily.com/pricing>,
  <https://docs.tavily.com/documentation/api-reference/endpoint/search>,
  <https://open-meteo.com/en/pricing>, <https://open-meteo.com/en/docs>.

## Matériel et infrastructure connus

### Terminal vocal

- Le 25 novembre, l'utilisateur précise la cible : un point d'écoute principal
  dans le salon, parfois bruyant, avec une qualité proche d'un Amazon Echo ou
  d'un Google Home. Il demande conseil sur un remplacement éventuel de l'ESP.
  Aucun achat ni remplacement validé. Recommandation à évaluer : ReSpeaker
  XVF3800 quatre micros avec traitement XMOS dédié, en USB sur un hôte local
  ou via un satellite ESP32-S3 compatible. Alternative intégrée : Home Assistant
  Voice Preview Edition (deux micros et XMOS XU316). L'intégration directe à
  Alfred reste à vérifier pour les deux pistes. Une portée constructeur ne
  prouve pas les performances dans ce salon ; comparer réveil, transcription,
  faux réveils et écoute pendant la réponse. Le son de l'ampli/TV externe sans
  référence audio reste un bruit concurrent, même avec AEC. Sources consultées :
  https://wiki.seeedstudio.com/respeaker_xvf3800_introduction/
  https://www.home-assistant.io/voice-pe/

- Le 25 novembre, l'utilisateur indique qu'il ne dispose pas d'un micro de
  studio pour le test Salon. Il demande un parcours avec les phrases à
  prononcer et le nommage automatique des prises. Le parcours principal
  utilise donc uniquement le téléphone et la Waveshare.

- Le 25 novembre, premier balayage du salon capté par la Waveshare : signal
  retrouvé vers 8,17 s, rapport précoce/tardif indicatif de +9,34 dB
  (50 ms / reste de la première seconde), aucune saturation. Cette mesure
  concerne le trajet téléphone–ESP32 et son traitement embarqué, à un point.
  Sur deux prises vocales, le passe-haut 120 Hz et les gains numériques de
  +6 et +12 dB n'améliorent pas de façon fiable les transcriptions.
  Aucun réglage actif modifié. Restent le témoin micro côte à côte et les
  balayages répétés pour comparer les positions ou le bureau.

- Le 24 novembre, l'utilisateur précise que le bureau est un studio traité
  acoustiquement et que le satellite a été déplacé au salon. Il rapporte une
  acoustique dégradée au salon et soupçonne de la réverbération ou un écho
  flottant, à mesurer. L'usage cible est la parole à distance depuis les
  emplacements habituels, y compris de côté et dos au satellite, sans devoir
  s'en approcher. Les essais proches servent de référence.

- Le 24 novembre, test guidé après déplacement : 20/25 (5/5 à 0,5 m, 8/10 à
  1 m, 4/5 à 2 m, 3/5 à 3 m), zéro réveil pendant les deux périodes de
  silence et aucune saturation relevée. Les cinq appels ratés ont été
  transcrits. « Al Fred » récupère l'essai 23 à 3 m sur les transcriptions
  enregistrées. Veille STT réarmée et flux reçu après réglage. Second passage
  à 3 m : 4/5 contre 3/5, les quatre réussites transcrites « Alfred ».
  Le raté a été transcrit « I'm flying ». Aucun faux réveil pendant les
  silences. Le gain propre à la variante et les faux réveils en conversation
  restent à évaluer.

- Le 16 novembre, première séance humaine au calme dans le bureau : réveil STT
  « Alfred » avec quatre variantes enregistrées, 22 appels détectés sur 25 :
  5/5 à 0,5 m, 9/10 à 1 m, 4/5 à 2 m et 4/5 à 3 m. Zéro déclenchement sur
  30 secondes de silence initial et final, aucune coupure ni saturation numérique
  relevée. Échantillon limité, faux réveils en conversation non évalués. Le STT
  a effectué des analyses pendant les essais manqués sans conserver les textes ;
  cause des ratés non établie. Le diagnostic des prochaines séances STT conserve
  jusqu'à cinq transcriptions courtes par essai, leur correspondance et leur durée,
  dans le journal existant, jamais l'audio. Aucun changement de gain ou variantes.
  Service relancé et ESP32 connecté ; veille au repos. Suivi T13.

- Le 16 novembre, pour la première séance au calme sur l'ESP32, l'utilisateur
  choisit le réveil **STT avec « Alfred »**. Il rapporte 100 % de réussite sur
  son téléphone, sans protocole chiffré fourni ; la méthode exacte et les
  conditions du téléphone ne sont pas établies comme identiques à l'ESP32.
  Ce choix pour l'essai ne constitue pas encore une validation acoustique ni
  l'abandon définitif d'openWakeWord. Suivi T13.

- Le 16 novembre après rebranchement signalé : identité de la Waveshare Bureau
  vérifiée, firmware v2.0.0 / ESPHome 2026.9.0 ; AFE et AEC actifs, gain post-AFE
  13. Diagnostic sans transcription : flux non nul sur 1,98 s. Correction du
  comptage doublé des octets en capture, 43 tests ciblés réussis et service
  relancé. Veille Jarvis arrêtée à l'issue du contrôle ; séance humaine à réaliser.

- Précision validée le 16 novembre : **priorité au réveil Jarvis au calme**, les
  essais avec musique viennent ensuite. L'utilisateur rapporte des difficultés
  même au calme sur l'ESP32 et un très bon fonctionnement de Jarvis sur téléphone.
  Il a remis Jarvis : service contrôlé en openWakeWord, modèle
  `jarvisse_20260916_004415.onnx`, seuil 0,3, vérification secondaire désactivée.
  Le chemin actuel ne filtre pas les trames openWakeWord avec Silero en amont.
  Au contrôle, carte déconnectée sans audio reçu ; l'utilisateur confirme qu'elle
  est débranchée ou hors du réseau. Cette indisponibilité n'explique pas à elle
  seule les difficultés antérieures. Diagnostic acoustique à reprendre carte
  disponible ; ne pas attribuer les ratés au modèle ni modifier les seuils sans
  observation. La mention d'Alfy v1 actif plus bas décrit l'état du 13 novembre.

- Le 16 novembre, l'utilisateur demande de travailler sur la qualité de captation
  ESP32. Point documentaire : la recette firmware épinglée utilise les deux
  microphones via ES7210, capture physique 48 kHz et sortie mono PCM16 16 kHz,
  AFE ESP-SR en mode low_cost, AEC avec référence du haut-parleur local, séparation
  de sources/amélioration bimicro (BSS/SE), AGC actif et NS dédié désactivé.
  Ces valeurs de source ne constituent pas une relecture de la carte ; le gain
  post-AFE 13 reste un relevé historique. Proposition : diagnostic acoustique et
  comparaison des réglages avant modification du firmware ou achat. La musique
  de l'ampli externe n'est pas fournie comme référence à l'AEC. Placement,
  gains/AGC, AFE high-performance et éventuel filtrage serveur sont des pistes
  à mesurer, sans adoption ni gain promis. Suivi T13 dans `CHECKLIST.md`.
  À la demande de l'utilisateur, comparaison documentaire avec Kustos Voice
  (https://github.com/Qorvano/kustos-voice) : mêmes principes AEC/BSS/AGC sur la
  même Waveshare, micro mono 16 kHz. L'auteur annonce une portée d'environ cinq
  mètres pendant la musique sur son exemplaire ; aucune supériorité face à notre
  chaîne ni en présence de l'ampli externe n'est démontrée. Différences relevées :
  gain analogique 33 dB (référence fixe 0 dB), réveil embarqué microWakeWord et VAD
  permissif à 0,03. Ce seuil n'est pas transposable aux détecteurs serveur Alfred.
  Firmware orienté Assist/Music Assistant ; intégration directe Alfred et modèles
  ONNX existants non validés. Piste de comparaison seulement, aucun flashage ni
  changement d'architecture décidé.

- Piste évoquée le 15 novembre : **M5Stack ATOM Echo classique (C008-C,
  désormais Atom Voice)** comme petit satellite supplémentaire. Documentation
  constructeur : ESP32-PICO-D4, flash 4 Mo, un micro SPM1423 et haut-parleur
  0,8 W ; tutoriel Home Assistant disponible. Avis technique proposé : intéressant
  pour un terminal compact de proximité, sans gain acoustique démontré face à la
  Waveshare actuelle. Portage du firmware/transport direct Alfred et essais de
  réveil en bruit nécessaires avant adoption. Aucun achat ni remplacement validé.
  Sources : <https://docs.m5stack.com/en/atom/Atom_Voice>,
  <https://www.home-assistant.io/voice_control/thirteen-usd-voice-remote/>.

- Décision du 15 novembre : conserver la Waveshare comme **satellite Wi-Fi sur
  prise USB**, sans câble de données vers le PC. Le serveur Alfred reste nécessaire
  et conserve STT, openWakeWord, IA et voix ; les réglages de réveil restent dans
  l'interface sans OTA. L'utilisateur confirme l'alimentation sur prise ; carte
  réellement identifiée en LAN, v2.0.0 / ESPHome 2026.9.0, protocole OTA vérifié
  sans écriture. Le firmware actuel est conservé. Reprise de veille mémorisée
  après activation ESP32 ; arrêt explicite ou transfert au navigateur annulent
  cette reprise, sans retour automatique à la fermeture de la page. Anciennes
  préférences sans marqueur : aucune activation implicite. Redémarrages réels
  serveur et carte : connexion et micro rétablis sans navigateur. Lecture Phonon
  téléchargée et terminée selon la carte. Recette et récupération documentées
  dans `docs/ESP32_WIFI_OTA.md` ; coupure réelle du Wi-Fi, écoute humaine et transfert
  OTA restent à vérifier. La migration Debian reste distincte.

- Le 3 novembre, l'utilisateur confirme disposer d'un Echo Show 5 stock de
  première génération, modèle H23K37 (`checkers`), et indique que le flashage
  ne le rebute pas. Priorité exprimée : conserver une très bonne détection du
  mot de réveil. Aucun firmware ni abandon du réveil « Alfred » n'est décidé ;
  aucune opération matérielle autorisée ou réalisée par cette seule discussion.
- Recherche documentaire du 3 novembre : `echo-dot-assist` prend en charge ce
  modèle et conserve Fire OS, le traitement audio Amazon et son moteur Pryon.
  Candidat proposé pour comparaison avec TECHO5, non choisi par l'utilisateur.
  Le guide distingue mots Amazon et modèles personnalisés microWakeWord ou
  openWakeWord ; aucun modèle Amazon « Alfred » ni qualité équivalente pour ce
  mot n'est établi. Le port checkers est essayé sur une unité ; ses notes laissent
  la latence et la référence d'annulation d'écho en lecture à mesurer. Ne pas
  généraliser la promesse du README à une performance acoustique vérifiée ici.
  Sources : <https://github.com/Gamer92000/echo-dot-assist>,
  <https://github.com/Gamer92000/echo-dot-assist/blob/main/docs/GUIDE.md>,
  <https://github.com/Gamer92000/echo-dot-assist/blob/main/docs/re-checkers.md>.
  TECHO5 reste une alternative avec écran plus riche ; le moteur et le traitement
  audio diffèrent de ceux d'Amazon. Kiosk Satellite : image checkers encore en
  développement selon <https://github.com/jxlarrea/lineageos-echo-kiosk-satellite>.

- Après autorisation du 2 novembre : prototype de liaison **directe Alfred ↔
  ESP32 par l'API native ESPHome**, sans connexion HA ni flashage. Identité de
  la carte vérifiée en LAN avant les opérations. Firmware v2.0.0 conservé.
  Lecture de la référence par la carte confirmée techniquement puis acceptée
  à l'écoute par l'utilisateur (« c'est bien ça fonctionne » après rejeu).
  Micro : 1,97 s de PCM reçus lors d'un diagnostic sans transcription ni IA.
  La conversation humaine via K2 est ensuite confirmée le 4 novembre ; latence
  et nouveau flux progressif font l'objet de S19. Voir `TERMINAL_DIRECT.md`.
- État vérifié le 2 novembre : Waveshare `eb05fc` (Bureau), firmware
  v2.0.0 / ESPHome 2026.9.0. À la demande de l'utilisateur, la carte n'étant
  utilisée dans HA que pour un test, connexion ESPHome désactivée et déchargée,
  relais Music Assistant désactivé dans HA. Configuration conservée pour
  réactivation ciblée ; aucun effacement ni flashage de la carte. Cibles Alfred
  vers cette carte retirées (annonces, sonneries et lecteur musical de test).
  Elle n'est pas encore reliée directement au service Alfred : T02/T04 ouverts.
- Le 27 octobre, l'utilisateur indique ne plus être chez lui. Le développement
  logiciel peut continuer à distance ; les essais acoustiques et manipulations
  physiques attendent sa présence. Aucun accès distant effectif n'est présumé.
- Le 26 octobre, l'utilisateur confirmait être chez lui avec le module branché.
  La lecture des ports série du PC ne montre que COM1, sans ESP32 identifié ;
  le mode de branchement reste à préciser. Aucun flashage réalisé dans cette séance.

- Carte reçue : **Waveshare ESP32-S3-AUDIO-Board**.
- Fiche fournie : <https://www.amazon.fr/dp/B0FP1VL37J>.
- Deux microphones, ES7210 pour l'entrée audio, ES8311 pour la sortie, amplificateur,
  connexion haut-parleur, Wi-Fi, 8 Mo de PSRAM, 16 Mo de flash et sept LED RGB.
- Documentation : <https://docs.waveshare.com/ESP32-S3-AUDIO-Board>.
- L'utilisateur confirme le 26 octobre la connexion de la carte à Home Assistant
  et le contrôle réussi des lumières. Firmware installé confirmé par l'utilisateur :
  projet ESPHome de jyoushiki, via
  <https://jyoushiki.github.io/esphome-waveshare-esp32-s3-audio-va/>.
  Version et canal installés, mode de déclenchement et qualité de restitution
  vocale restent à préciser ; ne pas présumer la version à partir du site actuel.
- Le contenu physique exact du kit, l'alimentation et les performances audio
  à distance restent à documenter. Premiers retours en présence de bruit ci-dessous.
- Premier prototype dans le **bureau**, puis essai en conditions réelles dans le
  **salon**. Déploiement dans plusieurs pièces à terme.

### Infrastructure existante

- Décision utilisateur du 8 novembre : futur hôte Alfred **Chuwi AuBox Ryzen 7
  8745HS, 32 Go DDR5, SSD 512 Go, Radeon 780M**, commandé et attendu prochainement.
  Il hébergera un homelab sous **Proxmox** ; **Alfred tournera dans une VM Debian**.
  La machine n’est pas encore reçue : ressources réellement libres, version Debian,
  allocation VM, topologie mémoire et performances restent à mesurer. Cela remplace
  l’hypothèse de la VM Alfred sur le Pentium G7400 ; le serveur existant n’est pas
  pour autant déclaré migré. Pas d’accès AMD à présumer dans la VM : passthrough
  et compatibilité du moteur à vérifier. CUDA/DirectML Windows ne sont pas la cible.
- 27 novembre : VM Debian de dev créée sur l’AuBox, Debian 13.8 amd64, 4 vCPU,
  7,8 Gio de RAM, disque de 75 Gio, IP LAN 192.168.1.71, fuseau Europe/Paris.
  Le CPU invité est encore exposé en « QEMU Virtual CPU 2.5+ » sans AVX/AVX2 ;
  le type Proxmox doit passer à `host` avant toute validation vocale. Le dépôt,
  les modèles utiles et les données ont été préparés ; le raccordement HA/ESP32
  et les mesures restent à valider. Cette VM est l’instance de dev active ; la
  future prod reste distincte.

Informations reprises le 26 octobre du document `docs/inventory.md` du projet
`D:\App en dev\Serveur`, fondées sur ses relevés des 23 et 24 octobre ; aucune
nouvelle mesure distante réalisée pour Alfred.

- Serveur principal : Proxmox, Pentium Gold G7400, 32 Go de RAM.
- Home Assistant : VM 102, adresse locale `192.168.1.102`, 8 Go de RAM,
  1 vCPU déclaré. La version Home Assistant relevée était 2026.10.2 ; version
  propre de HAOS à confirmer séparément.
- Raspberry Pi disponible : Pi 4, environ 4 Go de RAM, Debian 13 / Raspberry Pi OS,
  déjà employé pour la maintenance du homelab.
- Un ancien ordinateur portable peut également être envisagé ; caractéristiques
  non précisées.
- L'emplacement des futurs services Alfred et la capacité disponible restent à
  déterminer ; ne pas considérer toute la RAM du serveur comme libre.

### Services existants

- Home Assistant est le système domotique utilisé.
- L'ampli est déjà configuré dans **Music Assistant**, installé en module
  complémentaire de Home Assistant.
- Abonnement musical : **Qobuz**.
- Abonnement IA : **Command Code GOAT**, avec API disponible.
- Vérification documentaire du 26 octobre : GOAT inclut l'accès Provider API
  compatible OpenAI / Anthropic, décompté des mêmes crédits et quotas que les
  autres usages du compte. L'accès effectif avec le compte n'a pas été testé.
- URL de base documentée : `https://api.commandcode.ai/provider/v1`.
- Source : <https://commandcode.ai/docs/plans/goat>.
- Aucune capacité audio ou recherche web intégrée à cette API n'est présumée.

## Interaction et personnalité validées

- Le 11 novembre, l'utilisateur demande d'écrire tous les chiffres en toutes
  lettres dans les réponses d'Alfred. Les données et valeurs internes des actions
  restent numériques ; la conversion concerne la formulation des réponses.

- Décision du 13 novembre : **réveil configurable par STT Parakeet local ou
  openWakeWord, sur ESP32 et navigateur**. Réglages distincts par source et
  moteur. Le STT accepte une phrase libre de un à quatre mots/quarante caractères
  et jusqu'à huit variantes explicites ; valeur initiale **« Alfy »**, variante
  **« Alfi »**, sans préfixe « Hé » obligatoire. openWakeWord choisit un modèle
  entraîné installé (Hé Alfred, Jarvis, Alexa selon disponibilité) ou importé.
  Renommer un modèle ne change pas sa phrase acoustique. Import ONNX limité à
  dix Mo, validation en processus borné, données externes refusées.
- Une seule source en veille : activer l'une suspend l'autre ; aucun retour
  automatique à l'ESP32 après fermeture du navigateur. Le navigateur demande
  un clic et la permission micro, reste fermé au chargement et ferme la veille
  en arrière-plan ou sur perte de connexion. Commandes et réponses suspendent
  le réveil ; reprise de huit secondes conservée. Mot seul : six secondes pour
  donner la commande, puis retour en veille sans IA si silence. Audio et texte
  de veille restent en mémoire. Aucun achat ni flashage prévu. Le 13 novembre,
  l'utilisateur choisit `lfpoulain/wakeword-generator` pour entraîner lui-même
  deux modèles, « Alfy » et « Alfredo » ; préparation des recettes demandée,
  puis confirme avoir créé le modèle `alfy_v1.onnx` après écoute satisfaisante
  des extraits synthétiques. À sa demande suivante, modèle importé depuis `docs`
  et sélectionné pour ESP32 et navigateur avec openWakeWord, seuil 0,5. ESP32
  Bureau connecté, veille armée et flux reçu sans erreur ; qualité acoustique
  humaine non encore validée. Jarvis reste disponible pour retour manuel.
- Le modèle historique « Hé Alfred » du 6 novembre reste disponible. Auditer
  l'entraînement reste une piste, distincte de la livraison du réveil STT.
  La recette locale Hé Alfred déclare 20 000 positifs synthétiques, 2 000 de
  validation et des négatifs dont Fred ; cela ne prouve pas la diversité ni
  la qualité des données effectivement utilisées pour le modèle exporté.
  Alfy prononcé « al-fi » reste court (deux syllabes) ; proximité avec Fred
  probablement réduite, supériorité acoustique non établie. Un modèle Hé Alfred
  ne permet pas de juger Alfy sans entraînement dédié. Alfy v1 est désormais actif.
- Banc de réveil temporaire choisi le 8 novembre : **« Jarvis »**, à partir du
  fichier utilisateur `docs/jarvisse_20260916_004415.onnx`. Il remplace le banc
  Alexa pour l’essai demandé après les mauvais résultats du réveil Alfred.
  Détection openWakeWord sur PC, seuil initial 0,5, vérificateur Whisper désactivé.
  Retour utilisateur du 8 novembre : détection jugée parfaite pendant son essai,
  même à basse voix, avec une nette amélioration. Jarvis est conservé pour avancer
  sur le fonctionnement de l’assistant ; le travail sur le réveil personnalisé est
  différé par l’utilisateur. L’assistant conserve son nom Alfred. Essai musical
  reporté car il est tard ; aucune mesure chiffrée ni validation en bruit ou musique.
  Ce choix provisoire ne vaut pas abandon définitif du réveil Alfred.
- Un membre de la famille s'appelle **Fred** : limiter les faux déclenchements
  sur ce prénom sera un critère majeur de validation.
- Recherche initiale du 13 novembre sur les alternatives, avant la décision
  d'implémentation ci-dessus : Parakeet transcrit des extraits complets ; la
  nouvelle veille utilise des fenêtres de six secondes au maximum, mises à jour
  toutes les cinq cents millisecondes et en fin de parole via Silero VAD. Les
  correspondances doivent être au début de la prise, jamais une mention tardive
  au bord d'une fenêtre glissante. Charge et acoustique humaines à mesurer. microWakeWord
  permet des modèles personnalisés embarqués, avec entraînement difficile selon
  son README ; compatibilité du firmware Waveshare à vérifier avant tout essai.
  Porcupine accepte le français et les phrases personnalisées, mais exige une
  AccessKey valide ; un membre Picovoice annonce la fin des clés gratuites au
  30 juin 2026 et aucune offre non commerciale prévue. Tarif adapté non établi.
  Voicute/onnx-wakeword annonce des modèles français personnalisés et une
  inférence locale ONNX/TFLite. Vérification complémentaire : entraînement et
  essai Basic en ligne gratuits, téléchargement du modèle personnalisé payant
  selon <https://www.voicute.com/articles/custom-wake-word-en.html>.
  Budget gratuit uniquement confirmé ; Voicute écarté. La demande de réveil
  configurable remplace le comparatif comme priorité ; Jarvis reste le réglage
  ESP32 conservé, STT Alfy prêt à activer depuis le laboratoire vocal.
  Aucune supériorité démontrée pour « Hé Alfred » sur notre installation.
  Alfy v1 remplace désormais Jarvis ; comparer sur le même corpus : réveils manqués, faux
  réveils Fred/TV/musique, latence et charge, sans actions domotiques.
  Sources : <https://github.com/OHF-Voice/micro-wake-word>,
  <https://picovoice.ai/docs/model-api/porcupine/>,
  <https://github.com/Picovoice/porcupine/issues/1574>,
  <https://github.com/voicute/onnx-wakeword>.
- Après une réponse, laisser une fenêtre de **8 secondes** pour poursuivre sans
  répéter le mot de réveil. Dans le prototype navigateur v0.4, la fenêtre commence
  à la fin réelle de la lecture ; une phrase commencée à temps peut finir après,
  puis la réponse suivante renouvelle la fenêtre. Sans parole, le micro se ferme
  sans appel IA. Comportement logiciel implémenté ; essai acoustique à faire.
- Permettre de couper la parole à Alfred ; performance à valider avec le matériel,
  notamment en présence de musique.
- Si une autre personne intervient pendant la conversation, changer de profil
  selon le locuteur reconnu et préserver la séparation des souvenirs privés.
- Réponses domotiques et confirmations courtes.
- Personnalité de majordome inspirée d'Alfred de Batman, avec humour discret.
- Référence vocale souhaitée par l'utilisateur : voix française d'Alfred dans
  *Batman: The Animated Series* des années 1990. Le souhait exact est consigné ;
  aucune solution vocale n'est validée. Une voix originale de caractère proche a
  été proposée, sans choix final de l'utilisateur ni engagement de clonage exact.

## Comportements fonctionnels validés

### Domotique

- 13 novembre, recette humaine : refus sur la lumière d'ambiance du bureau malgré
  le groupe Moodlight autorisé et son alias. Cause vérifiée : groupe exposé à Assist,
  trois membres explicitement non exposés, aucune exclusion Alfred. Le contrôle
  initial exigeait l'autorisation individuelle de chaque membre et refusait le groupe.
  Décision suivante validée : piloter les groupes de lumières exposés, avec autorité
  sur leurs membres masqués uniquement via le groupe. Les exclusions explicites de
  groupe, sous-groupe ou lampe restent prioritaires. Membres imbriqués vérifiés,
  cycles/membres manquants refusés ; aucune nouvelle cible individuelle ni changement
  d'exposition HA. Implémenté et préparé en lecture seule sur Moodlight (F24).

- 13 novembre : l'utilisateur juge la couverture vocale insuffisante et demande
  l'analyse de ses essais récents, une recherche de solutions existantes et une
  cible de **99 % de réussite**. C'est un objectif à mesurer, pas un résultat.
  Constat : historique complet non implémenté ; seul le dernier échange ESP32 est
  accessible pendant quinze minutes. Audit et options dans
  `docs/COMPREHENSION_DOMOTIQUE.md` (F22, I05). Plan ensuite approuvé explicitement :
  voie locale rapide puis outil de lumière contrôlé avec l'IA configurée, contexte
  commun et historique local. Aucun comparatif ni changement de modèle. Lumières
  complètes selon capacités (intensité/couleur/blanc), puis fonctions existantes
  par étapes après recette. Remarques implicites : question courte avant action.
  Six échanges/cinq minutes, proposition trente secondes, quatre actions maximum.
  Extensions typées minuteur/appareil préparées mais non généralisées avant recette.
  Défaut de portée établi en simulation : « toutes les lumières du bureau »
  doit cibler le bureau et non toute la maison ; priorité de pièce corrigée.

- 13 novembre : l'utilisateur demande une compréhension plus souple après plusieurs
  refus. Nettoyage partagé des demandes domotiques pour la ponctuation, la
  courtoisie et les tournures orales usuelles. La capture « éteins la lumière du
  bureau s'il te plaît. » établit un défaut d'ordre du nettoyage, corrigé à sa
  source. Tolérance des variantes de politesse ; noms et alias des appareils/pièces
  toujours résolus sans approximation, exposition et exclusions conservées (F21).
  Une couverture générale du langage naturel par outil IA reste un travail distinct.

- Question du 13 novembre, **sans décision d'implémentation supplémentaire** :
  ouvrir l'application CANAL+ en disant « mets Canal Plus sur la télé » et demander
  « passe l'aspirateur dans la cuisine ». Le lancement d'app TV n'est pas raccordé
  aux commandes actuelles ; intégration, bonne cible et identifiant/lien de l'app
  restent à vérifier. Le nettoyage ciblé est raccordé sous « nettoie la cuisine »,
  mais le mapping HA du robot est toujours vide et la variante « passe l'aspirateur
  dans… » n'est pas encore reconnue. Suivi F20 ; aucune action réelle déclenchée.

- Demande complémentaire du 13 novembre : ajouter les `media_player` et `vacuum`
  au même contrôle vocal. Implémentation : état, allumage/extinction, lecture,
  pause, arrêt, pistes, volume/muet et source pour les lecteurs ; démarrage/reprise,
  pause, arrêt, retour à la base, localisation et puissance pour les aspirateurs.
  Seules les actions annoncées par `supported_features` sont disponibles, avec
  revalidation de l'état réel et des exclusions avant chaque action.
- Nettoyage d'une pièce via `vacuum.clean_area`, uniquement à partir des
  associations de pièces déjà configurées dans Home Assistant. Aucun identifiant
  de segment inventé ni repli sur un nettoyage global si une pièce manque.
  Groupes multimédias vérifiés, membres inclus ; un membre exclu ou non exposé
  bloque la commande. Les homonymes nécessitent une pièce ou des alias distincts.
  Music Assistant/Qobuz et son lecteur sélectionné conservent leur parcours.
  Le réglage du volume n'est pas interprété comme une recherche d'artiste.
- Recette des deux domaines sur HA simulé et lecture des capacités réelles ;
  aucune lecture multimédia ni aucun mouvement du robot déclenché pour les tests.
  Essais réels des nouvelles commandes restant à réaliser sur cibles choisies.
  Le catalogue réel contient sept lecteurs et un Roborock Q Revo. Celui-ci annonce
  la capacité de nettoyage par pièce, mais son mapping HA de pièces est vide au
  contrôle du 13 novembre ; ne pas inventer d'association à partir de la pièce
  où se trouve la base. Recette : 561 tests Python réussis, 2 ignorés et 34 JS réussis.

- Interface du 13 novembre : tableau triable par nom d'usage, pièce ou type en
  cliquant sur l'en-tête, avec alternance croissant/décroissant et indicateur.
  Les identifiants techniques sont masqués dans les lignes et restent accessibles
  au survol du nom d'usage. Le tri reste actif pendant les filtres/actualisations.

- Le 13 novembre, l'utilisateur confirme que les lumières fonctionnent au contrôle
  vocal et demande températures, switchs et helpers courants : `input_boolean`,
  `input_number`, `input_select`, `input_datetime`, `input_text`, `input_button`.
  Parcours direct texte/navigateur/ESP32 implémenté sans IA, avec exposition Assist
  moins exclusions et noms/alias HA/Alfred. Les helpers ne sont pas exposés
  automatiquement ; leur configuration Home Assistant n'est pas modifiée.
- Température : capteurs de classe température, valeur et unité actuelles ; pièce
  explicite ou pièce du terminal (configuration ESP32 distincte de celle du web).
  Plusieurs sondes : demander laquelle, sans moyenne implicite.
- Réglages : valeurs numériques bornées, incrément/décrément natif d'un pas,
  choix dans les options existantes, dates/heures selon les champs du helper et le
  fuseau HA, conservation de la partie non modifiée, texte dicté préservé et appui
  sur bouton. Les textes en mode mot de passe ne sont pas lus ni renvoyés dans
  le catalogue. Relecture après écriture ; résultat confirmé uniquement si l'état
  demandé est observé. Un appui envoyé n'atteste pas l'exécution d'une automatisation.
- **Climate différé par l'utilisateur jusqu'à sa présence au domicile** : aucun
  service `climate` n'est appelé. Helpers `timer`, compteurs et domaines natifs
  `number`/`select` hors de cette première extension ; minuteurs Alfred conservés.
  Recette automatisée avec HA simulé ; pas d'action réelle sur la maison pendant
  cette livraison. Essais humains et recette réelle des nouveaux types ouverts.
  Service Windows redémarré le 13 novembre ; santé, nouvelle interface et catalogue
  réel vérifiés HTTP 200, sans écriture dans HA. Les booléens, nombres, sélecteurs
  et textes ne sont pas encore exposés dans le catalogue réel observé.

- « Éteins toutes les lumières » cible **toute la maison**.
- Une commande sans pièce explicite, comme « allume la lumière », vise la pièce
  dans laquelle se trouve le terminal Alfred.
- La stratégie de clarification si plusieurs cibles restent possibles est à définir.

### Musique

- Exemple prioritaire : « Mets Airbourne sur l'ampli ».
- Utiliser l'installation Music Assistant et Qobuz existante.
- Le 30 octobre, premier raccordement fonctionnel livré. Le lecteur
  `media_player.amp_salon_2` est sélectionné explicitement dans Alfred ; le choix
  est enregistré localement dans `music.json`, sans secret. L'interface permet de
  choisir un autre lecteur ou de vérifier celui déjà configuré.
- Commandes directes sans IA : « mets/joue/lance [artiste] sur l'ampli », avec
  qualificatifs album, titre, artiste ou morceau ; pause, reprise, arrêt, morceau
  suivant et précédent. Le modèle dispose aussi d'outils bornés `jouer_musique` et
  `controler_musique` pour les formulations plus naturelles. Les réponses indiquent
  que la commande a été demandée à Home Assistant.
- Essai réel : « Airbourne » a été envoyée à `music_assistant.play_media` ; Home
  Assistant a rapporté le lecteur en état `playing` avec le titre « Rock 'N' Roll Ya »,
  puis la lecture a été arrêtée et le volume initial rétabli. Cet essai ne constitue
  pas une confirmation utilisateur de l'écoute ni une mesure acoustique.
- Le 30 octobre, atténuation automatique livrée pour le navigateur. Le volume
  musical passe par défaut à **25 % du volume courant**, avec un plancher à 3 %,
  et le pourcentage est réglable entre 5 et 80 % dans l'interface. La baisse
  commence dès l'ouverture du micro ou l'envoi écrit, reste active pendant la
  réponse et la fenêtre de reprise de huit secondes, puis la remise au volume
  initial suit la fin réelle de la lecture audio dans le navigateur.
- Un changement manuel du volume ou du mute pendant l'atténuation est conservé :
  la restitution automatique est abandonnée dans ce cas. Une fermeture normale de
  la page demande la restitution avec `keepalive` ; un filet de sécurité restaure
  aussi le volume après 90 secondes si l'onglet disparaît brutalement.
- Essai réel sur l'ampli : base à 12 %, baisse confirmée à 3 %, restitution
  confirmée à 12 %, puis volume initial de 47 % rétabli et lecture arrêtée. Cette
  recette concerne la boucle navigateur actuelle ; un terminal ESP32 devra déclencher
  la même interaction depuis son propre cycle audio en T04/T05.
- Retour utilisateur après l'essai : « c'est éteint ». Contrôle Home Assistant :
  lecteur `idle`, volume 47 %, non muet. La lecture et la restauration sont donc
  terminées proprement ; ce retour ne constitue pas encore une évaluation de la
  qualité ou de la latence perçues.
- Restent à faire : clarification et recette des recherches ambiguës, Qobuz et
  playlists, multi-terminaux, gestion des erreurs réseau et permissions.

### Musique et volume (13 novembre)

- Plan approuvé et première livraison du lot musique : ampli `media_player.amp_salon_2`
  choisi, aucune substitution de lecteur, playlist par défaut stockée par URI et
  sélectionnée dans le panneau. L'installation réelle Music Assistant expose dix-huit
  playlists (douze locales et six Qobuz). Les commandes locales et l'outil IA utilisent
  le même exécuteur et le même contexte.
- Variation « un peu » = cinq points de volume ; le réglage repart du volume normal
  et non du volume atténué pendant une réponse. Un lancement de recherche précis est
  seulement déclaré envoyé ; les réglages vérifiables sont relus. Incertitude ou panne
  arrête la suite sans retry. Lots mixtes entre familles restent refusés.
- Recette synthétique sur modèle actuel/appareils simulés : 20/20 développement et
  20/20 validation musicale indépendante, p95 2,263 s. Recette humaine, choix réel de
  la playlist et latence vocale restent à faire ; aucun 99 % global annoncé.

### Minuteurs (13 novembre)

- Après validation musicale, compréhension naturelle des minuteurs livrée : même
  stockage/étage, durées libres, ajout, consultation, annulation et Stop. L'outil IA
  ne peut ni changer d'étage, ni dépasser sept jours, ni retirer les protections
  contre les phrases mixtes ou négatives. Suites de quatre actions et interruption
  sans suppression des échéances déjà créées.
- Tests complets et validation synthétique 20/20. Service actif, veille ESP32 armée,
  minuteurs existants préservés. Recette micro/sonnerie et reprise après redémarrage
  restent humaines (F26).

### Minuteurs historiques

- **Alfred stocke et programme les minuteurs**, qui sont également consultables
  et commandables depuis HA. Un seul échéancier de référence, dans Alfred.
- Exemple prioritaire : « Mets un minuteur de 8 minutes ».
- Une minuterie mesure une durée, par exemple « mets une minuterie de 7 minutes
  40 » ; à la fin elle sonne sur tout l'étage, conformément à la règle ci-dessous.
  Le prototype reconnaît maintenant « minuterie » et « 7min40 » ou « sept minutes
  quarante » ; validé par tests automatisés, essai utilisateur restant.
- À échéance, faire sonner **tous les terminaux Alfred du même étage** que celui
  depuis lequel le minuteur a été lancé : rez-de-chaussée ou premier étage.
- L'affectation des terminaux aux pièces et étages doit être prise en compte.
- « Stop » arrête les sonneries actives à l'étage du terminal où l'on parle.
- Conserver les échéances après redémarrage. Un minuteur expiré pendant l'arrêt
  est marqué terminé, sans déclencher de sonnerie tardive. Les échéances encore
  futures reprennent leur cours.
- Les détails de consultation et d'annulation restent à spécifier.

### Fonctions personnelles et annonces

- Inclure dès la première version les **rappels**, les **listes de courses** et
  les **annonces dans la maison**.
- Rappels : personnels par défaut, possibilité de demander un rappel pour tout le
  monde et prise en charge de la récurrence. **Les données de calendrier et les
  rappels personnels sont conservés dans les calendriers Home Assistant** ;
  Alfred les consulte et les modifie en tant qu'interface vocale. Les calendriers
  personnel et familial sont associés localement ; aucun second calendrier de
  référence dans Alfred.
  Conserver les échéances après redémarrage. Un rappel personnel
  non délivré reste visible dans l'interface, sans annonce à toute la maison.
  Par défaut, annoncer un rappel personnel sur le terminal depuis lequel il a
  été créé ; permettre de choisir une autre pièce à la voix. Si aucun terminal
  n'est associé à la création (interface web ou HA), le choix du défaut reste à
  définir. Après redémarrage, un rappel dont l'échéance a été manquée est signalé
  dans l'interface, sans annonce ou sonnerie tardive. Pour les rappels récurrents,
  un rappel récurrent manqué pendant l'arrêt est signalé, puis la prochaine
  occurrence future est programmée, sans sonnerie tardive.
- Décisions utilisateur : un calendrier familial distinct dans HA ; seuls les
  événements identifiés comme rappels donnent lieu à une annonce, pas tous les
  événements des calendriers. Les rappels créés par Alfred portent un marqueur dans
  la description HA ; les événements ajoutés directement dans HA restent silencieux.
- Si l'annulation d'un rappel récurrent ne précise pas sa portée, Alfred demande
  s'il faut annuler seulement la prochaine occurrence ou toute la série.
- Clarification utilisateur du 29 octobre : le rappel est une échéance de type
  calendrier, ponctuelle ou récurrente, par exemple « rappelle-moi de sortir les
  poubelles tous les jeudis à 19 h » ou « rappelle-moi de payer la facture demain ».
  Si l'heure n'est pas précisée, Alfred demande l'heure. Cela ne constitue pas une
  décision d'ajouter un agenda général ; l'utilisateur a depuis choisi les
  calendriers Home Assistant comme source des rappels personnels.
- Le 29 octobre, l'utilisateur choisit de poursuivre avec les rappels. Premier
  socle logiciel : association explicite d'un rappel ponctuel à un profil ou à la
  famille, avec destination saisie dans l'interface web ; migration locale vers le
  schéma 3. Ce banc local est désormais suspendu suite à la correction utilisateur ;
  ses données sont conservées. L'interface n'est ni authentifiée ni filtrée par profil :
  pas de confidentialité garantie.
  Choix du comportement par défaut web/HA encore demandé à l'utilisateur ; saisie
  explicite de la pièce utilisée en attendant, sans la considérer comme décision.
  Diffusion, création vocale, permissions et exposition HA restent à faire.
- Avant suspension : récurrence hebdomadaire implémentée dans le banc local, heure de
  Paris conservée lors du changement d'heure ; un rappel manqué reste visible et la
  prochaine occurrence future est créée après reprise. Tests automatisés réussis.
  Comportement technique en attente de validation : heure inexistante au printemps
  décalée à la première minute valide, heure répétée en automne prise à sa première
  occurrence. Permissions et exposition HA restent à faire.
- Avant suspension : création de rappels à la voix via Command Code, avec
  contrôle local de l'heure explicite, du profil nommé, de la pièce et du jour ;
  dialogue testé avec profils et échéances fictifs. L'identité vocale n'étant pas
  reconnue, un nom de profil est demandé ; enregistrement ne signifie pas annonce.
  Ciblage des annonces et journal de tentative de rappel testés sur terminaux simulés.
  L'utilisateur choisit la voix cloud existante de Home Assistant ; le satellite
  Bureau/RDC est configuré ; la diffusion des anciens rappels est maintenant suspendue. La voix
  vient du pipeline HA du satellite, pas de Piper local ; la configuration exacte
  de ce pipeline, le fournisseur et le coût restent à vérifier. Une demande acceptée
  ne prouve pas que le son a été entendu ; une tentative incertaine n'est pas répétée.
  Aucun essai physique encore. Permissions et confidentialité applicative absentes.
- Liste de courses commune à la famille, consultable et modifiable à la voix et
  dans l'interface web ; elle doit également se retrouver dans **Home Assistant**.
  L'utilisateur n'utilise pas d'application de courses ; l'inspection HA a toutefois
  trouvé des listes existantes. HA est le stockage de référence retenu ; le mécanisme
  d'intégration précis reste à mettre en place.
- Précision après inspection HA : deux listes y existent déjà, mais l'utilisateur
  choisit **une nouvelle liste familiale Alfred**, avec HA comme référence.
  Aucun article transféré des listes existantes.
- Préparation logicielle du 27 octobre : sélection explicite d'une entité `todo`
  dans Alfred, ajout d'un article et lecture de la liste depuis l'interface et le
  dialogue, testés initialement avec HA simulé.
  Modification, suppression et permissions par profil restent ouvertes.
- Le 29 octobre : liste « Courses Alfred » créée via Local to-do dans HA, entité
  `todo.courses_alfred`, configurée dans Alfred. Lecture vide puis ajout et lecture
  d'un article temporaire réussis depuis le service Python d'Alfred avec HA réel ;
  article de test supprimé et liste vérifiée vide. Essai de l'interface et au micro
  toujours à effectuer ; pas de validation des permissions par profil.
- Le 29 octobre, l'utilisateur demande une compréhension plus naturelle des
  demandes et l'utilisation du LLM pour choisir les actions. Deux outils de courses
  (lecture et ajout d'un article) sont raccordés ; paramètres contrôlés par Alfred.
  Fournisseur réel avec liste simulée : lecture naturelle et ajout explicite réussis,
  ajout indirect instable ; essais réels de bout en bout restent à faire. Un essai
  avec la liste réelle a été refusé par l'examen automatique en raison de la possible
  transmission ultérieure des articles à Command Code via le contexte. Les permissions
  par profil ne sont pas encore raccordées ; les autres fonctions restent à intégrer.
- L'utilisateur autorise ensuite la transmission éventuelle des articles à Command
  Code dans le contexte de conversation. Test réel de « Que devons-nous acheter ? » :
  l'outil de lecture est appelé et la réponse vocale est produite. La compréhension
  d'ajouts indirects reste à améliorer et à vérifier.
- Essais complémentaires : ajout indirect et suite « et du café aussi » réussis
  sur liste simulée ; une réponse vide observée lors d'un autre essai avant
  augmentation de la limite de sortie de 512 à 1024 tokens. Questions générales
  et remarque sur un aliment sans action non souhaitée dans les essais. Fiabilité
  pratique, consommation et permissions par profil restent à valider.
- Retour utilisateur : problème lors de l'ajout de plusieurs articles. Les anciens
  fichiers de journal ne couvrent pas cet essai ; le code limitait les outils à un
  article/appel. Correction : jusqu'à huit articles séparés, validation préalable et
  signalement d'un résultat partiel ; test réel du modèle avec liste simulée réussi,
  essai vocal réel restant à confirmer.
- Décision utilisateur : un article déjà présent ne doit pas être ajouté ; Alfred
  le signale. Implémenté pour les articles non terminés avec comparaison des accents,
  majuscules et articles français simples ; quantités et variantes restent distinctes.
  Vérification avant écriture et refus de l'ajout si la liste est illisible. La
  comparaison ne reconnaît pas tous les synonymes et n'est pas atomique face à une
  modification simultanée depuis un autre client HA. L'utilisateur confirme que
  l'essai réel fonctionne ; les cas de synonymes et de concurrence restent ouverts.
- L'utilisateur souhaite remettre en liste active les articles cochés et pouvoir
  supprimer définitivement un article sur demande explicite. Fonctions implémentées,
  ainsi que modification du nom ou de la quantité ; cocher reste distinct de la
  suppression définitive. Ciblage par UID, refus des correspondances ambiguës ou des
  doublons actifs lors d'une remise. Essais HA simulé et fournisseur réel avec liste
  simulée réussis ; essais utilisateur sur liste réelle encore à confirmer. Le contrôle
  vocal de suppression exige une demande de suppression ; l'interface demande une
  confirmation. Les permissions par profil restent à raccorder.
- Correction utilisateur du 29 octobre : cocher signifie acheté ; décocher dans HA
  remet l'article en liste. Ajouter à la voix un article coché doit le décocher plutôt
  que le recréer. « Supprime le sucre » le supprime définitivement ; « purge la
  liste » ou « supprime tout » supprime définitivement les articles actifs et cochés.
  Implémenté et vérifié avec HA simulé ; phrases testées avec le modèle réel et
  une liste simulée. La purge supprime par identifiant et s'arrête si un résultat
  n'est pas confirmé ; l'utilisateur indique ensuite que cela fonctionne, sans
  détailler chaque scénario essayé. Les permissions restent à vérifier.
- Préparation de la suite : cocher un article demandé ou acheté, dans HA et depuis
  Alfred, plutôt que l'effacer définitivement. Article identifié par UID, ambiguïtés
  refusées. Tests HA simulé et fournisseur réel avec liste simulée réussis ;
  l'utilisateur confirme ensuite que l'essai réel fonctionne.
- Annonces ciblables sur **toute la maison, un étage ou une pièce**. Exemple :
  « annonce à l'étage que le repas est prêt ». Traitement de la musique en cours
  et modalités de diffusion restent à cadrer.
- Clarification utilisateur : une annonce diffuse immédiatement un message, avec
  choix du lieu de diffusion, par exemple « fais une annonce, le repas est prêt ».
  Si aucun lieu n'est précisé, la diffuser dans toute la maison. Si un étage ou une
  pièce est demandé, ne cibler que cette destination.
- 16 novembre : confirmation par appareil dans le panneau Domotique. Une case
  locale, enregistrée dans `home-confirmations.json`, impose une question avant
  toute commande qui modifie l'entité marquée ou un membre effectivement piloté
  de son groupe. Les lectures, températures, options et le panneau Musique restent
  directs. Une commande globale est bloquée en entier et confirmée en une fois ;
  oui/non sont interceptés avant le modèle dans la session du terminal, avec
  expiration à trente secondes. La page affiche Confirmer et Annuler ; aucun appel
  d'écriture Home Assistant n'est envoyé avant l'accord.
- Diagnostic du 17 novembre : essai de confirmation sur l'imprimante bloqué en
  amont. Journal navigateur : deux transcriptions incorrectes, puis « allume-la »
  reconnu à 09:17:46 et refus conversationnel sans résultat d'action. L'alias
  imprimante et la confirmation sont enregistrés sur le même switch, mais le
  relais IA `devices` était désactivé : ni outil appareil ni switchs transmis au
  modèle. Le support des commandes directes ne garantit donc pas la compréhension
  conversationnelle de cette famille. Après accord utilisateur, relais activé
  dans `.local/data/intent-settings.json`, relu à chaque tour sans redémarrage.
  Catalogue réel vérifié : alias imprimante, switch autorisé et confirmation
  obligatoire. 145 tests ciblés réussis avec HA simulé (oui/non, expiration,
  sessions, appareils et intentions). Modèle réel via API texte : demande explicite
  puis annulation réussies ; « allume-la » dans le même échange retrouve
  l'imprimante et demande confirmation. Après « oui », HA confirme l'activation,
  puis une lecture séparée confirme encore l'état activé. TTS réel généré, sans
  écoute ni capture micro humaine. Santé du service `ok` ; recette vocale humaine
  et autres appareils restent F23/F15/F33. Aucun changement des exclusions ou
  confirmations ; aucun autre appareil actionné.
- Arbitrer explicitement quelles fonctions et données sont gérées dans Home
  Assistant et lesquelles restent propres à Alfred avant de figer l'architecture.

### Architecture vocale — décision validée

- Retenir **Alfred autonome avec intégration Home Assistant**, suivant le principe
  d'un assistant externe. HA Assist ne sera pas le socle principal du dialogue.
- Le service Alfred coordonne l'identification des locuteurs, leurs permissions,
  le dialogue, les mémoires et les fonctions personnelles.
- Home Assistant fournit les pièces, étages, appareils et commandes domotiques ;
  Music Assistant pilote musique et Qobuz ; Command Code fournit le modèle de
  conversation via l'abonnement existant.
- Les terminaux ESP32 captent la voix, jouent les réponses et gèrent boutons/LED ;
  l'interface Alfred gère notamment les profils, restrictions et historique.
- Réutiliser des moteurs existants pour transcription, synthèse et reconnaissance
  des personnes. Firmware, transport audio, moteurs et hébergement ne sont pas
  choisis par cette décision. Réutilisation ponctuelle de fonctions Assist possible.
- Références corrigées : HA pour les courses et les calendriers personnels ; Alfred
  pour le stockage et la programmation des minuteurs. Alfred lit et modifie les
  calendriers HA ; méthode de diffusion des rappels, référence familiale et
  exposition des minuteurs dans HA restent à préciser.

#### Liaison domotique — proposition du 8 novembre, non validée

- Décision du 11 novembre : les entités accessibles à la domotique Alfred sont
  celles exposées à Assist dans HA, moins les exclusions choisies dans Alfred.
  Une nouvelle entité exposée est autorisée par défaut. Le catalogue affiche toutes
  les entités exposées et distingue les commandes disponibles. Lecture prévue par
  WebSocket, commandes de lumière REST conservées ; MCP n'est pas retenu pour ce
  premier chantier. Les sélections musique, courses et calendriers restent
  distinctes. Implémentation et vérification réelle restent à effectuer.
  Avancement : catalogue et exclusions raccordés ; lecture réelle du catalogue HA
  réussie, tests ciblés réussis. Recette physique et parité des entités sans entrée
  de registre encore ouvertes ; aucune validation d'ensemble n'est déduite.
  Demande ultérieure : tableau des entités avec alias locaux modifiables dans Alfred.
  Les alias sont raccordés aux lumières puis, le 13 novembre, aux températures,
  switchs et helpers courants ; ils ne modifient pas HA. Homonymes refusés ; exclusion et
  exposition continuent de s'appliquer. Recette vocale humaine restant à faire.

- L'utilisateur demande comment choisir les entités accessibles à Alfred et
  compare Assist, MCP et API ; aucun nouveau transport n'est encore choisi.
- Proposition : conserver Alfred autonome et utiliser le serveur MCP officiel
  HA avec le seul jeu d'outils « Device control » pour la domotique courante,
  afin de réutiliser les entités exposées à Assist dans HA. Vérifier auparavant
  les capacités de la version installée et la compatibilité du client Alfred.
- La documentation actuelle distingue ce jeu limité du jeu « Home Assistant »,
  qui accède à toutes les entités et actions ; ne pas confondre leurs périmètres.
- Le prototype utilise déjà REST pour les lumières et des fonctions spécialisées.
  Les appels REST directs ne sont pas automatiquement limités par l'exposition
  Assist : prévoir un contrôle explicite des cibles pour les chemins conservés.
- Music Assistant, calendriers et courses nécessitent une vérification de couverture
  avant de décider quels accès API spécialisés conserver. Les permissions par
  personne restent à appliquer dans Alfred en plus de la sélection globale HA.
- Source officielle vérifiée le 8 novembre 2026 :
  <https://www.home-assistant.io/integrations/mcp_server/>.

#### Justification documentaire et limites

- Choix motivé par le besoin de maîtriser le dialogue et les profils, avec
  intégration HA et réutilisation de composants existants.
- Assist reste utilisable pour certaines fonctions ; autonomie d'Alfred ne signifie
  pas réécrire la reconnaissance vocale, la synthèse ou tous les composants HA.
- Assist documente une chaîne réveil/STT/conversation/TTS, des agents remplaçables
  et des satellites avec annonces et conversations. ESPHome documente une écoute
  continue relancée après la réponse. La fenêtre de huit secondes nécessite une
  logique dédiée et ne correspond pas au simple délai de conservation du contexte.
- Les interfaces consultées ne documentent pas une solution complète native pour
  nos identités vocales persistantes, permissions par personne et mémoires séparées.
  L'API STT mentionne un identifiant de locuteur dans les résultats partiels, sans
  que cela constitue une identification familiale ; ces résultats partiels ne sont
  pas encore utilisés par la pipeline selon cette documentation.
- Inférence architecturale : maîtriser la chaîne audio et l'identité dans Alfred
  donne davantage de latitude pour ces exigences, au prix de davantage de code
  et de maintenance. Une solution autour d'Assist reste techniquement possible
  avec des extensions ; elle n'est pas déclarée impossible.
- Aucune garantie de latence ou de consommation sur le serveur existant : à mesurer.
  Firmware, transport audio, identification avant exécution et interruption avec
  annulation d'écho doivent faire l'objet d'un prototype avant de figer la pile.
- Sources officielles consultées le 26 octobre 2026 :
  <https://contributors.home-assistant.io/core/internals/assist-pipelines/>,
  <https://contributors.home-assistant.io/core/entities/stt/>,
  <https://contributors.home-assistant.io/core/entities/assist-satellite/>,
  <https://esphome.io/components/voice_assistant/>.

## Profils vocaux, permissions et mémoires

### Profils

- Précision validée du 18 novembre : la connexion à l'app Alfred se fera via HA,
  avec les comptes dédiés, Music Assistant compris dans le parcours souhaité.
  Prévoir ce contexte utilisateur pour le futur raccordement musical. La liaison
  des identités, sessions et droits HA/MA ainsi que la portée personnelle ou partagée
  des favoris restent à vérifier ; aucun SSO effectif ni propagation automatique
  des droits n'est établi. La première étape UI Musique ne réalise pas le login.
- Le 30 octobre, l'utilisateur choisit d'utiliser les comptes Home Assistant pour
  protéger l'accès à l'administration d'Alfred, si l'intégration le permet. La
  documentation officielle décrit un flux OAuth 2 avec PKCE pour une application
  externe : <https://contributors.home-assistant.io/core/internals/auth-api/>.
  L'intégration, la vérification des droits administrateur, l'association aux
  profils et la protection effective des routes restent à réaliser et tester.
  Ce choix ne modifie pas les permissions vocales des invités ci-dessous.
- Correction du 30 octobre : privilégier les fonctions pour le moment ; reporter
  l'authentification de l'interface et les droits de chacun avant la véritable
  mise en production. Le choix Home Assistant reste l'orientation envisagée, sous
  réserve de faisabilité ; aucune protection n'est actuellement implémentée.
- Reconnaître **deux adultes et un enfant de 4 ans** ; les autres personnes sont
  des invités.
- Les profils servent à personnaliser les réponses, retrouver les mémoires et
  appliquer les restrictions configurées.
- Les permissions et limitations doivent être **paramétrables dans une interface
  web**. Le détail des restrictions de l'enfant n'est pas encore choisi.
- Prévoir une **application web dédiée à Alfred**, accessible depuis Home Assistant.
- Prévoir des confirmations orales pour certaines actions importantes, configurables
  par action et indépendantes des restrictions par profil. Accord de principe donné ;
  liste des actions concernées et réglages par défaut encore à choisir.

### Règle de permissions explicitement corrigée par l'utilisateur

- **Appliquer des restrictions uniquement si un profil limité est reconnu.**
- Une voix inconnue est traitée comme invitée et dispose de toutes les fonctions.
- Les invités n'ont **pas de mémoire personnelle persistante** ; c'est la seule
  restriction fonctionnelle demandée pour eux.
- Ne pas introduire par défaut un blocage des invités, une validation sur téléphone,
  un code adulte ou une interdiction universelle des actions importantes.
- Conséquence déjà explicitée : si l'enfant n'est pas reconnu, il peut être traité
  comme invité et les restrictions de son profil ne s'appliquent pas.
- Les seuils de confiance, la gestion des voix incertaines et la différence entre
  invité reconnu et voix inconnue restent à préciser techniquement.

### Enrôlement des voix — décidé le 26 octobre

- Trois phrases courtes, chacune répétée deux fois : six passages de six secondes au
  maximum, soit environ vingt secondes de parole par personne.
- Les enregistrements audio sont conservés avec les empreintes sous
  `.local/data/profiles`, hors dépôt ; supprimer un profil efface aussi ses fichiers.
- Moteur retenu : ECAPA-TDNN VoxCeleb (SpeechBrain, licence Apache 2.0), empreinte de
  192 valeurs calculée localement, chargée depuis `.local/models` sans réseau.
- Rôles stockés : adulte ou enfant. Aucun profil invité, conformément à la règle des
  permissions ; la reconnaissance, les seuils et la normalisation restent à faire.

### Mémoire

- Une mémoire commune de la maison et une mémoire personnelle par membre de la
  famille, disponibles depuis tous les terminaux Alfred.
- Mémorisation automatique des informations utiles et préférences au fil des
  discussions, sans devoir systématiquement dire « retiens ceci ».
- Pour les invités : contexte temporaire pendant la conversation, aucune mémoire
  personnelle persistante. Les échanges des invités n'alimentent pas automatiquement
  la mémoire commune.
- Les invités ne peuvent pas consulter les souvenirs privés des membres de la
  famille. Cette précision a été acceptée lors de l'échange suivant.
- Retenir automatiquement les goûts et habitudes ; demander confirmation avant de
  mémoriser des informations personnelles sensibles. Les catégories précises et
  le mécanisme de confirmation restent à définir.
- Les limites d'accès entre profils familiaux, la conservation des souvenirs,
  la correction et l'effacement restent à cadrer.
- Les commandes « qu'as-tu retenu sur moi ? » et « oublie cette information » ont
  été proposées et restent à confirmer dans les fonctions de gestion de mémoire.

## Historique de diagnostic

- Extension demandée le 16 novembre, en réponse à la question sur un historique des
  commandes et appels : s'appuyer sur le journal I05 existant et ajouter un suivi
  du réveil (heure/source, modèle/seuil, score maximal par fenêtre, niveaux micro,
  ruptures de flux, résultat et lien vers la commande). Un marqueur utilisateur
  « appel raté » permettrait d'identifier les essais sans détection ; le logiciel
  ne peut pas les identifier avec certitude à partir de cette absence seule.
  Résumés techniques bornés, sans audio brut, rétention sept jours/100 Mo.
  L'utilisateur demande sa réalisation avec un onglet Logs et un test guidé :
  détection automatique ou bouton d'appel manqué pour passer à l'essai suivant.
  Parcours « réveil seul » choisi lors du plan. L'utilisateur exige ensuite le
  choix du moteur openWakeWord/STT et du mot d'appel depuis cette même page :
  modèle installé et seuil pour openWakeWord ; phrase et variantes pour STT.
  Les mesures STT (VAD, inférences, résultat de reconnaissance) ne sont pas un
  score openWakeWord. Paramètres constants pendant chaque séance ; comparaison
  entre séances. Proposition de recette au calme, pas encore validée : cinq
  appels à 50 cm, dix à 1 m, cinq à 2 m et cinq à 3 m, avec silence initial/final
  de trente secondes ; carte fixe dans le bureau. Priorité Jarvis au calme
  inchangée. Onglet Logs, choix du moteur et test guidé implémentés ; recette
  humaine sur ESP32 encore ouverte. L'historique est accessible sur l'interface
  LAN sans authentification propre. Suivi T13.

- Livraison du 13 novembre : journal local SQLite pour les nouveaux échanges,
  sept jours et cent Mo, purge périodique et à l'accès, sans audio brut. CLI de
  consultation/export/annotation CLI ; depuis l'onglet Logs du 16 novembre,
  consultation également possible sur l'interface LAN, sans authentification propre.
  Contrôle applicatif et SQLite effectué après redémarrage. Les anciens échanges
  perdus avant cette livraison n'ont pas été recréés (I05).

- 8 novembre : demande utilisateur de rétablir dans le laboratoire vocal les
  deux textes de la conversation ESP32 : « Ce qu’Alfred a compris » et « La réponse
  d’Alfred ». Raccordement au flux applicatif, affichage dès transcription puis
  réponse, y compris avant la synthèse vocale. Dernier échange uniquement en
  mémoire serveur (expiration après quinze minutes), endpoint dédié sans cache ;
  les statuts techniques restent sans contenu de conversation. Aucun historique
  durable ajouté par cette correction. Recette humaine après actualisation à faire.

- Conserver un historique pour le débogage sur **les sept derniers jours**, avec
  un plafond de **100 Mo**. Purger les entrées les plus anciennes pour respecter
  les deux limites.
- Contenu : transcriptions textuelles, réponses, actions exécutées, erreurs et
  temps de traitement. Ne pas conserver l'audio brut dans l'historique.
- Cet historique technique est distinct de la mémoire personnelle durable.
- Inclure les échanges des invités uniquement pour le diagnostic ; ne jamais
  les utiliser pour alimenter une mémoire personnelle.
- La conservation séparée des échantillons nécessaires à l'apprentissage vocal
  reste à définir lors du cadrage de l'enrôlement des profils.

## État d'implémentation — 26 octobre 2026

- Socle local v0.1.0 créé : FastAPI/Python, interface web française et API
  d'échéances SQLite. Lancement avec `python -m alfred` dans le venv, sur
  `127.0.0.1:8765` uniquement ; instructions et limites dans `README.md`.
- Minuteurs/rappels de test : création, annulation, transitions d'état et reprise
  après arrêt. « Stop » termine les minuteurs en sonnerie sur l'étage choisi.
  À la reprise, minuteurs expirés terminés et rappels manqués visibles, sans
  déclenchement tardif ; échéances futures préservées.
- Banc navigateur explicitement silencieux et sans identité personnelle. Les
  rappels arrivés à échéance attendent une délivrance réelle qui n'est pas encore
  connectée. Pas de récurrence, de micro, de moteur vocal, de LLM, d'intégration HA,
  de mémoire personnelle ou de connexion ESP32 dans cette version.
- Données de test hors Git dans `.local/data`, dépendances verrouillées, verrou
  mono-instance et schéma de base versionné. Authentification distante et
  déploiement serveur restent à faire ; ne pas exposer le banc sur le réseau.
- Vérifications : 28 tests automatisés réussis sous Python 3.14/Windows ; validation
  syntaxique JS ; navigateur réel : création d'un minuteur, échéance puis Stop
  vérifiés. Un avertissement de dépréciation httpx/Starlette dans les outils de test,
  sans échec ; aucune validation de performance vocale déduite.

### Évolution v0.2 — laboratoire vocal navigateur

- Capture micro implémentée via AudioWorklet après clic et autorisation navigateur,
  WAV mono PCM16, arrêt manuel/annulation et maximum 30 secondes ; fermeture des
  pistes et réécoute temporaire en mémoire. L'utilisateur confirme après essai :
  « ça fonctionne très bien » ; banc navigateur validé qualitativement.
- Moteurs faster-whisper 1.2.1 (base multilingue, CPU INT8) et Piper 1.8.0 avec
  Tom et Pierre (UPMC) français installés sur ce PC. Modèles publics préparés explicitement dans
  `.local/models`, révisions dans `sources.json`. Aucun téléchargement à l'inférence.
- Banc audio local : transcription et relecture de ce qui est compris, sans IA,
  profil, mémoire ou action domotique. Transcriptions, audio entrant et réponse
  audio non archivés ; ils restent en mémoire pour l'affichage et la lecture.
- Limites et erreurs WAV contrôlées, requêtes vocales sérialisées, anciennes
  réponses ignorées après annulation. Un calcul déjà démarré peut finir côté serveur.
- Vérifications : 42 tests Python réussis, dont boucle réelle Piper → Whisper sans
  microphone, et 2 tests JS WAV ; sample Piper lu dans le navigateur. Whisper base
  a mal transcrit le nom Alfred lors d'un essai synthétique ; comparaison `small`
  et essais humains nécessaires avant validation de qualité ou choix définitif.
- Ni l'intégration IA/HA/ESP32, ni les profils, ni la fenêtre de 8 secondes ne sont
  activés par cette évolution. Essai micro navigateur validé par l'utilisateur ;
  choix définitif de la voix et essais sur ESP32/serveur restent ouverts.

### Évolution v0.3 — conversation Command Code validée par l'utilisateur

- 20 novembre. Dans la PWA, « IA et recherche » ouvre la liste des modèles
  enregistrés dans une fenêtre modale depuis la ligne du modèle serveur.
  Le modèle actif est précoché à l’ouverture. Un autre choix s’applique avec
  « Valider ». « Annuler » ferme la fenêtre sans appliquer le choix.
  Ajouter un modèle conserve les précédents. Tester envoie un message
  générique à Command Code et mesure le délai jusqu’à la réponse complète,
  sans activer le modèle. La sélection explicite s’applique au serveur et
  persiste au redémarrage. Un modèle imposé au lancement garde la priorité.

- Connecteur Command Code implémenté avec endpoint officiel fixe, streaming de
  réponse à l'écran puis lecture Piper, à partir de texte saisi ou transcrit.
  Personnalité française de majordome, réponses courtes. Aucun outil/action IA,
  recherche web, profil ou mémoire durable dans cette évolution.
- Clé spécifique à Alfred à saisir dans le formulaire local, jamais dans le chat ;
  stockée avec protection DPAPI Windows ou fichier privé 0600 Linux. Ni clé ni
  détail d'erreur du fournisseur renvoyés au navigateur. Configuration possible
  par variables ALFRED au lancement ; aucune clé copiée d'une autre application.
- Mode Test audio entièrement local ; mode Conversation choisi explicitement.
  Dans ce dernier, texte/contexte/instructions envoyés à Command Code, pas l'audio.
- Contexte provisoire en mémoire par onglet aléatoire (six messages, expiration
  30 minutes, maximum 32 sessions), effaçable ; ce n'est pas la mémoire personnelle
  finale. Réinitialisation et changement de configuration invalident l'ancien contexte.
- Modèle initial proposé : exemple officiel `deepseek/deepseek-v4-flash`, modifiable
  et à vérifier avec GOAT. Réponse limitée à 256 tokens ; pas de retry/fallback
  automatique ni achat. Le plafond financier global S08 n'est pas implémenté.
- Lors de la préparation, aucune clé n'était configurée. Après livraison du
  formulaire, l'utilisateur confirme : « ça fonctionne bien ». Accès et parcours
  de conversation validés qualitativement par ce retour ; modèle effectivement
  utilisé, latence et consommation non relevés. Catalogue public interrogé sans
  clé pendant la préparation : HTTP 403, sans contournement.
- Recette : 61 tests Python passent, fournisseur Command Code simulé, voix locale
  réelle optionnelle incluse ; 5 tests JS. DPAPI testé avec secret fictif. S11 coché,
  S05 reste partiellement ouvert pour mesures/comparaison du modèle et appels
  d'outils, non inclus dans cette version ; accès conversationnel réel validé par retour utilisateur.

### Évolution v0.4 — boucle conversationnelle navigateur à essayer

- Conversation démarrée explicitement au micro, avec enchaînement actif par défaut
  dans ce mode. La phrase part après environ une seconde de silence ; le micro est
  fermé pendant le calcul et la lecture. La reprise de huit secondes à la fin
  est désormais limitée aux confirmations et précisions.
- Limite de 30 secondes par phrase, pré-enregistrement borné, phrase commencée avant
  l'échéance acceptée. Le silence ferme le micro sans nouvel appel IA.
- Arrêt au bouton : micro fermé, lecture coupée, réponse en cours ignorée. Décocher
  l'option empêche la reprise. Message écrit, sample Piper, erreur et réécoute ne
  réarment pas la capture ; réécoute pendant une capture ferme celle-ci. Onglet caché
  ferme la capture et désarme la reprise. Le contexte temporaire survit à la simple
  fermeture du micro ; « Nouvelle conversation » le supprime.
- Détection locale par énergie avec seuil adaptatif, minimum de voix et temporisation
  de silence. Elle ne reconnaît ni les personnes ni la TV/musique : fausses prises
  possibles, voix faibles manquables. Aucun profil, mot Alfred ni interruption
  vocale pendant la réponse n'est ajouté.
- Recette v0.4 : 61 tests Python et 25 tests JavaScript, dont contrôleur réel avec
  DOM, micro et audio artificiels et horloge contrôlée. Interface chargée dans le
  navigateur ; le vrai microphone n'a pas été ouvert pendant la recette.
- S12 coché côté logiciel ; S06 reste partiellement ouvert pour l'essai humain,
  le réglage acoustique et le changement de locuteur.

### Évolution v0.5 — lumières Home Assistant prêtes à connecter

- Client REST Home Assistant avec jeton propre à Alfred, protégé DPAPI (Windows)
  ou fichier privé 0600 (Linux), jamais renvoyé à l'interface.
- Test de connexion réel (nom, version, nombre de lumières, allumées), commande
  d'extinction de la maison, de la pièce du terminal ou d'une pièce nommée via
  `area_entities` Home Assistant.
- Analyse stricte des ordres de lumière : accents, politesse, « toutes/partout/maison »,
  pièce optionnelle. Une phrase mixte n'est pas exécutée comme commande partielle.
- Voie directe dans la conversation : la commande est exécutée localement, la réponse
  courte est prononcée, et aucun appel Command Code n'est effectué. Utilisable aussi
  sans clé IA configurée.
- Recette : 29 tests synchrones réussis avec Home Assistant simulé (analyse, jeton
  chiffré, comptage, ciblage des lampes allumées, modèle de pièce, refus 401/403,
  verrou de concurrence, API de configuration). Vérification des routes et import
  contrôlés.
- Retour utilisateur après relance : « c'est bon ça fonctionne », puis confirmation
  explicite que les lampes se sont éteintes sur ordre. Le panneau, la connexion
  réelle au Home Assistant, l'exécution réelle et le ciblage des lampes sont donc
  validés par l'essai du 26 octobre ; aucune mesure de latence ni comptage des
  lampes n'a été relevé.
- Limites : pas d'exclusion de lampes,
  pas de permissions par profil, pas de reprise après coupure réseau en cours de
  commande, et le nom de zone doit correspondre exactement.
- Recette HTTP interne (TestClient) non rejouée dans cette session : le bac à sable
  bloque désormais l'initialisation asynchrone et la validation automatique des
  accès hors bac à sable a dépassé son délai. Les tests synchrones font foi pour la
  logique ; le parcours HTTP complet reste à rejouer.

### Préparation v0.6 — socle des profils vocaux, non exposé

- Le schéma SQLite passe en version 2 avec deux tables : profils (nom unique, rôle
  adulte ou enfant) et empreintes (vecteur, dimensions, modèle, durée). La migration
  depuis la version 1 conserve les échéances existantes.
- Seules les empreintes sont enregistrées par ce module ; aucune capture, aucun
  écran, aucune reconnaissance et aucun moteur d'empreinte ne sont branchés. La
  conservation éventuelle des échantillons audio et le nombre de passages restent
  à décider lors du cadrage de l'enrôlement.
- Recette : 7 tests synchrones réussis (cycle de vie, noms et rôles, moyenne des
  empreintes, comparaison et seuil, suppression des empreintes, migration depuis la
  version 1, refus d'une version inconnue).

### Évolution — enrôlement des profils vocaux

- Écran **Les profils** : création (prénom, rôle), enrôlement guidé des six passages,
  réécoute du dernier échantillon, suppression complète.
- API : liste et création, renommage, suppression, enrôlement WAV, échantillons,
  identification diagnostique renvoyant des scores sans décider d'une identité.
- Stockage : schéma SQLite 2, WAV d'origine et empreintes, hors Git, supprimés avec le
  profil. Le calcul d'empreinte est sérialisé et reste local.
- Recette : 105 tests Python réussis et 1 ignoré, dont 12 nouveaux ; parcours HTTP réel
  sur le service local (création, deux enrôlements, réécoute, identification, suppression).
- Limites : aucun lien avec la conversation, aucun seuil validé. Mesure sur voix
  synthétique : 0,84 pour la même voix contre 0,93 entre bruits sans rapport, ce qui
  impose une normalisation et une calibration par personne.

## Points ouverts — propositions non encore validées

- 15 novembre : l'utilisateur demande un avis sur **Jev de TypeSafe AI**
  (nom précisé après « GEV »), sans autoriser son intégration. Piste à évaluer :
  choix parmi des intentions/cibles connues ou classement de résultats. La
  documentation officielle décrit des décisions typées, pas la génération de
  paramètres libres ni de réponses conversationnelles. Un routage suivi du même
  appel IA pourrait ajouter de la latence sans économie. Recommandation proposée :
  essai isolé seulement si un appel IA peut être évité, avec mesure en français,
  contexte, négations, ambiguïtés et demandes multiples ; aucune modification
  du parcours courant. Coût réel, latence depuis le domicile et calibration sur
  les usages Alfred non mesurés. Sources : https://docs.typesafe.ai/introduction
  et https://docs.typesafe.ai/primitives/choice ; suivi O07.

- Base de prototype validée sur le principe dans `PROPOSITION_TECHNIQUE.md` :
  faster-whisper local, Piper, SpeechBrain ECAPA et service autonome Python.
  Commencer par un prototype navigateur ; les essais conditionnent l'adoption
  définitive des moteurs. Firmware et modèle de réveil restent à prototyper.

### Essai matériel demandé le 26 octobre 2026

- L'utilisateur demande un protocole court de test vocal/audio en conditions
  semi-réelles, avec commande d'une lumière et éventuellement une question.
- Protocole proposé dans `PROTOCOLE_TEST_AUDIO.md` ; connexion à HA et contrôle
  des lumières confirmés par l'utilisateur. Mesures audio et distances à relever.
- Retour utilisateur : réveil plutôt satisfaisant au calme, compréhension médiocre
  en parlant normalement/un peu vite, avec par exemple « salon » transcrit
  « service ». STT déclaré : Home Assistant Cloud ; configuration non inspectée.
- L'utilisateur confirme que ces retours concernent le firmware de jyoushiki
  installé depuis son site. Version annoncée par l'utilisateur : **2.0** ; suffixe
  exact et canal non inspectés.
- Avec de la musique : besoin de parler très fort, réussite estimée à une fois
  sur quatre même ainsi. Précision utilisateur : musique de fond jugée peu forte,
  jouée par **l'ampli externe**, parole à environ **1,50 m**, et **mot de réveil
  non reconnu**. Estimation informelle, niveau sonore non mesuré.
- Distinguer l'échec du réveil local de la mauvaise transcription après réveil.
  Le STT Cloud n'est pas responsable de la décision locale de réveil. Tester le
  démarrage par bouton dans le même environnement pour séparer ces deux étapes.
- Retour après essai par bouton : la transcription semble utilisable, mais il faut
  bien articuler. Aucun nombre de réussites ni transcription exacte relevés.
  Cela renforce la piste d'une difficulté de réveil sans démontrer que la captation
  audio ou la transcription à débit naturel sont satisfaisantes.
- Inspection MCP HA du 26 octobre, en lecture seule : appareil Waveshare Voice
  eb05fc disponible, firmware installé **v2.0.0** (version stable proposée identique),
  réveil actif **Alexa**, second réveil désactivé, sensibilité **Slightly sensitive**,
  gain micro post-AFE **13**, détection de fin de parole **default**, microphone
  non muet, assistant sélectionné **Home Assistant Cloud**. Aucun réglage modifié.
- Après changement par l'utilisateur, sensibilité **Moderately sensitive** et
  gain **13** confirmés par MCP. L'utilisateur rapporte que cela semble mieux ;
  amélioration qualitative, sans comptage des réveils ou faux déclenchements.
  Aucun changement réalisé par l'assistant.
- L'utilisateur reporte la suite des essais audio à plus tard et demande de
  poursuivre la préparation de la solution. Suivi en T01 dans `CHECKLIST.md`.
- L'attribution au STT Cloud est une hypothèse de l'utilisateur, pas un diagnostic
  établi. Captation, traitement audio, découpage de parole et moteur STT à isoler.
- Piste de banc d'essai, non validée comme architecture Alfred : firmware
  communautaire ESPHome de jyoushiki pour cette carte, Assist, Speech-to-Phrase
  et Piper en français. Le dépôt annonce une installation précompilée par navigateur,
  une version stable v2.0.0, deux micros et une annulation d'écho ; documentation
  consultée le 26 octobre, fonctionnement sur notre exemplaire à vérifier.
- Sources : <https://github.com/jyoushiki/esphome-waveshare-esp32-s3-audio-va>,
  <https://www.home-assistant.io/voice_control/voice_remote_local_assistant/>.
- Le réveil temporaire « OK Nabu » est proposé pour ce test seulement. Le réveil
  « Alfred », les profils et la fenêtre de huit secondes restent à prototyper.

- Informations sensibles : catégories, confirmation et visibilité entre profils.
- Actions soumises à confirmation orale et réglages par défaut.
- Changement de locuteur : reconnaissance incertaine, reprise de contexte et
  traitement des informations déjà prononcées dans une conversation partagée.

Autres points à traiter avant de figer l'architecture :

- Services de reconnaissance et synthèse vocales, voix française retenue,
  reconnaissance des locuteurs et mot de réveil personnalisé.
- Hébergement, ressources CPU/RAM, latence mesurée et budget partagé avec le
  développement via Command Code ; plafond réel des dépenses supplémentaires.
- Recette réelle de la recherche web (fournisseurs décidés le 16 novembre), modalités des rappels/listes de courses/annonces et connexion
  à leurs données.
- Plusieurs terminaux entendant la même demande, interruption, reprise du volume,
  annonces et minuteurs à plusieurs utilisateurs.
- Administration web, accès et protection des mémoires ; enrôlement des voix.
- Conservation et suppression des données, sauvegarde, déploiement et mises à jour.
- Critères mesurables de réussite et tests en bureau puis salon : réveil sur Alfred,
  absence de réveil sur Fred, bruit/musique, enfant, invités et locuteurs incertains.

### Évolution v0.6 — commandes de minuteurs du banc navigateur

- Le 27 octobre, l'utilisateur choisit de développer les minuteurs à distance.
- Commandes directes texte/voix ajoutées sans LLM ni HA : création avec durée,
  consultation du temps restant, annulation et Stop. SQLite et reprise existants
  réutilisés ; l'étage doit être choisi explicitement dans le formulaire du banc.
- Choix d'implémentation du prototype, à confirmer à l'usage : consultation et
  annulation sur l'étage courant ; annulation de l'unique minuteur actif sinon
  clarification puis choix par numéro stable. Pas d'annulation collective implicite.
- Une phrase contenant « minuteur » qui n'est pas reconnue intégralement reçoit
  une clarification sans exécution ni appel IA. Un échec TTS après enregistrement
  signale que le suivi doit être consulté avant de renouveler la commande.
- Recette : 133 tests Python réussis, 1 intégration vocale réelle optionnelle non
  activée, 26 tests JS réussis. Tests HTTP hors du bac à sable Windows pour contourner
  le blocage asyncio ; voix, IA et HA simulés. Essai humain restant.
- Les échéances restent silencieuses dans ce banc. Diffusion ESP32, permissions
  par personne et intégration de ces commandes dans HA ne sont pas raccordées.

### Extension du 27 octobre — sonnerie sur le satellite du bureau

- À la demande de l'utilisateur, Alfred utilise les actions ESPHome existantes
  de la carte Waveshare `eb05fc`, dans Bureau / RDC selon Home Assistant 2026.10.4.
  La carte était visible et au repos ; firmware constaté v2.0.0. Les actions de
  démarrage et d'arrêt sont présentes et accessibles au compte HA d'Alfred.
- Configuration locale du RDC activée et service HTTPS redémarré sans échéance
  active. Sonnerie par étage à l'échéance, arrêt au dernier Stop ou annulation,
  sans doublon lors d'une réponse perdue, sans sonnerie tardive au redémarrage.
  Le firmware prévoit une coupure après quinze minutes. Le journal de commande
  permet de demander l'arrêt après redémarrage ; l'état de l'interface distingue
  requête envoyée et erreur sans prétendre que le son a été entendu.
- Recette simulée : 142 tests Python réussis, 1 vocal réel optionnel non activé,
  26 tests JS réussis ; test supplémentaire de nouvelle échéance après quinze
  minutes réussi. Son réel, arrêt depuis la carte et multi-terminaux à valider.
- Limite : cette sonnerie est partagée avec les minuteurs Assist ; un arrêt géré
  directement sur la carte ou par Assist ne met pas encore à jour Alfred.
- Source du firmware installé :
  <https://github.com/jyoushiki/esphome-waveshare-esp32-s3-audio-va/blob/v2.0.0/waveshare-va.yaml>.

## Journal des décisions

- 27 novembre 2026 : l’utilisateur demande de gérer l’option automatique, la
  recherche manuelle et la mise à jour forcée depuis Alfred. Implémentation
  pour le paquet Debian : un worker système utilise la source APT d’Alfred
  et les interventions dans l’interface demandent un code administrateur.
  L’automatique démarre désactivé. Activé, il vérifie à 4 h (heure du serveur).
  La mise à jour forcée vérifie et installe immédiatement une version
  supérieure, indépendamment de cette option. Publication et recette sur la
  VM restent à faire.

- 24 novembre 2026 : réglages de réveil du bureau sauvegardés localement avant
  l'ajustement du satellite déplacé. Ajout de « Al Fred » aux variantes STT du
  réglage actif. La validation au nouvel emplacement reste ouverte.

- 23 novembre 2026 : première publication du code sélectionné sur GitHub (bb7070d), avec maintien de la visibilité privée.

### 22 novembre 2026 — couleurs du satellite

Anneau éteint par défaut en veille. Couleurs de dialogue réglables depuis la
PWA et envoyées au satellite par Alfred via la connexion existante. Un effet
au choix par état, appliqué lorsque les LED de cet état sont allumées.

### 22 novembre 2026 — reprise sur demande de réponse

Huit secondes après la lecture pour une confirmation ou une précision.
Une réponse complète termine la prise conversationnelle.

### 21 novembre 2026 — deux types d’éclairage

La fiche propose Principal et Secondaire. Principal est le type par défaut.

### 21 novembre 2026 — catalogue repliable par pièce

Une ligne déplie ou replie les entités de chaque pièce dans le catalogue
Maison et appareils de la PWA.

### 21 novembre 2026 — rubriques des paramètres dans le volet desktop

Les rubriques remplacent la navigation principale à gauche. Chaque rubrique
ouvre son contenu à droite, avec Apparence sélectionnée à l’entrée.

### 21 novembre 2026 — présentation desktop de la PWA

Volet de navigation permanent à gauche et adaptation des écrans au format 16:9.
Présentation mobile et état des écrans partagés avec la version desktop.

### 20 novembre 2026 — affichage de la pièce d’origine

Afficher directement le nom de la pièce Home Assistant dans le sélecteur,
avec une petite maison à côté quand cette pièce est sélectionnée.

### 20 novembre 2026 — fiche d’édition des appareils

Le tableau et les lignes mobiles récapitulent les réglages. Le crayon ouvre une
fiche avec Valider et Annuler. Les nouvelles pièces sont choisies dans le registre
Home Assistant ; les réglages Alfred existants sont repris au premier enregistrement.

### 20 novembre 2026 — pièce des appareils utilisée par Alfred

L’utilisateur demande une affectation éditable dans la page Domotique, y
compris pour les appareils sans pièce. Elle est propre à Alfred.

### 20 novembre 2026 — nom des appareils utilisé par Alfred

L’utilisateur demande un nom distinct pour Alfred et choisit « Imprimante »
pour « PC_salon Commutateur ». Le nom personnalisé est partagé entre les
interfaces et géré dans Alfred.

### 18 novembre 2026 — formulations des minuteurs, musique et température

Supprimer les numéros prononcés pour les minuteurs. Enregistrer un nom et une
durée réutilisables depuis l’interface. Annoncer titre et artiste pour le morceau
en cours lorsqu’ils sont disponibles. Donner la température dans une phrase
directe. L’utilisateur demande des exemples pour les courses, rappels et annonces.

### 18 novembre 2026 — périmètre des consultations de lumières

L’utilisateur valide toute la maison par défaut, la pièce du terminal pour
« ici » et le lieu demandé lorsqu’il est explicite. Décision propre à la lecture.

### 18 novembre 2026 — noms des lumières allumées

Inclure directement les noms de toutes les lumières allumées dans la réponse,
même lorsque la question porte sur leur nombre.

### 18 novembre 2026 — affichage des échanges dans la PWA

L’utilisateur demande de supprimer le texte sous le champ de saisie et de
traiter ensuite les réponses sur les lumières. Pour cette future étape, résumer
les lumières allumées. Si aucune ne l’est, répondre « Aucune lumière n’est
allumée. » Si une seule l’est, indiquer son nom.
Après la correction, l’utilisateur confirme que l’affichage fonctionne et ouvre
le cadrage du format des réponses.

### 17 novembre 2026 — activation du relais IA des appareils

- À la demande de l'utilisateur, activation locale du relais `devices` après
  diagnostic du refus sur l'imprimante et tests simulés. Confirmation réelle
  vérifiée via le modèle en texte, annulation puis allumage après accord ; état
  activé relu. Compréhension vocale humaine et recette des autres appareils
  ouvertes ; chauffage et applications TV restent exclus.

### 17 novembre 2026 — fiabilisation de la synthèse Internet

Après retour utilisateur et reproduction de l'erreur de génération, désactiver
la réflexion pour le seul résumé documentaire DeepSeek V4. Modèle, outils,
plafond de sept cents jetons et protections conservés. Les réponses tronquées
restent refusées, avec une erreur spécifique et un journal sans contenu privé.
Tests de non-régression et essais réels documentés dans S07.

### 16 novembre 2026 — recherche Internet en trois modules

Plan validé puis implémentation demandée : actualités à la demande, météo avec
commune locale et culture générale avec recherche selon besoin. Open-Meteo et
Tavily retenus, priorité au gratuit, réponses brèves et liens dans l'interface.
Validation logicielle distincte des essais Tavily réels et de l'écoute humaine ;
suivi S07. Aucun nouvel abonnement ni clé demandé dans le chat.

- 16 novembre : validation de la confirmation des équipements sensibles. Le
  panneau Domotique ajoute une colonne de confirmation et un stockage local ;
  toutes les actions modificatrices sont concernées, y compris les helpers, les
  lecteurs, les aspirateurs et les membres de groupes. Les lectures et le panneau
  Musique restent directs. Une commande globale est confirmée en une fois. Le
  oui/non est traité avant l'IA et expire après trente secondes. Vérification :
  867 tests Python réussis, 2 ignorés ; 46 tests JavaScript réussis. Aucun appareil
  réel actionné pendant les tests ; recette humaine clavier/micro restante.

- 16 novembre : correction après signalement du clignotement rouge sur une demande
  de température du salon. Le catalogue réel ne contient aucune sonde associée au
  salon. Les lectures sans correspondance, ambiguës ou indisponibles renvoient une
  clarification normale dans la conversation, sans erreur technique du terminal.
  Les sondes et leurs pièces sont transmises au modèle avec l'outil de lecture.
  100 tests ciblés réussis ; essai vocal humain restant à confirmer.

- 16 novembre : la lecture des températures est raccordée au modèle configuré par
  un outil `lire_temperature` distinct, strictement en lecture et indépendant du
  relais des appareils. Le modèle reste l'interprète principal des demandes
  vocales et textuelles ; l'outil reçoit une pièce, un nom de capteur ou « ici » et
  reprend les contrôles d'exposition, d'exclusion et de groupe du catalogue.
  Le parcours local, utilisé sans modèle, reconnaît désormais « au bureau »,
  « à la chambre parentale », « quelle température fait-il… », « il fait quelle
  température… » et « combien fait-il… ». Un nom de pièce partiel ambigu, par
  exemple « chambre » avec deux chambres, demande une précision au lieu d'inventer
  une sonde. Vérification par 818 tests Python réussis et 2 ignorés ; la recette
  réelle de la sonde du bureau par l'outil donne 19,1 °C sans écriture. La recette
  conversationnelle réelle en texte utilise bien l'outil et renvoie 19,1 °C. La
  recette vocale humaine reste à confirmer dans F15.

- 15 novembre : adoption du satellite Wi-Fi/prise USB et préparation OTA
  autorisées. Détection et choix du mot restent sur le serveur, modifiables dans
  l'interface. Reprise persistante de la veille avec respect de l'arrêt volontaire
  et du transfert navigateur ; firmware v2.0.0 conservé sans flashage.

- 14 novembre : F30, secours VAD ajouté après récidive lors de phrases successives.
  Une énergie audio soutenue peut maintenant amorcer la transcription de veille
  même si Silero rejette le signal. Le STT doit toujours reconnaître le mot
  d'appel en tête ; le bruit seul n'exécute aucune commande. Mesure du recours
  au secours ajoutée. Hypothèse de filtrage de parole en amont encore à vérifier,
  sans affirmer que ce changement résout définitivement le gel observé.

- 14 novembre : récidive F30. Les nouveaux relevés écartent le verrou orphelin
  pour ce cas : détecteur non verrouillé et non occupé, aucune analyse en attente,
  micro reçu, trois analyses et trois détections, aucune requête IA active. La
  correction précédente ne suffit donc pas à expliquer cet incident. Ajout de
  niveaux PCM instantanés (crête/RMS, durée de zéros exacts) et probabilité VAD,
  sans conservation d'audio. Après relance, un réveil, une réponse et une reprise
  de conversation ont été observés. Cause de la récidive toujours à isoler ; ne
  pas déclarer le gel résolu sur la seule base des tests ou du flux réseau.

- 14 novembre : incident ESP32 signalé comme transcription bloquée pendant deux
  minutes. Relevé : phase `waking`, micro reçu, modèle libre, deux inférences de
  veille et deux détections, santé affichée `ok`. Réarmement effectué sans action
  domotique. Cause précise non prouvée faute d'état interne du détecteur dans
  l'ancienne télémétrie. Cas de panne identifié et corrigé : un réveil refusé
  laisse le détecteur STT verrouillé. Refus explicite désormais suivi d'une remise
  à zéro ; supervision d'un verrou orphelin après six secondes en veille, hors
  capture et traitement actifs. Exposition d'indicateurs busy/latched/pending/VAD,
  sans texte ni audio. Récupération automatique à confirmer en usage réel.

- 14 novembre : commandes de lumières avec exceptions demandées par l'utilisateur.
  « Éteins toutes les lumières sauf celles du bureau et du salon » préserve les
  pièces citées et n'éteint que les autres lumières encore allumées. Le LLM
  transmet `exclude_rooms` et/ou `exclude_entities` (noms, alias ou identifiants) ;
  Alfred soustrait les feuilles concernées après résolution des groupes, puis
  vérifie les cibles et les états avant envoi. Une exclusion inconnue bloque
  l'exécution. Essai réel DeepSeek avec HA entièrement simulé : Bureau et Salon
  correctement exclus, seule Cuisine éteinte. Aucun éclairage réel actionné.

- 14 novembre : décision validée — le modèle Command Code déjà configuré devient
  l'interprète principal de toutes les demandes vocales et textuelles (minuteurs,
  lumières, musique, courses et conversation). Les outils sont exécutés après
  validation. Le traitement local immédiat concerne l'arrêt de sonnerie, les
  mécanismes d'interruption et les extinctions globales explicites décrites
  dans la décision du 20 novembre, ainsi que les allumages explicites décrits
  dans la décision du 23 novembre.
  Le contexte du modèle inclut les minuteurs actifs de l'étage. Sans configuration
  IA, les commandes locales historiques restent disponibles ; une erreur du
  modèle configuré ne déclenche pas une deuxième exécution par un parseur.
  Aucun modèle local de langage ajouté.

- 22 novembre : établir un état de référence avant de décider du raccourci
  local pour les allumages explicites. Banc retenu sur l’ESP32 et les lampes
  réelles, cinq formulations et trois essais par formulation. Le taux de
  réussite au premier énoncé doit se maintenir après optimisation. Dans les
  diagnostics antérieurs, huit allumages ESP32 confirmés via Command Code
  donnent une médiane de 0,95 s de STT et 3,59 s du bloc modèle et Home
  Assistant cumulé. Ces valeurs ne datent pas l’allumage physique.

- 23 novembre : référence réelle complète sur l’ESP32 et les lumières de
  la cuisine. Les cinq formulations réussissent chacune 3/3 du premier coup,
  au total 15/15 via Command Code. Médianes : pause de fin de capture 0,91 s,
  transcription 0,85 s, envoi au modèle jusqu’à l’outil complet 2,21 s,
  décision jusqu’au premier envoi HA 0,26 s, premier envoi jusqu’au dernier
  état `on` 77 ms. Le délai fin de parole détectée jusqu’au dernier état
  `on` est de 4,42 s en médiane, de 3,85 à 5,71 s. Quatre lectures du
  catalogue précèdent le premier envoi sur chaque essai, dont une pour préparer
  le contexte du modèle.

- 23 novembre : raccourci local validé pour les allumages explicites de lampes
  ou de pièces résolues dans le catalogue. Une formulation libre ou une cible
  ambiguë est transmise à Command Code avec la même transcription. Le raccourci
  utilise le même exécuteur, avec revérification des cibles et confirmations.
  Une écriture non confirmée n’est pas renvoyée au modèle.
  Comparaison réelle du 23 novembre : 10 allumages locaux, 4 exécutés via
  Command Code et 1 tour sans action tracée. Sur les 10 essais passés en local,
  la médiane fin de parole détectée jusqu’au dernier état `on` passe de 4,35 s
  sur les essais de référence correspondants à 2,24 s. La formulation libre
  reste proche de 4,91 s. Le critère de fiabilité reste ouvert : 14/15 réussites
  attestées par le banc, contre 15/15 avant. Le STT a transcrit « la fumée » à
  la place de « la cuisine » sur l’essai sans commande tracée, malgré un
  allumage déclaré. Une autre transcription a omis « de » dans « plan de
  travail » et le modèle a allumé la bonne lampe.

- 23 novembre : accepter l’omission de « de » dans un nom de lampe si la
  correspondance reste unique dans le catalogue. Pour un allumage explicite
  avec une pièce inconnue, Alfred demande « Dans quelle pièce ? » et conserve
  l’ordre trente secondes dans la même session et le même profil. Le nom de
  pièce donné ensuite est résolu et vérifié avant envoi. Un nouvel ordre ou
  une annulation met fin à l’attente.
  Essai du dictionnaire Parakeet limité à « cuisine » : sur des WAV synthétiques,
  le nom de la pièce passe de 16/24 à 18/24, les témoins restent à 13/18 et six
  formulations supplémentaires avec « fumée » ou « usine » restent inchangées.
  La reconnaissance du mot seul ne valide pas l’ordre complet. Recette humaine
  à refaire avec d’abord le diagnostic STT sans action, puis le banc d’allumage.

- 20 novembre : « éteins toutes les lumières » sans lieu vise toute la maison,
  y compris avec « lumière » au singulier dans la transcription. Une pièce
  utilisée pour désigner une lampe dans « sauf… » qualifie l'exception.
  Si la lampe reste à identifier, Alfred demande quelle lampe préserver et
  conserve la commande globale dans la session et le profil courants pendant
  trente secondes. Le choix relance la validation des cibles, exclusions et
  autorisations avant exécution. L'annulation, une nouvelle demande ou
  l'expiration met fin à l'attente.

- 14 novembre : l'utilisateur précise que l'objectif est une compréhension
  résiliente, pas des corrections successives de phrases. Les commandes locales
  certaines restent rapides ; les formulations de minuteurs non reconnues sont
  confiées à l'interprétation IA via les outils typés existants. Les consignes
  qui invitaient systématiquement à reformuler sont supprimées. L'opération
  `remaining` distingue le temps restant du courant de la liste complète. Aucune
  durée ni aucun numéro ne doit être inventé ; clarification si nécessaire.

- 14 novembre : deuxième retour terrain F27, formulations « On met un minuteur
  de deux minutes » et « Il reste combien de temps sur le minuteur ? » rejetées.
  Grammaire locale élargie à ces tournures ; consultation courante préservée dans
  l'exécuteur local, au lieu d'une conversion en liste complète. Vérification par
  la route vocale avec transcription simulée et plusieurs minuteurs. L'essai
  acoustique devant l'ESP32 reste distinct des tests logiciels.

- 14 novembre : correction complémentaire F27. Le service de minuteurs reconnaissait
  « quel temps reste-t-il sur le minuteur » sans numéro, mais le raccourci vocal
  local filtrait encore cette formulation et affichait une demande de durée. Une
  fonction partagée reconnaît désormais la question du minuteur courant sur les
  deux chemins. Il reste à prononcer cette phrase devant l'ESP32 pour la recette
  acoustique ; l'essai HTTP du service actif a répondu au temps restant puis annulé
  le même minuteur sans appel IA.

- 14 novembre : retour utilisateur sur les minuteurs. Décision de commande :
  une demande au singulier sans numéro conserve un contexte courant — priorité
  à la sonnerie active, puis au minuteur créé le plus récemment à l'étage du
  terminal ; toute demande explicitement plurielle continue d'exiger un numéro.
  « Annule le minuteur » confirme le numéro choisi. Une sonnerie ESP32 se coupe
  localement au mot de réveil seul ; la reconnaissance est traitée par la carte
  avant toute commande réseau. Ne pas prétendre que la phrase « Alfredo, stop »
  arrive au serveur pendant la sonnerie après le réveil local. Il faut prononcer
  « Alfredo » seule, puis attendre l'arrêt du son. Recette acoustique du réveil
  pendant le timbre restant à confirmer ; aucun flashage. Suite complète : 778
  Python réussis/deux ignorés et 43 JS réussis. Service relancé, ESP32 identifié,
  veille active et santé transport/micro/détecteur `ok`.

- 13 novembre : l'utilisateur demande de réaliser les optimisations sans
  intervention pendant son sommeil. Lot de fond livré : santé du terminal sans
  contenu privé, incidents et renouvellements distingués, catalogue HA et statistiques
  partagés, actualisation uniquement du panneau visible, cache d'assets versionnés,
  certificat de développement renouvelé avec douze mois de validité, et première
  synthèse anticipée livrée pour le navigateur sur phrases complètes. Le moteur
  Phonon, les seuils/profils et les actions restent inchangés ; le mode standard
  reprend la main après toute erreur anticipée. Le stream anticipé reste sans
  réponse HTTP LAN pour la carte pendant cette étape. Service redémarré, ESP32
  identifié, veille active, 255 488 octets reçus en huit secondes, `health` API 200
  et transport/micro/détecteur `ok`. Suite finale 777 Python réussis/deux ignorés
  et 43 JS réussis. Validation acoustique réelle, annulation native et mesure
  p95 encore ouvertes. Ancien certificat conservé sous `.local/https`.

- 13 novembre : après l'audit, l'utilisateur demande un plan pour réaliser les
  améliorations. Plan livré dans `docs/PLAN_OPTIMISATIONS.md` (A10) : lot 0
  reprise/référence puis supervision/mesures, catalogue HA, interface/HTTPS,
  streaming vocal, sorties audio communes, vue quotidienne et exploitation.
  Dépendances de démarrage distinguées des validations finales pour éviter de
  bloquer O01 sur la recette T10, O03 sur la clôture S19 et O05 sur la totalité A01.
  L'ordre détaillé, les objectifs chiffrés et les règles de priorité audio restent
  proposés ; cette demande prépare la réalisation sans lancer les modifications.
  Conservation des moteurs actuels ; recettes humaines, reports et disponibilité
  de l'hôte Debian restent explicitement nécessaires aux validations concernées.

- 13 novembre : demande utilisateur d'un tour global et de propositions
  d'optimisation. Audit livré dans `docs/AUDIT_OPTIMISATIONS_2026-11-13.md` :
  769 tests Python réussis/deux ignorés, 43 JavaScript réussis ; routes de statut
  environ quatre à douze millisecondes au repos sur trois lectures locales,
  catalogue HA 43 entités/80,8 ms sur une lecture. Ce ne sont pas des mesures
  de latence vocale ni des p95. Certificat expiré le 3 novembre reconfirmé (A08).
  Inspection visuelle Firefox bloquée par l'outil Windows ; ergonomie analysée
  dans les sources seulement. O01–O06 sont des propositions non validées :
  stabilité/mesures, catalogue partagé, streaming, actualisations, interface et
  maintenance. Aucun moteur, réglage, accès, appareil ou service modifié par
  cette revue ; ordre conseillé distinct des priorités validées et reports.

- 13 novembre : l’utilisateur signale un gel de l’écoute ESP32 après quelques
  commandes, débloqué par arrêt puis réactivation. Au diagnostic, Bureau est
  connecté et transmet ; le gel n’est pas reproduit sur la carte à cet instant.
  Le pont relançait `start_va` sans arrêt préalable lorsqu’une session était
  bloquée ; le code ESPHome 2026.9.0 ignore ce départ hors IDLE. Une notification
  de fin de lecture perdue pouvait aussi laisser la phase `playing` sans garde.
  Correction logicielle de la récupération livrée (T10) : arrêt puis relance
  bornés, délai de trois cents millisecondes, garde de fin de lecture et compteur
  technique sans contenu privé. Suite complète : 768 réussites/deux ignorés ;
  36 tests réveil réussis après ajout du cas arrêt en échec puis récupération.
  Service relancé sans flashage ni changement des réglages de réveil.
  Après redémarrage : Bureau identifié, veille réarmée, 256 512 octets reçus
  en huit secondes, aucune erreur ni récupération intempestive au contrôle.
  Validation humaine prolongée restant ouverte.
  État réel au diagnostic : réveil STT, phrase « Alfredo » ; les sélections
  historiques Alfy/Jarvis ne décrivent donc pas le réglage actif de ce relevé.

- 13 novembre : l'utilisateur valide la musique en usage réel et demande la suite.
  Minuteurs raccordés à la compréhension naturelle ; ancien stockage et sécurité par
  étage conservés ; aucune nouvelle architecture de sonnerie ni de rappel HA.


- 13 novembre : l'utilisateur demande de passer aux fonctions suivantes après les
  lumières. Lot musique/volume livré en premier selon le plan, minuteurs ensuite.
  Aucune modification des modèles audio ou Command Code.


- 13 novembre : l'utilisateur valide le pilotage des groupes de lumières. Le groupe
  exposé autorise ses descendants pour ses commandes, même s'ils ne sont pas exposés
  individuellement. Exclusions explicites toujours prioritaires ; les descendants
  masqués ne deviennent pas des cibles autonomes. Aucun réglage HA modifié.


- 13 novembre : plan de compréhension naturelle approuvé avec instruction d'implémenter.
  Modèle et audio conservés ; outil IA borné et exécuteur commun pour les lumières,
  contexte partagé et diagnostic local. Propositions implicites à confirmer ; lots
  de quatre actions préparés avant envoi, arrêt sans retry après résultat incertain.
  Livraison progressive : premier lot lumières mis en service, historique I05
  raccordé, outils minuteur/appareil préparés mais désactivés. Validation au modèle
  configuré sur cent cas synthétiques distincts : cent réussites, p95 2,476 s sur
  texte/appareils simulés. Recette humaine/vocale et objectif de 99 % restent ouverts.


- 13 novembre : demande de souplesse confirmée après refus avec politesse et point
  final. Remplacement des nettoyages divergents par un traitement oral commun ;
  ponctuation et variantes de politesse prises en charge avant résolution des cibles.
  Les valeurs des helpers texte conservent leur ponctuation. Recette humaine ouverte.


- 13 novembre, capture ESP32 : « On éteint la lumière du bureau. » arrive encore
  à la conversation. Reconnaissance directe étendue aux formes « on éteint »,
  « on allume » et à l'homophone « éteint » pour les lumières ; contrôle des cibles
  et exclusions conservé. Essai humain après correction restant (F21).


- 13 novembre : diagnostic d'un refus IA sur une demande de lumière conversationnelle.
  Le routage direct n'acceptait pas « tu peux m'allumer… » ; l'instruction IA disait
  encore à tort que les lumières n'étaient pas connectées. Extension des préfixes
  interrogatifs et correction de cette consigne, sans ajout d'outil domotique au LLM.
  « luniere » figure dans le retour utilisateur ; pas de correction approximative
  des noms d'appareils, transcription exacte et nouvel essai humain à vérifier (F21).


### 13 novembre 2026 — recette Alfredo prête à générer

- À la demande de l'utilisateur, `training-alfredo.yml` créé dans son dépôt
  WSL `~/wakeword-generator`, avec nom `alfredo_v1`, graphies Alfredo/Alfrédo
  et négatifs dont Fred. `training-alfy.yml` conserve la recette Alfy ;
  `training.yml` inchangé. Chargement des recettes vérifié par le générateur,
  paramètres de calcul conservés. Après écoute des clips, l'utilisateur corrige
  la prononciation souhaitée : **al-frè-do**. Recette courante passée à
  `alfredo_v2`, graphies **Alfrèdo, Alfreido, Alfraido**, anciennes graphies
  retirées. Recette v1 sauvegardée dans `training-alfredo-v1.yml` ; clips existants
  conservés. Chargement v2 vérifié ; nouvelle écoute et qualité acoustique ouvertes.

### 13 novembre 2026 — activation du modèle Alfy v1 fourni

- Demande utilisateur : utiliser `docs/alfy_v1.onnx` (205 430 octets). Import
  par l’API existante, validation ONNX isolée réussie, copie installée identique
  vérifiée par SHA-256. Sélection openWakeWord pour ESP32 et navigateur, seuil
  initial 0,5 ; navigateur non activé automatiquement.
- ESP32 Bureau identifié et connecté ; veille Alfy armée, flux audio reçu sans
  erreur. Ancien réglage réel : STT Alfredo ; sauvegarde locale avant changement
  sous `.local/backups/wake-before-alfy-v1-20261113.json`. Jarvis reste disponible.
- Aucun changement de code ni flashage. Reconnaissance à la voix humaine, faux
  réveils Fred/TV/musique et distance restent à vérifier.

### 13 novembre 2026 — préparation des réveils Alfy et Alfredo

- L'utilisateur retient <https://github.com/lfpoulain/wakeword-generator> pour
  générer Alfy et Alfredo. Deux recettes distinctes proposées, avec graphies
  françaises et négatifs incluant Fred ; prononciation synthétique à écouter
  avant entraînement. Qualité acoustique, import et choix final restent ouverts.

### 13 novembre 2026 — réveil STT et sélection du mot d'appel

- L'utilisateur demande l'implémentation du réveil STT avec choix du mot pour
  les deux moteurs. ESP32 et navigateur retenus, import openWakeWord, une seule
  source active et Alfy/Alfi prérempli pour le STT. Ce chantier remplace le
  comparatif initial comme priorité ; aucun modèle Alfy openWakeWord entraîné.
- Livré : réglages, WebSocket navigateur, arbitrage, capture sans coupure,
  retrait central du préfixe et vérification stricte de la phrase STT complète,
  import ONNX isolé et borné. Validation : suite complète 594 Python réussis,
  deux ignorés ; 127 ciblés supplémentaires après durcissement du préfixe et
  43 JavaScript réussis. Interface testée avec DOM/micro simulés ; aucun
  navigateur pilotable disponible pour une vérification visuelle réelle.
- Essai Parakeet réel sur audio synthétique Phonon : un réveil, trois analyses,
  dernière analyse 81 ms ; transcription complète 245 ms sur 2,72 s d'audio.
  La transcription complète écrit « Al fit » dans cet essai : variante non
  acceptée automatiquement, à examiner sur la voix humaine avant tout ajout.
  Cela valide le déclenchement technique, pas une commande STT complète pour
  cette graphie ni une fiabilité acoustique domestique.
- Service réel relancé, santé et nouvelles routes HTTP 200 ; réglage ESP32
  Jarvis conservé et navigateur STT Alfy prêt à activer. Canal WSS réel testé
  avec audio synthétique : ready → detected → command, sans IA ni action.
  ESP32 initialement déconnecté au contrôle. Après rebranchement signalé par
  l'utilisateur le 13 novembre : Waveshare Bureau reconnue, connexion établie,
  veille Jarvis/openWakeWord armée, flux micro reçu sans erreur ; une détection
  au compteur. Ce contrôle ne valide pas encore le réveil STT sur voix humaine.
  Certificat de développement expiré signalé par TLS ; contrôles techniques
  effectués avec comparaison stricte au certificat local, sans modifier TLS.

### 13 novembre 2026 — températures, switchs et helpers

- Extension demandée ensuite aux lecteurs multimédias et aspirateurs ; actions
  natives bornées et capacités HA vérifiées. Pièces nettoyables reprises du mapping
  HA existant ; pas de modification de carte ou de configuration de l'aspirateur.

- Lumières vocales confirmées fonctionnelles par l'utilisateur. Extension validée
  aux températures, switchs et six types de helpers courants ; `climate` reporté
  jusqu'au retour au domicile. Tests simulés distincts de la recette réelle ;
  minuteurs HA exclus de cette étape.

### 11 novembre 2026 — sonnerie des minuteurs sur le pont direct

- Depuis la déconnexion de la carte de Home Assistant, `bell-targets.json` était
  vide : un minuteur passait bien en « sonne » mais aucun son n'était produit.
  La sonnerie native du firmware (`start_ringing` / `stop_ringing`), déjà utilisée
  par le banc HA, est désormais commandée par le terminal direct.
- Pour l'étage du terminal, Alfred démarre la sonnerie au premier minuteur en
  état « sonne » et la coupe après le dernier, y compris sur Stop ou annulation.
  Les commandes sont idempotentes ; une réponse perdue est retentée après deux
  secondes, sans double départ ni rejeu d'une échéance au redémarrage. La
  coupure de sécurité de quinze minutes du firmware reste inchangée.
- Un bouton « Tester la sonnerie » et une route locale permettent un essai bref
  de 2,5 s, refusé si un minuteur sonne déjà. Recette : 485 tests Python et
  34 tests JS réussis ; sonnerie de test acceptée par la carte et parcours réel
  d'un minuteur de 5 s vérifié jusqu'à l'arrêt. L'audition du son par l'utilisateur,
  la priorité avec musique et la diffusion vers plusieurs terminaux restent à
  valider (F07/T07).

### 11 novembre 2026 — nettoyage STT terminé

- À la demande de l’utilisateur, seule la chaîne Parakeet/Murmure retenue est
  conservée dans Alfred. Code/configuration de sélection, backend antérieur,
  API/interface/tests/scripts de comparaison supprimés. Modèles et corpus
  obsolètes retirés du projet via la Corbeille ; paquets de l’ancien STT et
  dépendance CTranslate2 désinstallés du venv, résidus nettoyés. L’application
  personnelle Murmure et ses réglages d’origine ne sont pas modifiés.
- Le Silero v6 utilisé pour finir les prises devient un asset autonome contrôlé
  par SHA-256, chargé directement par ONNX Runtime avec les mêmes options.
  Aucun changement des gains, du réveil, du PCM ou de la synthèse retenue.
  Préparation explicite via setup_vad, intégrée à setup_parakeet ; aucun
  téléchargement ou installation pendant une écoute.
- 480 tests Python et 17 tests JS ciblés réussis, 2 tests optionnels ignorés.
  Phrase publique témoin transcrite correctement en 217 ms après désinstallation,
  VAD réel sans parole sur silence. Sources Rust conservées, tests précédents
  96/96. Service relancé au repos/veille : Parakeet prêt, ESP32 connecté, veille
  précédemment active réarmée et réception confirmée. Routes et interface de
  comparaison absentes, voix Dumby conservée. Aucun micro de diagnostic ni
  commande de maison lancé. S03 reste ouvert pour charge/bruit/distance/Debian.

### 11 novembre 2026

- L’utilisateur demande de supprimer toutes les voix non Phonon. Retrait des
  choix Henri/Cloud, Pocket, Supertonic/référence, Chatterbox, Sopro et Melo/OpenVoice
  dans le registre, le sélecteur et l’API ; anciennes requêtes désormais 422.
  Chargements et synthèses des anciens moteurs, statuts spécifiques et replis
  retirés de VoiceService. Le worker local ne charge que Phonon, sans PyTorch.
  Dumby reste actif/par défaut ; ancien choix enregistré retiré ramené à Dumby,
  jamais à un ancien moteur. Pas de désinstallation globale ou suppression des
  références historiques conservées sous .local. Bibliothèques partagées avec
  d’autres fonctions et intégration HA de la maison non supprimées.
  Tests adaptés au retrait (dont refus des anciens identifiants et maintien des
  quatre profils), 480 tests Python réussis, 2 optionnels ignorés ; 34 tests JS.
  Service relancé : quatre voix Phonon seulement, anciens identifiants refusés,
  synthèse Dumby HTTP 200 en 307 ms / 3,2 s sans repli. Jarvis actif et flux reçu.

- L’utilisateur juge le profil précédent moins adapté, fournit un nouvel export
  et demande de l’appeler **Dumby**. Nouveau profil importé sous .local, séparément
  des versions Alfred 1/2 conservées. Choix `phonon-dumby-cpu`, libellé « Dumby ·
  Phonon · CPU », ajouté et activé pour essai ; ce nom désigne la voix, sans
  changement du nom fonctionnel Alfred ou du réveil Jarvis. Aucun appel de clonage
  ou transfert Cloud. Test natif long : 956 ms pour 11,36 s d’audio. Service HTTP :
  323 puis 244 ms pour une phrase de 3,2 s, moteur Phonon sans repli. 83 tests
  Python ciblés et 40 tests JS réussis. Jarvis réarmé, ESP32 connecté et flux reçu.
  Dumby devient le profil d’essai actif ; naturel, diction et préférence encore
  à recueillir auprès de l’utilisateur, pas de voix définitive déduite du chargement.

- L’utilisateur fournit un second clonage et demande son activation. Dernier export
  de docs identifié, différent du profil courant, copié et vérifié sous .local
  comme version 2. Profil et configuration précédents conservés pour retour arrière.
  Nouveau fichier chargé réellement après fermeture/réouverture du worker, pas
  seulement remplacé sur disque. Même choix `phonon-alfred-cpu`, aucune nouvelle
  requête de clonage ou transmission Cloud, aucun code applicatif changé.
  Test natif : texte comparatif en 849 ms pour 10,32 s d’audio. Service HTTP :
  présentation en 391 puis 341 ms, WAV de 3,92 s, Phonon sans repli. Jarvis réarmé,
  terminal connecté et trames reçues. Version 2 active pour essai, qualité/timbre
  et préférence face au premier profil encore à juger par l’utilisateur.

- L’utilisateur indique que son export vocal se trouve dans docs. Fichier unique
  .safetensors identifié puis copié et vérifié dans le stockage privé .local,
  sans afficher ses tenseurs ou métadonnées. Original conservé ; les .safetensors
  de docs sont désormais exclus de Git, aucun profil de ce dossier n’était suivi.
  Aucune nouvelle création de voix ou transmission de référence à Gradium par
  l’agent : simple chargement local du profil fourni. Voix `phonon-alfred-cpu`
  ajoutée au sélecteur et activée pour l’essai. Génération du texte comparatif
  complet en 794 ms pour 10,32 s d’audio ; présentation courte 369 ms pour 4,24 s.
  Contrôle du service HTTP : 395 puis 330 ms, moteur Phonon, aucun repli. Jarvis
  actif, ESP32 connecté, flux reçu. 82 tests Python ciblés et 39 tests JS réussis.
  Couverture des phrases vérifiée par transcription, sans validation humaine de
  la ressemblance ou des liaisons. Profil et choix actifs vérifiés techniquement ;
  écoute utilisateur encore attendue. Henri et les autres voix restent disponibles.

- L’utilisateur présente le formulaire de clonage Gradium Studio et demande conseil
  sur les champs. Conseils uniquement : extrait propre de dix secondes à un seul
  locuteur, attributs fidèles à l’audio, description de personnage comme proposition,
  amélioration Studio par défaut à comparer à la source. La capture ne permet pas
  d’évaluer la qualité acoustique ou de choisir un intervalle précis. Aucune voix
  créée, consentement coché, référence envoyée ou configuration active modifiée par
  l’agent. L’export d’une voix choisie vers Phonon reste à effectuer si l’utilisateur
  poursuit ; ne pas confondre conseils de formulaire et voix validée.
  Export expliqué ensuite : catalogue de voix Studio → menu ⋮ → Download for
  Phonon, fichier .safetensors. Le fichier a ensuite été fourni par l’utilisateur
  et raccordé localement pour essai ; création/export effectués par l’utilisateur,
  qualité et choix définitif toujours à valider.

- L’utilisateur demande de tester Phonon localement. Préparation autorisée et
  réalisée : SDK Rust/Python `ptts` 0.7.0, poids Phonon 40m français Q8 téléchargés
  avec accès déjà disponible ; aucune acceptation de conditions, création de compte
  ou clé exposée. Catalogue Gradium exporté localement pour Arnaud et Lucien,
  pas de clonage ni référence audio envoyée. Runtime séparé, CPU quatre threads,
  sans PyTorch ni requête API lors des synthèses, voix et catalogue locaux.
  Deux entrées ajoutées au sélecteur et vérifiées dans le service : Arnaud
  308/244 ms et Lucien 331/256 ms pour une phrase de 3,04/3,12 s, sans repli.
  Banc comparatif long : 735/755 ms ; premiers blocs natifs 62/39 ms, distincts
  du délai de premier son d’Alfred. Les phrases sont retrouvées par Whisper,
  sans preuve de qualité des liaisons ou du timbre. 479 tests Python réussis,
  4 optionnels ignorés ; 38 tests JS réussis. Henri reste actif jusqu’au choix
  humain, Jarvis réactivé et terminal connecté avec flux reçu. S28 et
  `docs/PHONON_ESSAI.md` suivent l’écoute et les validations restantes.
  Retour utilisateur suivant : « vraiment rapide ». Réactivité de Phonon
  appréciée qualitativement ; voix concernée et contexte exact non précisés.
  Diction, timbre et choix Arnaud/Lucien restent à recueillir, sans activation
  ou adoption définitive déduite de cette seule appréciation.

- L’utilisateur propose d’explorer Gradium puis précise son intérêt pour une
  utilisation locale. Recherche officielle : distinguer l’API Cloud Gradium et
  **Phonon**, son modèle ouvert embarqué. Candidat pertinent :
  `gradium/phonon-40m-fr`, 40 M paramètres, français, environ 75 Mo selon l’éditeur,
  synthèse en streaming sur CPU x86-64/ARM et runtime Rust `ptts` sans PyTorch.
  Windows et Linux fournis ; serveur local compatible OpenAI/Wyoming disponible.
  Les performances publiées portent sur Apple et Raspberry Pi, pas sur notre PC
  ou l’AuBox. Pas de qualité ni latence mesurée ici, pas d’équivalence garantie
  avec l’API Gradium ou Henri. Le modèle s’appuie sur Pocket TTS mais le checkpoint
  et le runtime sont distincts de nos essais Pocket précédents.
  Modèle français sous CC BY-NC 4.0, accès HF soumis à acceptation des conditions
  et partage des informations du compte ; le modèle public par défaut 31m est
  anglais uniquement. Aucun compte ni conditions acceptés dans cette étude.
  Voix de catalogue utilisables localement ; les voix créées/clonées dans Gradium
  Studio peuvent être exportées pour Phonon puis utilisées hors ligne. Création
  et export personnalisés nécessitent l’accès Studio/API, mais pas une requête
  cloud à chaque synthèse locale. Aucun audio de référence envoyé, téléchargement
  de modèle ou changement du service réalisé ; Henri conservé. Suite en S28.
  Sources : https://gradium.ai/phonon,
  https://github.com/gradium-ai/xn-ptts,
  https://huggingface.co/gradium/phonon-40m-fr,
  https://github.com/gradium-ai/xn-ptts/blob/main/ptts-openai-server/README.md.


### 11 novembre 2026 — retour STT positif

- L'utilisateur juge la transcription actuelle « vraiment très bien » et demande
  quel moteur et quelle reformulation sont actifs. Statut réel vérifié : Parakeet
  TDT 0.6B v3 INT8, stack Murmure 1.11.3 autonome, disponible et préchargé.
  Nettoyage/dictionnaire/formatage inclus, aucun LLM de réécriture du STT.
  Retour positif après intégration consigné ; micro, distance, bruit et nombre
  de prises non précisés. Aucun nouveau changement demandé ou effectué.

### 9 novembre 2026 — intégration STT Murmure

- L'utilisateur autorise explicitement l'intégration avec la même stack que
  Murmure après ses essais téléphone/ESP32. Code Rust 1.11.3, modèles INT8,
  dictionnaire, nettoyage et formatage intégrés dans un worker autonome, sans
  dépendance à l'application ni réécriture LLM. Ressources et réglages copiés
  localement, sources/licences conservées. Parité réelle 28/28 sur corpus
  synthétique étendu ; tests et contrôles HTTPS réussis. Parakeet est activé
  et préchargé, Henri conservé et ESP32 connecté. Conversation humaine intégrée
  et recette Debian à suivre ; aucun flashage, micro humain ou ordre HA lancé
  par l'agent pour cette intégration. Détails et limites dans STT.md.

### 9 novembre 2026

- Retour après essais Sopro/Melo : Henri est largement préféré en diction et
  rapidité de génération. Le timbre Alfred reste à retrouver. Explication : les
  mesures portent sur des modèles et infrastructures différents ; le coût de
  calcul local peut dominer les délais réseau. La bibliothèque Nabu Casa route
  le TTS vers Azure ; aucun matériel exact ni délai de premier paquet n’a été
  mesuré chez le fournisseur. Les 265–297 ms observées incluent notre chemin
  complet de récupération d’une courte phrase, pas tout le tour de conversation.
  Propositions non adoptées : comparer d’autres voix françaises du catalogue
  Nabu Casa (Claude/Maurice/Yves, à vérifier sur l’instance), puis au besoin un
  service de création de voix tel qu’ElevenLabs Voice Design et synthèse rapide.
  Ce dernier implique un coût supplémentaire : Starter affiché à 6 $/mois hors
  taxes, pas présumé compatible avec le budget de 5 € ; voix, quotas et délai
  réel à évaluer avant tout achat. Pas de nouveau compte, dépense, changement de
  voix ou nouvelle génération réalisés pour cette recherche. Henri reste actif.
  Sources : https://github.com/NabuCasa/hass-nabucasa/blob/master/hass_nabucasa/voice.py,
  https://github.com/NabuCasa/hass-nabucasa/blob/master/hass_nabucasa/voice_data.py,
  https://elevenlabs.io/docs/eleven-creative/voices/voice-design,
  https://elevenlabs.io/docs/eleven-api/concepts/latency-methodology,
  https://elevenlabs.io/pricing/api.

- L’utilisateur demande la mise en œuvre de Sopro et MeloTTS + OpenVoice pour
  tester les deux solutions locales. Installations CPU isolées, modèles publics
  téléchargés explicitement et référence synthétique Alfred existante réutilisée.
  Deux voix ajoutées au sélecteur et testées réellement via le service ; Henri
  reste actif jusqu’au choix humain. Aucun nouvel abonnement ni appel Cloud pour
  ces deux synthèses, aucune modification de la banque de référence.
  Mesures sur phrase identique, modèles chargés : Sopro 1 264/1 244 ms, Melo/OpenVoice
  3 373/1 801 ms. Banc long séparé : 3 178 et 8 629 ms. Ce sont des temps de WAV
  complet sur le PC actuel, pas le délai de premier son ou une mesure sur l’AuBox.
  Sept WAV vérifiés, couverture textuelle contrôlée par Whisper avec doute « amis »
  sur Melo ; diction, naturel, similarité et choix restent à juger à l’écoute.
  460 tests Python réussis, 4 optionnels ignorés ; 36 tests JS réussis. Rapport
  `docs/TTS_SOPRO_MELO_ESSAIS.md`, suite S26. ESP32 non joignable à ce contrôle ;
  l’utilisateur préfère commencer par les fichiers et le navigateur. Ne pas
  demander à nouveau un branchement pour terminer cette première comparaison.


### 9 novembre 2026

- L'utilisateur annonce avoir rebranché l'ESP32 pour le comparatif. API réelle :
  terminal Bureau connecté, phase idle, aucune erreur. L'utilisateur confirme
  ensuite le même résultat avec l'ESP32 : Murmure plus rapide et meilleur en
  transcription. Avantage qualitatif confirmé pour ses essais téléphone et
  ESP32, sans métrique, distance ou scénario de bruit détaillés. Aucun changement
  de moteur encore demandé ; intégration autonome Parakeet proposée pour la suite.
- Retour humain sur le comparatif depuis le téléphone : l'utilisateur juge
  Murmure nettement plus rapide et meilleur en transcription que Whisper.
  Cette appréciation qualitative concerne le micro du téléphone ; ne pas la
  convertir en score chiffré ni en validation du micro ESP32. Le comparatif
  inclut déjà le dictionnaire, nettoyage et règles de formatage de Murmure via
  `/api/transcribe`, sans post-traitement LLM. Les textes/délais des prises
  navigateur ne sont pas journalisés par Alfred ; aucune série de résultats
  de ces essais n'est récupérée. Aucun changement de moteur demandé à ce stade.
- L'utilisateur autorise le comparatif Whisper/Murmure proposé. API locale de
  Murmure 1.11.3 activée, boucle locale 4800 ; intégration limitée au banc de
  comparaison navigateur et au diagnostic ESP32 sur une même prise. Whisper
  small reste actif pour la conversation, Henri conservé. Aucun choix de migration.
  Les deux moteurs reçoivent les mêmes octets WAV 16 kHz ; les corrections de
  Murmure restent appliquées. Alfred conserve l'audio en mémoire ; l'API Murmure
  écrit un WAV temporaire qu'elle supprime après traitement. Aucun micro humain
  ouvert automatiquement ; diagnostic ESP32 sans IA/HA/TTS, résultat éphémère.
- Banc synthétique : dix phrases et un silence, deux passages, 22 succès par
  chaîne. Whisper : WER 4,26 %, médiane 1 079 ms ; Murmure : 7,45 %, 340 ms
  hors premier appel. Questions « est-ce que » correctes pour les deux, silence
  sans texte ; mise en forme Murmure imparfaite sur dix-neuf heures. Avantage
  de vitesse observé, aucune supériorité de précision établie pour la voix humaine.
  94 tests Python et 17 JS réussis ; service relancé et comparatif HTTPS réel
  HTTP200 vérifié, nouveaux contrôles servis. ESP32 déconnecté lors de la recette,
  essai humain et intégration autonome Debian restent ouverts. Voir STT.md/S03.

### 8 novembre 2026

- L’utilisateur demande les autres solutions locales après rejet des variantes
  audio d’Henri. Veille documentaire : nouveau candidat **Sopro V2 Turbo** (120 M,
  français, clonage depuis référence, streaming CPU selon l’auteur). Les ~300 ms
  annoncées concernent le premier bloc sur un CPU Apple M3, pas une mesure sur
  le PC actuel ni sur la future VM Ryzen. Le projet avertit que les nombres et
  certains symboles demandent une normalisation et que streaming/offline diffèrent.
  Autre proposition : **MeloTTS + OpenVoice V2**, génération française puis conversion
  vocale apprise ; vitesse de l’ensemble et fidélité non testées ici. Kokoro officiel
  reste limité par sa voix française féminine et l’absence de clonage direct natif.
  Pocket TTS reste un moteur déjà essayé : rapide sur les courts essais locaux,
  dérive de timbre signalée auparavant ; ne pas le présenter comme une découverte
  nouvelle ni comme un problème résolu. Priorité Sopro proposée, non choisie par
  l’utilisateur ; aucune installation, nouveau banc ou modification d’Henri.
  Sources : https://github.com/samuel-vitorino/sopro,
  https://github.com/myshell-ai/MeloTTS,
  https://github.com/myshell-ai/OpenVoice,
  https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md,
  https://github.com/kyutai-labs/pocket-tts.


- L’utilisateur apprécie la voix Henri mais regrette de ne pas pouvoir la régler
  pour la rapprocher d’Alfred. Vérification du connecteur Cloud officiel : choix
  de voix (et styles proposés selon les voix) et format de sortie, pas de réglages
  libres de hauteur/débit/timbre ni de clonage exposés par cette intégration.
  Proposition testée seulement sur échantillons : post-traitement léger d’Henri,
  cadence à 0,96, puis cadence 0,96 et hauteur 0,94 avec formants préservés.
  Deux WAV de 13,8 s, traitement local en 146/144 ms, contrôles PCM sans écrêtage.
  Cela ne prouve ni un rapprochement du personnage ni le naturel à l’écoute.
  Aucun traitement ajouté au service actif, aucune modification de la référence
  Supertonic archivée, aucun nouveau choix validé. Ce sont des essais distincts
  des anciennes patines abandonnées. Retour humain reçu : les deux variantes
  sont rejetées (« c’est mauvais »). Cette piste de traitements est abandonnée ;
  Henri original reste actif, sans effet. Le rapprochement vocal d’Alfred reste
  ouvert et aucune nouvelle voix n’est choisie par ce rejet (S04, S25).

- Étude Murmure demandée : l'utilisateur rapporte très peu d'erreurs sur son PC.
  Version installée 1.11.3 identifiée : Parakeet TDT 0.6B v3 INT8, CPU/ONNX
  Runtime, modèles présents. Dictionnaire, nettoyage et formatage complètent le
  moteur ; LLM réservé aux modes dédiés. API locale disponible mais désactivée.
  Comparatif via API puis moteur autonome Debian proposés, sans activation ni
  remplacement validé. Sources de cette version dans STT.md, suite en S03.
- Nouveau retour STT : précision jugée insuffisante ; « est-ce que tu peux me
  raconter une histoire » devient « c'est ce que tu peux me raconter une histoire ».
  Le choix documenté est Whisper small via faster-whisper, français, CPU INT8,
  beam5. L'API locale 8765 ne répond pas lors de cette vérification ; choix actif
  non reconfirmé. S03 reste ouvert pour cette régression qualitative, comparer
  les modèles sur une même prise et vérifier la conservation du début de parole.
  Confusion phonétique ou découpage : hypothèses, aucune cause établie ni nouveau
  moteur validé. Aucune prise humaine enregistrée pour ce constat.
- Retour utilisateur après essai Chatterbox CPU : délai inacceptable, chercher un
  autre moyen ou outil. Essai arrêté, référence rapide rétablie provisoirement,
  puis piste existante vérifiée : `tts.home_assistant_cloud`, voix `HenriNeural`,
  déjà présente dans un pipeline français. L’utilisateur confirme l’abonnement
  Home Assistant Cloud déjà payé. Le TTS fait partie du service existant ; aucun
  achat ni souscription réalisés. Éviter d’ajouter un abonnement de synthèse tant
  que cette piste n’est pas évaluée.
  Banc sans lecture sur la maison, cache disque désactivé dans la requête :
  trois courtes phrases distinctes en 265/297/295 ms (requête, récupération audio
  et conversion incluses) ; texte comparatif complet en 1 783 ms pour 13,25 s
  d’audio. Cela ne mesure pas tout le tour vocal ni toutes les conditions réseau.
  Intégration `ha-cloud-henri` livrée et activée, via API TTS et proxy audio HA
  sur le même hôte ; jeton existant protégé réutilisé, sans l’exposer ni en créer.
  Heures développées, négations laissées au moteur ; WAV mono en mémoire, pas de
  lecture HA ni modification du pipeline existant. Pas de repli vocal silencieux.
  Contrôle service réel : HTTP 200, 1 020 ms pour une phrase inédite de 5,02 s,
  voix Cloud sans repli. Jarvis réactivé, terminal connecté et flux reçu.
  443 tests Python réussis, 4 optionnels ignorés ; 32 tests JS réussis. Validation
  humaine de la voix Henri, de la diction et du délai conversationnel encore ouverte.

- L’utilisateur demande ensuite de tester immédiatement sur le CPU du PC actuel.
  Chatterbox CPU est ajouté aux voix sélectionnables et activé pour l’essai dans
  le service : mêmes poids v2 et référence synthétique que C, français, graine 42,
  exagération/CFG 0,5, quatre threads CPU ; GPU masqué et device CPU explicite.
  Processus persistant isolé des dépendances principales, protocole mémoire borné,
  arrêt sur erreur/délai, sans remplacement vocal silencieux. Développement des
  heures conservé ; les négations ne sont pas reformulées pour Chatterbox.
  Contrôle du service : d’abord 40,115 s sur une courte phrase en processus masqué ;
  réglage Windows HighQoS existant appliqué aussi au processus enfant. Nouveau
  contrôle HTTP réel : 9,096 s pour l’heure, WAV de 2,94 s, moteur Chatterbox CPU,
  sans repli. Ce temps ne mesure pas toute la conversation ni la cible AuBox.
  430 tests Python réussis, 4 optionnels ignorés ; 30 tests JS réussis ; 5 tests
  ciblés et contrôle réel après correction HighQoS. Veille Jarvis réactivée,
  terminal connecté et flux reçu ; recette humaine à effectuer. Préférence précédente sauvegardée
  localement et référence sélectionnable dans l’interface.

- Après préférence pour la diction Chatterbox, l’utilisateur autorise le travail
  de latence et précise le futur hôte : Chuwi AuBox 8745HS, 32 Go DDR5, SSD 512 Go,
  Radeon 780M, attendu prochainement ; Proxmox pour le homelab et Alfred dans une
  VM Debian. Cible retenue, dimensionnement et performances non encore mesurés.
  Banc local : RTX FP32 1,842 s de médiane courte, CPU PyTorch d’origine 9,826 s ;
  ONNX Q4 CPU 3,711 s mais essai long invalide, donc pas retenu. FP16 sans gain
  convaincant ; INT8 et changement de version CPU ne donnent pas de solution
  robuste. Alertes de nombres/omissions à contrôler à l’écoute ; aucune variante
  accélérée adoptée. Préparer les mesures sur la vraie VM à réception plutôt que
  supposer les résultats CUDA applicables à l’AMD. Service et référence vocale
  conservés ; script de banc portable et rapport livrés en S23.

- Après validation qualitative de Jarvis, l’utilisateur signale des prononciations
  françaises incorrectes du TTS : heures et « plus » négatif lu avec un s.
  Correction mise en place sans modifier la voix de référence ni le débit :
  préparation du seul texte à lire, heures explicites en lettres et reformulations
  limitées des négations d’absence non ambiguës. Les emplois comparatifs de « plus »
  sont conservés. Consigne IA de formulation adaptée à l’oral ; une liste de courses
  ne prouve pas le stock réel. 159 tests ciblés réussis et échantillon réel généré
  localement, sans diffusion sur ESP32. Retour utilisateur suivant : diction
  insuffisamment naturelle, liaisons manquantes et s de « plus » toujours signalé.
  La correction textuelle ne résout donc pas le problème perçu ; les tests vérifient
  le code, pas la qualité de prononciation. Hypothèse de limite du modèle à examiner
  avec le profil vocal, le débit et les coupures entre blocs ; cause non isolée.
  Comparaison sur phrases identiques autorisée ensuite par l’utilisateur (S22) :
  référence actuelle au débit 1,242, même profil au débit 1,0 et Chatterbox français.
  Banc isolé, sans changement du moteur actif ni nouvelle dépense. Choix final et
  qualité à l’écoute restent ouverts. Banc livré dans
  `.local/tts-comparison-20261108/` : trois extraits sur le même texte et mesures
  à chaud sur CPU. Réponse courte : médiane de 0,530 s à 1,242, 0,666 s à 1,0 et
  9,826 s pour Chatterbox v2, hors autres étapes. Douze WAV vérifiés, couverture
  des phrases principales contrôlée par Whisper ; ce contrôle ne juge pas la
  prononciation. Chatterbox sensiblement plus lent sur ce banc, aucune substitution
  automatique. Retour d’écoute : C jugé nettement meilleur ; A et B donnent le
  même résultat pour le français. Réduire le débit ne suffit donc pas selon cet
  essai humain. Préférence de diction Chatterbox validée pour l’extrait, sans
  validation de tous les cas français ni acceptation de son délai CPU en usage
  réel. Prochain point technique : faisabilité d’une latence compatible avec la
  conversation et l’hôte cible. Aucun changement du service actif réalisé.
  Rapport `docs/COMPARAISON_TTS.md` mis à jour.

- À la demande de l’utilisateur, installer le modèle Jarvis fourni dans `docs/`
  pour un essai sur la chaîne existante. ONNX compatible chargé avec les modèles
  de prétraitement locaux ; fichier TFLite conservé sans utilisation ni flashage.
  Configuration précédente sauvegardée localement ; modèle Hé Alfred conservé.
  Interface et commandes lumières, minuteurs, musique et courses acceptent Jarvis
  et la graphie Jarvisse. Service redémarré, carte identifiée et connectée, veille
  Jarvis active avec réception de 95 744 octets en trois secondes sans erreur.
  Retour humain ensuite positif : détection jugée parfaite, même à basse voix.
  L’utilisateur conserve Jarvis et diffère le travail sur le réveil pour se
  concentrer sur le fonctionnement de l’assistant. Essai avec musique reporté ;
  taux chiffrés, bruit et autres locuteurs restent à valider.

### 6 novembre 2026

- L'utilisateur veut un réveil préentraîné pour tester la chaîne globale avant
  de revenir à un mot personnalisé. Banc temporaire « Alexa » : modèle officiel
  openWakeWord sur PC, anglais, seuil 0,5, vérification Whisper du mot désactivée ;
  carte et modèle « Hé Alfred » conservés. Ce n'est ni le moteur Amazon ni un
  modèle dont la performance en français a été établie ; recette humaine ouverte.

- Essai utilisateur de cinq demandes à débit naturel après retour en veille :
  deux non-détections, deux réponses ne comprenant pas la demande et une bonne
  réponse. Les compteurs montrent trois détections supplémentaires et aucun rejet
  supplémentaire du filtre ; causes précises des incompréhensions encore inconnues.

- Après correction, l'utilisateur rapporte que le clavier ne déclenche plus lors
  de son essai, mais que « Hé Alfred » exige une parole trop lente et articulée.
  La reconnaissance naturelle reste insuffisante ; origine entre modèle et
  vérification locale à mesurer avant tout réglage du seuil.

- Bruit signalé comme déclenchant Alfred même après les huit secondes ; essai
  confirmé par l'utilisateur et détections attribuées au modèle de réveil. Ajout
  d'une confirmation locale du nom avant traitement d'un réveil, en attente de
  recette à la voix et au bruit. Effets sur latence et ratés encore inconnus.

- L'utilisateur rapporte que le réveil fonctionne difficilement et que le retour
  à l'écoute est très long. Correction des fins de prise et de l'auto-annulation
  de la relance ; résultats de tests simulés à confirmer sur la carte. La fenêtre
  de reprise de huit secondes reste une période pendant laquelle parler sans mot.
  La qualité du modèle reste à mesurer séparément sur la voix réelle.

- Après retour utilisateur « une fois sur 1000 » : correction logicielle de la
  supervision de veille et de l'affichage, avec reprise après silence et reconnexion
  testées en simulation. Flux confirmé sur la carte réelle à 32 Ko/s après
  activation ; recette humaine et reprise matérielle après conversation ouvertes.
  Comparaison avec Porcupine français envisagée, non installée ni adoptée.

- **Mot d'appel : « Hé Alfred », détection côté serveur.** L'utilisateur choisit
  le mot « Hé Alfred » puis valide l'architecture A : le micro de la carte streame
  vers Alfred, qui détecte le mot avec un modèle openWakeWord ONNX. Constat
  bloquant sur la carte réelle : la binaire flashée (2026.9.0, projet
  `jyoushiki.waveshare-voice` v2.0.0) ne contient **aucun** modèle de réveil
  (`available_wake_words=[]`, `max_active_wake_words=0`), alors que le YAML source
  v2.0.0 en déclare quatre. La variante embarquée aurait exigé un flash OTA et un
  modèle `.tflite` ; le générateur retenu (`lfpoulain/wakeword-generator`) produit
  un ONNX openWakeWord et sa documentation indique qu'il ne convient pas à
  microWakeWord sur microcontrôleur. Latence de détection supplémentaire mesurée
  comme négligeable (+250 à 350 ms sur un tour d'environ 5,7 s : STT 1,1 s, IA
  2,5 s, premier bloc TTS 2,0 s). Aucun flashage, donc retour arrière trivial.
- **Préfixe parlé traité dans le même chantier.** « Hé Alfred allume la lumière »
  n'exécutait pas la commande directe : le nettoyage ne reconnaissait que l'anglais
  « hey », alors que Whisper en français écrit « hé ». Corrigé pour les lumières,
  les minuteurs, la musique et les courses ; la phrase est désormais exécutée
  localement sans appel IA.
- Après le nouvel essai, l'utilisateur confirme « très bien ça fonctionne
  nickel ». La fin de prise ESP32 avec son fond chanté externe est validée pour
  ce cas, et le réglage Silero v6 est conservé (S20 terminé). Contrôle de reprise :
  carte connectée, pas d'erreur, dernier motif `speech_pause`, prise de 5 432 ms.
  Ce retour ne vaut pas mesure universelle sur tout chant, TV ou toute distance.
  Compréhension de base et scénario musical bloquant désormais acceptés ;
  recettes plus larges et hôte cible restent en S03/T01/A04.
- Retour utilisateur : transcription correcte pendant l'essai avec fond musical,
  mais la prise ne se termine qu'après coupure de la musique. Cas précisé :
  **ESP32**, musique **chantée**, provenant d'un **autre appareil**. La
  reconnaissance reste satisfaisante ; le défaut concerne le découpage temporel.
  Cause confirmée dans le code : déclenchement/fin sur RMS fixe, pas sur parole.
  Remplacé sur le pont ESP32 par Silero VAD v6 local, asset déjà fourni avec
  faster-whisper : fenêtres 32 ms, contexte/état séparés par prise, seuils de
  parole 0,5/0,35, pause de 900 ms conservée, pré-capture et PCM originaux gardés.
  Aucun changement des gains, du firmware, de la musique externe, du STT small
  ou de la voix. Le navigateur garde sa détection actuelle par énergie.
  Tests : 303 Python réussis, 4 optionnels ignorés ; les 4 tests du détecteur
  ont aussi été exécutés séparément avec intégration TTS réelle activée.
  Sur un fond **instrumental synthétique** continu, l'ancien RMS reste bloqué,
  le nouveau termine après la phrase sans couper ses premiers mots. Ceci ne
  valide pas le chant : le VAD ne reconnaît pas l'identité du locuteur et peut
  considérer un chanteur comme une voix. Service relancé, carte connectée,
  détecteur vérifié actif ; essai humain du fond chanté ensuite confirmé réussi.
  Le résultat de diagnostic indique désormais « fin de parole détectée » ou
  « durée maximale atteinte ». Aucun audio humain enregistré.
- Après acceptation de la compréhension de base, poursuite proposée des essais
  de distance puis de bruit, sans changer les réglages. Bouton « Tester à
  distance » ajouté au diagnostic STT : un clic arme le mode sans action puis
  demande le démarrage natif du micro, sans K2, pour éviter les déplacements et
  bruits de manipulation avant de parler. Même en cas de réponse perdue, une
  activation tardive reste diagnostique/expirée, jamais une commande de maison.
  Service relancé, bouton et script servis, carte connectée, Small/beam5 conservé.
  53 tests ciblés terminal/conversation réussis, syntaxe JS vérifiée ; aucun test
  micro déclenché automatiquement. Prochain essai humain : phrase témoin au calme
  à environ deux mètres, puis bruit ; aucun résultat de distance encore acquis.
- Après proposition de huit phrases de test, l'utilisateur juge le résultat
  « pas mal du tout » et ne détecte plus d'erreur. Retour humain positif :
  conserver Whisper small CPU INT8, beam5, température0, français et VAD.
  Qualité de base du prototype acceptée. Le retour ne précise pas si les huit
  phrases et les deux micros ont tous été essayés ; aucun taux d'erreur humain
  chiffré ni validation en bruit/distance/charge n'en sont déduits. Ces recettes
  restent à faire, sans nouveau réglage du STT demandé à ce stade.
- Priorité utilisateur : fiabiliser la transcription avant le réveil et les
  autres fonctions. Mots étranges et incompréhension fréquente sur **les deux**
  entrées, navigateur et ESP32 ; aucun exemple précis fourni, défaut général.
  Le moteur commun est donc la première piste, sans exclure la qualité audio.
  État constaté : Whisper base CPU INT8, deux threads et beam_size=1, français
  imposé, sans historique de transcription ; aucune prise humaine conservée.
  Comparaison base/small et décodages plus approfondis en préparation, à valider
  sur voix humaine et non sur la seule synthèse. Voix de sortie conservée.
  Réveil « Alfred » et autres nouvelles fonctions passent après ce chantier.
- Banc de sept phrases françaises synthétiques (aucune capture humaine) :
  base/beam1, WER normalisé 19,7 %, médiane 487 ms ; base/beam5, 19,7 %,
  médiane 387 ms ; small/beam5, 6,1 %, médiane 1 096 ms. CPU INT8 local, quatre
  threads pour les candidats, température 0, français imposé et VAD conservé ;
  silence synthétique sans texte. Ces chiffres ne mesurent pas la précision
  humaine. Small est activé comme candidat commun navigateur/ESP32, sans toucher
  à la voix de sortie. Révision publique téléchargée explicitement et conservée
  en métadonnées locales ; aucun téléchargement pendant une écoute.
  Sources : https://github.com/SYSTRAN/faster-whisper et
  https://huggingface.co/Systran/faster-whisper-small.
- Diagnostic humain livré : bouton « Tester la transcription ESP32 », puis K2,
  affiche le texte brut sans appel IA, TTS ni commande HA. Audio jamais sauvegardé,
  résultat textuel séparé du statut général et effacé après deux minutes.
  Armement de 60 s ; une activation tardive reste un test expiré, jamais une
  commande réelle. Le navigateur conserve son mode Test audio sans action.
  Service relancé : small/beam5 actif, référence TTS et débit 1,242 inchangés,
  carte reconnectée. Contrôle réel sur audio public synthétique via le banc sans
  action : « Alfred allume la lumière du bureau », STT à froid 2 145 ms.
  298 tests Python réussis, 3 réels optionnels ignorés ; 29 tests JS réussis.
  Le banc seul ne validait pas la compréhension humaine ; l'utilisateur confirme
  ensuite ne plus détecter d'erreurs sur son essai. Conserver ce candidat.
  Recette acoustique approfondie encore ouverte, priorité STT de base traitée.

### 5 novembre 2026

- Après rejeu de l'extrait corrigé, l'utilisateur répond « c'est très bien ».
  Lecture progressive avec marges silencieuses raccourcies validée à l'écoute.
  Conserver ce réglage, le profil `alfred-reference` et le débit 1,242 ; ne pas
  reprendre les essais de timbre. Cette validation porte sur le rendu de
  l'extrait, pas sur une mesure du délai complet après une demande au micro.
- Premier retour, avant correction des pauses : sur l'ESP32, l'utilisateur signale de petites
  pauses mais juge la voix propre. Qualité du rendu vocal confirmée ; continuité
  imparfaite, S19 reste ouvert. Conserver le profil et le débit actuels. Prochain
  point traité : mesurer et réduire ces pauses sans couper les mots ni modifier
  le timbre. Le retour seul ne permettait pas d'en déterminer l'origine.
  Latence globale en conversation encore à apprécier.
- Mesures sur le texte témoin : les blocs contiennent 320–620 ms de calme en
  tête et 440–715 ms en fin, cumulant 1 035 / 1 181 / 1 230 ms aux jonctions.
  La génération des suivants est suffisamment en avance sur cet extrait ; les
  silences déjà présents expliquent ces pauses, sans conclure pour tout contexte
  réseau futur. Correction ciblée du flux progressif : retirer l'excédent de
  calme seulement aux bords internes, avec seuil RMS -60 dBFS par trames de 10 ms,
  marges d'au moins 80 ms avant et 180 ms après activité, protection d'une trame
  et raccord sur faible amplitude. Première attaque, dernière fin et pauses
  internes conservées ; aucun effet, accélération ou changement de profil.
  Sur les mêmes échantillons : jonctions à 290 / 291 / 290 ms, 2 575 ms de
  silence retiré ; parole conservée bit à bit dans les tests, y compris consonnes
  faibles à trois fréquences. Correction déployée et extrait rejoué sur la carte :
  lecture de 12,70 s terminée, 2 276 ms de marges retirées sur cette nouvelle
  génération ; première demande audio à 1 969 ms, quatre blocs conservés.
  Profil `alfred-reference` et débit 1,242 vérifiés. Recette : 294 tests Python
  réussis, 3 optionnels ignorés. Nouvelle écoute ensuite validée par l'utilisateur.

### 4 novembre 2026

- Conversation ESP32 confirmée fonctionnelle par l'utilisateur, délai jugé trop
  long. Dernier échange mesuré : STT 2 126 ms, IA 2 584 ms, TTS 7 635 ms
  (12 345 ms cumulés, hors détection de pause et lecture réseau). Optimisation
  CPU testée sans changer la référence : quatre threads Supertonic au lieu de
  deux, gain de 11 % sur petit banc à deux graines et signal numériquement quasi
  identique. Le service Windows était lancé en tâche de fond ; priorité de tâche
  passée de 7 à 6 (normale), XML initial sauvegardé sous `.local/backups/`.
  Le levier principal observé est l'opt-out Windows EXECUTION_SPEED / HighQoS
  pour le seul processus Alfred : même texte de 215 caractères, synthèse chaude
  de ~6 400 à ~2 330 ms, 12,40 s d'audio inchangées. Réglage appliqué au lancement
  dans `alfred/runtime.py`, sans priorité haute ni modification du plan système.
  Après redémarrage : 3 729 ms à froid, 2 336 ms à chaud, carte reconnectée.
  Sources Microsoft : https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-setprocessinformation
  et https://learn.microsoft.com/en-us/windows/win32/taskschd/tasksettings-priority.
- L'utilisateur propose ensuite de générer et envoyer la voix par petits blocs
  pendant le calcul des suivants. Flux progressif livré sur l'ESP32 : réponse
  textuelle et actions finalisées d'abord, puis synthèse par phrases/clauses,
  profil verrouillé sur la réponse entière et débit 1,242 conservé. Un seul
  encodeur FLAC 48 kHz alimente HTTP chunked pendant le calcul des blocs suivants ;
  aucun fichier temporaire ni pause artificielle entre blocs. Pas de synthèse
  pendant la génération des arguments d'outils ou avant confirmation d'action.
  Test réel : quatre blocs, première demande audio à 2 053 ms alors qu'un seul
  bloc est prêt ; génération totale terminée à 4 480 ms ; 14,98 s d'audio,
  fin de lecture confirmée par la carte. Ces temps sont ceux de l'essai TTS,
  hors transcription et IA, et ne mesurent pas le premier son acoustique.
  Continuité et gain perçu en conversation encore à confirmer par l'utilisateur.
  Option locale `progressive_tts: false` pour revenir à la réponse complète.
  Recette finale : 290 tests Python réussis, 3 optionnels ignorés, 29 tests JS
  réussis ; le test de page statique a été adapté à la navigation du 4 novembre.
  Nouveaux timings sans contenu privé ajoutés au diagnostic terminal (préparation,
  première demande audio, conversion et durée/caractères de réponse). 74 tests
  ciblés réussis pour cette première optimisation ; perception du gain à confirmer.
- Demande utilisateur : simplifier l'interface web et accéder aux fonctions à
  tester sans parcourir une longue page. Réorganisation livrée : huit vues
  accessibles par menu (voix/conversation, échéances, lumières, musique, courses,
  annonces, profils et connexion IA), laboratoire vocal affiché à l'ouverture.
  Étage du navigateur commun en haut de page ; réglages secondaires et aide
  repliables. Les contrôles existants restent montés lors du changement de vue.
  C'est un choix d'implémentation ; appréciation utilisateur encore attendue.
- Vérification logicielle : 29 tests JS réussis ; navigation des huit vues,
  destination inconnue, focus et conservation des contrôles vérifiés avec DOM
  simulé ; structure HTML et références des contrôleurs vérifiées. Recette
  visuelle ordinateur/téléphone à faire, accès navigateur désactivé dans la session.
  Contrôle HTTPS réel bloqué par l'expiration du certificat local constatée le
  4 novembre ; aucun renouvellement ni changement du service effectué.

### 3 novembre 2026

- Echo Show 5 H23K37 stock confirmé par l'utilisateur comme matériel disponible.
  Flashage acceptable en principe ; qualité du réveil prioritaire. Comparaison
  TECHO5 / solutions conservant la chaîne Amazon ouverte, sans choix ni flashage.

### 2 novembre 2026

- Raccordement direct autorisé puis livré comme prototype : client natif
  aioesphomeapi 46.25.1, identité MAC vérifiée, firmware inchangé. Micro PCM16
  mono 16 kHz sur TCP, mêmes routes STT/conversation/outils/TTS que le navigateur.
  Le lecteur exige un transport adapté : FLAC mono 48 kHz, HTTP local 8766 avec
  accès limité à la carte, jetons aléatoires expirant à 90 s, réponses en mémoire
  uniquement et HTTP Range. Le premier essai WAV n'aboutissait pas ; FLAC et
  gestion des lectures partielles ont donné une fin de lecture confirmée.
  Test micro : 62 976 octets / 1,97 s, jetés sans traitement ; sample rejoué à la
  demande, fin confirmée et 2 327 ms de synthèse. L'utilisateur valide ensuite
  l'écoute. Bouton « Écouter sur l'ESP32 » et état ajoutés au laboratoire.
  Reconnexion, arrêt et fenêtre de reprise de huit secondes implémentés ; recette
  acoustique de conversation, réveil « Alfred », barge-in, diffusion des échéances
  et multi-terminaux encore ouverts. Home Assistant reste déconnecté de la carte.
  Recette : 282 tests Python réussis, 3 réels optionnels ignorés ; 29 tests JS
  réussis. Un test de sonnerie présentait une course entre appel HA simulé et
  écriture du journal ; son attente vise désormais l'état publié, sans changement
  du comportement des sonneries.
- Après une appréciation « acceptable » de la voix intégrée, l'utilisateur
  souhaite tester l'ESP32, puis demande de le déconnecter complètement de HA,
  où il ne servait qu'à un test. Périmètre : carte Waveshare `eb05fc` uniquement,
  pas les connecteurs HA d'Alfred. Aucune dépendance trouvée dans automatisations,
  scripts, scènes, helpers ou tableaux de bord. Entrée ESPHome ciblée désactivée
  et déchargée (`not_loaded`, `disabled_by=user`), appareil relais Music Assistant
  désactivé ; satellite confirmé `unavailable`. Aucun effacement de registre,
  reflashage, redémarrage HA ou désactivation globale de Music Assistant.
  Les trois configurations locales de routage ont été copiées et vérifiées sous
  `.local/backups/esp32-ha-disconnect-20261102/` avec notice de retour arrière.
  Cibles d'annonces et de sonneries vers la carte retirées ; lecteur musical local
  désélectionné car il pointait sur cette carte, sans choisir un autre lecteur
  à la place. Alfred relancé et vérifié sain, voix `alfred-reference` à 1,242.
  Les annonces et sonneries physiques attendent désormais le raccordement direct.
- L'utilisateur autorise le raccordement de la référence au service (S18).
  Voix `alfred-reference` ajoutée au sélecteur et à l'API, sélection persistante
  activée sur le service relancé. Chargement du profil archivé avec vérification
  SHA-256, recette 1,242 / 12 étapes / français et gain sans amplification ni
  effet, communs au sample et aux réponses. Profil absent, altéré ou recette
  différente : voix indisponible, sans remplacement silencieux. Les autres
  voix restent sélectionnables. Recette : 271 tests Python réussis, 3 réels
  optionnels ignorés ; 29 tests JavaScript réussis. Vérifications réelles :
  sample 2 013 ms, texte long 2 940 ms (12,40 s d'audio), conversation de
  253 caractères en 3 029 ms de synthèse ; même voix, débit 1,242, aucun repli.
  Écoute humaine de la conversation et essai ESP32 encore à faire.
- Décision finale de cette série d'écoutes : l'utilisateur abandonne l'essai
  « noble » et retient explicitement `essai-2-propre-1242-long.wav` comme voix
  de référence : profil synthétique 2, débit 1,242, sans effet. Ne pas poursuivre
  les variantes nobles ni la patine. La référence archivée reste inchangée ;
  le raccordement au service reste la tâche S18, non réalisé dans cet échange.
- L'utilisateur accepte à l'écoute la voix synthétique 2 propre à vitesse 1,242
  et demande de la conserver en banque comme référence, tout en poursuivant les
  essais. Archivage local vérifié sous `.local/data/voice-bank/alfred-reference-20261102/` :
  profil, paramètres, échantillons court/long, recette de génération, rapport et
  empreintes SHA-256. Libellé : « Alfred — référence validée ». Aucun traitement
  de patine ; âge perçu de 70 ans non validé séparément. Ce choix valide la base
  appréciée, sans activation automatique dans le service.
- Nouvel essai demandé : un petit côté noble, inspiré d'Alfred Pennyworth ;
  référence française de la série animée des années 1990 conservée. Recherche :
  DC décrit notamment un majordome britannique et acteur formé à Shakespeare
  (https://www.dc.com/characters/alfred-pennyworth). Cela étaye le personnage,
  pas une caractérisation acoustique de la VF. Interprétation de jeu proposée :
  diction soignée, aplomb, courtoisie et retenue. Essais séparés avec le même
  profil et débit : cadence seule sur le texte témoin, puis registre de langue
  plus soutenu ; pauses courtes explicites, sans bruit ajouté ni pitch-shift.
  Fichiers sous `.local/synthetic-voice-bench/noble-01/`. Aucun effet « noble »
  sémantique disponible dans le moteur. Après écoute, l'utilisateur abandonne
  cette piste et conserve la voix propre précédente.
- L'utilisateur rejette la version patinée : saturation audible évoquant un
  haut-parleur cassé. Le traitement de patine est abandonné pour les essais
  suivants, sans conclure à une panne matérielle ni à une cause mesurée.
  Il demande 15 % de débit supplémentaires : nouveau paramètre 1,242
  (1,08 × 1,15). Essai propre, sans coloration, souffle, saturation ajoutée ou
  changement de hauteur ; gain uniforme uniquement pour la réserve de niveau.
  Fichiers courts et longs générés sans échantillons écrêtés, réponse longue
  de 12,40 s produite en 2 590 ms. Nouvelle écoute et âge vocal de 70 ans
  toujours à valider ; voix du service inchangée.
- Sur le deuxième prototype, l'utilisateur demande un débit un peu plus rapide
  et un âge vocal perçu d'environ **70 ans**. Objectifs validés ; le réglage
  d'essai à 1,08 au lieu de 0,96 est ensuite augmenté à 1,242 à sa demande.
  Supertonic n'expose pas de
  paramètre d'âge dans l'API installée. Essai local de texture : coloration
  spectrale, saturation légère et souffle faible lié à la parole, sans changement
  de hauteur ni modulation périodique. Ce traitement ne constitue pas un modèle
  de vieillissement et ne prouve pas un âge perçu de 70 ans. Cette patine est
  ensuite rejetée pour saturation audible. Versions témoins
  accélérées sans traitement conservées pour comparaison ; service inchangé.
- L'utilisateur préfère le deuxième prototype synthétique : profil fixe
  Supertonic M2/M1 à 50/50, débit 0,96, conservé en privé sous
  `.local/synthetic-voice-bench/profil-2.json`. Cette variante devient la base
  des prochains essais. Ce choix comparatif ne valide pas encore la stabilité
  sur réponse longue, la latence ni la voix définitive ; service inchangé.

- 30 octobre : priorité aux fonctions ; authentification et droits par personne
  différés avant la mise en production. Orientation Home Assistant conservée.

### 30 octobre 2026

- L'utilisateur accepte d'explorer une voix originale à identité fixe, avec A
  comme repère d'écoute. Premier banc local Supertonic préparé : trois profils
  synthétiques fixes dérivés de M2/M1, par interpolation expérimentale des
  vecteurs de style (80/20, 50/50 et 20/80), débit 0,96. Il ne s'agit pas d'un
  entraînement depuis zéro ni d'un clonage de la référence. A sert uniquement
  à présélectionner les bases ; aucun échantillon privé n'entre dans ces profils.
  Pertinence perceptive et stabilité à confirmer, service actif inchangé.
- Comparaison à l'écoute : l'utilisateur préfère la variante **A** à B
  (`06-14-out.wav`, référence privée correspondant au passage 6,80–14,04 s).
  Préférence relative seulement : ni voix finale ni nouvelle configuration active
  validée. L'utilisateur demande si une voix entièrement synthétique originale
  pourrait mieux conserver timbre et façon de parler. Piste à évaluer, sans
  abandon validé du clonage, sans entraînement ni service payant autorisé.
  Vérification officielle : Qwen3-TTS propose VoiceDesign (création guidée par
  description) ; Supertonic 3 propose des profils fixes et une synthèse locale
  ONNX. Aucun de ces faits ne prouve une constance perceptive pour Alfred.
  Sources : https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign et
  https://huggingface.co/Supertone/supertonic-3/blob/main/README.md.
- Précision utilisateur sur la perte de ressemblance : les défauts concernent
  **le timbre et la façon de parler**, pas seulement la hauteur. Ces deux aspects
  doivent guider l'écoute comparative ; une stabilité accrue ou un meilleur
  score de similarité ne suffit pas. Aucun nouveau profil ni réglage accepté.
- Écoute du réglage à segments courts : l'utilisateur juge le résultat insuffisant
  et constate une perte du caractère vocal d'Alfred. Le réglage à 25 tokens n'est
  donc pas validé ; les mesures automatiques ne valent pas acceptation du timbre.
  Caractéristiques perceptives à préciser avant le prochain essai. L'ancien
  réglage reste lui aussi non validé en raison de la dérive signalée.
- Après correction du repli, l'utilisateur constate une dérive du timbre et des
  changements de hauteur après quelques mots : le clone actuel n'est pas validé.
  Essai de stabilisation appliqué : regroupement limité à 25 tokens au lieu de
  50, chaque segment repartant d'une copie du profil de référence. La température
  reste à 0,3 : la réduire à 0,15 n'améliore pas les essais. Sur deux textes longs
  et deux graines, similarité ECAPA moyenne avec la référence de 0,612 à 0,645,
  et de 0,464 à 0,532 pour les quatre dernières secondes ; couverture indicative
  des mots par Whisper de 78,4 % à 92,7 %. Comparaison limitée à ce petit banc,
  distinct des mesures antérieures sur textes courts. La stabilité de hauteur
  et l'acceptation du timbre restent à confirmer par écoute humaine.
- Retour utilisateur : le clone semble réservé au sample, les autres réponses
  utilisent la voix standard. Défaut reproduit sur l'API : abandon de Pocket
  après 2,5 s de génération totale, même avec progression normale. Délai corrigé
  pour mesurer l'intervalle entre blocs (2,5 s), avec une limite totale de 60 s.
  Le secours Supertonic reste actif en cas d'erreur ou de dépassement. Après
  relance, quatre synthèses successives sans repli, dont une de 2 835 ms ;
  22 tests ciblés réussis. Timbre et diction restent à valider à l'écoute.
  Vérification conversationnelle réelle : Command Code produit 312 caractères,
  synthétisés par Pocket en 3 809 ms sans repli.
- Retour utilisateur sur les voix locales : Tom et Pierre sont rejetés car ils
  n'arrivent pas à prononcer correctement « Alfred », et Pierre dit « majordoum ».
  L'hypothèse que changer de locuteur Piper suffirait est donc abandonnée. Le moteur
  neuronal local Supertonic 3 remplace Piper dans le prototype avec cinq voix
  masculines M1 à M5 ; la voix 3 est proposée par défaut. Le contrôle synthèse →
  reconnaissance transcrit correctement « Alfred » sur les cinq voix. La
  prononciation de « majordome » n'est pas validée par ce contrôle automatique et
  reste à écouter ; aucun timbre final ni lecture ESP32 ne sont validés.
- L'utilisateur fournit un échantillon de 30 s et demande un clonage rapide sur CPU.
  Qwen3-TTS 0.6B est écarté : le banc GGUF Q8 sur CPU produit 2,2 à 4,4 s d'audio
  en 5,4 à 9,1 s, donc n'est pas temps réel. Pocket TTS 4.0.1 est retenu : modèle
  français de 100 M paramètres, clonage par WAV. Le profil de l'échantillon complet
  (27,72 s après nettoyage) est exporté et actif en privé sous `.local` ; le runtime
  reste hors ligne. Après nettoyage de la référence, la similarité ECAPA moyenne
  passe de 0,426 à 0,475 et la reconnaissance de 81 % à 86,6 % sur trois phrases.
  Sur cinq réponses courtes, la médiane est de 600 ms et le p95 de 655 ms, sans
  repli ; la similarité reste nettement supérieure à Supertonic M3. « Alfred » est reconnu,
  « majordome » reste rapproché de « majeur d'homme » par Whisper. Le timbre et la
  diction doivent encore être validés par l'utilisateur à l'écoute avant d'être
  déclarés définitifs. L'objectif reste une imitation de caractère pour usage
  privé, sans usage trompeur ni publication non consentie.
- Music Assistant est raccordé pour la lecture sur l'ampli du salon. Les commandes
  locales et les outils du modèle sont bornés au lecteur configuré ; l'essai réel
  Airbourne a été accepté et arrêté. L'atténuation navigateur est réglable, respecte
  une modification manuelle du volume et a été vérifiée sur l'ampli réel.
- La liste de courses a été utilisée et son parcours d'ensemble confirmé par
  l'utilisateur : ajout multiple, refus des doublons, cocher comme acheté, remise
  en liste, modification, suppression explicite et purge. Les permissions par
  profil et une recette exhaustive restent ouvertes.
- La modification et la suppression d'événements de calendrier sont raccordées à
  la conversation. Alfred cible un UID, refuse une correspondance ambiguë et
  demande la portée pour une série récurrente. Une modification d'occurrence, un
  retrait d'occurrence puis le retrait complet d'un événement temporaire ont été
  vérifiés sur le calendrier HA réel, sans conserver l'événement de test. La
  modification de toute une série est explicitement refusée et reste à implémenter.
- La reconnaissance du locuteur est expérimentale : elle exige au moins deux
  personnes, six échantillons par personne et deux essais indépendants par personne.
  Les profils insuffisamment séparés sont refusés et toute modification des données
  invalide la calibration. L'identité reconnue peut choisir le calendrier personnel
  et le propriétaire d'un rappel, mais ne vaut pas authentification et ne remplace
  pas les permissions. Au 30 octobre, une seule personne était enrôlée avec six
  échantillons ; la calibration et la reconnaissance réelle ne sont pas validées.
- Le serveur de développement a été relancé le 30 octobre après le raccordement
  musical. L'adresse LAN est `192.168.1.23`, le service écoute en HTTPS sur le port
  8765 et `/health` répond `ok`.
- L'arrêt à la fin d'une session de commande empêchait l'accès depuis les autres
  appareils. Une tâche Windows utilisateur `Alfred Assistant Vocal`, déclenchée à
  l'ouverture de session, lance désormais le service de façon indépendante. Elle
  utilise `C:\Python314\python.exe` avec les dépendances du `.venv`, l'exécutable
  du venv n'étant pas couvert par la règle de pare-feu existante. Le certificat
  auto-signé est valide jusqu'au 3 novembre 2026 ; son avertissement peut être
  accepté sur les appareils du réseau.

### 29 octobre 2026

- Pour une demande d'annulation ambiguë d'un rappel récurrent, demander si elle
  concerne la prochaine occurrence ou toute la série.
- Retour utilisateur : « Ça fonctionne le rappel » après raccordement aux calendriers
  HA ; confirmation globale, sans détail sur les étapes ou le terminal essayés.
- L'utilisateur choisit un calendrier familial distinct et l'annonce des seuls
  événements identifiés comme rappels. Local Calendar « Familial », entité
  `calendar.familial`, créé et associé localement ; aucun événement ajouté.
- Création demandée d'un calendrier personnel dans HA : Local Calendar « Personnel »,
  entité `calendar.personnel`, chargée. Aucun événement ajouté ni transféré.
  Propriétaire confirmé par l'utilisateur et associé à un profil existant dans la
  configuration privée locale, sans lecture des empreintes. Calendrier familial
  reste à préciser ; le banc de rappels local Alfred reste suspendu.
- Client de calendrier HA préparé et testé en isolation avec un calendrier fictif ;
  désormais raccordé à la création et consultation vocales ainsi qu'au formulaire.
  Rappels identifiés par un marqueur dans leur description HA ; seuls ceux-ci sont
  annoncés, les événements ordinaires restent silencieux. Un journal local sans titre
  ni contenu évite les rediffusions ; les occurrences manquées restent signalées sans
  annonce tardive et les suivantes sont fournies par HA. Résultats de consultation
  non renvoyés à Command Code dans l'historique. Récurrence hebdomadaire vérifiée
  sur HA réel avec un événement de test retiré ensuite ; essai physique et permissions
  restent à faire. Marquage depuis HA et modification/suppression vocale encore ouverts.
- Correction utilisateur : les données de calendrier et rappels personnels
  appartiennent aux calendriers HA ; Alfred lit et écrit aux bons endroits comme
  interface vocale. L'ancienne décision de stocker les rappels dans Alfred est
  remplacée ; le banc local est suspendu et ses données préservées. Les minuteurs
  restent stockés par Alfred.
- Pour les annonces et rappels, l'utilisateur choisit la voix cloud Home Assistant
  existante plutôt que la préparation d'une sortie locale Piper.
- Une annonce sans destination explicite est diffusée dans toute la maison.
- Un rappel récurrent manqué pendant l'arrêt est signalé et sa prochaine occurrence
  future est programmée, sans annonce tardive.

### 27 octobre 2026

- L'utilisateur est hors domicile et choisit les minuteurs pour poursuivre le
  développement : v0.6 implémentée et testée. Consultation/annulation du prototype
  à confirmer à l'usage ; aucune validation acoustique déduite.
- Accès à distance via Codex, sans VPN sur ce client ; Android dispose de
  WireGuard `10.8.0.2/24`, via wg-easy sur `192.168.1.103`. Alfred tourne sur
  le PC `192.168.1.23`. Un HTTP 200 sur le PC ne valide pas l'accès du téléphone.
- Après une tentative de passerelle HTTPS supplémentaire, l'utilisateur corrige
  explicitement la direction : utiliser son VPN existant et ouvrir simplement
  le serveur de développement sur le LAN. Passerelle arrêtée et code retiré ;
  certificats temporaires retirés. Aucune configuration VPN ni règle Windows
  modifiée (les tentatives de création de règle avaient été refusées).
- Lancement LAN explicite ajouté : `python -m alfred --host 192.168.1.23`.
  Mode local conservé par défaut. Service relancé, santé v0.6.0 et page HTTP 200
  vérifiées sur `.23:8765` ; ports de la passerelle arrêtés. HTTP permet
  l'interface et les commandes écrites ; le
  microphone distant demande encore une origine HTTPS reconnue.
- Recette finale après simplification : 134 tests Python réussis, 1 test vocal
  réel optionnel non activé. Les 26 tests JS de v0.6 restent la dernière recette JS.
- L'utilisateur demande ensuite HTTPS directement : `--https` ajouté au lanceur,
  même IP/port `.23:8765`, certificat de développement auto-signé de sept jours,
  clé et certificat privés hors Git sous `.local/https`. Aucun proxy supplémentaire
  ni changement du VPN/pare-feu. Service HTTPS démarré ; page, script et santé
  vérifiés 200 avec validation du certificat côté PC ; 134 tests Python réussis,
  1 vocal optionnel non activé. L'utilisateur confirme ensuite que l'accès HTTPS
  fonctionne sur son téléphone. Il confirme ensuite le bon fonctionnement de
  l'essai vocal « Mets un minuteur de huit minutes » : micro et lancement validés
  qualitativement sur Android. Il confirme aussi le fonctionnement de la
  consultation, de l'annulation et de « Stop » sur ce banc. Aucune mesure de
  qualité ou de latence ni validation des sonneries physiques n'est déduite.

### 26 octobre 2026

- Premiers essais vocaux rapportés : réveil correct au calme, erreurs de
  transcription fréquentes avec HA Cloud, forte dégradation avec musique
  (environ 25 % de réussite estimée en parlant très fort). Cause non déterminée.
- Premier résultat matériel rapporté : carte connectée à HA, contrôle des lumières
  réussi. Configuration exacte et performances audio pas encore relevées.
- Demande d'un protocole de réception matériel avec tests audio/vocaux et domotique
  en conditions semi-réelles ; aucun choix de pile supplémentaire validé.
- Cadrage initial : domotique prioritaire, Home Assistant, Music Assistant/Qobuz,
  conversation et recherche web, budget supplémentaire de 5 €/mois maximum visé.
- Nom Alfred, français, fenêtre conversationnelle de 8 secondes, interruption
  souhaitée, bureau puis salon et plusieurs terminaux à terme.
- Cible maison pour toutes les lumières, pièce du terminal pour une commande
  locale implicite, musique atténuée pendant l'écoute, minuteurs par étage.
- Deux adultes, un enfant de 4 ans, profils vocaux et restrictions via interface web,
  mémoire commune et personnelle avec mémorisation automatique.
- Correction explicite : restrictions seulement pour un profil limité reconnu ;
  invités autorisés à tout faire, sans mémoire personnelle persistante ni accès
  aux souvenirs privés, et sans alimentation automatique de la mémoire commune.
- Demande de l'utilisateur : consigner les validations dans ce document et le
  compléter au fil des échanges ; règle inscrite dans `AGENTS.md`.
- Application web dédiée validée ; historique de diagnostic sur sept jours avec
  plafond de taille à préciser ; goûts/habitudes mémorisés automatiquement et
  confirmation pour les informations sensibles ; confirmations d'actions importantes
  configurables acceptées sur le principe ; changement de profil quand le locuteur change.
- Historique précisé : sept jours et 100 Mo maximum, textes/réponses/actions/erreurs/
  temps de traitement, invités inclus pour le diagnostic, sans audio brut ni
  alimentation de mémoire personnelle à partir des échanges invités.
- Fonctions supplémentaires retenues pour la première version : rappels, listes
  de courses et annonces dans la maison. Modalités encore à cadrer.
- Rappels personnels par défaut, collectifs sur demande et récurrents ; liste de
  courses familiale disponible dans HA ; annonces ciblables maison/étage/pièce.
  Répartition des responsabilités et données entre HA et Alfred encore à arbitrer.
- Après comparaison, choix validé : Alfred autonome intégré à HA ; Alfred coordonne
  dialogue, profils, permissions et mémoires, HA fournit la domotique, Music Assistant
  la musique et Command Code le modèle de conversation. Moteurs et firmware à choisir.
- Accord de principe sur la base technique du prototype : faster-whisper, Piper,
  SpeechBrain ECAPA, service Python et premier test via navigateur. Voix, modèles,
  performances, firmware et hébergement définitifs restent à valider par les essais.
- Création demandée d'une checklist vivante avec contraintes et dépendances,
  complétée automatiquement au fil des échanges ; suite des essais audio différée.
- Choix d'une nouvelle liste familiale Alfred dans HA, distincte des deux listes
  existantes. Proposition d'hébergement et d'interfaces dans `HEBERGEMENT_ET_HA.md` ;
  cible d'hébergement non encore validée. Liste créée le 29 octobre (voir ci-dessus).
- Décision initiale : Alfred source des rappels et minuteurs ; corrigée le
  29 octobre pour les rappels, désormais liés aux calendriers HA. Alfred reste
  source des minuteurs ; méthode de consultation et commande HA à concevoir.
- Validation : « Stop » arrête les sonneries de l'étage du terminal ; échéances
  persistantes après redémarrage ; rappel personnel non délivré visible dans
  l'interface, sans diffusion à toute la maison.
- Rappel personnel : diffusion par défaut sur le terminal de création, autre pièce
  sélectionnable à la voix. Défaut pour une création web/HA sans terminal à préciser.
- Reprise après arrêt : rappels manqués signalés dans l'interface, minuteurs expirés
  marqués terminés, aucune sonnerie tardive ; échéances futures conservées.
- Socle local v0.1.0 implémenté et testé (28 tests), interface et échéances de test
  réellement fonctionnelles ; S01/S09 cochés. Voix, IA, profils, HA et ESP32 restent
  à connecter ; le firmware et les services de la maison n'ont pas été modifiés.
- v0.2 : banc vocal navigateur et moteurs locaux implémentés, boucle synthétique
  réelle et lecture testées (42 tests Python, 2 JS). Micro humain et qualité vocale
  à valider, pas encore de conversation IA ; S10 coché, S02 reste en validation.
- Retour utilisateur après essai du banc vocal : « ça fonctionne très bien ».
  S02 validé/coché pour le navigateur ; aucune validation ESP32, serveur cible ou
  choix définitif de timbre déduite de ce retour.
- v0.3 : connecteur conversationnel prêt et testé sans clé réelle, formulaire de
  configuration locale livré ; accès GOAT réel à vérifier après saisie par l'utilisateur.
- Retour suivant : « ça fonctionne bien » pour Command Code. Conversation réelle
  du prototype validée qualitativement ; outils, mesures serveur, profils et HA
  restent à réaliser.
- v0.4 : boucle de reprise navigateur (huit secondes après la fin de la réponse,
  envoi après pause, arrêt) implémentée et testée avec micro et audio artificiels
  (61 tests Python, 25 JS). Le vrai micro n'a pas été ouvert pendant la recette ;
  essai utilisateur et réglage acoustique restent à faire. S12 coché, S06 partiel.
- v0.5 : lumières Home Assistant implémentées et recette simulée réussie (29 tests
  synchrones). Après relance, l'utilisateur confirme que la connexion réelle
  fonctionne et que les lampes se sont éteintes sur ordre : connexion, exécution
  et ciblage validés qualitativement, sans mesure chiffrée. Les cinq tests HTTP
  internes restent hors recette : dans le bac à sable de l'assistant, la boucle
  asyncio et le portail anyio de TestClient se bloquent, y compris sur une
  application FastAPI vide ; le défaut est donc environnemental, pas applicatif.
- Enrôlement décidé et implémenté : six passages (trois phrases deux fois), audio
  conservé, ECAPA-TDNN local, écran et API. Recette réelle sur le service : création,
  enrôlement de deux passages synthétiques, réécoute, identification, suppression.
  Aucun seuil validé ; la reconnaissance reste à brancher.
- Préparation des profils : schéma 2 avec tables profils et empreintes, migration
  testée depuis la version 1, comparaison par cosinus et seuil explicite. Aucune
  capture ni reconnaissance ; le choix des phrases d'enrôlement, de la conservation
  de l'audio brut et du moteur d'empreinte reste ouvert.
