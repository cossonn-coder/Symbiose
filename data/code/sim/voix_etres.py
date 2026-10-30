"""
SYMBIOSE — sim/voix_etres.py
LES ÊTRES PARLENT sous vision (sprint « le sol qui respire » ⑥, D111 §4) : 1 à 3
phrases à la 1ʳᵉ personne, GÉNÉRÉES depuis les vrais besoins mesurés au moteur.

📖 Pédagogie — deux étages, comme un diagnostic :
  1. `besoins_*` MESURE : chaque thème reçoit une intensité ∈ [0,1] lue sur l'état
     persistant (mémoires de sécheresse/ombre/asphyxie de la plante, facteur de
     nutrition N/P/K de sa croissance (D120 ③) et pH sous ses racines,
     allélopathie effective, racines voisines, rongeur/parasite, ravageurs, vent local ; pour une bête : excès de population sur ce que le lieu
     porte, abri, prédateurs, humidité).
     Un thème n'est dit que s'il dépasse SEUIL_DIRE — la voix ne ment jamais.
     Les seuils de PAROLE sont plus bas que ceux de DÉGÂT de la sémiologie : un être
     sent un manque avant d'en porter le signe sur ses feuilles.
  2. `phrases_*` PARLE : les MAX_PHRASES besoins les plus forts, chacun rendu par une
     variante du corpus (`voix_etres_corpus`) choisie par hash (graine, semaine, être,
     thème) → même être, même semaine = mêmes mots ; zéro RNG.
Aucun besoin → une phrase de bien-être.

LECTURE PURE (n'écrit rien), hors tick → golden NEUTRE.
"""
from __future__ import annotations

from fields.noise import _hash_noise, stable_str_hash
from fields.ecofields.constants import ALLELO_GERM_K
from fields.population import build_pollinator_registry
from sim import semiologie as S
from sim.nutrition_plante import nutrition_plante, NUTRITION_PLANCHER
from sim.voix_etres_corpus import (PLANTE, BETE, CHAMPIGNON, NUTRIMENTS, FAMILLES_FR,
                                   NOMS_BETES, BETES_HYGROPHILES)

SEUIL_DIRE = 0.25        # intensité minimale d'un besoin pour qu'il soit dit
MAX_PHRASES = 3
# Faim plante (D120 ③) : intensité = escompte de croissance `1 − facteur_nutrition`,
# pleine au plancher (1 − PLANCHER = 0,6) → dite (≥ SEUIL_DIRE) dès que la carence
# retire ≥ 15 % à la cible de croissance : ce que la plante dit, elle le SUBIT.
FAIM_PLEINE = 1.0 - NUTRITION_PLANCHER
# Faim bête (D120 ③) : part du déclin de la population que le lieu explique
# (`PopulationField.faim`) ; dite dès que le lieu explique une cible ≥ 10 % sous la population (déclin ≥ ~4,5 %/sem.).
FAIM_BETE_APPARITION, FAIM_BETE_PLEINE = 0.0, 0.4
_ramp = S._ramp          # même rampe bornée que la sémiologie (DRY)

# Préférences florales des pollinisateurs (donnée du registre, lue une fois).
_GOUTS = {ps.name: ps.attractivite for ps in build_pollinator_registry()}


# ─────────────────────────────── plantes ──────────────────────────────────────
def _moyenne(eco, champ, plots) -> float:
    return sum(champ.at_plot(r, c) for r, c in plots) / len(plots)


def _racines(plant, eco) -> list:
    return [(r, c) for r, c in (plant.root_plots or [plant.plot_foyer])
            if 0 <= r < eco.rows and 0 <= c < eco.cols] or [plant.plot_foyer]


def contexte_tuile(tile) -> dict:
    """Voisinage d'une tuile calculé UNE fois (mémoïsation, jamais de recalcul par
    plante) : vivantes + hauteurs, et index plot → plantes dont les racines y vont."""
    vivantes = [p for p in tile.plants if p.is_alive]
    par_plot: dict = {}
    for p in vivantes:
        for plot in p.root_plots:
            par_plot.setdefault(plot, []).append(p)
    return {"hauteurs": [(p, p.current_height) for p in vivantes], "par_plot": par_plot}


