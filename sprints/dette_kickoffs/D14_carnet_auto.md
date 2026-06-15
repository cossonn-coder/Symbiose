# Dette D14 — Carnet auto (descriptif → interprétatif)

> **Kickoff autosuffisant.** Lis ce fichier en entier, puis les sources, puis
> exécute. Français + pédagogie. **Conception SEULE d'abord** (`CONCEPTION_CARNET.md`,
> valider avec Nico, puis impl.). Ampleur **moyenne**.

## Ce que c'est, en une phrase
Concevoir le **carnet auto** : la 2ᵉ des trois voix narratives diégétiques —
**enregistrement automatique des événements**, consultable et indexé, qui **bascule
de descriptif à interprétatif** au seuil de maîtrise du concept concerné. C'est le
dispositif qui **préserve la méthode scientifique** pendant l'apprentissage (il
décrit sans expliquer) puis **révèle les causes** une fois la compréhension acquise.

## Le contexte (CLAUDE.md + conception faite)
- **CLAUDE.md, « Trois voix narratives »** : le carnet = **voix interne à la première
  personne**, **descriptif au début**, **interprétatif au seuil de maîtrise**.
  « Préserve la méthode scientifique pendant l'apprentissage, révèle les causes une
  fois la compréhension intériorisée. » Réglage d'aide : « Carnet interprétatif
  anticipé : OUI/NON (défaut NON) ».
- **La maîtrise pilote la bascule** (`CONCEPTION_MAITRISE.md` §7) : « D14 (carnet) —
  bascule descriptif → interprétatif au **seuil de maîtrise** d'un concept (table de
  mapping, §8) ». La table exacte des seuils = **D12.2** (séparé).
- **Les événements existent déjà comme marqueurs** : `sim/maitrise_detection.py` lit
  des **marqueurs** émis par le tick (`🌱` semis, `⏸` dormance, `🌑` mort,
  `❄` gel, `🌰` graine, etc.) avec une **identité de zone** `(tile_id, r, c)` et une
  **cause** (sec→eau, ombre→lumière, froid→météo). **C'est la matière première du
  carnet** : les mêmes événements qui nourrissent la détection de succès peuvent
  alimenter les entrées du carnet. Le carnet **n'a pas besoin de nouveaux signaux**,
  juste de les **formuler**.
- **Le concept de maîtrise par cause existe** : la détection mappe déjà sec→eau,
  ombre→lumière, froid→météo. Le carnet bascule **par concept** → il lit le **palier
  du concept** correspondant à l'événement.

## Ce qui est déjà tranché (ne pas re-débattre)
- Carnet = **dans la maison** (hub, fonction « Carnet »). Consultable, indexé.
- **Première personne**, voix interne. Pas de narrateur omniscient.
- Bascule pilotée par la **maîtrise du concept**, pas par le temps ni un compteur
  d'événements.
- Réglage d'aide « interprétatif anticipé » = **OUI/NON** déjà spécifié (défaut NON).

## 🔵 Choix de design à trancher
### Choix 1 — Le carnet stocke-t-il les événements, ou les re-dérive-t-il ?
- **(A) ⭐ Journal append-only borné** : chaque marqueur observé écrit une entrée
  `{semaine, zone, type, cause, texte}` dans une liste **plafonnée** (run éternel →
  pas de journal infini ; on garde les N derniers + un résumé agrégé des anciens,
  même logique de bornage que la structure de croissance). **Pour** : indexation et
  consultation triviales, fidèle au « enregistrement automatique ». **Contre** :
  state à sérialiser (save).
- **(B) Re-génération à la volée** depuis l'état + seed : zéro stockage. **Contre** :
  un carnet *auto* qui n'enregistre rien est un contresens ; et certains événements
  passés ne sont plus reconstructibles. **Déconseillé.**

> Reco : **(A)**, borné — c'est littéralement « enregistrement automatique ».

### Choix 2 — Granularité de la bascule descriptif → interprétatif
- **(A) ⭐ Par entrée, selon le concept au moment de la CONSULTATION** : une même
  entrée s'affiche descriptive si le concept n'est pas maîtrisé, interprétative
  sinon — recalculé à la lecture. **Pour** : une entrée ancienne « se révèle »
  rétroactivement quand tu maîtrises enfin son concept (moment de gameplay fort :
  relire ses vieilles notes et *comprendre*). **Contre** : il faut stocker le concept
  par entrée (trivial, déjà dans la cause).
- **(B) Gelée à l'écriture** : l'entrée garde le ton qu'elle avait quand elle a été
  écrite. Plus simple, mais perd la révélation rétroactive.

> Reco : **(A)** — la révélation rétroactive est le cœur émotionnel du dispositif
> (« la compréhension intériorisée révèle les causes »).

### Choix 3 — Qui écrit le texte ? (le vrai défi de contenu)
Le carnet est une **voix**. Deux registres par entrée (descriptif / interprétatif).
- **(A) ⭐ Gabarits paramétrés** : par `(type d'événement, cause)`, deux gabarits de
  phrase (descriptif : « *Le plant du coin nord a jauni cette semaine.* » /
  interprétatif : « *Encore la sécheresse — le sol y draine trop vite, je le sais
  maintenant.* »), avec des slots remplis depuis la zone/espèce. **Pour** :
  déterministe, traduisible, golden-neutre, volume gérable (≈ 2 × nombre de
  types×causes). **Contre** : écriture éditoriale à produire (ce *contenu* est le gros
  du travail — pas la mécanique).
- **(B) Génération procédurale plus libre** (variations) : plus vivant, plus risqué,
  reportable.

> Reco : **(A)** pour la v1. **Note** : la rédaction des gabarits est un **sujet
> hors expertise technique** — produire d'abord un *tableau type×cause → 2 phrases*
> comme livrable éditorial à relire, pas du code.

## Périmètre — phase CONCEPTION (livrable)
`docs/conception/CONCEPTION_CARNET.md` actant : les 3 choix ; la **source d'événements**
(réutiliser les marqueurs de `maitrise_detection.py`, **sans** toucher au tick) ;
l'**interface** (`carnet_consigner(event)` appelée par le **driver** après le tick —
même logement que la détection de succès, jamais importée par `engine`) ;
`carnet_lire(game_state, player, filtre) -> entrées` qui choisit le registre selon le
**palier du concept** ; le **bornage** (plafond + résumé) ; et **ce qui est renvoyé à
D12.2** (le *seuil* exact de bascule par concept). Plus le **tableau éditorial**
type×cause → 2 phrases (à relire par Nico).

## Hors périmètre
Le **seuil** exact palier→bascule (← D12.2). L'**UI Godot** du carnet. La rédaction
fine de tous les gabarits (itératif). L'**encyclopédie** (voix « naturaliste qui
observe » — distincte du carnet « je »). Portage C# (D24).

## Golden / vérification
Conception = zéro code. À l'impl. : le carnet vit **au-dessus du tick** (driver, comme
la détection de succès et la Vigueur) → **golden écolo INTACT** (jamais re-figé).
Tests : une entrée consignée par marqueur ; bascule de registre quand le palier du
concept franchit le seuil ; bornage (le journal ne croît pas sans fin). MAJ
`DETTE.md` D14 + `BACKLOG.md`.
