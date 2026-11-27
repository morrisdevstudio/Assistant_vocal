# Alfred — compréhension naturelle et recette

## Décision et périmètre

Plan approuvé le 13 novembre 2026 et implémentation engagée : conserver Parakeet,
Phonon, le transport ESP32 et le modèle Command Code configuré. Aucun comparatif ni
changement de modèle. Livraison progressive : lumières d'abord, extensions après
recette. La cible de 99 % n'est pas un résultat acquis.

## Parcours commun livré

Les formulations certaines passent par le traitement local ; les autres arrivent à
l'IA munie de l'outil structuré `controler_lumieres`. Les deux passent par le même
exécuteur. L'outil accepte une à quatre actions préparées avant la première écriture :
marche/arrêt, état, luminosité absolue ou relative, couleurs usuelles et température
de blanc en kelvins. Le catalogue, les capacités effectives, les membres des groupes
et les exclusions sont contrôlés côté serveur. Un groupe de lumières exposé autorise
ses descendants masqués uniquement via ce groupe, même imbriqué. Ils restent absents
du catalogue public et ne deviennent pas des cibles individuelles. Toute exclusion
explicite du groupe, d'un sous-groupe ou d'une lampe bloque ce chemin ; cycles et
membres inconnus sont refusés avant écriture. Une pièce explicite ne devient jamais
une commande globale. Une capacité absente ou des lampes partiellement compatibles
provoquent une clarification sans modification partielle.

Chaque action est identifiée, envoyée sans retry puis relue. Un résultat non confirmé
arrête la suite. Les statuts distinguent confirmation, proposition/clarification,
refus, interruption, résultat incertain et exécution partielle. Une reprise n'est
pas déclenchée par un échec de lecture vocale. Les accusés d'exécution sont produits
par l'exécuteur ; les textes libres du modèle ne prouvent jamais une action.

## Conversation

Six échanges pendant cinq minutes d'inactivité, séparés par source, session et
locuteur reconnu. Les commandes locales alimentent aussi le contexte : « rallume-la »,
« pareil dans le salon » et « non cinquante pour cent ». Une référence incertaine
n'est pas appliquée. La fenêtre acoustique de reprise de huit secondes reste inchangée.

Une remarque implicite prépare une proposition, sans envoi ; « oui » ne vaut que pour
la proposition de la même session pendant trente secondes. Une nouvelle demande,
« non » ou « laisse tomber » la supprime. Les cibles sont revérifiées lors du oui.
« Stop » interrompt les actions en attente et conserve sa fonction d'arrêt des sonneries ;
aucune promesse de défaire une commande déjà envoyée. Un résultat incertain invalide
la référence récente pour ne pas reprendre par erreur une ancienne cible.

## Historique local

Les prochains échanges sont enregistrés dans `.local/data/diagnostics.sqlite3` :
transcription, réponse, source, route, intentions, cibles, résultats, identifiants,
durées et compteurs d'usage disponibles. Aucun audio brut ni identifiant d'API.
Conservation : sept jours ET cent Mo ; purge à l'écriture, à la consultation
et chaque minute pendant le fonctionnement, même sans conversation.
Cette base n'est exposée par aucune route HTTP. Les anciens échanges antérieurs à
cette livraison n'ont pas pu être reconstitués.

Consultation sur le PC :

```powershell
.\.venv\Scripts\python.exe -m alfred.diagnostics --limit 30
.\.venv\Scripts\python.exe -m alfred.diagnostics --export .local/diagnostic-export.json
.\.venv\Scripts\python.exe -m alfred.diagnostics --annotate IDENTIFIANT --label cible --note "Mauvaise pièce"
```

Labels : `correct`, `transcription`, `comprehension`, `action`, `cible`. Ces données
restent locales et ne doivent pas être ajoutées à la documentation versionnée.
L'authentification de l'interface et les permissions par profil restent les travaux
I01/I03 différés par l'utilisateur ; ne pas prétendre qu'elles sont mises en place.

