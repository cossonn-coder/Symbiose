"""
SYMBIOSE — fields/ecofields/uptake.py
Responsabilité : le prélèvement racinaire (UPTAKE eau + N/P/K) modulé par la
mémoire physiologique, l'asphyxie/structure, le lockout pH, la faim d'azote et
la mycorhize. Le couplage sol → plante.

Mixin de comportement de `EcoFields` (scission refactor 2026-06-30, container
déjà dense). Aucun état propre : opère sur `self`. Comportement bit-identique
à l'ancien `container.py`.
"""

from __future__ import annotations

from .constants import *          # UPTAKE, BESOIN, HUM_EXCES, ASPHYXIE_*, STRUCT_*…
from .nutriments import dispo, immobilise_n   # cloche pH + immobilisation N


class UptakeMixin:
    """Consommation racinaire (eau + nutriments)."""

    def plant_uptake(self, r: int, c: int, stage_index: int,
                      shade_memory: float = 0.0,
                      drought_memory: float = 0.0,
                      share: float = 1.0,
                      volume_factor: float = 1.0) -> dict[str, float]:
        """
        Consommation racinaire modulée par la mémoire physiologique.

        shade_memory  → réduit la transpiration (plante étiolée, moins de surface foliaire)
        drought_memory → réduit la consommation d'eau (racines adaptées, stomates fermés)
        share         → fraction prélevée sur CE plot (1/nb plots de l'empreinte
                        racinaire), pour répartir l'uptake sur root_plots sans
                        multiplier la quantité totale (chantier B).
        volume_factor → AMPLIFICATEUR de prélèvement pour les conteneurs (pots/bacs,
                        sprint pots/bacs ③, CONCEPTION §3 levier 1). DÉFAUT 1.0 →
                        comportement HISTORIQUE strictement inchangé (les tuiles
                        passent toujours 1.0 → uptake bit-identique, golden NEUTRE).
                        Un petit pot passe `1/volume_norm > 1` : la plante retire,
                        sur le MÊME stock local, une part plus grande chaque tick →
                        l'eau et les nutriments du mini-sol chutent vite → sécheresse/
                        carence ÉMERGENTES via les mécanismes EXISTANTS. On amplifie
                        un FLUX rapporté au volume réel du réservoir, JAMAIS la plante
                        (philo #2 : pas de malus direct). Le prélèvement reste plafonné
                        par le stock local (Liebig / `min(amount, f.at_plot)`).

        Rétroaction rhizosphère : un microbiome riche améliore l'assimilation des
        nutriments (bonus borné UPTAKE_MICRO_BONUS) — la boucle vertueuse côté plante.
        """
        share *= volume_factor   # confinement de réservoir : flux rapporté au volume
        micro_norm = min(1.0, self.microbiome.at_plot(r, c) / 3.0)
        # Asphyxie palier 1 (§2.3 b, doux & RÉVERSIBLE) : au-dessus de HUM_EXCES, le
        # sol gorgé devient anoxique → les racines boivent mal → l'uptake de TOUT
        # baisse ∝ l'excès courant (≠ mémoire : se lève dès que le sol s'assèche).
        # En dessous du seuil (toute la tuile terre) → facteur 1.0, aucun effet.
        # ⑧ STRUCTURE (deux couplages lecteurs, §2.3) : un sol compacté (structure
        # basse) AGGRAVE l'anoxie (l'eau ne s'évacue pas des pores écrasés → la SÉVÉRITÉ
        # de l'excès est multipliée par (2−structure) ∈ [1,2]) ET freine la PÉNÉTRATION
        # racinaire (l'uptake résiduel descend jusqu'à STRUCT_UPTAKE_MIN en sol totalement
        # tassé). On plie les deux dans `asphyxie_factor`, déjà appliqué à l'uptake eau ET
        # au besoin N/P/K → la modulation se propage partout. structure terre 0.7 < 1.0
        # → mix < 1 systématique → golden re-figé maîtrisé.
        hum_local = self.humidite.at_plot(r, c)
        structure_local = self.structure_sol.at_plot(r, c)
        excess_norm = min(1.0, max(0.0, (hum_local - HUM_EXCES) / (3.0 - HUM_EXCES))
                          * (2.0 - structure_local))
        asphyxie_factor = max(ASPHYXIE_UPTAKE_FLOOR,
                              1.0 - excess_norm * ASPHYXIE_UPTAKE_MALUS)
        asphyxie_factor *= STRUCT_UPTAKE_MIN + (1.0 - STRUCT_UPTAKE_MIN) * structure_local
        consumed = {}
        for var, by_stage in UPTAKE.items():
            amount = by_stage.get(stage_index, 0.0) * share * asphyxie_factor
            if amount <= 0:
                continue
            if var == "humidite":
                # Ombre réduit la transpiration
                light = self.lumiere.at_plot(r, c)
                shade_factor = 1.0 - shade_memory * 0.2
                amount *= (0.5 + light * 0.5) * shade_factor
                # Stress hydrique adaptatif (plante économise l'eau)
                amount *= max(0.5, 1.0 - drought_memory * 0.3)
            f = self.get_field(var)
            real = min(amount, f.at_plot(r, c))
            if real > 0:
                f.add(r, c, -real)
                consumed[var] = round(real, 3)

        # Nutriments N/P/K (③) — prélèvement par BESOIN[stade] (REMPLACE
        # UPTAKE["fertilite"]). Chaque nutriment est plafonné par le champ local
        # (loi de Liebig : un sol carencé limite naturellement le prélèvement, sans
        # gate de croissance neuf — portage fidèle). Microbiome riche → meilleure
        # assimilation (bonus borné, ex-branche fertilite).
        # ④ LOCKOUT pH : le besoin est aussi modulé par la cloche dispo(ph, nut) — un
        # nutriment EN STOCK n'est pas forcément ASSIMILABLE (P bloqué hors zone
        # neutre, N peu sensible). Module un FLUX, pas la plante (philo #2).
        # ⑦ FAIM D'AZOTE : la litière C-riche fraîche (bois/BRF + substrat) immobilise
        # une part de l'azote LOCAL → seul `n − immob` est assimilable ce tick. Le
        # champ `n` n'est PAS amputé (on retire seulement le `real` réellement prélevé) :
        # le bridage est RECALCULÉ chaque tick depuis la masse de bois présente, donc
        # auto-réversible (bois mûri ⇒ immob → 0 ⇒ azote de nouveau disponible). La
        # plante ressent via l'uptake Liebig (③) qui plafonne sur ce N réduit → jaunit.
        ph_local = self.ph.at_plot(r, c)
        immob = immobilise_n(self.bois_fresh_at(r, c))
        for nut, fld in (("N", self.n), ("P", self.p), ("K", self.k)):
            besoin = (BESOIN[nut].get(stage_index, 0.0) * share * asphyxie_factor
                      * (1.0 + micro_norm * UPTAKE_MICRO_BONUS)
                      * dispo(ph_local, nut))
            # ③ MYCORHIZE (§2.2) : le réseau fongique relie ses hyphes aux racines et
            # fait passer le PHOSPHORE — P SEULEMENT (jamais N/K, décision figée ii).
            # Là où `mycelium` touche cette racine vivante, le FLUX prélevable de P est
            # amplifié ∝ réseau, plafonné par MYCO_P_BONUS. On modifie ce que le sol
            # REND DISPONIBLE, pas la plante (philo #2) ; le `min(besoin, dispo_stock)`
            # ci-dessous garde le bornage Liebig (sol pauvre en P ⇒ pas de miracle) et
            # `dispo(ph,"P")` reste limitant (le réseau ne déverrouille pas la fenêtre
            # pH). mycelium=0 ⇒ ×1.0 ⇒ uptake bit-identique à AVANT.
            if nut == "P":
                besoin *= 1.0 + MYCO_P_BONUS * self.mycelium.at_plot(r, c)
            if besoin <= 0:
                continue
            dispo_stock = fld.at_plot(r, c)
            if nut == "N":
                dispo_stock = max(0.0, dispo_stock - immob)   # part immobilisée non assimilable
            real = min(besoin, dispo_stock)
            if real > 0:
                fld.add(r, c, -real)
                consumed[nut.lower()] = round(real, 3)
        return consumed
