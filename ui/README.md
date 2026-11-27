# Interface Alfred

Interface React/TypeScript avec icônes Lucide React, raccordée au serveur Alfred.

Alfred sert la PWA compilée sur `/pwa/`, avec la même origine et la même
protection d’origine que le reste de l’API. C’est le mode normal sur la VM.

```bash
cd ui
npm ci
npm run build
```

Le build vise `/pwa/` par défaut (`ALFRED_UI_BASE` pour changer). Recharger
Alfred n’est pas nécessaire : relancer la page suffit. Pour le développement
avec rechargement automatique, `npm run dev` garde le proxy HTTPS décrit
ci-dessous.

Pour un accès sur le réseau local, générer le certificat UI avec
`scripts/setup_ui_https.py --host <IPv4-du-PC>` et renseigner dans `ui/.env.local` :

```dotenv
ALFRED_UI_HOST=192.168.77.23
ALFRED_UI_BACKEND=https://192.168.77.23:8765
```

Remplacer l’adresse d’exemple par celle du PC. Le certificat du serveur Alfred
doit couvrir l’adresse du backend. La commande de préparation conserve les
certificats existants. Relancer `npm run build` après une modification. Pour
le rechargement automatique, utiliser `npm run dev`.

Le proxy de la PWA transmet les routes autorisées à Alfred sur le port 8765 et
vérifie son certificat `.local/https/server.crt`. Le backend contrôle l’origine
des écritures. Les clés des services restent sur Alfred. Vite fournit ce proxy
en développement ; en production, Alfred sert directement `/pwa/` et la liste
des routes autorisées ne s’applique plus. L’authentification par comptes Home
Assistant reste à intégrer avant production.

La rubrique **À propos et diagnostic** utilise `GET /api/updates` et les
quatre opérations `POST /api/updates/{check,install,auto-on,auto-off}`. Le
proxy transmet `X-Alfred-Update-Key` sur ces requêtes. Le serveur n’accepte
les opérations qu’en HTTPS ou sur une adresse de boucle locale et vérifie
le code administrateur de la VM.

## Conversation

Entrée envoie à Alfred, Maj+Entrée insère une ligne. Les réponses arrivent en
flux et les sources s’affichent lorsqu’elles sont renvoyées. Le bouton micro
ouvre une prise de 30 secondes maximum. Touchez la flèche pour l’envoyer plus tôt.
Une commande permet d’interrompre la prise ou l’échange. Nouvelle conversation
efface l’affichage et demande la réinitialisation du contexte au serveur.
Le menu conserve la conversation et le brouillon pendant la navigation.
Sur Android, le bouton Retour ferme le menu ouvert ou revient à l’écran
précédent, y compris depuis une rubrique des paramètres ou une vue locale.

## Musique

