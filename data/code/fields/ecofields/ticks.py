"""
SYMBIOSE — fields/ecofields/ticks.py
Responsabilité : les TICKS DÉLÉGUÉS d'EcoFields — minces wrappers qui font évoluer
un champ en déléguant le calcul à un helper PUR du paquet (thermique, ph, structure,
mycelium, transport, rosée), plus les ticks de diffusion, lumière, abri (vent) et
perturbation. Le container reste ainsi dégagé du corps de ces calculs.

Mixin de comportement de `EcoFields` (scission refactor 2026-06-30, container
déjà dense). Aucun état propre : opère sur `self`. Comportement bit-identique
à l'ancien `container.py`.
"""

from __future__ import annotations

from .constants import *          # HUMIDITY_INERTIA, FERTILITY_INERTIA, MICROBE_INERTIA…
from .thermique import tick_thermique as _tick_thermique   # calcul pur T_sol (①)
from .thermique import snow_next as _snow_next              # manteau neigeux pur (⑦)
from .ph import tick_ph as _tick_ph                         # dérive pure du pH (physico-chimie ①)
from .structure import tick_structure as _tick_structure   # dérive pure de la structure du sol (physico-chimie ⑧)
from .mycelium import tick_mycelium as _tick_mycelium       # dynamique pure du réseau fongique (mycélium ①)
from .transport import tick_transport as _tick_transport    # transport éolien pur de la litière (vent ⑦)
from .rosee import tick_rosee as _tick_rosee                 # rosée & gelée blanche nocturnes (météo→champs ②)
from .allelopathie import tick_allelopathie as _tick_allelopathie  # décroissance labile de l'allélopathie (allélopathie ①)
from .autotoxicite import tick_autotoxicite as _tick_autotoxicite  # montée/redescente saisonnière de l'autotoxicité (allélopathie ④)


