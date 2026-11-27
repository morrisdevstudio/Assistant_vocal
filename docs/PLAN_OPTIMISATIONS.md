# Alfred — plan de réalisation des améliorations

Établi le 13 novembre 2026 à la demande de l'utilisateur, après l'audit global.
La demande porte sur la préparation du plan. Les lots ci-dessous décrivent le
travail à réaliser ; leur rédaction ne vaut ni livraison ni démarrage du code.
L'ordre détaillé et les objectifs chiffrés sont proposés pour l'exécution.

Références : [audit](AUDIT_OPTIMISATIONS_2026-11-13.md),
[checklist](../CHECKLIST.md), [cadrage](../CADRAGE.md).

## Résultats recherchés

1. Une écoute qui récupère ses incidents sans intervention et sans répéter les actions.
2. Une réponse vocale qui commence plus tôt, avec une latence mesurée de bout en bout.
3. Des échanges HA et une interface moins actifs au repos.
4. Une interface quotidienne claire et des sorties audio cohérentes.
5. Une installation maintenable, sauvegardée et préparée pour Debian.

Parakeet, Phonon et les profils actuels constituent la base. Les paramètres de
réveil actifs sont relevés avant intervention. Les permissions/authentification
restent au stade prévu avant production ; leur report n'empêche pas ces lots.
Les essais musicaux/acoustiques différés sont préparés avec des simulations puis
validés avec l'utilisateur lorsqu'il reprend ces essais. Pas de matériel nouveau
nécessaire aux premiers lots ; la disponibilité de Debian sera vérifiée au lot 7.

## Ordre, dépendances et taille relative

| Lot | Livraison | Références | Prérequis de démarrage | Taille relative |
| --- | --- | --- | --- | --- |
| 0 | État de référence, reprise et protocole de mesure | O06, A03, P05 | Audit disponible | Faible |
| 1 | Supervision vocale et mesures communes | O01, T10, S19, I05 | Lot 0 | Moyenne |
| 2 | Catalogue HA partagé et connexions réutilisées | O02, F01/F02 | Mesures du lot 1 disponibles | Moyenne |
| 3 | Actualisations utiles et HTTPS entretenu | O04, A08 | Lot 0 ; états du lot 1 pour l'affichage | Faible à moyenne |
| 4 | Synthèse pendant la génération du texte | O03, S19, S28 | Lot 1 stabilisé ; comparaison après lots 2/3 | Élevée |
| 5 | Sorties audio communes et musique | F03/F04, F06–F09, T05/T07 | Lots 1 et 4 ; connexions du lot 2 | Élevée |
| 6 | Vue quotidienne et diagnostic | O05, A01/A09 | États du lot 1 ; capacités réelles du lot 5 | Moyenne |
| 7 | Exploitation, coût et maintenance finale | O06, A02/A03, S08, P04 | Lots retenus stabilisés ; hôte pour Debian | Moyenne à élevée |

Les lots 2 et 3 peuvent être développés séparément après le socle ; leur activation
et leurs mesures restent successives pour attribuer les gains. Une maquette du
lot 6 peut être préparée avant le lot 5 ; son affichage final doit refléter les
capacités effectivement livrées. Les extractions de modules nécessaires sont
effectuées dans chaque lot, plutôt qu'une réécriture globale préalable.

## Lot 0 — Préparer une reprise fiable et une référence mesurable

- Inventorier code, dépendances, modèles et configurations utiles au fonctionnement.
- Préparer un état de retour local vérifié : exclusions de secrets, audio et données
  privées, historique Git local du code, copie privée des données/configurations.
  Vérifier qu'un retour de code reste compatible avec le schéma des données.
- Relever l'état initial des services et réglages sans afficher de secret.
- Constituer un corpus synthétique fixe : lumières simples/composées, minuteurs,
  musique simulée, question courte/longue, silence, arrêt et réponse en erreur.
- Définir les relevés à froid/à chaud et un essai humain distinct sur l'ESP32.

**Livrable :** procédure de reprise et tableau de référence reproductible.
**Sortie du lot :** restauration vérifiée sur une copie isolée, fichiers privés
exclus de l'historique et corpus sans action réelle involontaire.
Référence de tests issue de l'audit : 769 Python réussis/deux ignorés, 43 JS réussis.

## Lot 1 — Stabiliser l'écoute et relier les mesures

