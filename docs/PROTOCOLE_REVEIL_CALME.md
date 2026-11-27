# Protocole de réveil ESP32 au calme

Ce protocole permet de comparer les moteurs et réglages de réveil avec la
même carte Waveshare. Il porte sur le réveil seul. La validation humaine reste
à effectuer lorsque le satellite sera reconnecté.

## Préparation

Placer la carte à son emplacement habituel dans le bureau, micros dégagés.
Couper télévision et musique. Mesurer la distance entre la bouche et la carte.
Choisir le moteur et le mot d'appel ; noter le modèle, le seuil éventuel et les
réglages du micro. Garder ces paramètres et la carte fixes pendant la séance.
Vérifier que le terminal est connecté et que son flux audio est reçu.

## Séance

Commencer par trente secondes de silence. Se placer face à la carte, parler à
voix normale et prononcer une seule fois le mot choisi pour chaque essai.
Attendre trois secondes entre les essais. Noter chaque détection et chaque appel
volontaire non détecté ; recommencer un essai si la manipulation était incorrecte.

| Distance | Nombre d'appels |
| --- | ---: |
| 50 cm | 5 |
| 1 m | 10 |
| 2 m | 5 |
| 3 m | 5 |

Si la pièce ne permet pas une distance, noter l'étape non réalisée et la distance
disponible ; ne pas la compter comme échec. Terminer par trente secondes de
silence et noter les éventuels déclenchements spontanés.

## Résultats

Indiquer les réussites sur le nombre d'appels par distance, le niveau du micro,
les saturations et les interruptions éventuelles. Pour openWakeWord, relever le
score maximal et le seuil ; pour STT, relever l'activité vocale et le résultat
de reconnaissance. Une déconnexion invalide l'essai concerné.

Premier repère proposé : au moins neuf réussites sur dix à un mètre au calme.
Une minute de silence ne suffit pas à mesurer la fréquence des faux réveils.
Pour comparer deux méthodes, répéter la séance au même endroit, avec la même
voix et le même mot d'appel, en modifiant une seule variable à la fois.