## Réglages et extensions

```powershell
.\.venv\Scripts\python.exe -m alfred.intent_settings
.\.venv\Scripts\python.exe -m alfred.intent_settings --disable lights
.\.venv\Scripts\python.exe -m alfred.intent_settings --enable lights
```

Les réglages sont relus à chaque demande. Désactiver un relais retire ses outils IA
et les interdit aussi côté serveur ; les commandes locales existantes restent disponibles.
Familles : `lights`, `music`, `shopping`, `announcements`, `calendar`, `timers`, `devices`.
Les outils déjà utilisés pour musique/courses/annonces/calendriers restent actifs.
Les nouveaux outils typés de minuteur et d'appareil sont livrés mais désactivés par
défaut, en attente de la recette des lumières puis de leur propre recette. Ils réutilisent
les exécuteurs locaux, y compris bornes, capacités et exclusions ; pas de service libre.
Les lots composés concernent les lumières ; mélanger plusieurs familles d'outils dans
un même tour est refusé avant exécution. La généralisation des lots à plusieurs familles
reste à effectuer après les recettes, sans prétendre à une transaction entre appareils.
Chauffage et lancement de nouvelles applications TV restent hors périmètre.

## Recette reproductible

Un corpus exploratoire de cinq cents formulations synthétiques est généré par
`alfred.intent_benchmark` : quatre cents pour le développement et cent de validation.
Les familles de formulations sont distinctes entre les deux lots. Elles ne remplacent
pas les essais humains, les bruits du logement ou les vrais erreurs de transcription.
Le simulateur ne possède aucun accès Home Assistant ; ses écritures sont en mémoire.

```powershell
# Afficher des cas, sans IA ni appareils
.\.venv\Scripts\python.exe -m alfred.intent_benchmark --limit 5
# Appeler le modèle existant et son quota ; appareils toujours simulés
.\.venv\Scripts\python.exe -m alfred.intent_benchmark --live --limit 30
.\.venv\Scripts\python.exe -m alfred.intent_benchmark --live --split holdout --limit 100
```

La première recette sur trente cas de développement donne trente intentions exactes,
médiane 1,85 s et p95 2,695 s, sur texte et appareils simulés. Ce n'est ni le p95
vocal ni une garantie de 99 %. Un premier smoke test vérifie aussi six demandes avec
le modèle réel, sans lampe physique. Résultats détaillés sous `.local/performance`.
Validation indépendante : cent cas synthétiques sur cent correctement interprétés,
médiane 1,8005 s et p95 2,476 s. Pas de retouche du prompt à partir de ce lot.
Suite complète : 722 tests Python réussis, deux ignorés ; 43 tests JavaScript réussis.
Après les correctifs de maintenance, 263 puis 92 tests ciblés réussis.
Lecture du véritable HA vérifiée pour la lumière du bureau avec le pilote d'écriture
explicitement bloqué : résultat confirmé, 901 ms hors reconnaissance/IA/synthèse. Service
redémarré, santé/catalogue HTTP 200, modèle conservé, ESP32 reconnecté et veille
réarmée. Un tour applicatif de contrôle a vérifié voix générée et journal réels,
sans action d'appareil. Usage des deux lots : 294 211 tokens d'entrée et 12 690 de
sortie, quota partagé GOAT. Aucun achat de crédit ni nouvel abonnement. Les chiffres
ne permettent pas de prédire seuls le coût ou la fiabilité d'un mois d'usage.

La recette humaine doit couvrir formulation libre, reprise, corrections, commandes
composées, négations, homonymes et exclusions. Annoter les vrais échecs dans le journal.
Mesurer le réveil, la transcription, les bonnes cibles, l'exécution et l'état réel,
ainsi que la latence jusqu'à l'envoi et celle de la parole. Une clarification inutile
sur une demande claire compte comme un échec ; une vraie ambiguïté doit être clarifiée.
Aucune publication d'un taux de réussite quotidien à partir du seul corpus synthétique.


