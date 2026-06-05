# Sprint Croissance procédurale (D29 réorienté) — état partagé

> État léger partagé entre tronçons (≤ ~25 lignes utiles). Mis à jour en fin de
> chaque sous-sprint. Conception figée : `data/code/CONCEPTION_CROISSANCE.md`.

## Ce qu'on construit
Remplacer l'affichage par sprites figés par une **vraie morphogénèse** : chaque
plante possède une **structure de segments** (branches), en **Python** (source de
vérité, déterministe), dont la croissance est pilotée par l'**auxine le long de la
structure** + la **lumière** (`LightField`). L'empreinte (`height_at`/`canopy_radius_at`
…) sera **dérivée de la structure** (contrat inchangé, seule la source change). Rendu
**tout procédural** (branches + organes en pixels) côté Godot. **Profil de croissance
PAR ESPÈCE** (vitesse + `port_archetype`) à décrire pour les 14 espèces. Absorbe D29
hormones (le modèle « 2 scalaires » est mort ; `tailler` devient un appelant du seam).

## Stratégie golden (re-figeage MAÎTRISÉ, pas « intact »)
Le moteur permanent change le comportement de **toutes** les plantes → le golden
**sera re-figé**, mais **localisé et incrémental** : la structure est **construite
inerte d'abord** (tronçon 1, golden INTACT car non lue), **puis câblée à l'empreinte**
(tronçon 2, **re-figeage**), **espèce par espèce** (démonstratrice d'abord). On valide
(visuel + numérique vs gabarit `growth_stages`/`age_curve`) **avant** de figer.

## Découpage (sprint GROS → 6 tronçons ; révisable par Nico)
- **1 — Structure + croissance Python (cœur), INERTE.** ⬜ `Segment`, auxine le long
  de la structure, allongement/débourrement, **bornage** (chute du vieux bois, plafond),
  déterminisme (`_hash_noise`). **Non câblée à l'empreinte → golden INTACT.** Test de
  croissance libre (une espèce). *(raffinement vs §M du doc : golden intact ici,
  re-figeage au tronçon 2.)*
- **2 — Profil par espèce + dérivation d'empreinte.** ⬜ Schéma §E sur `PlantBase`,
  profil de la **démonstratrice (tomate)** calibré sur ses stages, `height_at`/
  `canopy_radius_at`/`foliage_density_at` lisent le **cache d'empreinte** (§G).
  **Re-figeage golden** (migration incrémentale §I). Racines = rayon dérivé.
- **3 — Seam `atteindre_segment` + `tailler`.** ⬜ Seam continu (§F), `tailler`
  rebranché (apex/branche), coût `MODERE`/gain ∝ maturité inchangés. Démonstratrice
  **pommier** (`etale`, fructification latérale). **Absorbe D29 hormones.**
- **4 — Rendu pixel structure (Godot).** ⬜ Projection iso + rastérisation segments
  aux zooms ×4…×32, LOD (§H.1/§H.3). Premier rendu visible des branches.
- **5 — Organes procéduraux (Godot) — RISQUE N°1.** ⬜ Générateur feuilles/fleurs/
  fruits, stades d'organe, palette/saison (§H.2). Itératif.
- **6 — Save de la structure.** ⬜ Sérialisation JSON bornée (§J), option d'allègement.

## Plus tard (hors chantier, ligne BACKLOG)
Déclencheurs naturels du seam (grêle/chenille/vent → `atteindre_segment`) ; marqueur
`🌿` (succès maîtrise §9.5) ; profil de croissance du **reste du catalogue** (§E.4) ;
portage C# (D24) ; structure racinaire réelle (gated, §8 = rayon dérivé).

## Décisions déjà actées (conception — `CONCEPTION_CROISSANCE.md` §B)
Segments / Python source de vérité / accumulation **bornée** / auxine le long des
segments / phototropisme `LightField` / empreinte **dérivée** (contrat inchangé) /
organes **tout procéduraux** / racines **rayon dérivé**. Intensité **continue**,
moteur **permanent**, déclencheurs naturels **plus tard**.

## Points ouverts (à trancher dans le tronçon concerné, défaut sobre + signaler)
- **1** : représentation exacte d'un `Segment` (base+dir+length vs base+extrémité) ;
  où loger la boucle de croissance (`engine._tick_*` vs module dédié `sim/growth.py`).
- **2** : forme du cache d'empreinte (recalcul/tick vs invalidation) ; ordre de
  migration des espèces.
- **3** : effet hormonal exact de `cible="branche"` (dominance ~inchangée).
