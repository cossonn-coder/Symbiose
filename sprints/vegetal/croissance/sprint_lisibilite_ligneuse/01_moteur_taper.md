# Tronçon ① — Moteur : pipe model + amincissement (taper) + girth par espèce

> Kickoff **autosuffisant**. Tu démarres à froid : lis `CLAUDE.md`, `00_etat.md`
> (même dossier) et ce fichier. Tu n'as besoin de RIEN d'autre de la conversation
> de conception. Doc de référence :
> `docs/vegetal/croissance/conception_lisibilite_ligneuse.md`.

## Objectif
Remplacer, dans la croissance procédurale, l'épaississement **uniforme et non
borné** du bois par une épaisseur qui **dérive de la topologie** (pipe model) et
d'une croissance secondaire **saturante par l'âge**. Résultat attendu : tronc
épais net, charpentières intermédiaires, brindilles fines ; tronc **borné** (plus
de « baobab ») et **amincissant** (plus de « ronces diamètre baobab »).

## Cause à corriger (déjà diagnostiquée)
`sim/growth/phases.py`, dans `_elongate_emit` : `s.thickness_cm += THICKEN_RATE`
épaissit tout segment non-apex d'une constante (0.03 cm/tick), uniforme, non
bornée, indépendante de l'ordre de branche → une vieille brindille devient aussi
grosse que le tronc, et le tronc croît sans plafond.

## Modèle à implémenter
```
thickness_i = THICKNESS_INIT + girth_max_espèce · sat(âge_i) · taper_i
   sat(âge) = 1 − exp(−âge_i / GIRTH_TAU)              (âge_i = Segment.age_weeks)
   taper_i  = (n_term_i / n_term_racine) ^ TAPER_EXP
```
- `n_term_i` = **nombre de segments terminaux** (extrémités : segments SANS
  enfant) portés dans le **sous-arbre** de `i`. Le collet (racine, index 0) porte
  `n_term_racine` = total des terminaux. Une extrémité porte `n_term=1`.
- `taper_i ∈ ]0,1]` (1 au collet), `sat ∈ [0,1[`. Le collet obtient
  `THICKNESS_INIT + girth_max·sat(âge_collet)` — le tronc, borné.
