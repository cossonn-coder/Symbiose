"""
SYMBIOSE — sim/engine/carnivore.py
Le premier couplage PLANTE → champ FAUNE : la plante carnivore (Drosera, ⑥ du
sprint HYDROLOGIE & MARÉCAGES) agit comme un PUITS sur la densité `moustique`.

Regroupé en `CarnivoreMixin` — hérité par l'`Engine` (boucle.py), appelé JUSTE
APRÈS `tick_populations` (qui met `moustique` à jour) et AVANT le résumé de tuile.
DISTINCT du registre `population` (prédation faune→faune) : la carnivore n'est
pas une guilde, c'est une PLANTE qui prélève une guilde — un hook dédié (kickoff
⑥, « ne pas recopier le mécanisme faune→faune »).

Modèle (déterministe, zéro RNG, borné ≥ 0) :
    pour chaque Drosera vivante:
        pour (r,c) in foliar_plots:
            capture = CARNIVORE_CAPTURE × moustique[r][c]
            moustique[r][c] -= capture      # prélèvement RÉEL, la nuée se raréfie

Le prélèvement DÉCALE la faune (observable à l'overlay ⑧) — c'est le FLUX, pas un
gain chiffré sur la plante (philo #1/#2). L'AZOTE que la carnivore tire de ses
proies est modélisé ailleurs, en LECTURE : `sim/vigueur_plante.qi_local` retire N
de la loi de Liebig pour une espèce `carnivore` → elle ÉCHAPPE à la faim d'azote
édaphique sans « gagner » de vitesse (P/K restent limitants). Aucun dépôt d'azote
dans le sol : son N est INTERNE (via les proies), il ne profite pas aux voisines.
"""

from __future__ import annotations

from fields.population.perception import SEUIL_PRESENCE   # dit = peint (MARE VIVANTE ①)

# Fraction de la densité `moustique` capturée par tick sur chaque plot foliaire
# d'une Drosera. Petit (une rosette ne vide pas une mare) mais OBSERVABLE : la
# nuée se creuse localement autour des rossolis. Knob de calibrage (F5, overlay
# `moustique`) — défini LOCALEMENT (patron des mixins d'engine, cf. SEUIL_FLEURI).
CARNIVORE_CAPTURE = 0.20


class CarnivoreMixin:
    def _tick_carnivore(self, tile, eco):
        """Puits carnivore → `moustique` (⑥). Pour chaque Drosera vivante, retire
        `CARNIVORE_CAPTURE` de la densité moustique sur son empreinte foliaire.
        Borné ≥ 0 (le `set` de PopulationField clampe au plancher du champ), zéro
        RNG, itération en ordre `tile.plants`.

        NEUTRE pour le golden : aucune Drosera dans le smoke → la boucle ne trouve
        aucune plante `carnivore` → zéro écriture. Et no-op strict si la tuile n'a
        pas de champ `moustique` (guilde de mare non initialisée sur cette tuile).
        Émet 🪰 UNE SEULE FOIS par plante (drapeau transient `a_capture`, hors
        `_PLANT_ATTRS`) → 1ʳᵉ capture consignée au ledger des voix (§9)."""
        moustique = eco.populations.get("moustique")
        if moustique is None:
            return []
        log = []
        for plant in tile.plants:
            if not plant.is_alive or not getattr(plant.plant_class, "carnivore", False):
                continue
            preleve, vue = 0.0, False
            for (r, c) in plant.foliar_plots:
                if not (0 <= r < moustique.rows and 0 <= c < moustique.cols):
                    continue
                dens = moustique.at_plot(r, c)
                vue = vue or dens >= SEUIL_PRESENCE
                capture = CARNIVORE_CAPTURE * dens
                if capture > 0.0:
                    moustique.set(r, c, dens - capture)   # borné ≥ 0 par le clamp
                    preleve += capture
            # Première capture d'une plante donnée → événement (voix §9). Le seuil
            # 1e-4 évite un log sur une capture infinitésimale (bruit numérique).
            # Dit = peint (MARE VIVANTE ①) : le carnet ne parle de « la nuée » que si
            # elle est VISIBLE au-dessus de la plante (densité ≥ SEUIL_PRESENCE).
            if preleve > 1e-4 and vue and not plant.a_capture:
                plant.a_capture = True
                log.append(f"    🪰 Capture {plant.name}@{plant.position} "
                           f"→ moustique −{preleve:.3f} (proies → azote interne)")
        return log
