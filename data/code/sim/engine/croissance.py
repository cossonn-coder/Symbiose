"""
SYMBIOSE — sim/engine/croissance.py
Échanges sol ↔ plante hebdomadaires : avancement de stade (conditionné par le
milieu), uptake racinaire spatial, exsudats (boucle rhizosphère) et mise à jour
des mémoires physiologiques.

Regroupés en `CroissanceMixin` — un thème (« la plante puise, dépose et
mémorise son milieu chaque semaine »). L'`Engine` (boucle.py) hérite ce mixin ;
les méthodes restent des méthodes d'instance (`self.week`, `self._eco`…)
résolues sur l'instance Engine. Comportement identique à l'ancien `engine.py`.
"""

from __future__ import annotations
from fields import (EXUDATE_BASE, EXUDATE_OM_SHARE, HUM_NOYE, HUM_EXCES,
                    ASPHYXIE_MEMORY_LERP)
from fields.ecofields.constants import T_PLANTE_ALPHA
from plants import EXPR_GAIN, EXPR_MIN, EXPR_MAX, TAU_UP, TAU_DOWN
from .calendrier import saison_de

# Sémiologie ② (CONCEPTION_SEMIOLOGIE_FOLIAIRE.md §2.5) — facteur de décroissance
# des marques de symptômes ÉVÉNEMENTIELS par tick de plante. Couplé au gain
# SYMPTOM_MARK_GAIN (resolution.py) : à 0.8, demi-vie d'une marque ~3 semaines
# (0.8³≈0.5) → cicatrisation visible en quelques semaines, purge sous epsilon
# (0.02) ensuite. Knob de calibrage.
SYMPTOM_DECAY = 0.8

# --- Plasticité ① : signaux d'exposition des DEUX mémoires nouvelles ------------
# cold_memory : froid SUB-LÉTAL (cold hardening). Le gel létal vit ailleurs
# (boucle.py, t_min_nuit < 0). Ici on intègre l'exposition DOUCE — sous un seuil
# de fraîcheur, AU-DESSUS de 0 °C — qui déclenche l'acclimatation au froid AVANT
# le coup dur. Lerp lent (même esprit que les autres mémoires). Knobs P6.
COLD_HARDENING_SEUIL = 10.0   # °C : sous ce seuil, le froid « compte » (sub-létal)
COLD_SEVERITY_REF    = 10.0   # °C d'écart sous le seuil donnant une sévérité ≈ 1
COLD_MEMORY_LERP     = 0.05   # intégration lente (miroir drought/asphyxie)
# infection_memory : pression pathogène VÉCUE (SAR / priming immunitaire). Proxy
# déterministe par plot = manque de protection du sol (disease_probability/base ∈
# [~0.02, 1] : 1 = microbiome mort, sol sans défense) × humidité normalisée (le
# champignon a besoin d'eau). Pas de tirage : c'est la PRESSION, pas l'événement.
INFECTION_BASE       = 0.30   # base_rate de référence pour normaliser la pression
INFECTION_MEMORY_LERP = 0.05  # intégration lente

# Appariement gène adaptogène ↔ mémoire d'exposition (plasticité ①, §2.3). La
# dynamique d'expression (lerp à hystérèse) glisse expression[g] vers
# 1 + EXPR_GAIN × mémoire(g). Étendre = ajouter une paire ici + sa mémoire.
_EXPR_MEMOIRE = {
    "tolerance_secheresse": "drought_memory",
    "tolerance_ombre":      "shade_memory",
    "rusticite_froid":      "cold_memory",
    "resistance_pathogene": "infection_memory",
    "tolerance_asphyxie":   "asphyxie_memory",
}


def _bolt_stage_index(plant_class) -> int | None:
    """Index du stade de MONTAISON d'une espèce = 1er stade portant un effet
    `floraison` (convention du gate bisannuel, catalogue enrichi ③). None si
    l'espèce ne fleurit pas par stade. Pure lecture de données."""
    for i, st in enumerate(plant_class.growth_stages):
        if any(e.get("type") == "floraison" for e in st.effects):
            return i
    return None


