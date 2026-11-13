# Conception — GESTES LISIBLES

> Figée le 2026-11-13 (`/conception`, dialogue avec Nico). Reprend **D136 (a)-(f)**, le
> retour F5 de la refonte des gestes (`conception_refonte_palette.md`). Sprint :
> `sprints/joueur/gestes/sprint_gestes_lisibles/`.
> **Hors sprint** : D136 (g) structures en volume (second sprint) ; (h) paysage (après la
> rivière) ; le mini-jeu des outils (`sprint_outils_atelier`, à concevoir) ; l'automate à
> intentions (`sprint_automate_intention`, à concevoir) ; le devenir des fruits récoltés
> (dette, à concevoir) ; les autres états du sol (D108, qui « remplira le canvas »).

## 1. Le problème (F5 de Nico, 2026-11-13)

Un geste se joue, mais **rien ne le raconte** :
- le curseur ne bouge presque pas : les animations sont l'icône 16×16 **décalée** de 1 à
  3 pixels de grille (7 recettes partagées, `visuals/AnimationGeste.cs`). Une lame qui
  avance d'un pixel = 2 px d'écran : invisible ;
- le jardin ne garde aucune trace : bêcher, ameublir, piétiner n'écrivent que des champs
  invisibles ; le paillis ne couvre pas le plot ; le cadavre déraciné reste debout ;
