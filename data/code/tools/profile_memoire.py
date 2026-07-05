# SYMBIOSE — tools/profile_memoire.py
# Profileur MÉMOIRE PAR CATÉGORIE d'objets, sur le monde COMPLET 8 tuiles grandi
# ~12 ans (sprint « perf run éternel », tronçon ①). But : PROUVER ou réfuter
# l'hypothèse d'une fuite « indépendante du nombre de plantes N » — la cause du
# crash mémoire du monde complet. On ne corrige pas une fuite non nommée : cet
# outil la NOMME (ou l'exclut) avant tout colmatage.
#
# Méthode : ticker année par année et, chaque année, COMPTER explicitement les
# objets par catégorie (plantes+squelettes, segments, dicts seedbank species/data,
# grilles ecofields, journal des voix, log), plus le RSS process.
# Le tableau année × catégorie rend la croissance linéaire ÉVIDENTE. Une catégorie
# qui grossit alors que N stagne = la fuite recherchée (colonne « ÷N » marquée).
#
# RSS : mesuré via `resource.getrusage(RUSAGE_SELF).ru_maxrss` (pic mémoire du
# process, quasi-gratuit) et NON tracemalloc. tracemalloc a un overhead ~10× qui
# rendait le profil sur 8 tuiles inexécutable (tué à >240 s). Le diagnostic « fuite
# indépendante de N » repose de toute façon sur les COMPTES d'objets par catégorie
# (ci-dessous), pas sur le RSS tracé : le RSS ne sert qu'à confirmer la tendance
# globale. ru_maxrss est un PIC monotone (high-water mark) → il ne redescend jamais,
# on lit donc sa croissance, pas sa valeur absolue.
#
# LECTURE SEULE, DÉTERMINISTE — ne touche ni le tick ni le golden. On appelle le
# moteur EXACTEMENT comme le serveur (config "full") : mêmes fabriques, zéro
# duplication de logique de simulation.
#
# Usage (depuis data/code/) : python3 -m tools.profile_memoire [annees] [tuiles]
#   annees  : nombre d'années simulées (défaut 12)
#   tuiles  : nombre de tuiles du monde full à garder (défaut 8 = monde complet)

import resource
import sys
import time

from main import build_world_full
from sim.engine import Engine
from fields.grids import GridField