def _ombreur(plant, ctx) -> str | None:
    """Le plus haut voisin vivant, plus haut que la plante, dont la couronne la couvre."""
    h, best = plant.current_height, None
    for o, ho in ctx["hauteurs"]:
        if (o is not plant and ho > h
                and (o.x_cm - plant.x_cm) ** 2 + (o.y_cm - plant.y_cm) ** 2 <= o.canopy_radius ** 2):
            h, best = ho, o
    return best.name if best else None


def _concurrents(plant, ctx, plots) -> list:
    """Plantes vivantes (distinctes, ordre stable) dont les racines partagent un plot."""
    vus, out = {id(plant)}, []
    for plot in plots:
        for o in ctx["par_plot"].get(plot, ()):
            if id(o) not in vus:
                vus.add(id(o))
                out.append(o)
    return out


def besoins_plante(plant, tile, eco, saison, ctx: dict | None = None) -> list[tuple]:
    """[(intensité, thème, champs)] des besoins d'une plante vivante (non triés).
    `ctx` = `contexte_tuile(tile)` partagé par un balayage (overdose) ; None → calculé."""
    ctx = ctx or contexte_tuile(tile)
    cls = plant.plant_class
    plots = _racines(plant, eco)
    out = [(_ramp(plant.drought_memory, 0.2, 0.8), "soif", {}),
           (_ramp(plant.asphyxie_memory, 0.2, 0.8), "noyade", {}),
           (S.ravageurs(plant, eco, saison), "ravageurs", {})]
    ombre = _ramp(plant.shade_memory, 0.2, 0.8)
    if ombre >= SEUIL_DIRE:
        voisin = _ombreur(plant, ctx)
        out.append((ombre, "ombre", {"voisin": voisin}) if voisin
                   else (ombre, "ombre_anonyme", {}))
    # Sol : UNE source de vérité avec la croissance (D120 ③) — le facteur de nutrition
    # qui escompte vraiment sa cible (Liebig relatif à la roche, poids du stade, sans N
    # pour une carnivore, P mycorhizé) et le nutriment limitant de ce même calcul.
    facteur, limitant = nutrition_plante(plant, eco, plots)
    if limitant is not None:
        out.append((_ramp(1.0 - facteur, 0.0, FAIM_PLEINE), "faim",
                    {"nutriment": NUTRIMENTS[limitant.lower()]}))
    ph = _moyenne(eco, eco.ph, plots)
    ecart = _ramp(abs(ph - cls.ph_opt) / cls.ph_tol, 0.6, 1.0)
    out.append((max(ecart, S.chlorose(plant, eco, saison)), "ph",
                {"sens": "acide" if ph < cls.ph_opt else "calcaire"}))
    allelo = sum(eco.allelo_effectif(r, c, cls) for r, c in plots) / len(plots)
    sens = cls.allelopathie_sensibilite * allelo / (allelo + ALLELO_GERM_K) if allelo > 0 else 0.0
    out.append((_ramp(sens, 0.15, 0.6), "allelopathie", {}))
    rivaux = _concurrents(plant, ctx, plots)
    if rivaux:
        fort = max(rivaux, key=lambda o: (o.root_radius, o.name))
        out.append((_ramp(len(rivaux), 2, 6), "concurrence", {"voisin": fort.name}))
    rong = S.rongeur_racinaire(plant, eco, saison)
    out.append((rong, "campagnol", {}) if rong > 0
               else (_ramp(max(plant.root_herbivory_memory, plant.pourriture_memory),
                           0.2, 0.8), "parasite", {}))
    if eco.vent is not None:
        out.append((_ramp(eco.vent.at_plot(*plant.plot_foyer), 0.9, 1.5), "vent", {}))
    return out


