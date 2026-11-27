# Alfred — prototype local

**Rappels :** les calendriers personnel et familial Home Assistant sont la source
des données. Alfred peut les consulter, y créer des rappels ponctuels ou
hebdomadaires, puis modifier ou supprimer un événement ciblé ; seuls ses rappels
identifiés sont annoncés. L'ancien banc local est suspendu et ses données conservées.
Les minuteurs restent gérés par Alfred.

Prototype v0.6 : minuteurs commandés à la voix et au clavier, interface française,
échéances SQLite, transcription locale et synthèse Phonon locale sur CPU,
commandes de lumière Home Assistant et connecteur conversationnel Command Code. Le connecteur demande votre clé propre à
Alfred ; un code installé ne signifie pas que l'accès au compte est déjà vérifié.
La reconnaissance vocale expérimentale est raccordée mais reste inactive tant que
sa calibration n'est pas validée ; les permissions par personne, la mémoire durable
ne sont pas encore livrées. Un ESP32 est raccordé en prototype direct : lecture
validée à l'écoute, transport micro vérifié, conversation humaine à confirmer.
Music Assistant reste disponible ; le lecteur de test ESP32 a été désélectionné ;
les rappels actifs sont
stockés dans les calendriers Home Assistant ; l'ancien banc local reste suspendu.

## Installer sur Debian

### Première installation

Exécuter ces commandes sur Debian 13 amd64. Le fichier de source contient la
clé publique du dépôt APT d’Alfred.

```bash
sudo apt update &&
sudo apt install -y curl ca-certificates &&
curl -fsSL 'https://github.com/morrisdevstudio/Assistant_vocal/releases/latest/download/alfred-home.sources' -o alfred-home.sources &&
sudo install -m 0644 alfred-home.sources /etc/apt/sources.list.d/alfred-home.sources &&
sudo apt update &&
sudo apt install alfred-home
```

### Mettre à jour Alfred

APT récupère la dernière version stable publiée sur GitHub avec la source déjà
configurée.

```bash
sudo apt update &&
sudo apt install --only-upgrade alfred-home
```