- Centraliser les transitions veille, capture, traitement, lecture et récupération.
- Identifier la session/le tour propriétaire ; ignorer les fins et callbacks périmés.
- Distinguer renouvellement périodique, flux absent, lecture terminée sans événement,
  échec d'arrêt et échec de relance ; conserver les erreurs techniques sans contenu privé.
- Publier la santé de chaque composant et l'âge du dernier progrès. Une veille
  désactivée volontairement reste un état normal, distinct d'une panne.
- Relier le diagnostic existant à fin de parole, STT, catalogue, IA, premier bloc,
  demande du lecteur et fin de lecture. Ajouter un indicateur du retard de boucle serveur.
- Afficher médiane/p95, erreurs et part de commandes sans IA, avec taille du corpus.
  Le premier son physique est une mesure acoustique séparée du téléchargement audio.

**Livrable :** supervision exploitable et bilan de latence commun navigateur/ESP32.
**Sortie du lot :** cent cycles simulés sans blocage définitif ni action dupliquée ;
incidents de transport et événements tardifs couverts ; essai proposé de vingt
commandes humaines successives, retour en veille et silence sans appel IA.
La partie logicielle peut avancer avant la clôture acoustique de T10.

## Lot 2 — Réduire les échanges Home Assistant

- Introduire un service de catalogue partagé, avec une seule synchronisation en cours.
- Séparer métadonnées relativement stables et états/capacités à vérifier pour l'action.
- Réutiliser les connexions HTTP ; reconnecter proprement la liaison de synchronisation.
- Invalider les registres/expositions modifiés et appliquer les exclusions locales.
- Réutiliser une vue cohérente lors de la préparation de commandes composées.
- Compter appels, connexions, temps catalogue et jetons de contexte par commande.

**Livrable :** catalogue et clients partagés utilisés par les chemins local et IA.
**Sortie du lot :** réduction mesurée des lectures complètes ; aucune nouvelle action
sur cible exclue, groupe modifié, entité retirée d'Assist ou capacité devenue invalide.
Tester les changements entre préparation et exécution ainsi que HA indisponible.
Le cache ne donne jamais à lui seul une autorisation d'exécuter devenue incertaine.

## Lot 3 — Alléger la page et entretenir HTTPS

- Remplacer les minuteries indépendantes par une actualisation coordonnée : vue
  affichée, page visible, opérations en cours et retour au premier plan.
- Garder les décomptes de minuteurs côté navigateur entre deux synchronisations.
- Ajouter délais, annulation et absence de requêtes superposées ; ralentir après erreur.
- Mettre en cache les JS/CSS versionnés et conserver les réponses privées sans cache.
- Renouveler le certificat, vérifier nom/adresses et dates, documenter la confiance
  PC/téléphone et prévoir un contrôle d'expiration. L'installation de confiance
  sur les appareils reste une étape utilisateur lorsque nécessaire.

**Livrable :** interface moins active et accès HTTPS entretenu.
**Sortie du lot :** comptage réseau réel avant/après. Objectifs proposés : au plus
soixante requêtes de suivi par minute au repos sur une page visible et arrêt du
suivi applicatif d'une page cachée ; synchronisation immédiate au retour.
Conserver la fermeture du micro navigateur lorsque la page passe en arrière-plan.
Valider aussi minuteurs, connexion perdue, mise à jour des assets et accès téléphone.

## Lot 4 — Avancer le début de la réponse vocale

- Créer un flux de phrases complètes stabilisées vers un producteur TTS à file bornée.
- Faire calculer la suite du texte pendant la génération/lecture du premier audio.
- Utiliser le même contrat d'événements pour navigateur et ESP32, avec un seul
  propriétaire de la lecture et conservation de la voix sélectionnée sur le tour.
- Borner mémoire et audio en attente ; propager arrêt, annulation et erreur entre
  producteur IA, synthèse et lecteur. Un calcul natif déjà parti ne livre aucun
  audio périmé et ne déclenche aucun bloc ou outil supplémentaire après annulation.
- Valider la préparation des nombres/négations aux frontières des phrases et
  réserver les confirmations d'action aux résultats effectifs des outils.
- Étudier les trames natives Phonon seulement si le premier palier laisse un coût
  significatif de synthèse. Vérifier alors l'API officielle disponible avant de figer
  le protocole ; ce second palier reste conditionnel aux mesures.

**Livrable :** réponse progressive de bout en bout, activable séparément pour recette.
**Sortie du lot :** premier son plus tôt sur réponses longues à corpus identique,
sans dégradation constatée des réponses courtes ; pas de coupure aux jonctions,
pas de lecture périmée, pas de confirmation prématurée ni de rejeu d'action.
Le gain et les limites sont consignés avant activation courante.

