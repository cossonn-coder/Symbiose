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
from fields.ecofields.constants import (T_PLANTE_ALPHA, ROSEE_SURFACE_REF,
                                        ROSEE_FOLIAIRE_MAX, ROOT_HERBIVORY_MEMORY_LERP,
                                        ALLELO_GERM_K, ALLELO_GROWTH_ESC_MAX,
                                        WETNESS_MEMORY_LERP, ROSEE_WET_GAIN,
                                        PLUIE_WET_GAIN, PLUIE_WET_REF, VENT_WET_DRY,
                                        RAD_WET_DRY, COUVERT_WET_SHELTER,
                                        ASPERSION_WET_GAIN, DOSE_ARROSAGE)
from plants import EXPR_GAIN, EXPR_MIN, EXPR_MAX, TAU_UP, TAU_DOWN
from .calendrier import saison_de
from .transpiration import facteur_transpiration
from .racines import eau_percue, pression_parasite, maj_pourriture

# Sémiologie ② (docs/narration/semiologie/conception_semiologie_foliaire.md §2.5) — facteur de décroissance
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
# wind_memory : exposition mécanique au vent VÉCUE (thigmomorphogénèse, vent ④).
# Signal = `vent_local` au plot (eco.vent ∈ [0,1+], champ d'abri spatialisé du ③),
# normalisé à [0,1] (au-delà de WIND_MEMORY_REF la sollicitation sature). Intégration
# LENTE (miroir des autres mémoires) → un semis exposé tôt accumule de la mémoire et
# durcit son port (`port_trapu`), un semis élevé à l'abri reste à 0 (fragile à la
# transplantation). Knobs P4.
WIND_MEMORY_REF  = 0.6    # vent local saturant le signal d'exposition (sév ≈ 1)
WIND_MEMORY_LERP = 0.05   # intégration lente (miroir drought/asphyxie)
# Transpiration foliaire (§3) : le vent amplifie la demande évapotranspiratoire de la
# plante exposée → renforce le stress hydrique foliaire des GRANDES feuilles par grand
# vent. On MAJORE le `drought_stress` du tick ∝ (vent_local × surface foliaire), borné.
# Effet additif sobre, neutre à vent nul (golden NEUTRE pour cette part). Knob P4.
WIND_TRANSPI_COEF = 0.25  # surcroît max de stress hydrique à vent plein × grande canopée