- les messages affichent des chiffres (contre la philo #5) et ces chiffres valent zéro,
  parce que les quantités (glaner, épandre, miel) sont minuscules ;
- certains gestes à deux temps (bouturer, épandre, déplacer un pot) ne disent pas qu'on
  tient quelque chose en main.

## 2. Principe : l'outil bouge, le jardin se souvient

Deux lieux, deux rôles (D1) :
- **le CURSEUR montre l'outil qui agit** : l'arrosoir se penche, le pied descend, la main
  tire. Petites animations **précuites image par image**, jouées une fois ;
- **le MONDE montre la conséquence**, au point du clic, à l'échelle du zoom : mottes
  retournées, empreinte de pas, paillis étalé, cadavre couché. C'est le **sol-canvas**.

Règle cardinale (D3, Nico : « non, on invente pas ») : **la vue ne dessine que ce que le
moteur sait**. Une trace sans fait moteur derrière n'existe pas.

## 3. Le sol-canvas (D2, D8)

Le sol est une surface où gestes et événements laissent des traces. Une **couche de
traces par tuile**, dessinée en lot (un maillage par tuile, reconstruit seulement quand sa
liste change — patron du sol en lot de D106). Deux sources honnêtes :

### 3.1 Registre des traces de gestes (moteur)
`game_state["traces_sol"]` : liste d'entrées `{tuile, r, c, x_cm, y_cm, sorte, semaine}`,
écrite par le geste **hors tick** (au moment où le pont applique l'action), déterministe,
sauvée avec le profil, exportée au pont. Une trace **s'efface** au-delà de sa durée ; la
purge se fait à l'écriture d'une nouvelle trace et à l'export (jamais dans le tick →
golden neutre ; le smoke n'a pas de joueur). Plafond de taille (FIFO) pour borner le save.

| sorte | geste | aspect (vue) | durée (calibrage F5) |
|---|---|---|---|
| `becher` | becher | mottes retournées, terre sombre et grumeleuse | 6 sem |
| `grelinette` | grelinette | raies parallèles d'aération, terre claire ameublie | 4 sem |
| `pas` | ecraser (au point x_cm, y_cm) | empreinte de botte | 2 sem |
| `epandre` | epandre | voile de compost brun foncé | 4 sem |
| `arroser` | arroser | auréole de terre mouillée, plus sombre | 1 sem |
| `creuser` | creuser | rebord de terre rejetée autour de la cuvette | 6 sem |

Les **autres conséquences sont déjà des faits moteur**, la vue doit seulement mieux les
dessiner : la cuvette de `creuser` (`altitude`, et la mare qui s'agrandit d'elle-même si
l'eau converge — émergent, rien de scripté) ; le paillis (`paillage`, profondeur +
nature) qui doit **couvrir tout le plot**, dans la DA, BRF bien visible ; la litière qui
quitte le plot à `empiler_bois` / `glaner` ; la pile qui **grossit avec sa quantité**.

**Cadavre déraciné** : `deraciner` passe par `deposer_mort`, qui marque `stade_mort =
"seche"` (debout). Une plante arrachée **gît au sol** : le geste la pose directement en
`"couchee"` (fait moteur ; touche la décomposition du seul cadavre déraciné ; hors tick).

### 3.2 Événements (états moteur déjà calculés)
- **Pluie qui éclabousse** : quand la météo du snapshot est pluvieuse, des éclaboussures
  au sol, densité ∝ intensité. Lecture du snapshot, effet transitoire de vue.
- **Sécheresse qui craquelle** : le pont exporte une liste CREUSE des plots secs
  (`humidite` sous un seuil) ; la vue y dessine un sol craquelé, avec **hystérésis**
  d'affichage contre le clignotement.

Le reste (imbibé, herbacé, litière par paliers…) = D108, sur ce même canvas, plus tard.

## 4. Animations du curseur précuites (D1)

- Chaque geste a une **suite d'images** (4 à 6) qui **décompose le mouvement**, cuites une
  fois (cache existant), jouées une fois à `applied`. Plus de recettes à ±1 px.
- Deux moyens de fabriquer une image, au choix par geste : **grille dessinée** (16×16,
  alphabet d'`IconeGeste`) pour les poses impossibles par transformation (main qui saisit
  une touffe, coccinelle qui ouvre les ailes, pied qui entre dans le cadre) ; ou
  **transformation** enrichie d'une **rotation autour d'un pivot** (l'arrosoir se penche
  de 30-45°) et de décalages **≥ 3 px de grille**. Le point chaud ne bouge pas.
- Décompositions demandées par Nico : `arroser` (s'incline, l'eau coule) ; `ecraser` (le
  pied monte puis descend franchement) ; `deraciner` (traction vers le haut, la motte
  suit) ; `arracher` (la main saisit une touffe et tire) ; `favoriser_auxiliaire` (la
  coccinelle ouvre les ailes) ; `pincer`, `glaner`, `drainer`, `bouturer`, `couper`,
  `tailler`, `retourner` (aujourd'hui invisibles). Tous les autres gestes passent au même
  standard.
- **Icônes** : inverser les outils (sécateur = `tailler`, scie = `couper`) ; redessiner
  `pincer` et `glaner` (incompris).
- Le **refus** reste une secousse, plus ample (±2 px de grille).
- Ces images servent **aussi dans le monde** : l'automate n'a pas de curseur, ses gestes
  se jouent comme un sprite de l'outil au point visé (§7).

## 5. Messages et quantités (D5)

- **Aucun chiffre** dans les messages de geste. Une quantité se dit en mots, par paliers
  exprimés en doses (`PAILLAGE_DOSE`) : « une pincée », « une poignée », « une brassée »,
  « un panier plein »… Un gain de Vigueur se dit en ressenti (« un peu de force revient »).
  Les phrases vivent au pont (`tools/simserver/`), là où elles sont fabriquées aujourd'hui.
- **Rééquilibrage À L'EXCÈS** (Nico) pour tester, quitte à réduire après : un glanage d'un
  plot ordinaire rapporte **au moins une dose** de paillis ; un bac plein donne **au moins
  un épandage franc** par saison ; une ruche peuplée donne un miel qui **se sent**. À
  mesurer d'abord (bancs), puis calibrer les constantes **côté geste** de préférence. Une
  constante lue dans le tick ne bouge que si le golden reste identique.

## 6. Règles et ergonomie

**Règles (D136 e)**
- `ecraser` **ne touche pas les animaux volants**. Attribut de donnée `vole` par espèce de
  faune (registre `fields/population/`), refus en amont au moteur (aucune Vigueur
  dépensée), et la vue ne propose pas un sprite volant comme cible. Volants : pollinisateurs
  (abeille, bourdon, papillon, syrphe…), libellule, moustique, oiseaux, rapace. Le code
  d'alarme « écraser une abeille » reste en place (règle « ne rien jeter »), devenu
  inatteignable par ce chemin ; l'alarme du miel sans équipement le garde vivant.
- **Pot posé hors du jardin** : bug à reproduire et corriger là où il naît (pont ou vue).
- `arroser` **reste un geste de base**. L'arrosoir à prendre (D4) part avec tous les outils
  dans `sprint_outils_atelier` (Nico, Q8 : « on touche à rien des outils en attendant »).

**Gestes incompris (D136 d) et ergonomie (D136 f)**
- **Objet en main** : tout geste à deux temps montre ce qu'on tient. Après le premier
  clic, le curseur porte l'objet (bouture pour `bouturer`, pelletée de compost pour
  `epandre`, brassée de litière pour `composter`, **le pot lui-même** pour `deplacer_pot`),
  et les cibles valides sont signalées (pour `bouturer` : la contrainte « même tuile » se
  voit, au lieu de se découvrir par un refus).
- `favoriser_auxiliaire` doit **se voir** : l'habitat posé (rondelle `auxiliaire` sur un
  tuteur de la tuile) est dessiné, et la coccinelle s'anime au curseur.
- **Catalogue des graines** de `planter` : trié (ordre alphabétique du nom affiché), il se
  **referme au choix**.
- `planter_conteneur` simplifié : un clic sur le pot plante la graine choisie, sans étape
  de plus que `planter`.
- **Récolter en cliquant le fruit**, pas le tronc : la désignation vise l'organe mûr ; un
  clic ailleurs sur la plante ne récolte pas et le dit.

## 7. L'automate (D7, D10 — part de ce sprint)

- **Reste actif fenêtre fermée** : fermer l'onglet ne le débranche plus ; la touche A le
  branche/débranche, un indicateur discret dit qu'il tourne.
- **Ses gestes se voient** : la vue lit le journal de l'automate du dernier tick et joue,
  au point visé, le sprite animé de l'outil (§4) ; les traces suivent (§3), puisqu'il passe
  par les mêmes gestes moteur.
- **Mode testeur** : un banc déclare un **plan de test** = liste ordonnée `(verbe, cible)`.
  La vue le déroule **par le même chemin qu'un clic du joueur** (dispatch d'action normal),
  un geste toutes les quelques secondes, et consigne appliqué / refusé dans un rapport.
  C'est le banc d'observation du sprint : on regarde les animations et les traces sans
  jouer 46 gestes à la main, au F5 comme à la capture VM.
- L'automate à intentions (« un semblant d'âme », diversité, récolte, luxuriance) =
  `sprint_automate_intention`, conception à part.

## 8. Philo, perf, golden

- #1/#2 : aucun bonus sur les plantes ; les traces sont un souvenir de geste, pas un effet.
  #3 : registre déterministe, purge par semaine. #5 : traces et mots au lieu de chiffres.
  #6 : bêcher se voit, ses conséquences sur les vers se voient ensuite — on apprend à l'œil.
- Perf : registre borné (FIFO) ; couche de traces en lot par tuile, reconstruite au
  changement seulement ; éclaboussures en nombre borné. Aucun coût au tick moteur.
- **Golden `b4a921f8…` intact sur tout le sprint.** Aucun re-figeage prévu : un
  rééquilibrage qui le ferait bouger est abandonné au profit d'une constante côté geste.

## 9. Tronçons

① moteur + pont · ② animations du curseur · ③ sol-canvas (vue) · ④ objet en main et
ergonomie · ⑤ automate (actif fenêtre fermée, gestes visibles, mode testeur) · ⑥ banc
d'observation, recette F5, clôture. Kickoffs dans le dossier du sprint.
