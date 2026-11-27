# Alfred — audit global et optimisations proposées

Revue du 13 novembre 2026. Propositions à arbitrer, sans nouvelle priorité validée.
Suite à la demande suivante, voir le [plan de réalisation](PLAN_OPTIMISATIONS.md).
Audit du code Python/Rust/JavaScript, de la documentation et des routes locales.
Aucune commande domotique, requête IA, synthèse, modification de réglage ou
réactivation d'un moteur historique déclenchée pour cet audit.

## État vérifié et limites

- Suite Python : **769 réussites, deux tests optionnels ignorés** en 56,82 s.
- Suite JavaScript : **43 réussites**. Ce sont des tests automatisés, pas une recette acoustique.
- ESP32 connecté, veille STT active au relevé. Aucun gel observé pendant cette revue.
- Routes de statut : environ **quatre à douze millisecondes**, trois lectures par route,
  PC client et serveur sur la même machine. Petit échantillon, pas un p95 ni une mesure mobile.
- Catalogue HA : **43 entités, 80,8 ms**, un seul GET depuis Alfred. Pas une moyenne.
- Le certificat de développement expire le **3 novembre 2026 à 13:10:05 UTC**.
- Le compteur de récupération inclut le renouvellement périodique : son augmentation
  seule ne permet pas de conclure à un nouveau gel.
- Aucun fichier suivi par Git dans cette copie du projet (`git ls-files` vide).
- Inspection visuelle Firefox bloquée par l'outil : vérification des URL non prise
  en charge dans le navigateur Windows actuel. Les remarques d'ergonomie ci-dessous
  viennent des sources HTML/JS, pas d'une recette visuelle ordinateur/téléphone.

## Recommandations par ordre proposé

### 1. Fiabiliser l'orchestration vocale et observer chaque récupération

**Constat.** Le correctif T10 ajoute une récupération du flux et une garde de lecture.
Le même compteur compte renouvellements et récupérations. Le contrôle `/health`
ne reflète que l'ordonnanceur ; une réponse HTTP 200 ne démontre pas que le micro,
le détecteur ou les workers vocaux fonctionnent. Les phases et annulations sont
réparties dans plusieurs méthodes du terminal.

**Proposition.** Centraliser les transitions et leur propriétaire, associer un
identifiant de session aux événements tardifs et distinguer arrêt demandé,
renouvellement prévu, absence de trames et fin de lecture perdue. Ajouter une santé
par composant avec âge du dernier progrès et erreur technique bornée. Distinguer
processus vivant et capacité réelle à traiter une demande, sans appel IA de contrôle.

**Validation.** Cent cycles simulés réveil/commande/réponse/reprise/silence,
événements retardés ou doublés, panne Wi-Fi, worker arrêté, puis essai humain
prolongé. Ne jamais rejouer une action pour récupérer le transport.

Impact utilisateur très élevé ; effort moyen. Références : `alfred/terminal.py`
(`_check_wake_word`, `_start_capture`, `_announcement_finished`), `alfred/app.py:617`.
Suite des tâches **T10, A04**, proposition **O01**.

### 2. Mesurer le délai réellement ressenti avant d'optimiser les moteurs

**Constat.** Des temps STT/IA/TTS, téléchargements et diagnostics existent déjà.
Ils ne forment pas encore un bilan consultable du réveil jusqu'au premier son.
La génération du premier bloc Phonon et la demande HTTP du lecteur ne prouvent
pas l'instant du son audible. Les réponses ESP32 à TTS différé sont journalisées
avant la synthèse effectuée par le terminal : leurs mesures doivent être raccordées.

**Proposition.** Réutiliser `Diagnostics` et l'identifiant d'échange : fin de parole,
STT, résolution/catégorie de commande, catalogue HA, premier texte IA, premier
bloc audio, demande du lecteur, notification de lecture quand disponible et fin.
Afficher médiane, p95, taux d'erreur et part des commandes exécutées sans IA.
Une mesure acoustique distincte restera nécessaire pour le premier son physique.

**Validation.** Corpus stable de commandes locales et questions, à chaud/à froid,
sur navigateur et ESP32 ; aucun pourcentage de gain annoncé avant comparaison.
Impact élevé ; effort modéré. **S19, P05, I05 ; proposition O01.**

### 3. Faire commencer la réponse vocale plus tôt

