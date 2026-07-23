# 2026-07-23 — Sprint LISIBILITÉ DE L'ARCHITECTURE LIGNEUSE (D90) — CLOS

**`/sprint-auto sprint_lisibilite_ligneuse` — tronçons ①→② clos.** Solde le
retour F5 « vieux pommier baobab/ronce » : le vieux pommier avait un tronc
uniforme ~120 cm (baobab) et des brindilles aussi grosses que le tronc (ronces
diamètre baobab), faute d'amincissement.

## ① Moteur — pipe model + taper + girth par espèce (`3f7da78`)
Remplace l'épaississement **uniforme non borné** (`s.thickness_cm +=
THICKEN_RATE`, 0.03 cm/tick pour tout segment non-apex) par une épaisseur
**dérivée de la topologie** :

```
thickness_i = THICKNESS_INIT + girth_max_espèce · sat(âge_i) · taper_i
   sat(âge) = 1 − exp(−âge_i / GIRTH_TAU)          (croissance secondaire bornée)
   taper_i  = (n_term_i / n_term_racine) ^ TAPER_EXP   (pipe model)
```

- `sim/growth/geometrie.py` : fonction **pure** `taper_thickness` — post-ordre
  O(n), `n_term_i` = nb de segments terminaux (sans enfant) du sous-arbre.
  Déterministe, zéro RNG (philo #3). Écrit `thickness_cm` seul.
- `sim/growth/phases.py` : retrait du `+= THICKEN_RATE`, appel unique par tick
  dans `grow_plant` (garde `procedural_growth`), import orphelin nettoyé.
- `sim/growth/constantes.py` : `GIRTH_TAU=300`, `TAPER_EXP=0.5` (placeholders
  → F5) ; `THICKEN_RATE` **conservé** + commenté obsolète (garde-fou).
- `plants/base/familles.py` : `PlantBase.girth_max_cm=1.5` (défaut faible :
  herbacées fines, proches de l'actuel).
- `plants/perennials.py` : `girth_max_cm` posé sur les 10 ligneux (pommier 18,
  cerisier 15, figuier 12, noyer 30, chêne 40, hêtre 35, bouleau 14, charme 18,
  sapin 25, aulne 16) — **seul le pommier l'exerce** (unique `procedural_growth`).
- `tools/maquette/organes.py` : `LEAF_MAX_THICK_CM 1.6→2.5`.
- Tests (`tests/test_croissance.py`, 75/75) : taper monotone (parent ≥ enfant,
  collet le plus épais), tronc borné à 5 ET 50 ans, déterminisme.

Résultat pommier 10 ans : **collet 15,1 cm borné, brindilles 0,31 cm**.

### ⚠️ Golden NON re-figé — prémisse du kickoff FAUSSE
Le kickoff/conception annonçait un **re-figeage maîtrisé** (« `thickness_cm` est
sérialisé, le smoke verra les épaisseurs changer »). En réalité le digest golden
**ne sérialise PAS `thickness_cm`** (que des attributs écologiques + gènes +
rondelles + eco) : `thickness_cm` a **zéro couplage écologique**, donc le golden
est resté **INCHANGÉ `57c166d8…`**. Confirmé par vérification directe
(`grep thickness tests/test_golden.py` → absent). Toutes les autres suites
vertes. **À retenir** : une grandeur purement morphologique/rendu ne touche pas
le golden actuel.

## ② Vue Godot — recalibrage rendu ligneux + banc F5 (`6e9b0fc`)
Pur-vue C#, **golden INTACT**, `dotnet build` vert (0 err, 0 avert).

- `visuals/PlantRenderer.cs` : facteur de largeur de trait `×2.2` (calé sur
  l'ancienne accumulation ~120 cm) → constante nommée **`WoodWidthFactor=1.5`**,
  centralisée sur les 3 sites (DrawSegments, DrawSkeleton, DrawHighlight). Collet
  ~17 cm → ~10 px, brindille → 1 px (plancher). Contraste tronc↔brindille lisible.
- `visuals/PlantRenderer.Organs.cs` : seuil feuilles `LeafMaxThickCm 1.5→2.5`
  (aligné maquette) → brindilles feuillues, charpente nue. Commentaire d'en-tête
  corrigé : la **couleur** du bois est age-based (`LignifyFullWeeks`), l'ancien
  lien épaisseur↔lignification n'existe plus (deux axes indépendants).
- Banc F5 `bancs/croissance.py → vieux_pommier` (NEUF, registré) : déroule un
  Engine local `WARMUP_ANS=15` ans (nappe forcée pour survie de l'arbre isolé à
  racines concentrées) et renvoie le monde déjà vieilli. `init
  config="vieux_pommier"` côté Godot. Golden neutre (banc au niveau `main.py`).

## Périmètre & suites
- **Effet visible sur le pommier seul** (unique `procedural_growth=True`). Les 9
  autres arbres (silhouette de couronne) ont leur `girth_max_cm` posé mais SANS
  effet tant qu'ils ne sont pas migrés → **D91** (migration procédurale des 9).
- Refactor auto-léger : **no-op** (aucun fichier > 400 LDC pur ; Organs.cs à 313
  en jaune mais pré-existant, non poussé en rouge par ce sprint).

## Reste — F5 Nico
Calibrage visuel à l'œil sur le banc `vieux_pommier` : `GIRTH_TAU=300`,
`TAPER_EXP=0.5`, `girth_max_cm` (pommier 18), `WoodWidthFactor=1.5`,
`LeafMaxThickCm=2.5` — tous placeholders. `dotnet build` vert (filet), le F5
visuel reste à Nico.
