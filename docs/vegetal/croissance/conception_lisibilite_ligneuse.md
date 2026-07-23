# Conception — Lisibilité de l'architecture ligneuse (le vieux pommier)

**Date :** 2026-07-23 · **Statut :** FIGÉ, prêt pour `/sprint-auto`
**Type/thème :** `vegetal/croissance` (lignée D29 croissance procédurale, D21 pérennes)
**Origine :** retour F5 Nico — un vieux pommier a un « tronc comme un baobab »,
des « branches emmêlées comme des ronces », un « diamètre uniforme (ronces
diamètre baobab) » ; « on ne sait pas trop ce qu'on regarde ».

Problème de **lisibilité de forme**, pas d'exactitude botanique. Objectif :
qu'un vieux pommier **se lise comme un arbre** (tronc net + houppier
hiérarchisé), pas comme un roncier épaissi.

---

## 1. Cause racine (établie par lecture du moteur — source de vérité)

Le défaut vit dans le **moteur Python** (`sim/growth/phases.py`), pas dans la vue.
À chaque tick, `_elongate_emit` fait, pour **tout segment non-apex** :

```python
s.thickness_cm += THICKEN_RATE       # 0.03 cm/tick — constant, uniforme, NON borné
```

L'épaississement est **constant, uniforme, non borné, et indépendant de l'ordre
de branche**. Combiné au pommier (`wood_persistence = 4000` sem., le bois vit
~77 ans) :

| Symptôme observé | Mécanisme |
|---|---|
| Tronc « baobab » | `0.03/tick × ~4000 sem → ~120 cm`, sans plafond |
| « Ronces diamètre baobab » (pas d'amincissement) | même incrément pour la brindille et le tronc → une vieille brindille est aussi grosse que le tronc |
| Branches « emmêlées » | conséquence : sans contraste d'épaisseur, l'œil ne distingue plus tronc → charpentières → rameaux |

Deux faits qui cadrent la solution :

- **La topologie encode déjà l'ordre de branche** (`_depths`, `_children`,
  `_subtree` dans `sim/growth/geometrie.py`) — elle n'est simplement **pas lue**
  par l'épaississement. La hiérarchie flèche/buisson existe déjà via l'auxine
  (`apical_dominance_base`). → **pas de nouvelle mécanique de ramification** ;
  l'« emmêlement » est d'abord un défaut de **contraste d'épaisseur**.
- **`thickness_cm` n'a AUCUN couplage écologique** (ni lumière, ni compétition,
  ni biomasse — vérifié par balayage). C'est une pure grandeur morphologique de
  rendu. Changer son modèle ne ripple **pas** dans l'écosystème.

---

## 2. Modèle figé — pipe model + croissance secondaire saturante