**Constat.** `alfred/app.py:1164` consomme le flux IA, puis lance la synthèse une
fois la réponse terminée. L'ESP32 joue des blocs successifs, mais chaque bloc
Phonon est encore un WAV complet : `PhononVoice.synthesize` appelle `model.synth`.
Le navigateur attend aussi son audio complet. Le streaming existant ne couvre
donc pas toute la chaîne IA → Phonon → lecteur.

**Proposition.** Première étape : synthétiser une phrase complète stabilisée
pendant que l'IA prépare la suite. Étape suivante, seulement si le gain le justifie :
transporter les trames natives Phonon. Préserver voix et paramètres sur tout le
tour, borner la file audio, vérifier les nombres français aux frontières et
réserver toute confirmation d'action au résultat effectif des outils.

**Validation.** Premier son, fluidité entre phrases, interruption, erreur après
action déjà exécutée, réponses avec nombres et négations. Conserver le moteur
Phonon retenu et les profils actuels. Impact potentiellement élevé sur les réponses
longues ; effort élevé. **S19, S28 ; proposition O03.**

### 4. Éviter les reconstructions complètes du catalogue Home Assistant

**Constat.** Chaque `HomeCatalog.snapshot` ouvre un WebSocket, s'authentifie et
enchaîne huit lectures. Le catalogue est redemandé pour le contexte IA, la
préparation et les vérifications avant les actions. Ces derniers contrôles sont
utiles ; leur coût augmente avec les commandes composées. `LightActions.catalog`
recrée un `HomeCatalog`. Les clients HTTP des services sont également créés puis
fermés à répétition.

**Proposition.** Partager un catalogue de métadonnées et une synchronisation
unique, réutiliser les connexions HTTP et invalider explicitement les changements
de registres/exposition. Relire les exclusions locales et les états/capacités
nécessaires juste avant une action. Ne pas remplacer un contrôle d'autorisation
par un cache ancien ; refuser une exécution si sa validité ne peut être établie.

