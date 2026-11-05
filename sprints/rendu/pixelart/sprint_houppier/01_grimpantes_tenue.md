# ① Grimpantes : tenue du lierre et du jasmin — golden INTACT attendu

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `docs/rendu/pixelart/conception_houppier.md` §3, `plants/species/grimpantes.py`, `sim/growth/phases.py` (`_elaguer`).

## Objectif

Le lierre et le jasmin ne régressent plus hors tempête et neige fortes : ils s'allongent jusqu'au plateau du cap, et grossissent.

## À faire

1. **Référence** : `accroches_adultes`, seed 42, 156 semaines, depuis `data/code/` : longueur totale, zmax, épaisseur max, nombre d'apex, chutes de plus de 15 % en une semaine, par cause. Le banc de patch mémoire était simple : envelopper `_elaguer`, `_casse_vent`, `_casse_neige`, `_cladoptose`.
2. **Réglages** sur `Ivy` et `Jasmine` : `emit_length_cm` 20, `max_segments` 80, `wood_persistence` 4000, `fragilite_bois` 0,3, `girth_max_cm` 6, `max_height_cm` et `max_extent_cm` 2000. Commentaire pédagogique pour chacun. Vérifier d'abord que ces champs portent bien sur ces classes (patch mémoire fait sur les classes).
3. **Attendu** : lierre et jasmin ≥ 1 200 cm en s156 et pas de baisse nette entre s52 et s156 ; épaisseur max en hausse. Repère : lierre 1 262 → 1 342, jasmin 1 337 → 1 526, 3,03 → 4,18 cm entre s26 et s156 [`accroches_adultes`, seed 42, n=1 run, VM]. Rapporter chaque chiffre avec son étiquette.
4. **Effets de bord** : `update_footprint` et l'ombre projetée avec plafonds relevés ; tick du banc avant/après ; `visuals/PlantRenderer.Lianes.cs` lit les segments, emit 8 → 20 change l'espacement des feuilles : capture `tools/capture_vm.sh` avant/après à ×4 et ×8, corriger la vue si le lierre se dégarnit.
5. Golden, `tests/bancs/test_bancs_grimpe.py`, `tests/simserver`, suites de grimpe. `dotnet build Symbiose.csproj` si la vue change.
6. Bilan dans `00_etat.md` ; commit.

## Golden

**INTACT** (lierre et jasmin patchés : identique [smoke]). S'il bouge : anomalie à diagnostiquer, pas de re-figeage.

## NE PAS

Toucher au haricot, à la tomate, à `_elaguer`. Traiter le dépassement du treillis : c'est le ②. Lancer `tests/test_epaisseur_500ans.py`.