Le lecteur configuré dans Alfred fournit les métadonnées, la progression et les
commandes de lecture. Les favoris et la recherche viennent de Music Assistant,
par catégorie Artistes, Albums, Titres ou Playlists. Le lecteur est commun au
serveur et la pochette reste générique. [Actions Music Assistant dans Home Assistant](https://www.home-assistant.io/integrations/music_assistant/)

## Liste de courses

La liste familiale de Home Assistant est la vue par défaut. Ajout, cochage,
remise à acheter, renommage des articles à acheter et suppression confirmée.
« Sur cet appareil » ouvre la liste locale historique, avec annulation de la
suppression. Le service worker ne met aucune de ces données en cache.

## Rappels et minuteries

Rappels familiaux à venir dans le calendrier Home Assistant. La création demande
une pièce d’annonce déclarée sur le serveur. « Sur cet appareil » conserve les
anciens rappels, leur modification et leur état terminé.

Les minuteries serveur sont visibles par étage. Elles peuvent être créées ou
annulées depuis l’application. La sonnerie suit le routage d’Alfred par étage.
« Sur cet appareil » conserve le décompte local, la pause et la reprise.
Le son local est activable pour la session et dépend de la visibilité de la PWA.

## Paramètres

Les huit rubriques sont accessibles depuis l’accueil, avec retour par la
flèche à gauche du titre. Le thème clair, sombre ou système et les autres
préférences d’interface sont enregistrés sur cet appareil.

Voix et conversation affiche la voix du serveur. Lecture des réponses écrites
et débit sont appliqués dans le navigateur. Le personnage, le mot de réveil
et l’écoute enchaînée restent des préférences locales à ce stade.

Maison et appareils affiche les états Home Assistant et ESP32 du backend. Les
pièces, l’adresse de référence et les affectations restent dans le navigateur.
La pièce du navigateur fournit l’étage aux demandes écrites et vocales.
Le tableau et les lignes mobiles récapitulent les réglages des entités
exposées à Assist. Le crayon ouvre une fiche pour modifier le nom, la pièce,
l’accès, le mode confirmation et les alias Alfred. Valider enregistre ces
changements ensemble. Annuler et Échap abandonnent le brouillon. Vider le
champ du nom rétablit le nom Home Assistant. Le sélecteur de pièces propose le
registre Home Assistant, y compris pour un appareil sans affectation.
La pièce d’origine est présélectionnée par défaut et signalée par une petite
maison. La sélectionner rétablit l’affectation Home Assistant. La pièce choisie
dans la fiche sert au ciblage des commandes dans Alfred.

IA et recherche affiche l’état de Command Code et du fournisseur de recherche.
En mode « Sur demande », le globe autorise les outils Internet pour un échange.

Musique choisit la catégorie de favoris initiale. Notifications et sonneries
règle la sonnerie des minuteries locales et affiche le service d’annonces des
rappels. Les notifications dans le navigateur restent à raccorder.

Données et confidentialité exporte les préférences et données enregistrées dans
le navigateur. Les messages affichés et le brouillon restent en mémoire jusqu’au
rechargement. Alfred traite les demandes envoyées et conserve un contexte temporaire.

À propos et diagnostic affiche les versions, le réseau et le stockage locaux,
le service worker et la disponibilité d’Alfred.

## Installer sur Android

Ouvrir l’adresse dans Chrome puis toucher **Installer** dans l’en-tête.
Le bouton ouvre l’invitation native quand Chrome la propose ; sinon, une aide
indique le menu ⋮ → Ajouter à l’écran d’accueil / Installer l’application.
Le bouton disparaît dans l’application installée. La décision d’installation
reste contrôlée par Android et le navigateur.

Si Chrome refuse le certificat HTTPS privé, télécharger l’autorité publique
depuis l’aide d’installation (`/alfred-local-ca.crt`), puis l’ajouter dans les
paramètres Android : rechercher « Installer un certificat » → « Certificat CA ».
Cela accorde à cette autorité le droit de valider des certificats sur le téléphone.
Les clés privées restent dans `.local/https/`, dont les ACL sont limitées à
l’utilisateur Windows et SYSTEM. Aucune confiance système n’est installée par le script.
Fermer et rouvrir Chrome après l’ajout du certificat.

Le script `scripts/setup_ui_https.py` prépare l’autorité et le certificat UI sans
écraser les fichiers existants ; il copie seulement le certificat public dans
`ui/public/` (copie ignorée par Git). Les icônes sont reproductibles avec
`python scripts/generate_ui_icons.py`.

`vite-plugin-pwa` fournit le manifeste et le service worker, en développement et
dans le build. Seuls les fichiers statiques compilés sont précachés en production ;
aucune API, conversation, synthèse audio ni certificat n’est précaché. Le serveur de
développement nécessite le réseau. Les mises à jour ne forcent pas le rechargement
d’une conversation ouverte ; fermer les fenêtres de l’application puis la rouvrir.
La dépendance `glob` de Workbox est surchargée vers la version corrigée 14.0.6
pour éviter les alertes npm des versions précédentes ; valider le build à sa mise à jour.

Documentation : https://vite-pwa-org.netlify.app/guide/ et
https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable

Référence des icônes : https://lucide.dev/guide/react/