## Correctif groupes du 13 novembre

Pilotage validé par l'utilisateur : un groupe exposé autorise ses membres masqués
via ce groupe uniquement. Graphe de descendants conservé dans le catalogue interne
de contrôle, jamais dans la réponse HTTP ni dans les cibles individuelles du modèle.
Exclusions explicites, sous-groupes, cycles, membres absents et déduplication couverts.
Les références conversationnelles conservent la cible autorisée du groupe.
Préparation réelle de Moodlight : trois lampes autorisées via le groupe, toujours
masquées individuellement ; aucune écriture HA pendant le contrôle. Suite complète
733 tests réussis/deux ignorés ; après attente bornée des états, 294 tests ciblés
réussis. Service redémarré, ESP32 connecté et veille réarmée. Recette humaine encore
à confirmer. Aucun réglage d'exposition Home Assistant n'a été modifié.

## Lot musique et volume

Le lecteur `media_player.amp_salon_2` est maintenant sélectionné dans Alfred ; aucune
autre cible n'est substituée. Le catalogue réel confirme son exposition, ses
capacités et l'absence d'exclusion Alfred. L'API Music Assistant renvoie dix-huit
playlists : douze locales et six Qobuz, sans homonyme exact ; la recherche affiche
le fournisseur pour départager les futures collisions. L'URI est conservée dans `music.json`, et
une absence de playlist par défaut produit une clarification avant toute lecture.

Les formulations locales et l'outil IA partagent `MusicActions` et le contexte
général. Marche/arrêt, reprise, pistes, sourdine, volume exact et variation de cinq
points sont couverts. « Baisse un peu » est ambigu sans contexte musical ; Alfred
demande musique ou lumière. La recherche précise `play_media` reste déclarée
envoyée sans certitude de la piste ; la playlist par défaut et les réglages
vérifiables peuvent être confirmés après relecture.

Le volume normal est conservé séparément de l'atténuation temporaire. Un réglage
demandé pendant une réponse vise le volume normal, puis devient la valeur à
restaurer si aucun changement manuel externe ne l'a remplacé. Une erreur ou une
réponse perdue arrête la suite sans retentative. Les lots mixtes restent refusés.

Corpus musical synthétique : 104 formulations, dont vingt de validation distincte.
Avec le modèle actuel et des appareils simulés, le développement passe 20/20 et la
validation indépendante 20/20 ; p95 de 2,263 s pour cette dernière. Ces chiffres ne
valident pas la recette vocale ou acoustique. La suite complète doit être relancée
après les derniers tests ciblés avant le redémarrage du service.

## Lot minuteurs

Le même service de minuteurs historique reste l'autorité : stockage SQLite,
étage du terminal, numéros stables, limite d'une seconde à sept jours et sonnerie
existante. `TimerActions` réunit la compréhension locale et l'outil IA ; il accepte
« mets/lance/programme un minuteur », « dans cinq minutes … », « … d'une heure »,
« ajoute deux minutes au minuteur », la consultation, l'annulation et l'arrêt de
sonnerie. Une négation ou un mélange lumière/minuteur produit une clarification.

Les quatre actions d'un tour sont ordonnées. Une interruption n'annule pas les
minuteurs déjà créés ; un échec n'entraîne pas de répétition. L'outil IA est proposé
uniquement si le relais `timers` est actif et reçoit le contexte du terminal. La
valeur par défaut est désormais active après la recette, tandis que le relais
appareils reste désactivé jusqu'à sa propre recette.

Recette synthétique : 20/20 développement et 20/20 validation indépendante, sur un
stockage temporaire. La suite complète compte 763 tests Python réussis/deux ignorés
et 43 tests JS réussis. Service redémarré avec six minuteurs existants préservés,
santé et échéances HTTP 200, ESP32 connecté et veille réarmée. La production réelle
d'une sonnerie, le micro et la reprise d'un minuteur après redémarrage restent à
valider humainement.
