# 2026-07-04 — Sprint GRIMPANTES (D49 volet A) — CLOS, SPRINT TERMINÉ

Exécution en **carte blanche façon `/sprint-auto`** du **dernier tronçon ⑥**
(vue Godot + pont + banc), qui clôt le sprint **GRIMPANTES** ①→⑥. Conception
figée le 2026-07-03 (entrée 95). La grimpe des plantes grimpantes est désormais
une **mécanique moteur réelle** (couche A Python = vérité), rendue à l'écran.

## Ce qui existait déjà (①→⑤, clos les 03–04/07)
Traits (`hauteur_autoportante`, `mode_grimpe`) + **affalement géométrique** sans
support (①) ; **supports posables** (`world/support.py`) + mur maison + accroche
bornée (`sim/grimpe.py`, ②) ; **plante-hôte vivante** + **étranglement émergent**
par le `LightField`, sans règle dédiée (③) ; gestes joueur `poser_*`/`palisser`
+ maîtrise data-driven + exemption verse (④) ; catalogue **lierre** (crampon) +
**jasmin** (sarmenteux) + 5 voix chacun (⑤). Modèle **GÉOMÉTRIQUE** de bout en
bout : la hauteur reste `max(z)` des segments — au-delà de `hauteur_autoportante`
sans appui la tige s'affale (plancher d'apex effondré), accrochée elle grimpe
(plancher renforcé) — **jamais de clamp** → consommateurs (nécromasse/abri/pot)
justes.

## Tronçon ⑥ livré ce jour (3 blocs)
- **Pont (0.5.18)** : `serialize.py` expose au snapshot le bloc **`supports`**
  par tuile `[{type, x_cm, y_cm, height_cm, finesse}]` et l'état **`support`**
  `{type, height_cm}` par grimpante accrochée (duck-typing local str=mur /
  `support_type`=Support posé / sinon=hôte — aucun import de `sim/grimpe`).
  `version.py` bumpé 0.5.17→**0.5.18** ; asserts recalés + check de présence du
  bloc `supports` (`tests/simserver/structures.py`).
- **Vue C#** : `visuals/SupportRenderer.cs` NEUF (placeholder procédural
  **pieu/grille/portique**, patron `CompostStructure`) + `world/WorldView.Support.cs`
  NEUF (`ApplySupports`, reconstruction pleine YSort) câblé dans `Snapshot.cs`
  + nettoyage `Camera.cs`. **Vrilles** : `PlantRenderer.SetSupport` +
  `DrawTendrils` (spirale discrète au tip le plus haut de l'accrochée) — lève le
  **rendu de vrille différé** `CONCEPTION_RENDU_FEUILLAGE §7/E6`. La grimpe
  elle-même est **gratuite** côté vue (géométrie du snapshot, décision A) →
  `PlantRenderer` la dessine sans code neuf. `dotnet build` **vert** (0/0).
- **Banc `grimpantes`** (`bancs/biotique.py` + registre) : 3 tuiles — GRIMPE
  (haricot↔tournesol **hôte émergent** + haricot pré-attaché tuteur + jasmin
  pré-palissé treillis), MUR_SUD (lierre crampon pré-collé au mur sud),
  POTAGER_SUD (Solanaceae au sud). `init config="grimpantes"` monte le banc.

## Golden & tests
**Golden `a6c2f651…` — JAMAIS re-figé** sur tout le sprint (①②③⑤ NEUTRE, ④⑥
INTACT). La dérive d'affalement prévue au kickoff ① ne remonte pas au digest
(cf. `sprints/sprint_grimpantes/00_etat.md` §REPRISE — mécanique correcte, juste
plus douce que prévu au digest ; à calibrer au F5 si besoin). Verts :
`test_golden`, `test_grimpe` 10/10, `test_sim_server` **245/245** (+1 check
supports). LDC pur 🟢 partout (serialize 234, biotique 104, SupportRenderer 75,
WorldView.Support 37).

## Signalé
`serialize.py` calcule `eau_surface_by_tile` mais ne l'inclut **pas** dans le
`return` du snapshot (WIP hydrologie ② non branché, **pré-existant** à ce
sprint — non touché, code mort à reprendre au sprint hydrologie).

## Suites
Dette **D49 → ✅ FAIT** ; **E6 vrilles** levée. Reste hors périmètre : D26
(glycine/courge/kiwi/vigne/akébia), D62 (rampantes/traçantes). **F5 = Nico**
(calibrage à l'œil : hauteurs de supports, allure des vrilles, `DROOP_Z` de
l'affalement).
