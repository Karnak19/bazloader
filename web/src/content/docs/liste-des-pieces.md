---
title: Liste des pièces
description: Tout ce qu'il faut commander pour construire un BULLOADER+, avec les pièges à éviter au moment de choisir.
---

Cette page sert de liste de courses. Tout se trouve chez les vendeurs d'électronique en ligne
(AliExpress et compagnie). Pas de liens ni de prix ici, ils changent trop vite : à la place, des
**termes de recherche** à copier-coller, et surtout **ce qu'il faut vérifier sur la fiche du
produit** avant de cliquer sur « acheter ».

Les valeurs (résistances, condensateurs, broches) sont celles de la page
[Câblage](/bulloader-plus/cablage/). Si un jour les deux pages ne disent pas la même chose, c'est le
câblage, et au-dessus de lui
[`firmware/src/config.h`](https://github.com/Karnak19/bulloader-plus/blob/main/firmware/src/config.h),
qui font foi.

Les quantités proposées incluent un peu de marge : ces pièces coûtent quelques centimes à quelques
euros, et attendre trois semaines une deuxième livraison pour une LED abîmée coûte bien plus cher.

## Avant de commander : la tension du servo

:::danger[Vérifiez votre servo avant de passer commande]
Le servo d'origine du BULLOADER est branché **directement sur la batterie 2S**, qui monte à
**8,4 V** une fois pleine. Beaucoup de servos « 35 kg » ne sont prévus que pour **4,8 à 6,8 V** :
au-delà, ils chauffent et finissent par griller. Seuls les servos dits **HV** (*high voltage*)
acceptent 8,4 V.

1. Relevez la référence imprimée sur l'étiquette du servo et cherchez sa fiche technique.
2. **Si la plage de tension monte jusqu'à 8,4 V (servo HV)** : rien à ajouter, il reste sur la
   batterie.
3. **Sinon**, ajoutez à la commande un **BEC** (un petit régulateur de modélisme) ou un second
   convertisseur, dédié au servo. Ce qu'il faut regarder :
   - **le courant** : au moins le **courant de blocage** du servo (*stall current*, ce qu'il tire
     quand il force à l'arrêt, sur la fiche technique). Pour un 35 kg, comptez plusieurs ampères :
     visez **5 A en continu ou plus** ;
   - **la tension de sortie** : dans la plage du servo, par exemple **6,0 V** pour un servo
     4,8–6,8 V. Les UBEC de modélisme ont souvent un cavalier 5 V / 6 V ;
   - **l'entrée** : compatible 2S (7,4 V, 8,4 V pleine).

   Termes de recherche : « UBEC 5A 6V », « UBEC 2-6S 5A ».

**Un MP1584 ne suffit pas pour le servo.** Celui de la liste alimente seulement l'ESP32 : il tient
environ 3 A en pointe, bien moins que ce que tire un gros servo bloqué.
:::

Si vous ajoutez un BEC, le condensateur de 470 µF va à sa sortie, au plus près du servo.

## Ce que vous avez déjà

Ces pièces viennent du BULLOADER d'origine et sont réutilisées. **Ne les commandez pas.**

| Pièce                          | Quantité | Statut       | Utilisée pour                                                                                   |
| ------------------------------ | -------- | ------------ | ----------------------------------------------------------------------------------------------- |
| Batterie LiPo 2S (7,4 V)       | 1        | déjà présent | Alimente tout. Le chargeur LiPo qui va avec aussi.                                              |
| Servo 35 kg 360° (rotation continue) | 1  | déjà présent | Entraîne le mécanisme. Voir l'encadré ci-dessus pour sa tension.                                |
| Interrupteur marche/arrêt      | 1        | déjà présent | Coupure générale, entre la batterie et tout le reste.                                           |
| Bouton (l'ancien bouton 12 V)  | 1        | déjà présent | Devient le bouton **GO** : un simple contact entre GPIO 4 et la masse, débranché de l'ancien 12 V. |

## Électronique principale

| Pièce | Quantité à commander | Spécification exacte | Ce qui compte au moment de choisir | Utilisée pour |
| ----- | -------------------- | -------------------- | ---------------------------------- | ------------- |
| ESP32-C3 SuperMini | **3** (1 utilisée + 2 de secours) | Carte ESP32-**C3** « SuperMini », USB-C, environ 22 × 18 mm. Recherche : « ESP32-C3 SuperMini ». | Bien **C3** : il existe des « SuperMini » en S3, C6 ou H2, qui ne prennent pas ce firmware ni ce brochage. Certains lots ont une antenne faible (portée Bluetooth médiocre) : en prendre plusieurs permet de garder la meilleure. Elles coûtent peu. Les barrettes de broches sont en général livrées à part, non soudées. | Le cerveau : compte les billes, pilote le servo, l'écran et le Bluetooth. |
| Convertisseur abaisseur MP1584 | **2** (1 + 1 de secours) | Module MP1584**EN**, environ 22 × 17 mm, entrée jusqu'à ~28 V, ~3 A en pointe. De préférence à **sortie fixe 5 V** ; sinon **réglable** (petite vis de potentiomètre). Recherche : « MP1584EN 5V fixed output » ou « MP1584EN step down adjustable ». | La version **5 V fixe** est la plus sûre : il n'y a rien à régler, donc pas de vis à mal tourner. Une version réglable convient aussi, mais elle sort d'usine à une tension quelconque, parfois proche de celle de la batterie : il **faut** la régler à 5,0 V au multimètre. Dans les deux cas, **mesurer la sortie au multimètre avant de brancher l'ESP32**. Pas d'autre module à la place : le « Mini-360 », lui, utilise une autre puce. | Fournit le 5 V de l'ESP32 à partir de la batterie. Pas le servo. |

## Capteur infrarouge

| Pièce | Quantité à commander | Spécification exacte | Ce qui compte au moment de choisir | Utilisée pour |
| ----- | -------------------- | -------------------- | ---------------------------------- | ------------- |
| LED infrarouge 3 mm | **1 sachet** (10 à 50 pièces, il en faut 1) | LED émettrice IR, boîtier **3 mm**, **940 nm**. Recherche : « 3mm IR LED 940nm emitter ». | La **longueur d'onde** : **940 nm**, la même que le phototransistor. C'est l'erreur la plus fréquente : une LED 850 nm (elle luit en rouge sombre) avec un capteur 940 nm, ou l'inverse, donne un signal faible et capricieux. Boîtier 3 mm, pas 5 mm : le collier est dessiné pour 3 mm. | Émet le faisceau que les billes coupent. |
| Phototransistor 3 mm | **1 sachet** (10 à 50 pièces, il en faut 1) | Phototransistor NPN, boîtier **3 mm**, **940 nm**, 2 pattes. De préférence en **époxy foncé** (noir ou violet très sombre). Recherche : « 3mm phototransistor 940nm black ». | **940 nm**, comme la LED. L'époxy **foncé** filtre la lumière visible : moins de soucis en plein soleil, à privilégier. Attention aux faux amis : un « récepteur IR » à **3 pattes** (VS1838B, TSOP…) est un récepteur de télécommande, il ne marche pas ici. Une photodiode ressemble à s'y méprendre mais donne un signal bien plus faible : la fiche doit dire *phototransistor*. | Voit le faisceau, et donc chaque bille qui passe. |

## Interface

| Pièce | Quantité à commander | Spécification exacte | Ce qui compte au moment de choisir | Utilisée pour |
| ----- | -------------------- | -------------------- | ---------------------------------- | ------------- |
| Encodeur rotatif KY-040 | **2** (1 + 1 de secours) | Module **KY-040** : encodeur à crans avec clic, monté sur sa petite carte avec ses résistances de tirage, 5 broches (CLK, DT, SW, +, GND). Recherche : « KY-040 rotary encoder module ». | Prendre le **module sur carte**, pas l'encodeur nu. Il se branche en **3,3 V** (pas 5 V), voir le [câblage](/bulloader-plus/cablage/). Si un cran fait avancer de 2 au lieu de 1 (ou l'inverse), ça se règle dans `config.h`, pas besoin de rendre le module. | Régler le nombre de billes, valider d'un clic. |
| Bouton pour l'encodeur | **2** | Bouton de potentiomètre pour axe de **6 mm**, gros diamètre (25 mm ou plus), crénelé ou caoutchouté. Recherche : « knob 6mm shaft knurled ». | Regarder l'axe de votre KY-040 : **cannelé** (crans tout autour) ou **à méplat** (en D). Le bouton doit être prévu pour le même. Gros et crénelé pour s'en servir **avec des gants**. Certains KY-040 sont livrés avec un petit bouton, souvent trop petit. | Tourner la molette sur le terrain. |
| Écran OLED 0,96" | **2** (1 + 1 de secours) | OLED **0,96"**, **128 × 64**, contrôleur **SSD1306**, interface **I2C à 4 broches** (VCC, GND, SCL, SDA). Recherche : « 0.96 OLED SSD1306 I2C 4 pin 128x64 ». | **4 broches, I2C.** Les versions à **7 broches** (SPI) sont les mauvaises. **L'ordre VCC / GND change selon les vendeurs** (GND-VCC-SCL-SDA ou VCC-GND-SCL-SDA) : lire la sérigraphie avant de souder, une inversion grille l'écran. Adresse I2C **0x3C** le plus souvent, parfois **0x3D**. Préférer une couleur unie (blanc ou bleu) : les « jaune/bleu » ont une bande jaune figée en haut. | Afficher l'état, le compte et la batterie. |

## Composants passifs

| Pièce | Quantité à commander | Spécification exacte | Ce qui compte au moment de choisir | Utilisée pour |
| ----- | -------------------- | -------------------- | ---------------------------------- | ------------- |
| Condensateur 470 µF | **5** (il en faut 1) | Électrolytique (chimique) **470 µF**, **16 V ou plus**. Recherche : « 470uF 16V electrolytic capacitor ». | La tension : **16 V minimum** (25 V convient aussi, juste un peu plus gros). Un 10 V ou 6,3 V ne tient pas les 8,4 V de la batterie. Il est **polarisé** : la patte `−` est marquée d'une bande sur le boîtier. | Sur l'alimentation du servo, au plus près de lui : évite les chutes de tension au démarrage du servo. |
| Condensateur 100 nF | **10** (il en faut 1) | Céramique **100 nF** (marqué « 104 »), 50 V. Recherche : « 100nF 104 ceramic capacitor ». | Rien de piégeux. Souvent vendu par 50 ou 100, c'est normal. | Entre GPIO 0 et la masse : lisse la mesure de la batterie. |
| Résistance 220 Ω | dans le kit (il en faut 1) | 220 Ω, 1/4 W. | | En série avec la LED IR (environ 10 mA). |
| Résistance 10 kΩ | dans le kit (il en faut 1) | 10 kΩ, 1/4 W. | | Tirage du phototransistor vers 3,3 V. |
| Résistance 100 kΩ | dans le kit (il en faut 1) | 100 kΩ, 1/4 W. | | Pont diviseur batterie, côté batterie. |
| Résistance 20 kΩ | dans le kit (il en faut 1) | 20 kΩ, 1/4 W. | **20 kΩ** exactement : le firmware calcule la tension batterie avec 100 kΩ / 20 kΩ. À 8,4 V, la broche de l'ESP32 voit alors 1,40 V. | Pont diviseur batterie, côté masse. |
| Kit de résistances | **1** | Assortiment de résistances à couche métallique 1/4 W, 1 %, avec **220 Ω, 10 kΩ, 20 kΩ et 100 kΩ** dedans. Recherche : « metal film resistor kit 1/4W 1% ». | Le plus simple : un kit couvre les quatre valeurs et servira pour la suite. Vérifier dans la liste des valeurs du kit que **20 kΩ** y est (les kits courants de 30 valeurs l'ont). Un **1 MΩ** dans le kit sert aussi si le récepteur IR s'avère être une photodiode plutôt qu'un phototransistor. | Toutes les résistances ci-dessus. |

## Câblage et visserie

| Pièce | Quantité à commander | Spécification exacte | Ce qui compte au moment de choisir | Utilisée pour |
| ----- | -------------------- | -------------------- | ---------------------------------- | ------------- |
| Plaque à pastilles | **1 lot** (5 à 10 plaques) | Plaque d'essai à pastilles, pas de **2,54 mm**, double face, format 5 × 7 cm (à recouper). Recherche : « PCB prototype board double sided 5x7 ». | Pastilles (une par trou), pas de bandes. Double face, les pastilles tiennent mieux. Les cotes exactes du support de l'électronique viendront plus tard : une plaque 5 × 7 cm se recoupe facilement. | Porter l'ESP32, le convertisseur et les petits composants. |
| Barrette femelle 2,54 mm | **1 lot** | Barrettes femelles sécables, pas de 2,54 mm. Recherche : « female pin header 2.54mm ». | Permet d'enficher l'ESP32 au lieu de le souder : on peut le changer en deux secondes. | Support de l'ESP32 sur la plaque. |
| Fil silicone épais | **1 m** de rouge + **1 m** de noir | Fil silicone souple **18 AWG** (environ 0,8 mm²). Recherche : « silicone wire 18AWG ». | Silicone : souple et ne fond pas au fer. Assez gros pour le **courant du servo**, qui se compte en ampères. | Batterie, interrupteur, servo (ou BEC), entrée du convertisseur. |
| Fil fin pour les signaux | **1 lot** (plusieurs couleurs) | Fil silicone **26 ou 28 AWG**, plusieurs couleurs. Recherche : « silicone wire 26AWG 10 colors ». | Plusieurs couleurs pour ne pas se tromper (une couleur par fonction). Le silicone se plie bien dans un boîtier serré. | LED IR, phototransistor, encodeur, écran, bouton GO, signal du servo. |
| Connecteurs JST-XH 2,54 mm | **1 kit** (2, 3, 4 et 5 broches) | Kit JST-XH 2,54 mm : embases à souder et fiches. Le plus simple : des **câbles déjà sertis**. Recherche : « JST XH 2.54 pre-crimped cable » ou « JST XH connector kit ». | De quoi **débrancher** chaque pièce (écran, encodeur, capteur IR, bouton) pour démonter sans dessouder. Avec des fiches à sertir, il faut une pince à sertir : les câbles pré-sertis l'évitent. Les Dupont font aussi l'affaire, mais tiennent moins bien aux vibrations. **Pas pour le courant du servo** : gardez pour lui sa prise d'origine. | Brancher l'électronique sur la plaque. |
| Vis M3 × 10 | **1 lot** (il en faut 1) | Vis **M3 × 10 mm**, tête cylindrique à six pans creux (BTR). Recherche : « M3 x 10 socket head screw ». | Longueur **10 mm**. Un assortiment M3 de 6 à 20 mm sert aussi pour la suite (support de l'électronique). | Ferme le collier IR autour du tube. |
| Écrou M3 | **1 lot** (il en faut 1) | Écrou hexagonal **M3** standard (5,5 mm sur plats, 2,4 mm d'épaisseur). Recherche : « M3 hex nut ». | Écrou hexagonal ordinaire, pas un écrou à embase ni un frein en nylon : il doit entrer dans son logement hexagonal du collier. | Logé dans le collier IR, en face de la vis. |
| Gaine thermorétractable noire | **1 assortiment** | Gaine thermo **noire**, diamètres de 1,5 à 6 mm. Recherche : « heat shrink tube black assortment ». | **Noire** : en plus d'isoler les soudures, elle protège le dos du phototransistor de la lumière. | Isoler les soudures, et ombrer le phototransistor et ses pattes. |

## Impression

| Pièce | Quantité à commander | Spécification exacte | Ce qui compte au moment de choisir | Utilisée pour |
| ----- | -------------------- | -------------------- | ---------------------------------- | ------------- |
| Filament PETG ou PLA | **1 bobine** (le collier n'en prend que quelques grammes) | PETG ou PLA **noir** (ou très foncé), **opaque**. | Une couleur claire ou translucide laisse passer l'infrarouge à travers les parois et éblouit le capteur au soleil. **Noir opaque**, pas de « transparent » ni de « silk ». | Le [collier IR](https://github.com/Karnak19/bulloader-plus/tree/main/cad) et sa pièce de test (`fit_coupon`). |

Les fichiers à imprimer et la façon de les régler sont dans le dossier
[`cad/`](https://github.com/Karnak19/bulloader-plus/tree/main/cad) du dépôt.

## Outils

| Outil | Indispensable ? | Pourquoi |
| ----- | --------------- | -------- |
| Multimètre | **Oui** | Régler le convertisseur à 5,0 V avant d'y brancher l'ESP32. Sans multimètre, pas de montage. Sert aussi à calibrer la mesure de la batterie. |
| Fer à souder, étain, flux | Oui | Toutes les connexions. Un fer réglable en température est bien plus agréable. |
| Pied à coulisse | Oui | Mesurer le diamètre du tube de sortie (*inner barrel*) et des composants IR, pour ajuster le collier. Un modèle numérique bon marché suffit. |
| Foret de **1,5 mm** (avec un porte-foret à main ou une petite perceuse) | Oui, très probablement | Le tube de sortie est sans doute en métal, donc opaque à l'infrarouge : il faut y percer **deux trous face à face**, alignés avec les fenêtres du collier, pour que le faisceau passe. |
| Câble USB-C **de données** | Oui | Flasher l'ESP32. Beaucoup de câbles USB-C ne font que charger : si la carte n'apparaît pas sur l'ordinateur, essayez un autre câble. |
| Pince à dénuder, pince coupante | Oui | Préparer les fils. |
| Pistolet à air chaud ou briquet | Pratique | Rétracter la gaine. |
| Pince à sertir JST-XH / Dupont | Seulement avec des fiches à sertir | Inutile avec des câbles pré-sertis. |

## À la réception

Avant de souder quoi que ce soit :

1. **Écran OLED : lire l'ordre des broches** sur la sérigraphie (VCC et GND peuvent être inversés
   par rapport au [schéma](/bulloader-plus/cablage/#schéma-de-câblage)). Notez-le.
2. **LED et phototransistor : vérifier le marquage 940 nm** sur les sachets, et ranger les deux à
   part pour ne pas les mélanger (ils se ressemblent).
3. **Convertisseur : le régler à 5,0 V au multimètre, ESP32 débranché**, avant toute autre chose.
   Voir la [première mise sous tension](/bulloader-plus/cablage/#première-mise-sous-tension).
4. **Mesurer le diamètre du tube de sortie** au pied à coulisse, à l'endroit où ira le collier, ainsi
   que le corps de la LED et du phototransistor. Reporter les valeurs dans
   [`cad/params.py`](https://github.com/Karnak19/bulloader-plus/blob/main/cad/params.py).
5. **Imprimer la pièce de test** (`fit_coupon`) pour trouver le bon jeu, comme expliqué dans le
   [README du dossier `cad/`](https://github.com/Karnak19/bulloader-plus/tree/main/cad#fit_coupon),
   avant d'imprimer le collier.

Ensuite, place au [câblage](/bulloader-plus/cablage/).