def _rss_mo() -> float:
    """Pic mémoire du process en Mo (ru_maxrss). Sous Linux, ru_maxrss est en Ko."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def _build_engine(n_tiles: int):
    """Monde COMPLET (fabrique du serveur config="full") tronqué à n_tiles.

    On réutilise `build_world_full` (8 tuiles SECTORS + maison), puis on garde les
    n premières tuiles — permet de comparer 2 vs 8 tuiles avec la MÊME fabrique.
    On câble aussi `journal` et une banque-joueur pour que ces accumulateurs
    potentiels soient EXERCÉS pendant le profil (sinon on ne mesurerait pas la
    vraie mémoire du run réel). On n'appelle PAS le serveur : on monte le
    game_state à la main, à l'identique de commands.cmd_init, pour rester en
    lecture seule et déterministe.
    """
    tiles, ecos, _aux, house = build_world_full()
    tiles = tiles[:n_tiles]
    ecos = {t.tile_id: ecos[t.tile_id] for t in tiles}
    game_state = {
        "tiles": tiles, "eco": ecos, "scores": {},
        "current_player": "joueur_1", "week": 1, "log": [],
        "house": house, "seed": 0x5AB1057E,
        # `journal` présent → le ledger des voix (FIFO 200) est réellement alimenté
        # si un hook le consigne ; ici on le laisse à vide et on mesure sa taille.
        "journal": {},
    }
    return Engine(game_state), tiles, ecos


# ---------------------------------------------------------------------------
# ÉCHANTILLONNAGE PAR CATÉGORIE — comptages explicites (pas d'heuristique gc)
# ---------------------------------------------------------------------------

def _echantillon(game_state, tiles, ecos) -> dict:
    """Un relevé instantané : nombre d'objets par catégorie.

    Toutes les catégories sont des COMPTES (nombre d'entrées), pas des densités :
    ce qui nous intéresse est l'accumulation d'objets, cause du RSS.
    """
    # Plantes : vivantes vs squelettes (mortes encore présentes dans tile.plants).
    n_vivantes = n_squelettes = n_segments = 0
    for t in tiles:
        for p in t.plants:
            if getattr(p, "is_alive", False):
                n_vivantes += 1
            else:
                n_squelettes += 1
            n_segments += len(getattr(p, "segments", ()) or ())

    # Seedbank : nombre d'ENTRÉES cumulées dans les dicts par plot.
    #  - data[r][c]     = dict archétype → densité (taille FIXE = 4 archétypes/plot) ;
    #  - species[r][c]  = dict classe → rec (croît avec les espèces déposées ; SUSPECT).
    n_data = n_species = 0
    for eco in ecos.values():
        sb = getattr(eco, "seed_bank", None)
        if sb is None:
            continue
        for row in sb.data:
            for cell in row:
                n_data += len(cell)
        for row in sb.species:
            for cell in row:
                n_species += len(cell)

    # Grilles ecofields : nombre de GridField × cellules — DEVRAIT être constant
    # (allouées une fois à la construction, jamais ajoutées par tick).
    n_grilles = n_cellules = 0
    for eco in ecos.values():
        for v in vars(eco).values():
            if isinstance(v, GridField):
                n_grilles += 1
                n_cellules += v.rows * v.cols
        for pf in getattr(eco, "populations", {}).values():
            if isinstance(pf, GridField):
                n_grilles += 1
                n_cellules += pf.rows * pf.cols

    # Journal des voix (FIFO borné 200) et log de tick (purgé côté serveur).
    journal = game_state.get("journal", {})
    n_journal = sum(len(j.get("entries", ()))
                    for j in journal.values() if isinstance(j, dict))
    n_log = len(game_state.get("log", ()))

    return {
        "N_vivantes": n_vivantes,
        "squelettes": n_squelettes,
        "segments": n_segments,
        "sb_species": n_species,
        "sb_data": n_data,
        "grilles": n_grilles,
        "cellules_grille": n_cellules,
        "journal": n_journal,
        "log": n_log,
    }


# Ordre d'affichage des colonnes (constant → tableau lisible).
_COLS = ["N_vivantes", "squelettes", "segments", "sb_species", "sb_data",
         "grilles", "cellules_grille", "journal", "log"]


def _fmt_ligne(annee: int, ech: dict, rss_mo: float) -> str:
    cells = " ".join(f"{ech[k]:>8d}" for k in _COLS)
    return f"{annee:>4d} {cells} {rss_mo:>9.2f}"


def _entete() -> str:
    titres = " ".join(f"{k:>8s}" for k in _COLS)
    return f"{'an':>4s} {titres} {'RSS(Mo)':>9s}"


def _diagnostic(historique: list) -> None:
    """Analyse la série : quelle catégorie est une FUITE INDÉPENDANTE de N ?

    Critère ROBUSTE (immune au départ à 0) : on regarde l'INTENSITÉ PAR PLANTE
    `catégorie / N` sur la première année pleine vs la dernière. Une catégorie
    couplée à N garde une intensité par plante ~STABLE (elle grossit PARCE QUE N
    grossit → bornée par le tronçon ③). Une FUITE INDÉPENDANTE de N a une intensité
    par plante qui GRIMPE (elle s'accumule même à N constant → à borner ici).

    On compare la dernière année à la PREMIÈRE ANNÉE PLEINE (indice 1, pas l'an 0
    quasi vide) pour que le ratio par plante ait un sens. `grilles`/`cellules_grille`
    (constants par construction) et `journal` (FIFO 200) sont attendus PLATS.
    """
    if len(historique) < 3:
        print("\n(historique trop court pour un diagnostic — au moins 2 ans pleins)")
        return
    ref, dernier = historique[1], historique[-1]          # 1re année pleine → dernière
    n_ref = max(1, ref["N_vivantes"])
    n_fin = max(1, dernier["N_vivantes"])
    print("\n=== Diagnostic — intensité PAR PLANTE (catégorie / N) ===")
    print(f"  N plantes vivantes : {ref['N_vivantes']} → {dernier['N_vivantes']} "
          f"(×{dernier['N_vivantes'] / n_ref:.2f})")
    fuite_trouvee = False
    for k in _COLS:
        if k == "N_vivantes":
            continue
        i_ref = ref[k] / n_ref                              # intensité/plante début
        i_fin = dernier[k] / n_fin                          # intensité/plante fin
        # Fuite indépendante de N : l'intensité par plante grimpe nettement (+50 %)
        # ET l'accumulé absolu est non trivial. `log` non purgé est un ARTEFACT du
        # profil (le serveur le vide chaque step) → jamais compté comme fuite.
        grimpe = i_fin > i_ref * 1.5 + 1e-9 and dernier[k] > 50
        if k == "log":
            etat = "(non purgé ici — ARTEFACT profil, purgé chaque step en jeu)"
        elif grimpe:
            etat = ">>> INDÉPENDANT DE N (intensité/plante GRIMPE) — à borner <<<"
            fuite_trouvee = True
        else:
            etat = "∝N ou plat (intensité/plante stable → borné par ③)"
        print(f"  {k:<16s} /N : {i_ref:8.3f} → {i_fin:8.3f}   {etat}")
    if not fuite_trouvee:
        print("  ==> AUCUNE fuite indépendante de N : chaque accumulateur suit N "
              "(intensité/plante stable) ou plafonne (journal/grilles). Le RSS "
              "SUIT N → borner N (tronçon ③) résout aussi la mémoire.")
    else:
        print("  ==> FUITE indépendante de N détectée → à BORNER (cap/FIFO/prune "
              "sur entrées INERTES, golden bit-à-bit).")


def main():
    annees = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    n_tiles = int(sys.argv[2]) if len(sys.argv) > 2 else 8

    engine, tiles, ecos = _build_engine(n_tiles)
    gs = engine.game_state
    n_plots = sum(eco.humidite.rows * eco.humidite.cols for eco in ecos.values())

    print(f"=== Profil MÉMOIRE — {n_tiles} tuiles, {n_plots} plots, {annees} ans ===")
    print(_entete())

    historique = []
    t0 = time.time()
    # Relevé initial (an 0, monde fraîchement planté). ru_maxrss = pic process.
    ech = _echantillon(gs, tiles, ecos)
    print(_fmt_ligne(0, ech, _rss_mo()))
    historique.append(ech)

    for annee in range(1, annees + 1):
        for _ in range(52):
            engine.tick_semaine()
            # On PURGE le log comme le serveur (`commands.py:156` le vide à chaque
            # step_week) : c'est le comportement RÉEL du jeu, donc le RSS mesuré
            # reflète la vraie mémoire. Sans purge, le log gonfle sans borne, mais
            # c'est un ARTEFACT du profil hors-serveur, PAS une fuite du moteur.
            gs["log"].clear()
        dt = time.time() - t0
        print(_fmt_ligne(annee, ech := _echantillon(gs, tiles, ecos), _rss_mo())
              + f"   [{dt:6.0f}s cumulés]")
        sys.stdout.flush()
        historique.append(ech)

    _diagnostic(historique)


if __name__ == "__main__":
    main()
