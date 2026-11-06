"""
SYMBIOSE — sim/engine/anemophilie.py
Pollinisation ANÉMOPHILE déterministe (sprint VENT & ÉVAPOTRANSPIRATION ⑤, §5.3).

Voie de nouaison PARALLÈLE à l'entomophilie des butineurs (§F) : les espèces à
pollen porté par le vent (`pollination_mode == "wind"` : graminées, orties,
noisetier, chêne…) reçoivent du `pollen_recu` SANS aucun insecte. La dose dépend
du FLUX vent → contrainte écologique → réponse biologique (philo #2) :

    pollen_recu(cible) ∝ vent_local(cible) × Σ floraison des congénères EN AMONT

« En amont » = dans la direction d'où vient le vent (`wind.direction`, §2.1) : un
nuage de pollen ne voyage que sous le vent, donc une cible ne capte que les
émetteurs placés au vent d'elle. Une plante isolée capte AUSSI son propre pollen
(auto-anémophilie : le panache retombe en partie sur la même plante) → une
graminée solitaire noue un peu, un peuplement dense noue beaucoup.

Tension réaliste enseignée (§5.3) : jour VENTEUX = bon pour la graminée (pollen
brassé), mauvais pour l'abeille (butineurs cloués, cf. butineurs.py). Jour CALME =
l'inverse. Le joueur découvre qu'aérer un coin sert les anémophiles.

GOLDEN NEUTRE par construction : on n'écrit QUE `pollen_recu` (hors `_PLANT_ATTRS`
du digest), lu UNIQUEMENT par la nouaison `_tick_fruits` en mode `wind` — or aucun
fruitier anémophile n'atteint sa maturité dans le smoke (noyer 15 ans / chêne
25 ans > 4 ans simulés), donc personne ne lit cette dose → bit-identique.
Déterminisme (philo #3) : tout dérive de la géométrie + de la floraison du tick,
zéro RNG vivant.
"""

from __future__ import annotations
import math

# Calibrage de la dose anémophile (knobs post-test, §5.3).
# Force locale de vent en-deçà de laquelle le panache ne brasse rien (l'air doit
# bouger pour transporter le pollen) — sous ce seuil, dose nulle.
ANEMO_VENT_SEUIL = 0.05
# Conversion « floraison × vent » → dose de pollen_recu (échelle sur g() de la
# nouaison, demi-saturation POLLEN_DEMI=1.0 depuis le sprint FLORAISON·FRUCTIFICATION ② :
# une belle floraison ventée noue plein — dose typique ANEMO_DOSE_COEF≫DEMI → g≈1).
ANEMO_DOSE_COEF  = 6.0
# Part du panache qui retombe sur l'ÉMETTEUR lui-même (auto-anémophilie) : une
# plante isolée noue un peu sans congénère. ∈ ]0,1[.
ANEMO_AUTO_FRAC  = 0.35


def _wind_from_vector(direction: float) -> tuple[float, float]:
    """Vecteur unitaire (dx, dy) pointant vers la SOURCE du vent (« d'où il
    vient »), dans le repère sol cartésien. `direction` ∈ [0, 2π) est l'angle
    d'origine de la masse d'air (`sim.wind.WindState.direction`). Un émetteur est
    « en amont » d'une cible si (émetteur − cible)·(ce vecteur) > 0."""
    return (math.cos(direction), math.sin(direction))


class AnemophilieMixin:
    def _tick_anemophilie(self, tile, eco, wind_dir: float, wind_force: float) -> None:
        """Dépose `pollen_recu` sur les fleurs anémophiles ∝ vent local × congénères
        en amont (§5.3). Appelée une fois par tuile et par semaine (boucle.py), à
        côté de `_tick_butineurs` (voie entomophile). N'émet aucun log, n'écrit que
        `pollen_recu` → golden NEUTRE.

        Calme (`wind_force ≈ 0`) → aucun brassage → dose nulle (le vent EST le
        vecteur ; sans air en mouvement, le pollen lourd des anémophiles ne voyage
        pas). Coût : O(fleurs²) par ESPÈCE anémophile en fleur — quelques unités
        par tuile, négligeable (effet par-plante, §5.3)."""
        if wind_force < ANEMO_VENT_SEUIL:
            return
        # Émetteurs = fleurs anémophiles vivantes, groupées par espèce (constance
        # florale : le pollen d'une espèce ne noue qu'une fleur conspécifique).
        emetteurs: dict = {}
        for p in tile.plants:
            if (not p.is_alive or p.floraison <= 0.0
                    or p.plant_class.pollination_mode != "wind"):
                continue
            emetteurs.setdefault(p.plant_class.name, []).append(p)

        wx, wy = _wind_from_vector(wind_dir)
        for groupe in emetteurs.values():
            if len(groupe) == 1 and ANEMO_AUTO_FRAC <= 0.0:
                continue
            radius_cm = groupe[0].plant_class.pollination_radius_cm
            radius2 = radius_cm * radius_cm
            # Dose d'espèce si posée (VERGER VIVANT ③ : noyer), sinon commune.
            dose = groupe[0].plant_class.anemo_dose
            coef = ANEMO_DOSE_COEF if dose is None else dose
            for cible in groupe:
                r, c = cible.position
                vent = eco.vent.at_plot(r, c) if eco.vent else 0.0
                if vent < ANEMO_VENT_SEUIL:
                    continue
                # Σ floraison des congénères EN AMONT (projection > 0) à portée +
                # auto-anémophilie (le panache retombe en partie sur soi).
                amont = ANEMO_AUTO_FRAC * cible.floraison
                for src in groupe:
                    if src is cible:
                        continue
                    dx, dy = src.x_cm - cible.x_cm, src.y_cm - cible.y_cm
                    if dx * dx + dy * dy > radius2:
                        continue
                    if dx * wx + dy * wy > 0.0:        # src est au vent de la cible
                        amont += src.floraison
                if amont > 0.0:
                    cible.pollen_recu += coef * vent * amont
