# ⑦ Nectar par espèce

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §5.
**Golden** : re-figé SI une plante fleurit dans le smoke (la ressource nectar change le
champ pollinisateur → pollinisation). Annoncé, une fois ; sinon constater intact.

## Objectif
- Attribut d'espèce `nectar` ∈ [0,1] (donnée, défaut à décider et justifier) renseigné
  sur TOUT le catalogue : phacélie, bourrache, trèfle, tilleul (si présent) haut ;
  pommier moyen ; tomate ≈ 0 (pollen vibré) ; graminées 0 ; etc. (lister dans le rapport).
- `fields/population/registry.py::_make_nectar_grid` : poids = floraison × nectar espèce ×
  goût de famille (`attractivite`). Revoir `FLOWER_REF`
  (`fields/population/constants.py`) si la normalisation n'a plus de sens.
- Le bourdon « buzz » les Solanacées : préserver ce cas (pollen), ne pas l'effacer par
  nectar ≈ 0 — décider au code (ex. pollen comme seconde ressource du bourdon, ou goût
  famille déjà porteur) et le justifier.
- Re-mesurer D110 (i) avec `sprints/narration/semiologie/sprint_infobulle_vivant/mesures/
  mesure_nourriture.py` : distribution de la nourriture des butineurs avant/après [n=…].
- `tests/test_catalogue_lot2.py` appelle `_make_nectar_grid` : l'adapter si besoin.

## Ne PAS faire
Pas de nouveau champ par tick. Pas de dessin. Pas de 500 ans.
