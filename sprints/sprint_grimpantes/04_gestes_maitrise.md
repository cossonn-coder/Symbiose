# ④ — Gestes joueur (poser support / palisser) + maîtrise + résistance verse

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/conception/CONCEPTION_GRIMPANTES.md` §6. **Golden INTACT** (event-driven,
> hors tick). Repose sur ①②③. Lancement depuis `data/code/`.

## Objectif
Donner au joueur les gestes pour poser des supports et palisser une grimpante
sarmenteuse, déclarer les objets de maîtrise, et accorder la résistance à la
verse aux grimpantes accrochées. TOUT event-driven → golden inchangé.

## Fichiers
- `sim/actions.py` :
  - `poser_tuteur(gs, tile, r, c)` / `poser_treillis(...)` / `poser_pergola(...)`
    — instancient un `Support` (② `world/support.py`) à la position du plot ciblé
    et l'ajoutent à `tile.supports`. Phase planification. Coût via `cout_action`
    (`MODÉRÉ`). Patron des gestes de pose existants (bac/pile décompo).
  - `palisser(gs, tile, plant)` — attache MANUELLEMENT une grimpante `sarmenteux`
    à un support adjacent compatible (met `plant.support`). C'est le seul canal
    d'accroche du mode `sarmenteux` (cf. compatibilité ②). Coût `MODÉRÉ`.
  - `cout_action` : ajouter les entrées de ces gestes (placeholder calibrage).
- `sim/maitrise.py` / `sim/maitrise_detection.py` : DÉCLARER (non câbler au tick)
  les objets de maîtrise — outil `tuteur`, technique `palissage` (patron des
  objets outil/technique existants). Pas de nouvelle logique de tick.
- Verse/vent (D37) : là où le vent couche les hautes plantes (`sim/wind.py` ou
  l'aléa tempête, chercher « verse »/`lodg`), **exempter** une grimpante dont
  `plant.support is not None` (le support la porte). Le tuteur ne casse PAS
  (écarté, §6). C'est une lecture d'un aléa event-driven → golden intact.

## Golden
**INTACT** — hash inchangé vs ①. Aucun de ces gestes/déclarations ne tourne dans
le tick du golden (le golden ne pose pas de support, ne palisse pas, et son aléa
n'exerce la verse que sur des plantes non accrochées → comportement inchangé).
1. `python3 -m tests.test_golden` → **inchangé** vs hash ①.
2. Si l'exemption de verse fait bouger le golden : le golden a-t-il une grimpante
   accrochée en tempête ? Non (aucun support) → si ça bouge, l'exemption fuit vers
   des plantes libres → corriger.
3. Suite ciblée (`tests/test_grimpe.py`) : pose de support → accroche possible ;
   `palisser` attache un sarmenteux ; grimpante accrochée survit à une verse qui
   coucherait une libre.

## Ce qu'il NE faut PAS faire
- Pas de câblage maîtrise dans le tick (déclaration seule).
- Pas de casse de tuteur en tempête.
- Pas de rendu (⑥).

## F5
- (au ⑥) poser un tuteur puis voir une grimpante s'y accrocher ; palisser un
  jasmin ; une grimpante tuteurée tient dans la tempête.