# Appariement gène adaptogène ↔ mémoire d'exposition (plasticité ①, §2.3). La
# dynamique d'expression (lerp à hystérèse) glisse expression[g] vers
# 1 + EXPR_GAIN × mémoire(g). Étendre = ajouter une paire ici + sa mémoire.
_EXPR_MEMOIRE = {
    "tolerance_secheresse": "drought_memory",
    "tolerance_ombre":      "shade_memory",
    "rusticite_froid":      "cold_memory",
    "resistance_pathogene": "infection_memory",
    "tolerance_asphyxie":   "asphyxie_memory",
    "port_trapu":           "wind_memory",
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
    franchit PAS son stade de montaison tant qu'elle est dans son an 1 : rosette
    pendant TOUTE l'an 1 (52 semaines), montaison/floraison à partir de l'an 2
    (puis mort monocarpique, mortalite.py).

    `age_years` accumule `1/52` par tick, donc à la semaine 52 il vaut ~1.0 au
    bruit flottant près (en pratique `1.0000000000000002`). On ouvre le gate avec
    une marge d'un demi-tick (`ANNEE_1`) : la semaine 52 reste rosette, la montaison
    ne devient possible qu'en semaine 53 (an 2 sans ambiguïté). Sans cette marge,
    « rosette l'an 1 » fuirait d'un tick sur la frontière (off-by-one).

    N'a d'effet QUE pour `life_cycle == "biennial"` → AUCUNE espèce du smoke n'est
    bisannuelle ⇒ golden NEUTRE. Si ce gate déplaçait le hash golden, c'est qu'il
    fuit sur une espèce non bisannuelle (BUG, pas un re-figeage)."""
    ANNEE_1 = 1.0 + 0.5 / 52.0   # frontière an1/an2 robuste au bruit flottant
    cls = plant.plant_class
    if cls.life_cycle != "biennial" or plant.age_years > ANNEE_1:
        return False
    bolt = _bolt_stage_index(cls)
    return bolt is not None and plant.current_stage + 1 >= bolt


def _f_croissance_allelo(allelo: float, sensibilite: float) -> float:
    """Facteur d'ESCOMPTE du gain de croissance sous allélopathie racinaire (sprint
    ALLÉLOPATHIE ③, D1/D6). Même RAMPE DOUCE Monod qu'à la germination (②, `_f_allelo`
    dans succession.py — cohérence), mais bornée par ALLELO_GROWTH_ESC_MAX :

        rampe(x)     = x / (x + ALLELO_GERM_K)                     (Monod, saturante)
        f_croissance = 1 − ALLELO_GROWTH_ESC_MAX · sens · rampe(x) (borné < 1)

    `allelo` = concentration MOYENNE de `allelopathie` sur l'empreinte racinaire ;
    `sensibilite` = trait d'espèce `allelopathie_sensibilite` (1 = sensible standard,
    0 = tolérant). N'escompte JAMAIS totalement la croissance (ESC_MAX < 1) : la
    plante affaiblie PLIE, l'écosystème fait le reste (philo #2, dépérissement
    émergent). INVARIANT GOLDEN : `allelo = 0` ⇒ `rampe(0) = 0` ⇒ `f_croissance = 1`
    ⇒ gain STRICTEMENT inchangé (K>0, aucun /0). Court-circuit à 1.0 sur sol propre
    (chemin du golden au repos). Pur, déterministe, zéro RNG (philo #3)."""
    if allelo <= 0.0:
        return 1.0
    rampe = allelo / (allelo + ALLELO_GERM_K)
    return max(0.0, 1.0 - ALLELO_GROWTH_ESC_MAX * sensibilite * rampe)


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

    def _apply_uptake(self, tile, eco, saison=None, week_in_year=None,
                      demande=None):
        """
        Uptake racinaire SPATIAL (chantier B) : la plante puise sur toute son
        empreinte racinaire `root_plots`, pas seulement le plot central. La
        quantité prélevée est répartie (share = 1/nb plots) — on ne duplique
        pas la consommation. La compétition souterraine entre voisines devient
        alors émergente : deux empreintes qui se chevauchent puisent le même sol.

        Transpiration foliaire (sprint « le sol qui respire » ①, D111 §1c) : la
        boucle passe la saison, la semaine et la `demande` climatique du tick → le
        prélèvement d'EAU est modulé par plante (feuillage présent × type de
        feuillage). `demande=None` (appelant sans météo) → facteur 1.0 historique.
        """
        log = []
        for plant in tile.plants:
            if not plant.is_alive: continue
            transp = (1.0 if demande is None else
                      facteur_transpiration(plant, saison, week_in_year, demande))
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
                                            root_herbivory_memory=plant.root_herbivory_memory,
                                            root_loss_tolerance=plant.plant_class.root_loss_tolerance_base,
                                            share=share,
                                            transpiration=transp)
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
            health_factor = plant.vitalite
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

    def _update_physiology(self, tile, eco, nebulosite=1.0, pluie_event=0.0):
        """
        Mise à jour des mémoires physiologiques des plantes.
        Appelée après l'uptake, chaque semaine. `nebulosite`/`pluie_event` (météo du
        tick, passés par boucle.py) alimentent l'humectation foliaire (①) ; leurs
        défauts inertes (ciel clair sec, pas de pluie) laissent les autres appelants
        (tests) inchangés.
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
            # Vent LOCAL au plot (champ d'abri spatialisé du ③). None (pots/bacs,
            # outils sans abri) → 0.0 : aucune sollicitation mécanique ni transpiration
            # éolienne → wind_memory/port_trapu au repos, golden NEUTRE pour ces sites.
            vent_local = eco.vent.at_plot(r, c) if getattr(eco, "vent", None) else 0.0
            # Shade memory : intégration lente de l'ombre vécue
            plant.shade_memory += (1.0 - light - plant.shade_memory) * 0.10
            plant.shade_memory  = max(0.0, min(1.0, plant.shade_memory))
            # Drought memory : stress quand humidité < 0.5. Humidité RESSENTIE (D111 ④) :
            # des racines rongées/pourries (`root_herbivory_memory`) n'atteignent plus
            # toute l'eau du plot → `eau_percue` (sim/engine/racines.py). Mémoire 0 ⇒
            # `hum` inchangé ⇒ bit-identique.
            hum_p = eau_percue(plant, eco, hum)
            drought_stress = max(0.0, 1.0 - hum_p / 0.5) if hum_p < 0.5 else 0.0
            # Captation foliaire de la rosée (sprint météo→champs ⑤, §6) : une CANOPÉE
            # intercepte la rosée du matin → le feuillage hydraté ALLÈGE le stress
            # hydrique (interconnexion « tout coexiste »). On RABOTE le drought_stress
            # ∝ la rosée moyenne déposée sur l'empreinte foliaire de la plante
            # (`eco.rosee_last`), borné par ROSEE_FOLIAIRE_MAX. Effet marginal mais réel
            # (un LEVIER, pas une pluie) : à rosée nulle → terme nul → comportement
            # antérieur (golden NEUTRE pour cette part). Lecture PURE de `rosee_last`.
            # Rosée MOYENNE captée sur l'empreinte foliaire — calculée UNE fois, DEUX
            # consommateurs (captation foliaire du drought_stress ci-dessous +
            # humectation ① plus bas). On ne recalcule JAMAIS dans un tick ce qui l'a
            # déjà été. Le garde `capte > 0.0` est STRICTEMENT équivalent à l'ancien
            # `rosee is not None and plant.foliar_plots` pour le rabot : capte>0 implique
            # rosée présente et canopée non vide ; et capte==0 laissait `relief=0` donc
            # `drought_stress` inchangé (×1.0) → drought_stress reste bit-identique.
            capte = 0.0
            rosee = getattr(eco, "rosee_last", None)
            if rosee is not None and plant.foliar_plots:
                capte = sum(rosee.at_plot(fr, fc) for (fr, fc) in plant.foliar_plots
                            if 0 <= fr < eco.rows and 0 <= fc < eco.cols)
                capte /= len(plant.foliar_plots)            # rosée MOYENNE sur la canopée
            if capte > 0.0 and drought_stress > 0.0:
                relief = ROSEE_FOLIAIRE_MAX * min(1.0, capte / ROSEE_SURFACE_REF)
                drought_stress = max(0.0, drought_stress * (1.0 - relief))
            # Transpiration foliaire (vent ④, §3) : le vent assèche aussi la PLANTE
            # (demande évapotranspiratoire), pas que le sol. Une GRANDE canopée exposée
            # au vent perd plus d'eau → on MAJORE le stress hydrique du tick ∝ (vent_local
            # × surface foliaire). Borné [0,1]. Vent nul ⇒ terme nul (golden NEUTRE).
            if drought_stress > 0.0 and vent_local > 0.0 and plant.foliar_plots:
                leaf_factor = min(1.0, len(plant.foliar_plots) / 5.0)
                transpi = WIND_TRANSPI_COEF * min(1.0, vent_local) * leaf_factor
                drought_stress = min(1.0, drought_stress * (1.0 + transpi))
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
            # Humectation foliaire (sprint HUMECTATION FOLIAIRE ①, §2.2) : l'eau se POSE
            # sur le feuillage (rosée `capte` déjà calculée ci-dessus + pluie du tick)
            # puis SÈCHE (vent, soleil ciel clair). Le vent ne PÉNÈTRE pas un couvert
            # dense (`foliage_density_at` — jamais None, repli strate) → l'aération
            # devient un levier de MILIEU (espacer, tailler — philo #1). L'aspersion au
            # feuillage (ASPERSION_WET_GAIN) est le geste `arroser(feuillage=True)` du ③ :
            # la source la plus MOUILLANTE (on vise directement la canopée). Carte
            # transiente `eco.aspersion_last` (posée par le geste, effacée par le tick),
            # moyennée sur l'empreinte foliaire comme la rosée — `getattr` défensif → un
            # `eco` sans la carte (pots/bacs, outils) reste inerte. NULLE au repos (aucun
            # `arroser(feuillage=True)`) → terme nul → golden NEUTRE pour cette part.
            # DÉPLACÉE AVANT infection_memory (② §2.3) : les deux sites de pression fongique
            # — fungal_disease ET infection_memory ci-dessous — lisent désormais
            # `wetness_memory`. Elle doit donc être à jour du tick COURANT avant sa lecture,
            # sinon infection_memory retarderait d'un tick (décalage silencieux).
            asp = getattr(eco, "aspersion_last", None)
            aspersion = 0.0
            if asp is not None and plant.foliar_plots:
                aspersion = sum(asp.at_plot(fr, fc) for (fr, fc) in plant.foliar_plots
                                if 0 <= fr < eco.rows and 0 <= fc < eco.cols)
                aspersion /= len(plant.foliar_plots)   # aspersion MOYENNE sur la canopée
            dens = plant.plant_class.foliage_density_at(plant)
            vent_eff = vent_local * (1.0 - COUVERT_WET_SHELTER * dens)
            mouillage = (ROSEE_WET_GAIN * min(1.0, capte / ROSEE_SURFACE_REF)
                         + PLUIE_WET_GAIN * min(1.0, max(0.0, pluie_event) / PLUIE_WET_REF)
                         + ASPERSION_WET_GAIN * min(1.0, aspersion / DOSE_ARROSAGE))
            sechage = ((1.0 - VENT_WET_DRY * min(1.0, max(0.0, vent_eff)))
                       * (1.0 - RAD_WET_DRY * (1.0 - nebulosite)))
            wet_sig = max(0.0, min(1.0, mouillage * sechage))
            plant.wetness_memory += (wet_sig - plant.wetness_memory) * WETNESS_MEMORY_LERP
            plant.wetness_memory  = max(0.0, min(1.0, plant.wetness_memory))
            # Infection memory (plasticité ①) : pression pathogène VÉCUE = manque de
            # protection du sol × HUMECTATION du feuillage (② : c'était `min(1, hum/3)`,
            # l'humidité du SOL — même proxy faux que fungal_disease ; le champignon
            # germe sur l'eau LIQUIDE posée sur la feuille, pas dans le sol humide).
            # Pression déterministe, pas l'événement aléatoire de fungal_disease.
            infection_sig = ((eco.disease_probability(r, c, INFECTION_BASE) / INFECTION_BASE)
                             * plant.wetness_memory)
            plant.infection_memory += (infection_sig - plant.infection_memory) * INFECTION_MEMORY_LERP
            plant.infection_memory  = max(0.0, min(1.0, plant.infection_memory))
            # Wind memory (thigmomorphogénèse, vent ④) : exposition mécanique VÉCUE,
            # intégrée lentement depuis `vent_local` (normalisé par WIND_MEMORY_REF). Un
            # semis exposé tôt l'accumule → port_trapu monte (robuste) ; un semis élevé à
            # l'abri (vent_local≈0) reste à 0 → choc à la transplantation (hardening off).
            wind_sig = min(1.0, vent_local / WIND_MEMORY_REF)
            plant.wind_memory += (wind_sig - plant.wind_memory) * WIND_MEMORY_LERP
            plant.wind_memory  = max(0.0, min(1.0, plant.wind_memory))
            # Root herbivory memory (campagnol, sprint santé & résilience ③) : intégration
            # lente de la densité `herbivore_vertebre` locale = pression du rongeur sur le
            # chevelu racinaire. Miroir des autres mémoires (même lerp). Lue par
            # `plant_uptake` (via `_apply_uptake`) où elle réduit l'uptake effectif → la
            # plante s'affame par les voies EXISTANTES (philo #2). Densité nulle (smoke) →
            # signal 0 → mémoire reste 0 → uptake bit-identique → golden NEUTRE.
            # + PARASITE DE FAIBLESSE (D111 ④) : un champignon parasite du registre
            # pourrit les racines d'un hôte DÉJÀ affaibli (0 sur hôte sain / non listé).
            # ⑦bis : la même pression CUMULE le pourridié du collet (sans plafond,
            # `maj_pourriture`) → un hôte affaibli attaqué durablement peut mourir.
            pression = pression_parasite(plant, eco)
            maj_pourriture(plant, pression)
            rong = min(1.0, eco.category_density("herbivore_vertebre", r, c)
                       + pression)
            plant.root_herbivory_memory += (rong - plant.root_herbivory_memory) * ROOT_HERBIVORY_MEMORY_LERP
            plant.root_herbivory_memory  = max(0.0, min(1.0, plant.root_herbivory_memory))
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
            # Escompte ALLÉLOPATHIQUE de croissance (sprint ALLÉLOPATHIE ③, EFFECTIVE au
            # ④) : une plante sensible dont les racines explorent des plots chargés voit
            # son GAIN de croissance escompté (jamais sa santé décrémentée — philo #2).
            # On lit la concentration MOYENNE de l'allélopathie EFFECTIVE de CETTE espèce
            # (`allelo_effectif` = ambiant + AUTOTOXICITÉ si la plante EST l'émetteur
            # récurrent du plot — la monoculture fatigue SA propre croissance) sur
            # l'empreinte RACINAIRE déjà dérivée (`plant.root_plots`, la même que
            # l'uptake — RÉUTILISÉE, pas recalculée) et on rabote la cible du
            # growth_factor par f_croissance ∈ [1−ESC_MAX, 1]. Le facteur EST stateful
            # via le lerp (growth_factor converge, ne compound pas). Champ nul au repos
            # (aucun émetteur avant ⑤ → autotox jamais armé) ⇒ moyenne 0 ⇒ f_croissance=1
            # ⇒ target_g inchangé ⇒ golden NEUTRE. Court-circuité si l'empreinte ne
            # touche que du sol propre (rampe 0 → 1.0).
            roots = [(rr, cc) for (rr, cc) in plant.root_plots
                     if 0 <= rr < eco.rows and 0 <= cc < eco.cols] or [(r, c)]
            allelo_rac = sum(eco.allelo_effectif(rr, cc, plant.plant_class)
                             for (rr, cc) in roots) / len(roots)
            target_g *= _f_croissance_allelo(allelo_rac,
                                             plant.plant_class.allelopathie_sensibilite)
            plant.growth_factor += (target_g - plant.growth_factor) * 0.10
            plant.growth_factor  = max(0.3, min(1.0, plant.growth_factor))
