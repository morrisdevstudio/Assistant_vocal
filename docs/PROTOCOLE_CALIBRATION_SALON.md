# Calibration du satellite dans le salon

Le résultat attendu est de pouvoir appeler Alfred et lui parler depuis les
places habituelles, y compris de côté ou de dos. Le bureau traité sert de
témoin si on peut y reproduire une géométrie comparable. Le repère à 50 cm
vérifie l'installation. Il ne participe pas au choix du réglage Salon.

## Parcours guidé sans micro de référence

Ouvrir [Logs → Test acoustique guidé · Salon](https://192.168.1.23:8765/#logs)
sur le téléphone. Couper la TV et la musique, puis renseigner la distance
canapé–ESP32 si elle est connue. Suivre les dix étapes affichées : deux
balayages au canapé, puis les mêmes deux phrases à 50 cm et au canapé de
face, de côté et de dos. Pendant un balayage, attendre l'enregistrement puis
appuyer sur **Jouer le balayage**. Pour les étapes vocales, lire une fois la
phrase affichée à voix normale, après le début de l'enregistrement.

À la fin de chaque étape, choisir **Valider et continuer** ou **Refaire la
prise**. Télécharger le ZIP à la fin. Il contient les WAV numérotés, dont
`10-canape-dos-enceinte.wav`, et `parcours.json` avec les phrases attendues.
Les prises validées restent en mémoire dans l'onglet. Un ZIP partiel peut
être téléchargé pendant le parcours. Le test mesure l'effet de la distance
et de l'orientation sur la Waveshare. La comparaison directe avec une
autre chaîne de captation, décrite ci-dessous, reste un contrôle facultatif.

## Préparation

- Dans [Alfred](https://192.168.1.23:8765/#voice), vérifier que l’ESP32 est
  connecté et que le micro est disponible. Conserver le réglage actuel
  et relever le mot, les variantes, les contrôles micro visibles et la
  position de la carte. Le réglage Bureau est déjà sauvegardé.
- Choisir les deux places les plus utilisées, par exemple le canapé et le
  passage. Noter la distance bouche–micros, la hauteur de la carte et le
  sens dans lequel elle est tournée. Laisser les ouvertures des micros dégagées.
- Placer un micro de studio, ou un téléphone enregistreur, à côté de la carte
  sans masquer ses micros. Pour le balayage, il faut un téléphone émetteur
  et un récepteur distinct. Préférer une prise WAV sans traitements
  automatiques quand le matériel le permet.
- Prévoir 30 à 40 minutes pour la comparaison et le balayage. Faire la
  confirmation sur une séance séparée. La lecture du signal se fait au
  volume confortable d'une voix, sur le haut-parleur du téléphone.

## 1. Référence et comparaison des captations

TV et musique coupées. Dans **Voix & conversation**, utiliser **Tester la
transcription ESP32**, puis K2, ou **Tester à distance** depuis un autre
appareil. Parler seulement après le signal. Enregistrer en parallèle avec
le micro de référence, une prise par phrase. Relever le texte affiché par
Alfred à chaque essai. Le diagnostic n'exécute aucune commande.

| Position | Orientation de la voix | Phrases |
| --- | --- | ---: |
| 50 cm | Face | A, B |
| Place 1 | Face, côté, dos | A, B, C par orientation |
| Place 2 | Face, côté, dos | A, B, C par orientation |
| Place la plus difficile | Côté et dos, TV au volume habituel | A, B, C par orientation |

- **A** « Allume la lumière de la cuisine. »
- **B** « Quel temps reste-t-il sur le minuteur du four ? »
- **C** « Baisse le volume de l’ampli du salon. »

Dire chaque phrase une seule fois à voix naturelle. Pour tester le réveil
séparément, utiliser [Logs → Test guidé du réveil ESP32](https://192.168.1.23:8765/#logs).
À chaque distance choisie, noter l'orientation réelle dans le relevé.
Faire les mesures de face et de dos dans des sessions distinctes si nécessaire
pour garder les résultats identifiables. Marquer chaque raté avec le bouton
prévu. Le test guidé mesure uniquement le mot « Alfred ».

Pour les prises du micro de référence, exporter un WAV PCM16 mono par
phrase. Les renommer avec place, orientation et phrase, par exemple
`salon-p1-dos-A-reference.wav`. Lancer depuis la racine d'Alfred sur le PC
qui a déjà les modèles locaux, avec les chemins des fichiers à comparer.

```powershell
.\.venv\Scripts\python.exe -m alfred.room_benchmark transcrire prise-A.wav prise-B.wav
```

Si une prise est dans un autre format, l'exporter en WAV avec
`ffmpeg -i prise.m4a -ac 1 -ar 16000 -c:a pcm_s16le prise.wav`.
Pour un enregistrement continu, découper par phrase en laissant un peu de
silence de part et d'autre. Comparer les mots qui changent le sens, comme le
nom de pièce, l'action et l'appareil. Noter également les phrases coupées.

| Place / orientation / bruit | Phrase | Texte ESP32 | Texte référence | Mots clés ESP32 / réf. | Coupure ou incident |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

Pour une comparaison sans différence de durée imposée par la détection de
parole, utiliser la prise WAV ESP32 décrite plus bas et le micro de référence
en même temps. Découper les deux fichiers autour de la même phrase.

Un écart répété en faveur du micro de référence, sur les mêmes phrases et
dans plusieurs conditions, indique une limite de la **chaîne de captation**
Waveshare. Celle-ci inclut son matériel, son prétraitement et la façon dont
Alfred borne la prise. La comparaison ne départage pas ces trois éléments.

## 2. Mesure de la pièce au téléphone

Sur le téléphone, utiliser les étapes de balayage du parcours guidé.
La conversation est suspendue pendant chaque prise de 12 secondes. Le WAV
est transféré en mémoire dans l'onglet avant validation et export ZIP.
Pour reproduire la mesure hors parcours, le fichier de balayage peut être
généré localement.

```powershell
.\.venv\Scripts\python.exe -m alfred.room_benchmark signal .local/balayage-salon.wav
```

Le micro de référence reste à la position du satellite. Depuis chaque
place, tenir le téléphone à hauteur de bouche, toujours dans la même
orientation. Démarrer la prise avant la lecture et garder au moins une
seconde de silence après le son. Faire trois prises par position, TV éteinte.
Si possible répéter dans le bureau traité avec le même volume, le même
micro et une distance comparable. Éviter d'utiliser le Bluetooth pour la
lecture, qui déplacerait la source sonore.

```powershell
.\.venv\Scripts\python.exe -m alfred.room_benchmark mesure salon-p1-1.wav salon-p1-2.wav salon-p1-3.wav
```

L'outil donne un rapport indicatif entre l'énergie des 50 premières
millisecondes et celle du reste de la première seconde. Un rapport plus bas
et répétable indique davantage d'énergie tardive pour cette géométrie.
Conserver le même couple téléphone/micro pour les comparaisons. Écarter les
prises saturées, bruitées par un événement ponctuel ou dont l'arrivée est
mal repérée. Ce rapport n'est pas un RT60 ni une identification d'écho
flottant. Le WAV de la Waveshare contient le signal reçu par Alfred après
le traitement embarqué. Le micro de référence permet un contrôle indépendant.

## 3. Réglages, placement et confirmation

1. Retenir la place et l'orientation où l'ESP32 perd le plus de mots ou de
   réveils. Comparer la position actuelle de la carte à une position plus
   dégagée, en gardant exactement la même place de parole. Remettre le
   satellite à sa position de départ pour un dernier passage témoin.
2. Si un réglage micro est effectivement exposé, relever sa valeur puis
   comparer une seule modification à la fois. Si le balayage fait ressortir
   une énergie tardive marquée, la réduction de réverbération côté serveur
   est un candidat à expérimenter. Pour commencer à comparer les traitements
   sur un même WAV, utiliser la commande ci-dessous. Elle compare le témoin
   à un passe-haut à 120 Hz pour les bruits graves. Une hausse de gain peut
   aussi relever le bruit. Comparer sur les transcriptions et les réveils.
3. Pour départager deux candidats, faire dix appels par candidat dans la
   condition difficile, en alternant le réglage de départ et le candidat
   par blocs courts. Ajouter cinq nouvelles phrases par candidat en
   mélangeant côté et dos. Avec le candidat retenu, faire dix minutes de
   TV ou de conversation sans appel volontaire et noter les faux réveils.
4. Conserver le réglage de départ si le bénéfice disparaît sur les nouveaux
   essais. Sinon, consigner comme profil Salon les réglages, la position et
   les résultats. Rapporter les comptes d'essais et le contexte de bruit
   avec chaque taux. Garder les prises de test uniquement dans un dossier
   local de travail, hors Git.

```powershell
.\.venv\Scripts\python.exe -m alfred.room_benchmark transcrire --comparer .local/salon-p1-dos.wav
```

Références de mesure  
[Balayage et réponse impulsionnelle, AES](https://aes.org/publications/elibrary/elibrary-page/?id=10211) ·
[Énergie précoce et tardive, ODEON](https://odeon.dk/learn/articles/concert-hall-acoustics/)