## Lot 5 — Unifier les sorties et achever leurs raccordements

- Définir puis tester la politique entre réponse, sonnerie, annonce et rappel.
  Priorités, préemption et reprise constituent des choix à expliciter, pas des
  décisions déduites de ce plan. L'interruption vocale reste une recette distincte.
- Réutiliser le transport ESP32 existant pour les annonces et rappels, puis raccorder
  l'atténuation musicale au cycle réveil/conversation/reprise/erreur.
- Restaurer le volume sans écraser une modification manuelle ; conserver les règles
  actuelles par étage, de confidentialité et de rappel manqué après redémarrage.
- Exposer séparément enregistrement, mise en file, envoi et lecture confirmée quand
  celle-ci peut l'être ; maintenir la prévention des doublons après résultat incertain.

**Livrable :** gestionnaire audio commun sur le terminal Bureau, puis extension.
**Sortie du lot :** collisions simulées, arrêt et indisponibilité couverts ; essais
humains ciblés des sonneries/annonces/rappels et de la musique à leur reprise.
L'arbitrage de plusieurs terminaux reste lié à T06 : le succès sur Bureau seul
ne clôture pas T07 ni la recette multiroom.

## Lot 6 — Livrer une interface quotidienne

- Préparer une vue « Alfred » : écoute réelle, préparation, réponse, reconnexion,
  dernier échange, parler/arrêter et échéances utiles.
- Regrouper moteurs, seuils, modèles et bancs d'essai dans les réglages/diagnostics.
- Afficher l'état provenant du service et distinguer rappel enregistré, diffusion
  disponible et livraison non confirmée. Afficher les fonctions indisponibles clairement.
- Conserver les parcours existants et l'état des formulaires pendant la navigation.
- Ajouter les indicateurs utiles du lot 1, sans exposer de secrets ni de profils privés.

**Livrable :** interface adaptée ordinateur/téléphone avec diagnostic accessible.
**Sortie du lot :** vérification visuelle réelle, clavier/petits écrans, erreur réseau,
états de récupération et essais des tâches courantes. Si l'outil navigateur reste
bloqué, la validation visuelle est explicitement à faire avec l'utilisateur.

## Lot 7 — Préparer l'exploitation durable et réduire le coût mesuré

- Isoler les attentes SQLite de la boucle audio tout en conservant un ordonnanceur
  unique et la fin de transaction avant libération de son verrou à l'arrêt.
- Terminer les extractions ciblées de routes, orchestration et client worker générique.
- Produire un bilan d'usage depuis les diagnostics : requêtes et jetons réellement
  disponibles, familles de commandes et limites de collecte. Réduire contexte/outils
  sur corpus de non-régression ; pas de tarif ou coût extrapolé sans données vérifiées.
- Préparer le service Debian, répertoires persistants, arrêt propre, redémarrage,
  état de santé et contrôle d'expiration. Vérifier ressources de l'hôte avant migration.
- Tester sauvegarde/restauration des données privées dans leur emplacement protégé.
  Reconfigurer les secrets sur Debian selon la procédure prévue ; DPAPI reste lié à Windows.
- Mettre à jour l'état courant et la procédure de retour ; conserver les décisions
  historiques clairement identifiées. Traiter authentification/droits avant production
  conformément au report existant, sans les déclarer livrés par ces optimisations.

**Livrable :** installation supervisée et reprise vérifiée ; bilan coût/usage.
**Sortie du lot :** arrêt/redémarrage, worker défaillant, verrou SQLite, retour de
version et restauration isolée validés. Migration réelle conditionnée à l'hôte disponible.

## Règle de livraison de chaque lot

Chaque lot fournit un changement relisible, ses tests ciblés, les mesures avant/après,
les limites restantes et un retour arrière. Utiliser les tests du comportement
modifié, puis la suite complète aux jalons d'intégration ; ne pas relancer les tests
optionnels réels ni provoquer une action dans la maison pour un simple contrôle de code.
Les recettes humaines complètent les tests logiciels et restent marquées ouvertes
jusqu'au retour effectif. Mettre à jour `CHECKLIST.md` et `CADRAGE.md` à chaque livraison.

Le prochain lot exécutable est le **lot 0**, puis le **lot 1**. Les tailles indiquées
sont relatives ; aucun calendrier ni pourcentage de gain n'est engagé avant les
mesures de référence et la disponibilité des recettes matérielles.