L’installeur sauvegarde les données avant la bascule, conserve les réglages et
les modèles, puis contrôle le redémarrage du service.
[Guide d’installation et de configuration Debian](https://github.com/morrisdevstudio/Assistant_vocal/blob/v0.6.0/deploy/debian/README.md)

### Instance de développement Debian

La VM de dev exécute le clone modifiable plutôt que le paquet APT :

```bash
systemctl --user start alfred-dev.service
```

Ouvrir `https://<IP_VM>:8765`. Les données et modèles sont dans
`/home/<utilisateur>/projects/repos/Assistant_vocal/.local`. Le type de CPU Proxmox `host`
reste recommandé pour le wheel officiel ; à défaut, `ptts` est reconstruit
depuis les sources.

## Démarrer sur Windows

**Transcription retenue le 9 novembre : stack Murmure 1.11.3 autonome**, Parakeet
TDT 0.6B v3 INT8 sur CPU avec ONNX Runtime, dictionnaire, nettoyage et formatage.
Elle est le seul STT conservé pour le navigateur et l'ESP32. Préparer les ressources avec
`python -m alfred.setup_parakeet --murmure-settings CHEMIN`, puis
relancer Alfred. Voir STT.md et [le worker](native/murmure-stt/README.md).
Dans le laboratoire,
**Tester la transcription ESP32** puis K2 affiche les mots reconnus sans appel
IA ni commande de maison. Le mode **Test audio** sert à essayer le navigateur.

**Nettoyage du 11 novembre :** anciennes transcriptions et comparatifs retirés,
modèles obsolètes mis à la Corbeille, dépendances devenues inutiles désinstallées.
La fin de parole conserve exactement le modèle Silero v6, chargé directement
avec ONNX Runtime et préparé par `python -m alfred.setup_vad` (ou automatiquement
lors de la préparation Parakeet). Murmure peut rester fermé ; aucun STT distant.

Depuis la racine du projet, Python 3.12 ou plus récent :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m alfred
```

Ouvrir <http://127.0.0.1:8765>. Arrêter avec Ctrl+C dans le terminal.
Le menu donne accès à une fonction à la fois : voix/conversation, minuteurs et
rappels, lumières, musique, courses, annonces, profils et connexion IA. Le
laboratoire vocal s'ouvre par défaut ; les réglages secondaires et l'aide se
déplient à la demande. L'étage du navigateur se choisit en haut de la page et
s'applique aussi aux commandes vocales. Les liens comme `/#music` permettent
d'ouvrir directement un module ; changer de vue conserve les champs saisis.
Autre port : `python -m alfred --port 8766` avec le Python du venv.
Sous Linux : utiliser `.venv/bin/python` au lieu de `.venv\Scripts\python.exe`.
Les dépendances verrouillées incluent les outils de test du prototype.

La PWA React est servie par le même service sur `/pwa/`, après
`npm --prefix ui install` puis `npm --prefix ui run build`. Sans build présent,
seul le banc d'essai est disponible. Aucun second serveur n'est nécessaire.

### Accès LAN persistant

Le satellite ESP32 fonctionne en Wi-Fi sur prise USB, sans câble de données vers
le PC ni page web ouverte. La veille activée reprend après redémarrage du service ;
l'arrêt volontaire ou le passage au micro navigateur désactive cette reprise.
Le mot d'appel et son mode de détection restent réglables dans l'interface.
Alfred peut démarrer à l'ouverture de session via le Planificateur de tâches Windows.

## Préparer et tester la voix locale

**Depuis le 11 novembre, seules les voix Phonon sont proposées par Alfred.**
Dumby reste le choix actif et par défaut ; les autres profils sont Alfred cloné,
Arnaud et Lucien. Les anciens choix Henri, Pocket, Supertonic, Chatterbox, Sopro
et Melo/OpenVoice sont retirés du sélecteur et refusés par l’API. Aucune ancienne
voix n’est utilisée en secours.

Phonon tourne dans `.local/phonon-env`, avec `ptts` 0.7.0, le modèle français Q8
et des fichiers de voix locaux. Préparation et mesures dans
PHONON_ESSAI.md. Les modèles ne sont jamais téléchargés lors
d’une conversation. Une voix manquante produit une erreur, pas un autre timbre.

Dans le laboratoire vocal :

1. Choisir **Dumby · Phonon · CPU**, **Alfred · Phonon · voix clonée**,
   **Phonon · Arnaud · CPU** ou **Phonon · Lucien · CPU**.
2. Utiliser **Écouter la voix française** pour l’échantillon. Le modèle est conservé
   en mémoire ; le changement de voix ferme le worker précédent.
3. Utiliser le micro navigateur après son autorisation, ou Jarvis/K2 sur l’ESP32
   connecté. Voir TERMINAL_DIRECT.md.
4. **Annuler / arrêter la lecture** annule l’écoute et la lecture ; une synthèse
   déjà engagée peut finir sans que la réponse soit rejouée.

L’audio de conversation reste en mémoire. Le choix est persistant. Après une
ancienne préférence retirée, Dumby devient le choix local ; si son profil est
absent, le service le signale sans sélectionner automatiquement une autre voix.
Les archives et échantillons des anciennes recherches sont conservés sous `.local`
pour historique ; ils ne sont pas des voix utilisables dans le service.
Les profils vocaux privés ne sont jamais versionnés.

## Connecter Command Code GOAT

1. Dans la page locale, section **Command Code**, saisir la clé API de votre compte
   et l'identifiant du modèle, puis **Enregistrer localement**. Ne pas coller de clé
   dans le chat. Source : <https://commandcode.ai/docs/provider>.
2. **Tester l'accès** envoie une courte demande générique. Elle vérifie réellement
   la clé et l'accès au modèle et consomme le quota du compte. Une erreur n'entraîne
   ni achat, ni nouvelle tentative automatique, ni changement de modèle.
3. Passer explicitement le sélecteur en **Conversation · Command Code**, puis
   écrire un message ou enregistrer une phrase. La réponse s'affiche au fil du
   flux, puis est synthétisée et lue par le profil Phonon choisi. Test audio reste entièrement local.

La clé est protégée avec **DPAPI lié au compte Windows**, dans
`.local/data/commandcode.secret`, jamais renvoyée par l'API, affichée ni passée au
modèle. Sur Linux : fichier de configuration privé 0600. Le fichier Windows ne
constitue pas une clé portable vers une VM ou un autre compte : la reconfigurer
sur la cible. Une clé facultative peut aussi être fournie au lancement via
`ALFRED_COMMAND_CODE_API_KEY`, et le modèle via `ALFRED_COMMAND_CODE_MODEL` ; dans
ce cas l'interface n'écrase pas la configuration d'environnement. Aucun fichier
`.env` n'est lu automatiquement et aucun identifiant d'une autre application n'est repris.

Modèle initial proposé : `deepseek/deepseek-v4-flash`, identifiant de l'exemple
officiel ; accès effectif et qualité à confirmer avec votre compte. Identifiant
modifiable, endpoint fixé à `api.commandcode.ai`, pas d'URL fournisseur arbitraire.

Seul le texte est envoyé à Command Code (transcription ou message écrit, contexte
temporaire, instructions de personnalité et résultats documentaires en cas de recherche). L'audio reste sur ce PC. Le contexte
est en mémoire, séparé par identifiant aléatoire d'onglet : six échanges conservés pendant cinq minutes d'inactivité,
séparés par source, session et locuteur reconnu, purge à la prochaine demande et au
redémarrage. Les commandes directes alimentent aussi ce contexte. « Nouvelle conversation » permet de l'effacer avant. Ce n'est pas la
mémoire familiale/personnelle finale et aucune identité n'est reconnue.

Les réponses sont courtes ; l'interprétation avec outils est limitée à 1024 tokens,
la synthèse documentaire à 700 tokens. Quotas GOAT partagés
avec les autres usages, pas de garantie de plafond financier global à ce stade :
le suivi budgétaire S08 reste à réaliser. Les éventuels crédits prépayés déjà
présents sur le compte suivent les règles du fournisseur ; Alfred n'en achète pas.
Les jetons d'usage sont transmis dans la réponse lorsqu'ils sont fournis par l'API,
avec journal de diagnostic local borné à sept jours et cent Mo, sans audio brut.

La recherche web et la météo disposent d'outils documentaires (voir ci-dessous).
Les phrases explicites de lumière et de minuteur
sont exécutées directement, sans LLM ; les courses disposent aussi d'outils IA
pour lecture et ajout ; des outils permettent aussi les annonces et les rappels HA.
Les profils et leurs permissions restent à raccorder.
Le mode dialogue est actif par défaut après une demande vocale. Alfred rouvre
le micro pour huit secondes après une demande de confirmation ou de précision.
Annuler arrête la lecture et le flux côté navigateur ; une requête fournisseur
déjà partie peut consommer des tokens jusqu'à son interruption. Aucun succès
n'est inventé après une erreur de quota, d'accès ou de connexion.

## Internet : actualités, météo et culture générale

Dans **Réglages → Internet et météo**, recherchez puis sélectionnez la commune
par défaut et enregistrez. La météo utilise Open-Meteo sans compte ni clé pour
l'usage personnel non commercial : aujourd'hui et les six prochains jours,
températures, pluie et vent. Une commune explicitement demandée remplace le
défaut pour cet échange ; précisez région/pays si plusieurs lieux correspondent.

Pour les actualités et recherches générales, créez un compte gratuit Tavily puis
saisissez sa clé uniquement dans ce formulaire local. N'activez pas sa facturation
payante. **Tester la recherche** consomme un crédit ; la synthèse de conversation
utilise aussi Command Code. Alfred ne configure aucun abonnement fournisseur.

Exemples : « Quelles sont les actualités ? », « Que se passe-t-il sur ce sujet ? »,
« Va-t-il pleuvoir demain ? », « Quel temps fera-t-il à Lyon ce week-end ? »,
« Vérifie qui dirige cette entreprise ». Les connaissances stables restent
traitées sans recherche. Les liens sont affichés sous la réponse, y compris pour
le dernier échange ESP32. Aucun bulletin programmé ni vigilance météo dans ce lot.

Une recherche Tavily simple par tour, cinq résultats maximum. Plafond local
de mille crédits par mois UTC, abaissable à zéro ; réservations persistantes,
y compris les tentatives dont la réponse est perdue. Le quota gratuit du compte
est partagé avec ses autres applications : un refus fournisseur arrête la recherche.
Un nouveau mois réinitialise le compteur local ; remplacer la clé ne l'efface pas.
Les réglages et compteurs sont dans `internet.sqlite3` sous le répertoire de données,
la clé dans `tavily.secret` (DPAPI Windows ou fichier privé 0600 sous Linux).
Ils restent exclus du dépôt. Les requêtes météo communiquent le lieu à Open-Meteo ;
Tavily reçoit la question de recherche, sans l'historique personnel complet.

Les requêtes réseau sont bornées, sans relance automatique. Résultats absents,
quota, accès refusé ou panne sont annoncés sans inventer de réponse actuelle.
Les documents externes sont synthétisés dans un appel sans outils domotiques.
Avec DeepSeek V4, cette seule synthèse utilise `reasoning_effort=off` sur
Command Code pour réserver les jetons à la réponse, sans changer l'interprétation
des demandes. Une sortie tronquée reste refusée ; elle n'est jamais lue comme
une réponse complète ni relancée automatiquement.
Accès Tavily et circuit texte → recherche → résumé → TTS vérifiés en réel ;
l'écoute humaine après correction reste à confirmer. Les tests automatisés
utilisent des fournisseurs simulés.

## Mode dialogue

Le mode est actif par défaut dans la PWA, dans le laboratoire en mode Conversation
et sur le satellite ESP32. Dans les interfaces web, le réglage **Mode dialogue**
permet de désactiver la reprise. Dans la PWA il se trouve dans **Voix et
conversation**.

Le micro se ferme pendant le traitement et la lecture. Quand Alfred attend
une confirmation ou une précision, l’écoute reprend à la fin de la lecture
pour huit secondes. Après une réponse complète comme « J’ai éteint les
lumières », l’échange est terminé et le satellite revient à la veille du mot
d’appel si elle est active. Le silence ferme la reprise sans nouvel appel IA.
Dans le navigateur, une phrase commencée avant l’échéance peut se terminer
après un bref silence, avec une limite de 30 secondes.

**Arrêter la conversation** ferme le micro, coupe la lecture et invalide la réponse
en cours. Le contexte temporaire reste disponible ; « Nouvelle conversation »
l'efface. Décocher l'option empêche la prochaine reprise. Quitter l'onglet ferme une
capture active et désarme la reprise. Un message écrit, l'échantillon vocal ou une
réécoute ne relancent pas la capture ; réécouter pendant une capture ferme celle-ci.

La détection de parole est locale et fondée sur l'énergie du signal. Elle ne
reconnaît ni les personnes ni la télévision : musique et bruit peuvent provoquer une
fausse prise, une voix faible peut être manquée. L'essai avec le vrai microphone et
le réglage des seuils restent à faire, de même que le mot Alfred et l'interruption
pendant une réponse.

## Musique avec Music Assistant

Home Assistant doit être configuré et Music Assistant disponible. Dans la section
**Musique**, choisir le lecteur puis l'enregistrer. Alfred conserve ce choix dans
`.local/data/music.json` ; ce fichier ne contient aucun secret.

En mode Conversation, les commandes certaines sont exécutées sans IA : « mets
Airbourne sur l'ampli », « joue l'album Powerage sur l'ampli », « pause la musique »,
« reprends la musique », « arrête la musique » ou « musique suivante ». Les commandes
moins formatées passent par les outils bornés du modèle. L'interface permet aussi de
lancer un artiste, un album, un titre, une playlist ou une radio, puis de commander
pause, reprise, arrêt, suivant et précédent.

Une confirmation signifie que Home Assistant a accepté la demande ; elle ne prouve
pas que le son a été entendu. Pendant une interaction dans le navigateur, la musique
est réduite à 25 % de son volume courant par défaut, sans descendre sous 3 %. Ce
pourcentage se règle entre 5 et 80 % dans le panneau **Musique**. Alfred laisse la
réduction active pendant la reprise de huit secondes et restaure le volume à la fin
du son. Un réglage ou un mute manuel pendant cette période est conservé.

## Minuteurs à la voix et au clavier — v0.6

Après redémarrage du service et actualisation de la page :

1. Choisir **Conversation · commandes et dialogue**, puis l'étage de ce terminal
   dans le formulaire **Une nouvelle échéance**. Aucune clé IA n'est nécessaire ;
   Home Assistant est nécessaire pour la sonnerie sur le terminal physique.
2. Écrire ou dire « mets un minuteur de huit minutes ». Durées acceptées : secondes,
   minutes, heures, chiffres ou nombres français jusqu'à 99, « une heure et demie »,
   « une demi-heure », « deux minutes trente secondes ». Limites : 1 seconde à 7 jours.
3. « Liste les minuteurs » ou « combien de temps reste-t-il au minuteur ? » consulte
   les minuteurs actifs de cet étage. Chaque minuteur est annoncé avec son numéro
   stable ; les dix premiers sont lus au maximum, avec le total s'il y en a davantage.
4. « Annule le minuteur » annule l'unique minuteur actif de l'étage. S'il y en a
   plusieurs, Alfred demande de préciser : « annule le minuteur deux », par exemple.
5. « Stop » termine uniquement les minuteurs en sonnerie de l'étage sélectionné ;
   les échéances futures restent actives. « Arrête le minuteur » équivaut à annuler.

Le suivi apparaît dans **Minuteurs & rappels**, avec le même stockage persistant
que les formulaires. Sans étage choisi, Alfred le demande sans créer de minuteur.
Une demande mixte ou mal comprise contenant « minuteur » reçoit une clarification,
sans exécution ni appel IA. Les commandes locales ne sont pas ajoutées au contexte LLM.
Après un échec de lecture vocale, vérifier le suivi avant de renouveler la commande :
l'action déjà enregistrée n'est pas annulée par un problème de synthèse.

La carte Waveshare du bureau est configurée comme terminal du **RDC**. À échéance,
Alfred demande à Home Assistant sa sonnerie native ; « Stop » ou l'annulation du
dernier minuteur en sonnerie de cet étage demande son arrêt. Plusieurs minuteurs
sonnent ensemble sur le même terminal. Une échéance du premier étage ne cible pas
la carte du bureau. La validation vocale des commandes dans le navigateur a été
confirmée par l'utilisateur ; **le son réel sur la carte reste à essayer**.

La configuration non secrète est dans `.local/data/bell-targets.json` ; sans
ce fichier, aucune sortie n'est activée. Home Assistant doit être configuré et
joignable. Le suivi affiche « Sonnerie demandée au terminal » lorsqu'il accepte la
requête : cela ne prouve pas que le son a été entendu. Une erreur est affichée si
le démarrage ou l'arrêt ne peut pas être confirmé. En cas de perte de réponse, le
démarrage n'est pas répété ; l'arrêt est retenté. Au redémarrage, les anciennes
échéances ne sont pas rejouées et une éventuelle sonnerie lancée par Alfred est
arrêtée. Le firmware coupe de lui-même sa sonnerie au bout de quinze minutes.

Le firmware emploie la même sonnerie pour ses minuteurs Assist : les deux systèmes
ne distinguent pas encore leurs sonneries respectives. L'arrêt matériel ou vocal
géré directement par Assist ne met pas encore à jour l'état d'Alfred. Les profils,
permissions et diffusion sur plusieurs terminaux réels restent à raccorder et tester.

## Profils vocaux — enrôlement

Alfred calcule une empreinte vocale par personne, sur ce PC.

1. Section **Les profils**, puis **Ajouter un profil** : prénom et rôle (adulte ou enfant).
2. **Enrôler la voix** affiche trois phrases, chacune dite deux fois : six passages de six
   secondes au maximum, environ vingt secondes de parole par personne.
3. Chaque passage produit une empreinte ECAPA de 192 valeurs, conservée avec son WAV dans
   `.local/data/profiles/<profil>/`.
4. **Réécouter** rejoue le dernier échantillon ; **Supprimer** efface le profil, ses
   empreintes et ses fichiers audio.

Le moteur est ECAPA-TDNN (`speechbrain/spkrec-ecapa-voxceleb`, licence Apache 2.0),
exécuté localement par SpeechBrain 1.1.2 et PyTorch 2.14.1. Le modèle d'environ 85 Mo
vit dans `.local/models/speechbrain` et se télécharge par `python -m alfred.setup_voice` ;
les dépendances ajoutent environ 1 Go au venv. Aucun réseau n'est sollicité pendant un
enrôlement.

Une reconnaissance expérimentale est raccordée à la conversation, mais elle ne
s'active qu'après une calibration avec au moins deux personnes, six échantillons
chacune et deux essais indépendants par personne. Une voix non reconnue ou un score
insuffisamment séparé reste inconnu. Ce mécanisme n'est pas une authentification.
Au 30 octobre, un seul profil était enrôlé et la calibration n'était donc pas
validée. Mesure ancienne sur voix synthétique Piper : 0,84 de similarité pour la même
voix, 0,93 entre deux bruits sans rapport ; la calibration refuse désormais les voix
qui ne sont pas assez séparées.

## Courses familiales — préparation

La liste « Courses Alfred » a été créée dans Home Assistant le 29 octobre et son
identifiant `todo.courses_alfred` enregistré dans Alfred sur ce PC. Après lancement,
la section **Courses familiales** permet de vérifier ou modifier cette sélection.
Le jeton Home Assistant déjà configuré doit avoir accès à la liste.

Avec Command Code configuré, le modèle peut choisir les outils de lecture ou
d'ajout, y compris pour certaines formulations indirectes. Les résultats contenant
des articles peuvent être transmis à Command Code dans le contexte d'une demande
ultérieure de la même conversation. Les modèles peuvent se tromper ; ajout indirect
encore irrégulier lors des premiers essais avec liste simulée. Sans clé, les phrases
explicites continuent à fonctionner localement. L'activation des outils porte le
maximum de sortie de 256 à 1024 tokens et les réponses textuelles sont affichées à
la fin de la génération. Les quotas du compte restent partagés.

L'interface permet de lire la liste, d'ajouter un article et de le cocher comme
acheté. En mode conversation, « j'ai acheté le lait » coche l'article correspondant :
il disparaît de la liste active et reste marqué terminé dans Home Assistant. Si
plusieurs articles correspondent, Alfred demande une précision dans Home Assistant.
Les articles cochés sont consultables et peuvent être remis dans la liste ; un
article actif peut être renommé, quantité comprise. « Supprime le lait » l'efface
définitivement ; « purge la liste » ou « supprime tout » efface tous les articles,
cochés compris. Une demande de retrait ordinaire coche l'article sans l'effacer.
L'interface demande une confirmation avant suppression ou purge.
En mode conversation,
dire ou écrire « ajoute du lait et du pain à la liste de courses » ou « il y a quoi
dans la liste ? ». Avec l'IA, jusqu'à huit articles sont traités séparément ; sans
clé, la commande directe accepte un article à la fois. En cas d'échec pendant une
demande multiple, Alfred indique les ajouts acceptés, l'ajout non confirmé et ceux
qu'il n'a pas encore demandés à Home Assistant. Une réponse perdue ne déclenche pas de
nouvelle tentative : consulter la liste avant de recommencer. La lecture vocale
énumère au maximum 20 articles, l'interface affiche tous les articles reçus.

Avant un ajout, Alfred vérifie les articles non terminés : s'il trouve le même,
il le signale sans l'ajouter. Les accents, majuscules et articles comme « du » ne
comptent pas dans la comparaison ; les quantités et variantes restent distinctes.
Si l'article est coché, l'ajout le remet dans la liste active au lieu de le recréer.
Les synonymes ou le singulier/pluriel ne sont pas systématiquement reconnus ; un
ajout simultané depuis un autre client peut passer entre vérification et écriture.

L'ajout et la lecture ont été vérifiés avec un article temporaire depuis le code
d'Alfred vers Home Assistant réel ; l'interface et le micro restent à essayer.
Les permissions par profil ne sont pas encore raccordées. Les fonctions de
modification, remise et suppression ont été testées avec HA simulé ; leur essai
sur la liste réelle reste à faire. La fonction pour cocher a été confirmée par
l'utilisateur sur la liste réelle.

## Domotique Home Assistant

Depuis le 13 novembre, le parcours direct prend aussi en charge les températures,
switchs et helpers `input_boolean`, `input_number`, `input_select`, `input_datetime`,
`input_text` et `input_button`, au clavier, au micro navigateur et sur l'ESP32.
Les `media_player` et `vacuum` sont également raccordés : leurs actions disponibles
dépendent des capacités annoncées par Home Assistant et sont affichées dans le tableau.
Les entités doivent être exposées à Assist dans HA et autorisées dans le panneau
Domotique d'Alfred. Les helpers ne sont pas exposés automatiquement. Utilisez leurs
noms ou leurs alias HA/Alfred ; ajoutez la pièce si un nom désigne plusieurs entités.

Le tableau comporte une colonne **Confirmation**. Cochez un appareil puis cliquez
sur **Enregistrer les modifications** pour qu'Alfred demande « Voulez-vous
vraiment… ? » avant toute commande qui le modifie. Le oui/non fonctionne au
clavier, au micro du navigateur et sur l'ESP32 ; la confirmation expire après
trente secondes. Les lectures, les températures et le panneau Musique restent
directs. Une commande globale touchant un appareil sensible est bloquée en entier
et confirmée en une fois ; la page Domotique affiche alors **Confirmer** et
**Annuler**. Aucune écriture n'est envoyée à Home Assistant avant l'accord.

Exemples, à adapter à vos noms :

- « Quelle température dans le salon ? », « Quelle température au salon ? »,
  « Quelle température fait-il au bureau ? » ou « Quelle température ici ? ».
- « Active mode vacances », « Désactive prise du bureau », « Lis mode vacances ».
- « Règle seuil à vingt et un », « Augmente seuil d'un pas ».
- « Liste les options de ambiance », « Mets ambiance sur nuit », « Option suivante de ambiance ».
- « Règle réveil à sept heures trente », « Mets départ à demain à huit heures ».
- « Écris message à Bonjour Élodie ! », « Appuie sur routine ».
- « Mets télé en pause », « Reprends télé », « Piste suivante sur télé ».
- « Règle le volume de télé à trente pour cent », « Coupe le son de télé ».
- « Liste les sources de ampli », « Règle la source de ampli sur TV ».
- « Démarre l'aspirateur », « Mets l'aspirateur en pause », « Renvoie l'aspirateur à sa base ».
- « Liste les puissances de aspirateur », « Règle la puissance de aspirateur à silencieux ».
- « Liste les pièces nettoyables par aspirateur », « Nettoie le salon ».

Pour nettoyer une pièce, elle doit déjà être associée à la carte de l'aspirateur
dans Home Assistant ; une pièce inconnue n'entraîne jamais de nettoyage global.
Voir la [configuration native des pièces](https://www.home-assistant.io/integrations/vacuum/#mapping-your-vacuum-areas-to-home-assistant-areas).
Les lecteurs homonymes nécessitent des alias distincts ou une précision de pièce.
Un groupe multimédia contenant une entité exclue ou non exposée n'est pas piloté.
La recherche de musique sur le lecteur Music Assistant sélectionné reste inchangée.

Les températures utilisent les sondes de classe température et leur unité ; plusieurs
sondes dans une pièce nécessitent une précision. « Ici » vise la pièce configurée
du terminal utilisé (réglage web ou configuration du terminal ESP32). Les dates
relatives utilisent le fuseau de HA ; modifier seulement l'heure conserve la date.
Les bornes numériques et options sont contrôlées ; les textes en mode mot de passe
ne sont pas lus. Une écriture est confirmée seulement si l'état attendu est relu.
Un appui envoyé à un bouton ne confirme pas la fin de l'automatisation associée.

En conversation avec le modèle configuré, un outil `lire_temperature` distinct est
proposé pour les questions de température de pièce. Il ne peut que relire une sonde
autorisée du catalogue ; il n'active pas les autres commandes d'appareils, qui
restent soumises à leur réglage de relais. Le parcours local sans modèle accepte les
mêmes formules de pièce et reconnaît un nom partiel comme « chambre » lorsqu'il est
ambigu, afin de demander une précision plutôt que d'inventer un capteur.

**Climate différé jusqu'au retour de l'utilisateur chez lui.** Aucun appel de
commande climate ; les helpers `timer`, compteurs et domaines natifs `number` et
`select` restent hors de cette étape. Les nouveaux types sont testés avec HA simulé ;
leur recette réelle reste à effectuer sur des cibles choisies explicitement.

### Configuration et lumières existantes

1. Dans Home Assistant : **profil → Sécurité → Jetons d'accès longue durée → Créer un jeton**.
2. Dans Alfred, section **La maison** : adresse (par exemple `http://homeassistant.local:8123`),
   jeton, pièce du terminal, puis **Enregistrer localement** et **Tester la connexion**.
3. Les commandes reconnues sans IA : « éteins toutes les lumières », « allume toutes
   les lumières », « éteins les lumières du salon », « éteins la lumière » (pièce du
   terminal). Elles fonctionnent au micro comme au clavier, en mode Conversation.

Le jeton Home Assistant est chiffré par DPAPI sous Windows (fichier privé 0600 sous
Linux) dans `.local/data/homeassistant.secret` et n'est jamais renvoyé par l'API.
Seules les phrases de lumière complètes sont exécutées ; une demande mixte comme
« éteins la lumière et raconte une blague » part vers la conversation, qui n'a aucun
outil de maison. « Toutes les lumières » ne cible que les lampes allumées pour une
extinction, et compte ce que Home Assistant a réellement rapporté.

**Essai réel confirmé le 26 octobre** : la connexion au Home Assistant de la maison
fonctionne et les lampes se sont éteintes sur ordre. La recette automatisée repose
sur un serveur simulé (29 tests synchrones) ; les cinq tests HTTP internes n'ont pas
été rejoués dans la session qui les a ajoutés. Les lampes non concernées ne sont pas
exclues, les permissions par profil ne sont pas branchées, et la résolution d'une
pièce dépend du nom exact des zones Home Assistant.

Le lanceur écoute par défaut sur `127.0.0.1`, avec un seul worker. Le mode
LAN de développement est explicite via `--host` (voir ci-dessous). Il n'y a pas
encore d'authentification applicative ; aucune exposition Internet. Le choix d'accès distant/authentification reste suivi dans la checklist.

## Essayer

1. Choisir l'étage du terminal navigateur, créer un minuteur de quelques secondes.
2. Son état passe de « En attente » à « Sonnerie demandée au terminal » si un
   terminal est configuré sur cet étage. « Stop » termine les minuteurs en
   sonnerie de cet étage et demande l'arrêt du terminal ; pas d'annulation des
   échéances futures. Son physique à vérifier sur place.
3. Un rappel demande une date future, un destinataire et une pièce ; le formulaire
   convertit l'heure locale du navigateur en UTC. Un rappel arrivé à échéance est
   « À délivrer », pas faussement annoncé comme délivré.
4. Après arrêt/redémarrage : échéances futures inchangées, minuteurs expirés ou
   précédemment en sonnerie terminés, rappels manqués visibles ; pas de sonnerie tardive.

L'ancien banc local, désormais suspendu, conservait la même heure de Paris pour
les rappels hebdomadaires ; après
un arrêt, une occurrence manquée est signalée et la prochaine occurrence future est
programmée. L'heure saisie est celle du navigateur : si son fuseau diffère de Paris,
vérifier l'heure correspondante. Une heure inexistante au printemps est décalée à la
première minute valide ; en automne, la première occurrence est choisie. L'interface
associe le rappel personnel à un profil sélectionné mais ne protège pas encore son
  accès. Dans cet ancien banc, la diffusion était demandée au satellite configuré ;
  une réponse acceptée ne prouve pas que le rappel a été entendu. Une tentative
  incertaine n'est pas rejouée automatiquement. Le défaut de destination web/HA reste
  à trancher et la pièce est demandée explicitement dans le banc. Les messages sont
  synthétisés par la voix du pipeline Home Assistant (cloud selon le choix utilisateur),
distincte des voix locales Pocket TTS/Supertonic ; aucun essai acoustique physique n'a encore été confirmé.
La page affiche les 100 premières échéances (actives en priorité), sans purge
automatique de cette table. L'historique de diagnostic sept jours/100 Mo est un
module distinct encore à construire ; les transcriptions ne sont pas enregistrées ici.

## Réveil configurable · ESP32 et navigateur

Dans **Laboratoire vocal → Mot d’appel**, chaque source possède ses réglages :

- **STT local · Parakeet** : saisir un mot ou une phrase de un à quatre mots
  (quarante caractères maximum), avec des variantes séparées par des virgules.
  Valeur initiale : **Alfy**, variante **Alfi** ; aucun « Hé » obligatoire.
  Si Parakeet emploie une autre graphie, ajoutez-la explicitement aux variantes.
  Une phrase complète qui ne confirme aucune variante du réveil STT est refusée
  avant les outils et l'IA.
- **openWakeWord** : choisir un modèle installé et son seuil. Le menu indique
  la phrase réellement entraînée. Hé Alfred, Jarvis et Alexa sont proposés
  lorsqu'ils sont présents. Un nouveau mot nécessite un modèle entraîné.
- Cliquer sur **Enregistrer**, puis **Activer** pour la source souhaitée.
  Activer une source suspend la veille de l'autre. Le choix ESP32 existant
  est conservé à la migration ; Jarvis reste disponible pour revenir en arrière.

Le navigateur ouvre le microphone uniquement après un clic et votre permission,
en HTTPS ou sur localhost. Garder la page visible : passer en arrière-plan,
fermer la page ou perdre la connexion ferme la veille. L'ESP32 ne se réactive
pas automatiquement. Le navigateur transmet le PCM au serveur Alfred local ;
aucun service de transcription externe n'est appelé.

Le mot doit commencer la prise de parole. Vous pouvez dire **« Alfy allume la
lumière »** sans pause. Après le mot seul, six secondes sont laissées pour la
commande ; le silence ne déclenche pas l'IA. Après une réponse, la reprise
habituelle de huit secondes reste disponible. Le réveil est suspendu pendant
la réponse ; l'interruption pendant la lecture n'est pas ajoutée par ce mode.

**Importer un modèle openWakeWord** demande son nom, sa vraie phrase et un
fichier ONNX de dix Mo au maximum. La validation refuse les modèles incompatibles
et les données externes ; elle n'évalue pas leur qualité acoustique. Les fichiers
microWakeWord TFLite ne conviennent pas. Aucun modèle existant n'est remplacé.

Les modèles entraînés sont installés localement. Sur une nouvelle copie, le
réveil STT du navigateur peut utiliser Parakeet une fois celui-ci installé.
Pour utiliser openWakeWord, importer un ONNX que vous êtes autorisé à utiliser.
Pour installer un fichier Jarvis existant sous son nom attendu :

```powershell
.\.venv\Scripts\python.exe -m alfred.setup_wake_word --model "C:\chemin\jarvisse_20260916_004415.onnx" --name jarvisse_20260916_004415.onnx
```

La commande prépare les fichiers de prétraitement et installe le modèle sous
`.local/models/wake-word/`. Le réveil openWakeWord requiert ces fichiers.

Préférences : `.local/data/wake-settings.json` ; catalogue personnalisé :
`.local/models/wake-word/catalog.json`. Le STT réutilise Parakeet et Silero VAD
installés. Audio et transcriptions de veille restent en mémoire et ne sont
pas journalisés. La qualité réelle d'Alfy, notamment avec TV/musique, est à
valider sur votre voix et vos microphones.

## Accès de développement sur le LAN

Alfred écoute sur `127.0.0.1` par défaut. Pour l'ouvrir sur votre réseau
privé, remplacer l'adresse d'exemple par l'IPv4 privée du PC.

```powershell
.\.venv\Scripts\python.exe -m alfred --host 192.168.77.23
```

Pour HTTPS, placer `server.crt` et `server.key` sous `.local/https`, puis relancer
avec `--https`. Le certificat doit couvrir l'adresse utilisée. La clé reste
locale. Ce mode de développement ne comporte pas d'authentification applicative.

Le certificat doit être signé par l'autorité locale du projet, sinon chaque
appareil affiche un avertissement ou refuse la page. Sur la machine de
développement, après `scripts/setup_ui_https.py --host <IP>` :

```bash
.venv/bin/python scripts/renew_dev_certificate.py --directory .local/https \
  --address <IP> --ca-cert .local/https/ui-ca.crt --ca-key .local/https/ui-ca.key
```

L'autorité publique est ensuite servie sur `/alfred-local-ca.crt` : à importer
une fois par appareil (« Installer un certificat » → « Certificat CA » sur
Android). Redémarrer Alfred après avoir renouvelé le certificat.

## Configuration et données

- Variable optionnelle `ALFRED_DATA_DIR` : dossier des données, par défaut
  `.local/data` à la racine du projet (hors Git).
- Base `alfred.sqlite3`, schéma version 6 ; verrou `scheduler.lock` empêchant deux
  ordonnanceurs sur les mêmes données. Une version de schéma inconnue est refusée.
  La version 2 ajoute les profils et empreintes ; la version 3 associe les rappels
  à un profil ou à la famille ; la version 4 ajoute les séries hebdomadaires et la
  version 5 prépare le suivi de l'ancien banc de rappels et la version 6 ajoute
  le journal technique de suivi des rappels HA, sans y recopier leurs contenus.
  Les échéances existantes restent inchangées.
  L'enrôlement des voix existe et la reconnaissance expérimentale est raccordée ;
  elle reste inactive tant que la calibration et les essais indépendants ne sont pas validés.
- Les échéances sont stockées en UTC. Le navigateur les affiche dans son fuseau ;
  la récurrence hebdomadaire est calculée dans le fuseau Europe/Paris.
- Pour copier les données manuellement, arrêter le service avant de copier tout le
  dossier de données. Une sauvegarde/restauration de production reste à valider.
- Aucun jeton requis pour le test audio ou les minuteurs locaux ; une clé et des
  appels sortants sont nécessaires pour le dialogue général avec Command Code.
  Ne pas mettre de secrets ou
  d'informations personnelles réelles dans les données de ce banc sans authentification.

## API et vérifications

Routes : `GET /health`, `GET /api/status`, `GET /api/schedules`,
`POST /api/schedules`, `POST /api/schedules/{id}/cancel`, `POST /api/stop`.
Voix : `GET /api/voice/status`, `POST /api/voice/config` (choix `pocket-alfred` ou
`supertonic-m1` à `m5`),
`POST /api/voice/speak` (JSON texte, réponse WAV),
`POST /api/voice/turn` (corps WAV, réponse JSON texte/audio base64/durées).
Profils : `GET/POST /api/profiles`, `PATCH/DELETE /api/profiles/{id}`,
`POST /api/profiles/{id}/enroll` (corps WAV), `GET /api/profiles/{id}/samples`,
`GET /api/profiles/{id}/samples/{fichier}`, `POST /api/profiles/identify` (corps WAV,
scores seulement, sans décision d'identité).
Musique : `GET/POST /api/music/config`, `GET /api/music/players`,
`POST /api/music/play`, `POST /api/music/control`, `POST /api/music/duck`,
`POST /api/music/restore`.
Conversation : `GET/POST /api/ai/config` (lecture sans clé), `POST /api/ai/check`,
`POST /api/conversation/text`, `POST /api/conversation/voice` (WAV + en-tête
`X-Alfred-Session`), `POST /api/conversation/reset`. Pour les minuteurs, le texte
accepte `floor_id` (`rdc` ou `etage1`) et la voix l'en-tête `X-Alfred-Floor`.
Les deux routes de conversation
renvoient du NDJSON : phases, transcription, deltas, réponse, puis audio et durées,
ou une erreur explicite. Le client ignore les réponses d'une demande annulée.
Schéma détaillé : `/openapi.json`. La documentation interactive `/docs` utilise
les assets CDN habituels de FastAPI et n'est pas nécessaire à l'interface locale.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
node --test tests/audio-utils.test.mjs tests/conversation-stream.test.mjs
```

Test réel optionnel, modèles préparés, audio synthétique en mémoire sans microphone :

```powershell
$env:ALFRED_TEST_VOICE='1'
.\.venv\Scripts\python.exe -m pytest -q
```

Tests : reprise/redémarrage, absence de diffusion tardive, isolation par étage,
annulation, concurrence SQLite, fuseaux, unicité de l'ordonnanceur, validation API,
origine des requêtes et état de santé. Tests vocaux : limites WAV et rééchantillonnage,
gestion d'erreurs/concurrence, absence d'audio sur disque et chaîne de transcription locale
optionnelle. Ils ne valident pas la captation réelle, les profils ni l'acoustique ESP32.
Tests Command Code réalisés avec transport HTTP simulé : streaming, erreurs 401/
403/429, contexte isolé et réinitialisation, silence sans appel IA, validation de
configuration et absence de clé dans les réponses d'erreur. DPAPI testé sur Windows
avec une clé fictive. Aucune validation du compte réel sans sa clé configurée.
Recette v0.4 : 61 tests Python et 25 tests JavaScript. Ces derniers incluent le
contrôleur d'interface exécuté avec DOM, micro et lecteur artificiels : reprise
après lecture, phrase commencée près de l'échéance, arrêt, permission refusée ou
tardive, silence sans appel IA, réécoute et onglet caché.

Recette v0.6 du 27 octobre : **133 tests Python réussis, 1 test vocal réel optionnel
non activé ; 26 tests JavaScript réussis**. Les tests HTTP s'exécutent hors du bac
à sable Windows, qui bloque asyncio ; fournisseurs IA/HA et moteurs vocaux simulés,
données de test isolées. Création, persistance, temps restant, numéros, annulation
ambiguë, étages, Stop, demandes mixtes et panne TTS couverts.

Recette du 30 octobre après raccordement de Pocket TTS : **262 tests Python réussis,
2 tests réels optionnels ignorés ; 28 tests JavaScript réussis**. Le test vocal réel
synthèse locale → transcription a aussi été exécuté avec succès. Un essai
réel Airbourne a été accepté par Music Assistant, constaté en lecture par Home
Assistant, atténué de 12 % à 3 % puis restauré à 12 %, avant arrêt et retour au
volume initial de 47 %. L'audition par une personne et les futures interactions
sur un terminal ESP32 restent à valider.


## Compréhension naturelle et historique local

Le panneau Musique permet désormais de choisir une playlist par défaut, recherchable
par nom et fournisseur. « Mets de la musique » lance cette playlist ; sans sélection,
Alfred demande laquelle choisir. Les commandes naturelles de volume et de lecture
partagent le contexte avec les lumières : « baisse un peu » vaut cinq points.


Les commandes certaines restent locales ; l'IA configurée dispose maintenant d'un
outil de lumière contrôlé pour les formulations libres. Marche/arrêt, état, intensité,
couleur et blanc selon capacités, reprises « rallume-la »/« pareil dans le salon »,
propositions explicites à confirmer et lots de quatre actions. Une réponse incertaine
arrête la suite sans répéter les commandes. Le modèle et les moteurs audio sont conservés.

Consulter l'historique sur le PC avec `python -m alfred.diagnostics --limit 30`,
exporter avec `--export .local/diagnostic-export.json`, annoter avec
`--annotate IDENTIFIANT --label comprehension --note "Description de l'échec"`.
Aucune nouvelle route réseau d'historique. Réglages des relais par fonction :
`python -m alfred.intent_settings --disable lights` / `--enable lights`.

Le corpus synthétique et les tests logiciels ne prouvent pas une fiabilité vocale
quotidienne de quatre-vingt-dix-neuf pour cent ; la recette humaine reste nécessaire.


Les minuteurs acceptent désormais les formulations libres (« dans cinq minutes,
crée un minuteur », « ajoute deux minutes au minuteur ») tout en conservant le
stockage par étage et les limites existantes. Le relais IA des minuteurs est actif ;
l'outil appareils reste désactivé jusqu'à sa recette. « Stop » conserve l'arrêt des
sonneries. Les suites sont arrêtées par une interruption sans supprimer les minuteurs
déjà créés.