# ──────────────────────────────── bêtes ───────────────────────────────────────
def _nom(cle: str) -> str:
    return NOMS_BETES.get(cle, cle)


def besoins_bete(cle: str, tile, eco, r: int, c: int, cache: dict | None = None) -> list[tuple]:
    """[(intensité, thème, champs)] d'une bête au plot (r, c). `cache` (optionnel)
    mémoïse la grille d'habitat par (tuile, espèce) le temps d'un snapshot."""
    field = (eco.populations or {}).get(cle)
    if field is None:
        return []
    spec = field.spec
    out = []
    faim = _ramp(field.faim(r, c), FAIM_BETE_APPARITION, FAIM_BETE_PLEINE)
    proies = sorted(n for n, f in eco.populations.items() if cle in f.spec.predators)
    if cle in _GOUTS:
        fam = max(sorted(_GOUTS[cle]), key=lambda f: _GOUTS[cle][f])
        out.append((faim, "faim_fleurs", {"famille": FAMILLES_FR.get(fam, fam)}))
    elif proies:
        proie = max(proies, key=lambda n: eco.populations[n].at_plot(r, c))
        out.append((faim, "faim_proies", {"proie": _nom(proie)}))
    else:
        out.append((faim, "faim", {}))
    key = (tile.tile_id, cle)
    if cache is not None and key in cache:
        hab = cache[key]
    else:
        hab = spec.habitat_fn(eco, tile, tile.plants)
        if cache is not None:
            cache[key] = hab
    out.append((_ramp(1.0 - hab[r][c], 0.7, 1.0), "abri", {}))
    preds = [(eco.populations[n].at_plot(r, c), n) for n in spec.predators
             if n in eco.populations]
    if preds:
        _, pred = max(preds)
        out.append((_ramp(sum(d for d, _ in preds), 0.2, 0.8), "predation",
                    {"predateur": _nom(pred)}))
    if cle in BETES_HYGROPHILES:
        out.append((_ramp(0.8 - eco.humidite.at_plot(r, c), 0.0, 0.6), "sec", {}))
    return out


# ─────────────────────────────── parole ───────────────────────────────────────
def _variante(variantes: tuple, seed: int, week: int, ident: str, theme: str) -> str:
    u = _hash_noise(seed ^ stable_str_hash(ident), week, stable_str_hash(theme) & 0xFFFF, 0)
    return variantes[min(int(u * len(variantes)), len(variantes) - 1)]


def _parler(corpus: dict, besoins: list, seed: int, week: int, ident: str) -> list[str]:
    dits = sorted((b for b in besoins if b[0] >= SEUIL_DIRE),
                  key=lambda b: (-b[0], b[1]))[:MAX_PHRASES]
    if not dits:
        dits = [(1.0, "bien", {})]
    return [_variante(corpus[t], seed, week, ident, t).format(**champs)
            for _, t, champs in dits]


def phrases_plante(plant, tile, eco, saison: str, seed: int, week: int,
                   ctx: dict | None = None) -> list[str]:
    ident = f"{tile.tile_id}|{plant.x_cm:.1f}|{plant.y_cm:.1f}"
    return _parler(PLANTE, besoins_plante(plant, tile, eco, saison, ctx), seed, week, ident)


def phrases_bete(cle: str, tile, eco, r: int, c: int, seed: int, week: int,
                 cache: dict | None = None) -> list[str]:
    ident = f"{tile.tile_id}|{cle}|{r}|{c}"
    return _parler(BETE, besoins_bete(cle, tile, eco, r, c, cache), seed, week, ident)


def phrases_champignon(role: str, tile, r: int, c: int, seed: int, week: int) -> list[str]:
    """Un champignon dit son rôle local (`sim/champignon_role`, b/r/h)."""
    variantes = CHAMPIGNON.get(role, CHAMPIGNON["h"])
    return [_variante(variantes, seed, week, f"{tile.tile_id}|champi|{r}|{c}", role)]