**Validation.** Compter connexions et appels par commande ; modifier une exclusion,
un groupe et une capacité entre préparation et exécution ; tester HA indisponible.
Le principe de réutilisation des connexions est décrit dans la
[documentation HTTPX](https://www.python-httpx.org/advanced/clients/).
Impact moyen à élevé selon les commandes ; effort moyen. **F01/F02 ; proposition O02.**

### 5. Réduire le travail de l'interface au repos

**Constat.** Hors tests et sans requêtes initiales, les minuteries JS représentent
environ **220 GET/minute par page visible** : trois routes toutes les 1,5 s,
conversation ESP32 chaque seconde, statut ESP32 et réglages du réveil toutes les
trois secondes. Les changements de vue masquent les panneaux sans désactiver ces
boucles. Certaines vérifient `document.hidden`, d'autres non. C'est un calcul des
fréquences du code, pas une capture réseau ; les gardes et temps de réponse peuvent
réduire le nombre réel. Le middleware impose aussi `Cache-Control: no-store` aux
JS/CSS ; ce comportement est confirmé sur `app.js`.

**Proposition.** Actualiser seulement la vue utile ; au repos ralentir les statuts,
rafraîchir immédiatement après action ou retour au premier plan. Mutualiser les
états ; envisager ensuite un flux d'événements unique si nécessaire. Ajouter des
délais et une protection contre les requêtes superposées. Cacher uniquement les
assets statiques versionnés, garder les données personnelles et audio sans cache.

Références : `alfred/static/app.js:69`, `terminal-panel.js:126`,
`wake-panel.js:135`, `alfred/app.py:607`. Principes documentés par MDN :
[visibilité de page](https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API),
[contrôle du cache](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control).
Impact sur activité réseau, batterie mobile et chargement ; gain vocal direct
probablement limité au vu des routes rapides au repos. Effort faible à moyen.
**A01/A07 ; proposition O04.**

### 6. Passer du banc d'essai à une interface d'usage quotidien

**Constat.** La page d'accueil dit « Que voulez-vous tester ? ». Le laboratoire
mélange conversation, tests, import de modèles, moteurs et seuils. Les rappels
sont présentés comme annoncés alors que `AnnouncementService.send` utilise encore
le chemin HA, sans raccordement au terminal direct actuel.

**Proposition.** Une vue « Alfred » avec état écoute/pensée/réponse/reconnexion,
dernier échange, parler/arrêter et échéances utiles. Déplacer réglages de moteurs,
tests et import de modèles dans « Réglages et diagnostic ». Présenter séparément
« rappel enregistré » et « diffusion disponible ». Montrer le moteur et la phrase
actifs depuis le service, sans libellés historiques ambigus.

**Validation.** Recette visuelle mobile/ordinateur et essais d'un utilisateur qui
ne connaît pas les moteurs. Aucune refonte ni modification de réglage réalisée.
Impact quotidien élevé ; effort moyen. **A01, F06/F07/T07 ; proposition O05.**

### 7. Compléter les fonctions qui ont une sortie audio commune

**Constat.** La sonnerie directe existe. Annonces et rappels passent encore par un
autre chemin ; le parcours ESP32 ne raccorde pas l'atténuation musicale comme le
navigateur. Ce sont des fonctions à achever, plutôt que des gains CPU.

**Proposition.** Un gestionnaire commun des sorties : réponse, sonnerie, annonce,
rappel, priorités, interruption/reprise et restauration du volume. Réutiliser la
voix active et le transport direct. Éviter une seconde connexion cliente audio.

**Validation.** Rappel pendant conversation, minuteur pendant lecture, arrêt,
modification manuelle du volume, terminal absent et redémarrage sans double annonce.
**F03/F04/F06–F09, T05/T07** existants ; aucune nouvelle priorité décidée.

### 8. Rendre l'exploitation durable et éviter les gels de boucle serveur

**Constat.** Certificat expiré ; démarrage actuel lié à la session Windows et
aucune reprise automatique configurée sur la tâche (`RestartCount=0`).
`store.tick` est synchrone dans une tâche asynchrone : en cas de verrou SQLite,
l'attente de connexion peut atteindre cinq secondes et retarder les autres tâches.
C'est un risque identifié dans le code, pas la cause démontrée du gel ESP32.

**Proposition.** Renouveler le certificat et prévoir son entretien ; sur Debian,
service supervisé et arrêt propre des workers. Isoler le travail SQLite pouvant
attendre, en conservant un seul ordonnanceur et en attendant sa transaction avant
de libérer le verrou à l'arrêt. Vérifier sauvegarde/restauration et récupération.
Le traitement du code bloquant est expliqué dans la
[documentation FastAPI](https://fastapi.tiangolo.com/async/).

Authentification et droits restent **différés par l'utilisateur avant production** :
ce constat ne relance pas ce chantier et ne bloque pas le prototype.
Impact fiabilité élevé ; effort variable. **A02/A03/A08, P04/P06 ; proposition O06.**

### 9. Réduire le coût et simplifier la maintenance sans changer de modèle à l'aveugle

**Constat.** Le contexte conversationnel contient le catalogue d'appareils et de
nombreux outils ; les compteurs de jetons sont déjà collectés quand le fournisseur
les renvoie. `app.py` dépasse 1 400 lignes, `terminal.py` 1 100 lignes. Le client
Phonon hérite d'un client nommé Chatterbox, ce qui brouille le moteur actif.
La documentation conserve des états historiques contradictoires.

**Proposition.** Réutiliser les usages existants pour un bilan par famille de
commande, puis réduire le contexte et les outils transmis seulement si les tests
de compréhension restent bons. Pas de routage de modèle ni de nouvelle dépense
par défaut. Extraire progressivement routes, orchestration et protocole worker
générique. Établir une page courte de l'état actuel, distincte du journal historique.
Préparer un premier historique Git local en vérifiant les exclusions, puis un
retour arrière reproductible. Aucun ajout/commit/push réalisé pendant cet audit.

Impact coût/maintenance ; effort moyen. **S08, I05, A02/A03 ; proposition O06.**

## Ordre de réalisation conseillé, non validé

1. Stabilité et mesures (T10/O01), entretien HTTPS (A08).
2. Catalogue et actualisations (O02/O04), avec mesures avant/après.
3. Premier son plus rapide (O03), guidé par le bilan de latence.
4. Interface quotidienne et sorties audio communes (O05, F06–F09/T07).
5. Exploitation Debian, sauvegardes et maintenance (O06), selon disponibilité de l'hôte.

Les gains ne sont pas additionnés et aucun gain chiffré n'est promis. Les reports
utilisateur et les validations humaines déjà requises restent applicables.
