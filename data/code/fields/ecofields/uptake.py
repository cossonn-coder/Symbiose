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


def facteur_racinaire(memoire: float, tolerance: float, mycelium: float) -> float:
    """Fonction racinaire restante ∈ [ROOT_UPTAKE_FLOOR, 1] d'une plante dont le chevelu
    est rongé (campagnol) ou pourri (parasite de faiblesse, D111 ④) : mémoire /
    tolérance d'espèce, compensée par la mycorhize, plancher ROOT_UPTAKE_FLOOR.
    SOURCE UNIQUE : lue par `plant_uptake` (ce que le sol cède) ET par la physiologie
    (`sim/engine/racines.eau_percue` : ce que la plante en ressent). mémoire = 0 ⇒
    1.0 exactement (golden NEUTRE). Pure, zéro RNG."""
    root_loss = memoire / max(1e-6, tolerance)
    root_loss *= max(0.0, 1.0 - MYCO_ROOT_COMPENS * mycelium)
    return max(ROOT_UPTAKE_FLOOR, 1.0 - root_loss * ROOT_HERBIVORY_UPTAKE_MALUS)


class UptakeMixin:
    """Consommation racinaire (eau + nutriments)."""

    def plant_uptake(self, r: int, c: int, stage_index: int,
                      shade_memory: float = 0.0,
                      drought_memory: float = 0.0,
                      root_herbivory_memory: float = 0.0,
                      root_loss_tolerance: float = 1.0,
                      share: float = 1.0,
                      volume_factor: float = 1.0,
                      transpiration: float = 1.0) -> dict[str, float]:
        """
        Consommation racinaire modulée par la mémoire physiologique.

        shade_memory  → réduit la transpiration (plante étiolée, moins de surface foliaire)
        drought_memory → réduit la consommation d'eau (racines adaptées, stomates fermés)
        root_herbivory_memory → herbivorie racinaire vécue (campagnol, sprint santé &
                        résilience ③) : le chevelu racinaire rongé prélève MOINS →
                        réduit l'uptake de TOUT (eau + N/P/K), comme l'asphyxie. La
                        plante s'affame par les voies EXISTANTES (philo #2), pas par un
                        malus direct. Compensé par la mycorhize (le réseau relaie ce que
                        les racines n'atteignent plus) et divisé par la niche d'espèce
                        `root_loss_tolerance`. À 0.0 → root_factor = 1.0 → uptake
                        bit-identique (golden NEUTRE au smoke, densité campagnol = 0).
        root_loss_tolerance → capacité D'ESPÈCE à encaisser la perte de racines
                        (`root_loss_tolerance_base`, >1 racines profondes/mycorhizées,
                        <1 bulbeuses superficielles). DÉFAUT 1.0 = neutre.
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
        transpiration → facteur de TRANSPIRATION FOLIAIRE (sprint « le sol qui
                        respire » ①, D111 §1c) calculé côté `sim` (saison, météo,
                        feuillage présent, type de feuillage de l'espèce) : il module
                        le prélèvement d'EAU SEUL (pas N/P/K — une plante dormante
                        sans feuilles ne pompe plus l'eau, sa racine vit toujours).
                        C'est la demande atmosphérique qui TIRE l'eau du sol (flux,
                        philo #2). DÉFAUT 1.0 → historique bit-identique (conteneurs).

        Rétroaction rhizosphère : un microbiome riche améliore l'assimilation des
        nutriments (bonus borné UPTAKE_MICRO_BONUS) — la boucle vertueuse côté plante.
        """
        share *= volume_factor   # confinement de réservoir : flux rapporté au volume
        micro_norm = min(1.0, self.microbiome.at_plot(r, c) / MICROBE_EFFECT_REF)
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
        # HERBIVORIE RACINAIRE (campagnol, sprint santé & résilience ③, §3) : le chevelu
        # rongé prélève moins → on RABOTE l'uptake comme l'asphyxie (facteur multiplicatif
        # replié dans `asphyxie_factor`, donc propagé à l'eau ET au N/P/K). Trois couches :
        #   1. perte = mémoire / tolérance d'espèce (racines profondes encaissent mieux) ;
        #   2. la MYCORHIZE la compense (le réseau touchant la racine relaie eau/nutriments
        #      que les racines rongées n'atteignent plus) — `mycelium.at_plot` DÉJÀ lu plus
        #      bas pour le bonus P → zéro coût de lecture neuf ;
        #   3. root_factor = 1 − perte·MALUS, jamais sous ROOT_UPTAKE_FLOOR (une plante
        #      rongée boit encore un minimum). mémoire = 0 (aucun campagnol) ⇒ root_factor
        #      = 1.0 ⇒ uptake bit-identique ⇒ golden NEUTRE. Philo #2 : on module un FLUX
        #      du sol vers la racine, jamais la plante.
        root_factor = facteur_racinaire(root_herbivory_memory, root_loss_tolerance,
                                        self.mycelium.at_plot(r, c))
        asphyxie_factor *= root_factor
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
                # Transpiration foliaire saisonnière (D111 ①) : sans feuilles ou
                # sous un ciel froid/couvert, la plante ne tire presque plus d'eau.
                amount *= transpiration
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
        # ACCÈS NPK PAR L'ÉPAISSEUR (D57 ①b) : un sol PROFOND met une plus grande PART
        # de son stock N/P/K à disposition (plus de volume de sol prospecté par les
        # racines). Lit `epaisseur_sol` du tick PRÉCÉDENT (uptake étape 8 AVANT
        # `tick_epaisseur` 13b-bis — même décalage 1 tick que l'hydro, déterministe).
        # Amplificateur BORNÉ appliqué comme MYCO_P_BONUS : sur le BESOIN, pas sur le
        # stock (le stock physique reste borné par le champ ; amplifier le besoin puis
        # `min(besoin, dispo_stock)` garantit qu'on ne prélève JAMAIS plus que présent →
        # aucun champ négatif, invariant conservé). ⚠️ D41 (famine édaphique VOULUE) : à
        # epaisseur=0 le facteur vaut EXACTEMENT 1.0 → jamais PIRE que le baseline ; la
        # famine reste possible sur sol maigre car le `min(besoin, dispo_stock)` de Liebig
        # plafonne par le STOCK réel (un sol pauvre ne fait pas de miracle même épais).
        # L'épaisseur ATTÉNUE la carence sur sol humifère profond, elle ne la SUPPRIME
        # pas. Flux du sol, pas la plante (philo #2). PLAFONNÉ, jamais infini.
        ep_uptake = 1.0 + EPAISSEUR_NPK_BONUS * min(
            1.0, self.epaisseur_sol.at_plot(r, c) / EPAISSEUR_NORM_REF)
        for nut, fld in (("N", self.n), ("P", self.p), ("K", self.k)):
            besoin = (BESOIN[nut].get(stage_index, 0.0) * share * asphyxie_factor
                      * (1.0 + micro_norm * UPTAKE_MICRO_BONUS)
                      * dispo(ph_local, nut) * ep_uptake)   # épaisseur : accès NPK (①b)
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