def _bolt_bloque(plant) -> bool:
    """Gate annuel des BISANNUELLES (catalogue enrichi ③). Une bisannuelle ne
    franchit PAS son stade de montaison tant que `age_years < 1.0` : rosette
    l'an 1, montaison/floraison l'an 2 (puis mort monocarpique, mortalite.py).
    Bloque le passage VERS le stade de montaison (et au-delà) avant 1 an.

    N'a d'effet QUE pour `life_cycle == "biennial"` → AUCUNE espèce du smoke n'est
    bisannuelle ⇒ golden NEUTRE. Si ce gate déplaçait le hash golden, c'est qu'il
    fuit sur une espèce non bisannuelle (BUG, pas un re-figeage)."""
    cls = plant.plant_class
    if cls.life_cycle != "biennial" or plant.age_years >= 1.0:
        return False
    bolt = _bolt_stage_index(cls)
    return bolt is not None and plant.current_stage + 1 >= bolt


class CroissanceMixin:
    def _avancer_stades(self, tile, eco):
        log = []
        saison = saison_de(self.week)
        for plant in tile.plants:
            if not plant.is_alive: continue
            plant.age_weeks += 1
            plant.age_years += 1.0 / 52.0   # âge total (courbe d'âge des pérennes)
            stage = plant.stage
            if stage.duration_weeks == 0: continue
            r, c = plant.position
            hum   = eco.humidite.at_plot(r, c)
            light = eco.lumiere.light_received(plant)   # lumière reçue (canopée, auto-ombrage exclu)
            t_air = eco.temperature.at_plot(r, c)            # T_air (masse, uniforme — météo 02)
            t_sol = eco.temperature_sol.at_plot(r, c)        # microclimat de surface local (①–④)
            temp  = T_PLANTE_ALPHA * t_air + (1.0 - T_PLANTE_ALPHA) * t_sol   # T ressentie (⑤)
            # Seuils de croissance : humidité ET lumière ET température suffisantes.
            # tolerance_secheresse abaisse le seuil d'humidité (gène >1 → la plante
            # continue de croître en sol plus sec avant de stagner).
            # Humidité suffisante par le BAS (sécheresse, modulée par le gène) ET
            # pas excessive par le HAUT (asphyxie « noyé » au-delà de HUM_NOYE,
            # §2.3 b). La borne haute est inerte sous le seuil (toute tuile drainante
            # / terre : hum ≤ HUM_NOYE → ok_hum inchangé, message « sec » conservé).
            ok_hum   = (hum >= 0.15 / plant.expressed_gene("tolerance_secheresse")
                        and hum <= HUM_NOYE)
            ok_light = light >= 0.2   # trop d'ombre = stagnation
            ok_temp  = temp  >= plant.plant_class.temp_min_growth   # trop froid = stagnation
            can_grow = ok_hum and ok_light and ok_temp
            # vigueur accélère l'avancement de stade (gène >1 → durée requise réduite) ;
            # le coût de défense (plasticité ③) la freine : une plante sur-exprimant
            # ses tolérances a re-routé sa vigueur → croissance plus lente (compromis
            # croissance/défense, neutre = 1.0 tant qu'aucune sur-expression).
            needed = stage.duration_weeks / (plant.gene("vigueur") * plant.cout_defense())
            if plant.age_weeks >= needed and can_grow:
                if _bolt_bloque(plant):
                    # Bisannuelle an 1 : reste en rosette (ne monte pas à fleur).
                    log.append(f"    🌿 {plant.name}@{plant.position} en rosette "
                               f"(bisannuelle, an 1)")
                elif plant.advance_stage():
                    log.append(f"    🌱 {plant.name}@{plant.position} → [{plant.stage.name}] "
                               f"(hum={hum:.2f} lum={light:.2f} t={temp:.1f}°C)")
            elif not ok_temp:
                log.append(f"    ❄ {plant.name}@{plant.position} stagne (froid t={temp:.1f}°C)")
            elif not ok_light:
                log.append(f"    🌑 {plant.name}@{plant.position} stagne (ombre lum={light:.2f})")
            elif not ok_hum:
                if hum > HUM_NOYE:
                    log.append(f"    🌊 {plant.name}@{plant.position} stagne (noyé hum={hum:.2f})")
                else:
                    log.append(f"    ⏸  {plant.name}@{plant.position} stagne (sec hum={hum:.2f})")
        return log

    def _apply_uptake(self, tile, eco):
        """
        Uptake racinaire SPATIAL (chantier B) : la plante puise sur toute son
        empreinte racinaire `root_plots`, pas seulement le plot central. La
        quantité prélevée est répartie (share = 1/nb plots) — on ne duplique
        pas la consommation. La compétition souterraine entre voisines devient
        alors émergente : deux empreintes qui se chevauchent puisent le même sol.
        """
        log = []
        for plant in tile.plants:
            if not plant.is_alive: continue
            plots = [(r, c) for (r, c) in plant.root_plots
                     if 0 <= r < eco.rows and 0 <= c < eco.cols]
            if not plots:
                plots = [plant.position]
            share = 1.0 / len(plots)
            total = {}
            for r, c in plots:
                consumed = eco.plant_uptake(r, c, plant.current_stage,
                                            shade_memory=plant.shade_memory,
                                            drought_memory=plant.drought_memory,
                                            share=share)
                for k, v in consumed.items():
                    total[k] = round(total.get(k, 0.0) + v, 3)
            if total:
                parts = " ".join(f"{v}↓{d:.3f}" for v, d in total.items())
                log.append(f"    🌿 {plant.name}@{plant.position} ×{len(plots)}plt : {parts}")
        return log

    def _apply_exudates(self, tile, eco):
        """
        Boucle rhizosphère (chantier A) — exsudats racinaires.

        Chaque plante vivante « paie » le sol en carbone : elle dépose des
        exsudats proportionnels à sa photosynthèse (lumière reçue × surface
        foliaire × santé) sur son empreinte racinaire. L'essentiel nourrit le
        microbiome local, une fraction l'om_fresh.

        Borne (anti-emballement, piège n°1) : le dépôt de microbiome décroît à
        mesure que le microbiome local sature (×(1 − micro_norm)). La boucle
        exsudats → microbiome → santé/uptake → exsudats converge, n'explose pas.
        """
        log = []
        deposited_total = 0.0
        for plant in tile.plants:
            if not plant.is_alive:
                continue
            # Photosynthèse : lumière reçue (canopée, auto-ombrage exclu) × surface × santé
            light = eco.lumiere.light_received(plant)
            leaf_factor = min(1.0, len(plant.foliar_plots) / 5.0)
            health_factor = plant.health / 3.0
            photo = light * leaf_factor * health_factor
            if photo <= 0.0:
                continue

            exudate = EXUDATE_BASE * photo
            roots = [(r, c) for (r, c) in plant.root_plots
                     if 0 <= r < eco.rows and 0 <= c < eco.cols]
            if not roots:
                roots = [plant.position]
            micro_share = exudate * (1.0 - EXUDATE_OM_SHARE) / len(roots)
            om_share    = exudate * EXUDATE_OM_SHARE / len(roots)
            for r, c in roots:
                micro_norm = min(1.0, eco.microbiome.at_plot(r, c) / 3.0)
                eco.microbiome.add(r, c, micro_share * (1.0 - micro_norm))
                eco.deposer_litiere(r, c, "diffus", om_share)
                deposited_total += micro_share * (1.0 - micro_norm) + om_share

        if deposited_total > 0.001:
            log.append(f"    🦠 Exsudats → microbiome/om +{deposited_total:.3f} "
                       f"(boucle rhizosphère)")
        return log

    def _update_physiology(self, tile, eco):
        """
        Mise à jour des mémoires physiologiques des plantes.
        Appelée après l'uptake, chaque semaine.
        shade_memory  = lerp(actuel, 1 - lumiere_locale, 0.10)
        drought_memory = lerp(actuel, stress_hydrique, 0.05)
        cold_memory / infection_memory = lerp(actuel, signal, 0.05) (plasticité ①)
        Puis dynamique d'EXPRESSION plastique (lerp à hystérèse vers la cible de
        chaque gène adaptogène) — INERTE tant qu'aucun consommateur ne lit
        expressed_gene (tronçon ②).
        """
        for plant in tile.plants:
            if not plant.is_alive: continue
            r, c = plant.position
            light = eco.lumiere.light_received(plant)
            hum   = eco.humidite.at_plot(r, c)
            t_air = eco.temperature.at_plot(r, c)
            # Shade memory : intégration lente de l'ombre vécue
            plant.shade_memory += (1.0 - light - plant.shade_memory) * 0.10
            plant.shade_memory  = max(0.0, min(1.0, plant.shade_memory))
            # Drought memory : stress quand humidité < 0.5
            drought_stress = max(0.0, 1.0 - hum / 0.5) if hum < 0.5 else 0.0
            plant.drought_memory += (drought_stress - plant.drought_memory) * 0.05
            plant.drought_memory  = max(0.0, min(1.0, plant.drought_memory))
            # Asphyxie memory : MIROIR haut de la sécheresse — stress d'excès quand
            # hum > HUM_EXCES, même intégration lente (ASPHYXIE_MEMORY_LERP = 0.05).
            # Réversible : s'efface dès que le sol redescend (exces_stress → 0). Sous
            # le seuil (terre/sol drainant) → reste 0.0, aucun effet (§2.3 b, palier 2).
            exces_stress = (max(0.0, (hum - HUM_EXCES) / (3.0 - HUM_EXCES))
                            if hum > HUM_EXCES else 0.0)
            plant.asphyxie_memory += (exces_stress - plant.asphyxie_memory) * ASPHYXIE_MEMORY_LERP
            plant.asphyxie_memory  = max(0.0, min(1.0, plant.asphyxie_memory))
            # Cold memory (plasticité ①) : froid sub-létal intégré (cold hardening).
            cold_sev = max(0.0, min(1.0, (COLD_HARDENING_SEUIL - t_air) / COLD_SEVERITY_REF))
            plant.cold_memory += (cold_sev - plant.cold_memory) * COLD_MEMORY_LERP
            plant.cold_memory  = max(0.0, min(1.0, plant.cold_memory))
            # Infection memory (plasticité ①) : pression pathogène VÉCUE = manque de
            # protection du sol × humidité (le champignon a besoin d'eau). Pression
            # déterministe, pas l'événement aléatoire de fungal_disease.
            infection_sig = ((eco.disease_probability(r, c, INFECTION_BASE) / INFECTION_BASE)
                             * min(1.0, hum / 3.0))
            plant.infection_memory += (infection_sig - plant.infection_memory) * INFECTION_MEMORY_LERP
            plant.infection_memory  = max(0.0, min(1.0, plant.infection_memory))
            # Dynamique d'EXPRESSION plastique (§2.3) : chaque gène adaptogène glisse
            # vers cible = 1 + EXPR_GAIN × mémoire(g), en lerp à HYSTÉRÈSE (montée
            # TAU_UP rapide, descente TAU_DOWN lente). Borné [EXPR_MIN, EXPR_MAX].
            # INERTE au ① : lu par PERSONNE (expressed_gene branché au ②).
            for g, mem in _EXPR_MEMOIRE.items():
                cible = 1.0 + EXPR_GAIN * getattr(plant, mem)
                cur   = plant.expression.get(g, 1.0)
                tau   = TAU_UP if cible > cur else TAU_DOWN
                plant.expression[g] = max(EXPR_MIN, min(EXPR_MAX, cur + (cible - cur) * tau))
            # Marques de symptômes ÉVÉNEMENTIELS (sémiologie ②) : maladie/gel/grêle
            # s'estompent ici, AVEC les autres mémoires physiologiques (même endroit,
            # une fois par tick). Pas de gain ici (il vient des ReduceHealth, cf.
            # resolution.py) — uniquement la décroissance/cicatrisation.
            plant.decay_symptoms(SYMPTOM_DECAY)
            # Growth factor : la lumière EFFECTIVE module la hauteur (feedback →
            # ombre). Tolérance à l'ombre (Q6) = base d'espèce × gène individuel :
            # un sciaphile garde sa croissance à l'ombre (light_eff relevé, cap 1.0),
            # un héliophile ombragé décroît (et s'étiole — tronçon 3).
            tol = plant.plant_class.shade_tolerance_base() * plant.expressed_gene("tolerance_ombre")
            light_eff = min(1.0, light * tol)
            target_g = 0.6 + 0.4 * light_eff
            plant.growth_factor += (target_g - plant.growth_factor) * 0.10
            plant.growth_factor  = max(0.3, min(1.0, plant.growth_factor))