Remplacer l'accumulation uniforme par un modèle où l'épaisseur **dérive de la
topologie** (philo #2) :

```
thickness_i = THICKNESS_INIT + girth_max_espèce · sat(âge_i) · taper_i

   sat(âge)  = 1 − exp(−âge_i / GIRTH_TAU)          ∈ [0,1[   (âge en semaines)
   taper_i   = (n_term_i / n_term_racine) ^ TAPER_EXP ∈ ]0,1]
```

- **`taper_i` — pipe model** (Léonard de Vinci / Shinozaki 1964 : la section
  d'une branche ≈ somme des sections qu'elle porte). `n_term_i` = **nombre de
  segments terminaux** (apex + extrémités feuillues) portés dans le sous-arbre
  de `i`. Le tronc porte tous les terminaux (`taper=1`), une brindille n'en
  porte qu'un (`taper` minimal). ⟹ **amincissement** tronc → charpentières →
  brindilles ⟹ tue « ronces diamètre baobab » et rend l'arbre lisible.
- **`sat(âge)` — croissance secondaire (cambium) SATURANTE.** Un segment
  épaissit avec l'âge, mais l'effet **plafonne** (asymptote `girth_max`). ⟹ un
  tronc reste **vénérable** (gros, net) **sans jamais devenir baobab** ⟹ tue
  « baobab ».
- **`girth_max_espèce`** — épaisseur cible du tronc mûr, **par espèce** (nouveau
  levier `girth_max_cm`, §3). Cohérent #7 et avec la façon dont `perennials.py`
  porte déjà les gabarits par espèce.

L'« âge = vénérable » émerge donc **doublement** : un vieil arbre a un houppier
plus grand (⟹ plus de terminaux ⟹ `taper` du tronc plus fort **relativement**)
ET des segments plus vieux (⟹ `sat` plus proche de 1). Les deux effets sont
**bornés** (max_segments plafonne les terminaux, `sat < 1` plafonne l'âge).

### Propriétés garanties
- **Amincissement monotone** : `thickness_parent ≥ thickness_enfant` (le
  sous-arbre d'un parent contient celui de chaque enfant ⟹ `n_term` décroît vers
  les feuilles ; à âge égal, la monotonie tient). Testable.
- **Tronc borné** : `thickness_tronc ≤ THICKNESS_INIT + girth_max_espèce`.
- **Déterministe, zéro RNG** (philo #3) — pur post-ordre sur la topologie.
- **Perf neutre** : **1 passe O(n) post-ordre par tick** (n ≤ `max_segments`,
  70 pour le pommier), qui **remplace** l'incrément O(n) existant. Le comptage de
  terminaux réutilise `_children`. Aucune boucle O(n²) ajoutée. Calculé **une
  seule fois par tick**, en fin de `grow_plant` après élagage (la topologie est
  alors stable) — pas de recalcul intra-tick (garde-fou mémoïsation).

### Calibrage (placeholders → F5, posés au tronçon ①)
- `GIRTH_TAU` (semaines de saturation d'âge) et `TAPER_EXP` (`p`) = leviers de
  **module** dans `sim/growth/constantes.py`. `p = 0.5` = pipe model physique
  (section ∝ n_term) ; `p → 1` = hiérarchie visuelle plus marquée. Défaut à
  poser, ajusté à l'œil au F5.
- `girth_max_cm` par espèce ligneuse. Défaut **faible** sur `PlantBase` pour que
  les **herbacées procédurales** (tomate, grimpantes) restent proches de
  l'actuel — l'amplitude du re-figeage est ainsi **concentrée sur les ligneux
  visibles**.

### Périmètre — effet visible sur le pommier seul (arbitré Nico 2026-07-23)
Parmi les 10 arbres du catalogue, **un seul est `procedural_growth=True` : le
pommier** ; les 9 autres (aulne, hêtre, bouleau, cerisier, figuier, sapin, charme,
chêne, noyer) n'ont **aucune topologie de segments** — ils sont rendus par une
**silhouette de couronne** (empreinte), sans branches individuelles. Le modèle
taper est **générique** et `girth_max_cm` est posé **sur toutes les espèces
ligneuses** (valeurs cohérentes prêtes), mais il ne **produit un effet visible**
que sur les espèces procédurales — **aujourd'hui le pommier** (+ tomate/grimpantes
côté non-arbres). **Migrer les 9 autres arbres en croissance procédurale = sprint
distinct** (chaque espèce doit régler ses leviers de croissance comme le pommier),
**ouvert en dette** (cf. D29/D26). Ce sprint reste fidèle au retour F5 : la
lisibilité de l'ossature ligneuse, là où elle est dessinée.

---

## 3. Où ça s'insère

- `sim/growth/constantes.py` — `THICKEN_RATE` devient **obsolète** (l'accumulation
  disparaît) ; nouveaux leviers `GIRTH_TAU`, `TAPER_EXP`. `THICKEN_RATE` est
  **conservé** (commenté « obsolète », non supprimé — garde-fou « conserver le
  code »).
- `sim/growth/geometrie.py` — nouvelle fonction pure `taper_thickness(segs,
  girth_max, tau, exp)` : compte les terminaux par sous-arbre (post-ordre via
  `_children`) et retourne l'épaisseur par segment. Pure, déterministe.
- `sim/growth/phases.py` — `_elongate_emit` : retirer la ligne
  `s.thickness_cm += THICKEN_RATE`. `grow_plant` : appeler `taper_thickness`
  **une fois** en fin de passe (après `_elaguer`), pour les espèces
  `procedural_growth`, et écrire `thickness_cm` sur chaque segment.
- `plants/base/familles.py` — nouvel attribut de classe `girth_max_cm` sur
  `PlantBase` (défaut faible), lu par `grow_plant`.
- `plants/perennials.py` — `girth_max_cm` par espèce ligneuse (pommier plus gros
  que cerisier/aulne, etc.).
- `tools/maquette/organes.py` (`LEAF_MAX_THICK_CM`) — recalibrer contre la
  nouvelle échelle (maquettes SVG). *(Côté C# = tronçon ②.)*

---

## 4. Respect de la philosophie #1–#7
- **#2** ✓ — l'épaisseur **dérive** de l'état (topologie + âge), aucun bonus/malus
  plaqué. Plus #2-conforme que l'accumulation actuelle.
- **#3** ✓ — post-ordre déterministe, zéro RNG.
- **#5** ✓ — la **forme** porte l'information : tronc épais net + brindilles fines
  disent l'âge et l'espèce à l'œil, sans chiffre.
- **#7** ✓ — deux pommiers (topologies distinctes via `form_seed`) diffèrent, mais
  **tous deux se lisent comme des pommiers**.

## 5. Interconnexions
- **D29** (croissance procédurale, topologie de segments) — socle direct.
- **D21** (pérennes ligneuses, `perennials.py`) — porte les `girth_max_cm`.
- **Couplage rendu** : largeur de trait (`×2.2`) et placement des feuilles
  (`LeafMaxThickCm`) côté C# lisent `thickness_cm` → recalibrage au tronçon ②. La
  **couleur du bois est AGE-based** (`LignifyFullWeeks`), donc épargnée.

## 6. Voix narratives
Le pommier existe déjà au catalogue (D21) ; **aucune espèce ajoutée** ⟹ aucune
voix nouvelle obligatoire. Complément d'**encyclopédie** optionnel au tronçon ②
(le port de l'arbre âgé : tronc dégagé, charpentières, houppier) si utile — pas
bloquant.

---

## 7. Découpage (2 tronçons)

- **① Moteur — pipe model + taper + girth par espèce.** `taper_thickness` pure,
  branchement dans `grow_plant`, `girth_max_cm` sur `PlantBase` + espèces
  ligneuses, retrait de l'accumulation, recalibrage `LEAF_MAX_THICK_CM` maquette.
  Tests : amincissement monotone (parent ≥ enfant), tronc borné, déterminisme.
  **Golden RE-FIGÉ maîtrisé et annoncé** (dérive localisée au champ `thickness_cm`
  des plantes `procedural_growth` — concentrée sur les ligneux).
- **② Vue Godot — recalibrage + banc F5.** Recalibrer la largeur de trait
  (facteur `2.2`) et le seuil feuilles `LeafMaxThickCm` contre la nouvelle échelle
  d'épaisseur ; banc/observation F5 « vieux pommier » ; complément encyclopédie
  optionnel. **Golden INTACT** (pur-vue C#).