- **Déterministe, zéro RNG** (philo #3).

## Fichiers à toucher

### 1. `sim/growth/constantes.py`
- Ajouter les leviers de **module** :
  ```python
  GIRTH_TAU  = 300.0   # semaines : échelle de saturation de la croissance secondaire (placeholder → F5)
  TAPER_EXP  = 0.5     # exposant du pipe model (0.5 = section ∝ n_term ; →1 = hiérarchie visuelle plus marquée) (placeholder → F5)
  ```
- `THICKEN_RATE` : **NE PAS supprimer** (garde-fou « conserver le code »). Le
  laisser, ajouter un commentaire « OBSOLÈTE depuis le sprint lisibilité ligneuse
  (remplacé par le pipe model `taper_thickness`) — conservé pour mémoire ».

### 2. `sim/growth/geometrie.py`
- Ajouter une fonction **pure** `taper_thickness(segs, girth_max, tau, exp, init)`
  qui écrit `thickness_cm` sur chaque segment :
  - compter les enfants via `_children(segs)` ; un segment **terminal** = sans
    enfant (l'attribut `is_apex` ne suffit pas : un apex retiré peut avoir des
    enfants, une extrémité sénescente sans enfant est terminale).
  - `n_term_i` par **post-ordre** (enfants avant parent) : terminal → 1 ; sinon
    somme des `n_term` des enfants. Réutilise `_depths` pour l'ordre
    (profondeur décroissante = enfants d'abord), comme `_apex_in_subtree`.
  - `n_root = n_term[0]` (collet). Si `n_root ≤ 0` (structure dégénérée d'1
    segment), forcer `taper=1`.
  - écrire `s.thickness_cm = init + girth_max * (1 - exp(-s.age_weeks / tau)) *
    (n_term_i / n_root) ** exp`.
  - **O(n)** (n ≤ max_segments). Pure : ne lit/écrit que `thickness_cm`.

### 3. `sim/growth/phases.py`
- `_elongate_emit` : **retirer** la ligne `s.thickness_cm += THICKEN_RATE` (la
  branche `if not s.is_apex:` ne fait plus que `continue`). Importer `THICKEN_RATE`
  devient inutile → retirer l'import s'il n'est plus référencé (orphelin dû à TON
  changement — à nettoyer).
- `grow_plant` : après `_elaguer(...)` et le rejet de souche, **avant**
  `update_footprint`, pour les espèces `cls.procedural_growth`, appeler **une
  fois** :
  ```python
  from .geometrie import taper_thickness
  taper_thickness(plant.segments, cls.girth_max_cm, GIRTH_TAU, TAPER_EXP, THICKNESS_INIT)
  ```
  (import `GIRTH_TAU, TAPER_EXP, THICKNESS_INIT` depuis `.constantes`.) **Une
  seule fois par tick**, topologie stable (garde-fou : pas de recalcul intra-tick).

### 4. `plants/base/familles.py`
- Ajouter un attribut de classe sur `PlantBase`, près des leviers de croissance
  procédurale (vers `growth_speed`/`max_segments`) :
  ```python
  girth_max_cm: float = 1.5   # épaisseur cible du "tronc" mûr (cm). Défaut FAIBLE :
                              # les herbacées procédurales (tomate, grimpantes) restent
                              # fines, proches de l'actuel. Les ligneux surchargent haut.
  ```
  (Valeur de défaut à ajuster si le golden herbacé dérive trop — viser une
  épaisseur de tige d'herbacée proche de l'ancienne accumulation à âge mûr.)

### 5. `plants/perennials.py`
- Poser `girth_max_cm` **par espèce ligneuse** (les 10 `PerennialWoody`). Seul le
  pommier a un effet visible aujourd'hui (seul `procedural_growth=True`), mais on
  pose des valeurs cohérentes prêtes pour tous. Ordre de grandeur (tronc mûr ~cm) :
  pommier ~18, cerisier ~15, figuier ~12, noyer ~30, chêne ~40, hêtre ~35,
  bouleau ~14, charme ~18, sapin ~25, aulne ~16 (placeholders → F5). Commenter que
  seul le pommier les exerce pour l'instant.

### 6. `tools/maquette/organes.py`
- `LEAF_MAX_THICK_CM` filtre les segments feuillus (fin = feuillu). Sous le
  nouveau modèle, les brindilles restent fines (~`THICKNESS_INIT` + peu) et le
  bois épaissit fort → **recalibrer** ce seuil pour que les brindilles portent
  encore des feuilles et le tronc/charpentières soient nus. Vérifie visuellement
  via une maquette SVG (`tools/render_structure.py` / `tools/maquette/apercu.py`)
  et un venv cairosvg /tmp si besoin (cf. mémoire rendu SVG). Note la valeur
  choisie dans le commit.

## Tests (à ajouter/adapter dans `tests/test_croissance.py`)
1. **Amincissement monotone** : sur un pommier grandi N semaines, pour tout
   segment non-collet, `thickness_parent ≥ thickness_enfant` (à tolérance flottante
   near-equal). Le collet est le plus épais.
2. **Tronc borné** : `thickness_collet ≤ THICKNESS_INIT + girth_max_cm + ε` à
   n'importe quel âge (teste à ~5 ans ET à ~50 ans — la borne tient).
3. **Déterminisme** : deux runs identiques (même seed/âge) → épaisseurs
   identiques.
4. Ne PAS lancer `test_epaisseur_500ans` (interdit, cf. `00_etat.md`/mémoire).

## Golden
**RE-FIGÉ maîtrisé et ANNONCÉ.** `thickness_cm` est sérialisé (9 champs bois du
`Segment`) → le smoke `tests/test_golden.py` (2 tuiles × 4 ans, pommier < 5 ans)
verra les épaisseurs changer. Dérive **localisée au champ `thickness_cm`** des
plantes `procedural_growth`, **attendue et expliquée** par ce modèle. Procédure :
1. Faire tourner, constater la nouvelle valeur, **vérifier qu'elle est
   cohérente** (pas d'explosion, tronc borné, brindilles fines) avant de figer.
2. Re-figer le(s) hash du golden dans le test, **noter le nouveau hash** dans le
   commit et dans `00_etat.md`.
3. Vérifier que les **autres suites** (génétique, vigueur, population, ombre,
   phototropisme, sénescence…) restent vertes — le champ n'a aucun couplage
   écologique, elles ne doivent PAS bouger. Si l'une bouge, c'est un bug → annuler.

## À NE PAS faire
- Ne PAS toucher au rendu C# (tronçon ②).
- Ne PAS supprimer `THICKEN_RATE` (le commenter obsolète).
- Ne PAS migrer d'autres arbres en procédural (hors périmètre → dette).
- Ne PAS introduire de RNG ni de recalcul intra-tick.

## Fin de tronçon
Mettre à jour `00_etat.md` (nouveau hash golden, valeur `LEAF_MAX_THICK_CM`,
défauts posés), commit, puis tronçon ②.