class TicksMixin:
    """Ticks délégués (thermique, pH, structure, mycélium, rosée, neige, transport)
    + diffusion, lumière, abri/vent, perturbation."""

    # --- Tick diffusion ---

    def tick_diffusion(self) -> None:
        """
        Diffusion spatiale des champs continus.
        Microbiome inertie 0.92 → aura progressive des aromatiques.
        """
        self.humidite.diffuse(inertia=HUMIDITY_INERTIA)
        # Les trois nutriments diffusent à la même inertie que l'ancien `fertilite`
        # (③ : le proxy unique éclaté en N/P/K, dynamique spatiale conservée).
        self.n.diffuse(inertia=FERTILITY_INERTIA)
        self.p.diffuse(inertia=FERTILITY_INERTIA)
        self.k.diffuse(inertia=FERTILITY_INERTIA)
        self.microbiome.diffuse(inertia=MICROBE_INERTIA)

    # --- Microclimat de surface (T_sol) ---

    def tick_thermique(self, saison: str, nebulosite: float = 0.0) -> None:
        """Recalcule `temperature_sol` (solaire·nébulosité − latente − isolation, ④).
        `nebulosite` = scalaire météo du tick (0 = ciel clair). Délègue au helper
        pur `thermique.tick_thermique` (container déjà dense)."""
        _tick_thermique(self, saison, nebulosite)

    def tick_ph(self, amend_dir: int = 0) -> None:
        """Fait dériver `ph` (décennal) vers sa cible héritée/acidifiée (physico-
        chimie ①). Délègue au helper PUR `ph.tick_ph` (container déjà dense). À
        appeler APRÈS la décompo (il lit la litière `om_fresh_at`). `amend_dir`
        = direction d'amendement de la tuile (⑥ : +1 chaux / −1 soufre / 0 sinon),
        calculée par la boucle (couche `fields` n'importe pas `world`). 0 par
        défaut → golden NEUTRE (aucune rondelle chaux/soufre dans le smoke)."""
        _tick_ph(self, amend_dir=amend_dir)

    def tick_structure(self, plants, pluie_norm: float = 0.0) -> None:
        """Fait dériver `structure_sol` (lent) sous bioturbation/pivots/battance
        (physico-chimie ⑧). Délègue au helper PUR `structure.tick_structure`
        (container déjà dense). À appeler APRÈS la décompo (il lit la litière
        `om_fresh_at`). `pluie_norm` = PRECIP_NORM de l'événement météo du tick
        (0 hors pluie battante), calculé par la boucle. Les gestes becher/grelinette
        mutent `structure_sol` DIRECTEMENT (hors de ce tick, plein effet)."""
        _tick_structure(self, plants, pluie_norm=pluie_norm)

    def tick_mycelium(self) -> None:
        """Fait croître/décliner le réseau fongique `mycelium` (sprint mycélium ①).
        Délègue au helper PUR `mycelium.tick_mycelium` (container déjà dense). À
        appeler APRÈS `tick_structure` (litière/humidité/T_sol à jour ce tick) et
        AVANT `tick_diffusion`. Au tronçon ① le champ est calculé mais lu par
        PERSONNE (effets §2 débranchés) → golden NEUTRE (mycélium nul au repos)."""
        _tick_mycelium(self)

    def tick_allelopathie(self) -> None:
        """Décline le champ d'allélopathie racinaire `allelopathie` (sprint
        ALLÉLOPATHIE ①) : perte spontanée + détox ∝ microbiome. Délègue au helper
        PUR `allelopathie.tick_allelopathie` (container déjà dense). À appeler dans
        la zone décompo/sol (après `tick_mycelium`, avant `tick_diffusion`). Le champ
        est ALIMENTÉ ailleurs (`inject_field`, route générique) ; ici on ne fait que
        décliner. Au tronçon ① champ nul au repos + aucun émetteur + lu par personne
        → golden NEUTRE (germination ②, croissance ③ branchées plus tard)."""
        _tick_allelopathie(self)

    def tick_autotoxicite(self, plants: list) -> None:
        """Fait monter/redescendre l'autotoxicité `autotox` (sprint ALLÉLOPATHIE ④,
        fatigue du sol de la monoculture) et met à jour le traceur d'espèce
        `autotox_espece`. Délègue au helper PUR `autotoxicite.tick_autotoxicite`
        (container déjà dense). À appeler EN FIN DE SAISON (cadence lente, avec
        `tick_soil_memory`) : la fatigue est un ressort pluriannuel, pas hebdo. Le
        champ MONTE sur un plot ré-occupé par la même espèce ÉMETTRICE
        (`allelopathie_emission > 0`), redescend à la rotation / sol nu (détox ∝
        microbiome). Lu par la SEULE espèce traceée via `allelo_effectif`. Aucun
        émetteur au repos (avant le ⑤) → champ nul reste nul → golden NEUTRE."""
        _tick_autotoxicite(self, plants)

    def tick_snow(self, temp_now: float, is_neige: bool) -> None:
        """Met à jour le manteau neigeux `eco.snow` (⑦). Délègue au helper PUR
        `thermique.snow_next` (container déjà dense). Accumule si l'événement du
        tick est `Neige`, fond sinon (∝ température). À appeler AVANT le gel
        nocturne (qui lit `snow` via `t_min_nuit_at`)."""
        self.snow = _snow_next(self.snow, temp_now, is_neige)

    def tick_rosee(self, t_air: float, nebulosite: float) -> list:
        """Dépose la rosée / accumule-fond le givre nocturne (②). Délègue au helper
        PUR `rosee.tick_rosee` (container déjà dense) : il lit le thermomètre nocturne
        `t_min_nuit_at` + l'humidité du sol, écrit `humidite` (rosée + fonte différée)
        et `eco.givre` (dépôt gelé). À appeler ENTRE la thermique (2b) et l'hydrologie
        (3) : la rosée lit l'humidité de fin du tick précédent, son dépôt est ensuite
        drainé/diffusé. Renvoie les marqueurs de log diégétiques (💧/❄). No-op (liste
        vide, golden-safe) si aucune condensation nulle part."""
        return _tick_rosee(self, t_air, nebulosite)

    # --- Lumière ---

    def tick_light(self, plants: list, saison: str,
                   house=None, tile_origin: tuple = (0.0, 0.0)) -> list[str]:
        """Recalcule le champ de lumière pour ce tick (+ ombre/albédo de la maison
        si `house` est fournie ; `tile_origin` = offset monde de la tuile)."""
        return self.lumiere.compute(plants, saison,
                                    house=house, tile_origin=tile_origin)

    # --- Vent spatialisé (champ d'abri) ---

    def tick_abri(self, plants: list, wind_dir: float, wind_force: float,
                  house=None, tile_origin: tuple = (0.0, 0.0)) -> None:
        """Recalcule `eco.vent` (force LOCALE par plot, ③) depuis la masse d'air
        (`wind_dir`/`wind_force`, `sim.wind.wind_at` ①) MODULÉE par la géométrie
        d'abri. Délègue au helper PUR `fields.abri.compute_abri` (container déjà
        dense) qui porte la mutualisation capsule + le CACHE directionnel (§7B).
        À appeler APRÈS la lumière (les obstacles/hauteurs sont à jour), AVANT
        l'hydrologie (qui lit `eco.vent`). À `wind_force=0` (calme) → champ NUL →
        évaporation/wind chill inchangés."""
        from fields.abri import compute_abri   # import local (évite un cycle au load)
        compute_abri(self, plants, house, tile_origin, wind_dir, wind_force)

    def tick_transport(self, wind_dir: float, wind_force: float) -> list:
        """Transport ÉOLIEN de la litière légère sous le vent (⑦, §5.6). Délègue au
        helper PUR `transport.tick_transport` : il lit `eco.vent` (champ d'abri ③) et
        DÉPLACE une fraction de la litière transportable (feuille/herbace) des plots
        exposés vers leur voisin plus abrité sous le vent. PASSE CONDITIONNELLE
        (sautée si `wind_force < TRANSPORT_SEUIL`, levier perf §7B) → coût nul les
        jours calmes. Renvoie les marqueurs diégétiques 🍃 (consommés HORS tick par le
        ledger des voix). À appeler APRÈS la décompo (litière à jour), dans la zone
        décompo/transport de la boucle."""
        return _tick_transport(self, wind_dir, wind_force)

    # --- Perturbations ---

    def tick_disturbance(self, seed: int, week: int) -> None:
        """Met à jour le champ de perturbation spatiale (bruit déterministe)."""
        self.disturbance.tick(seed, week)
