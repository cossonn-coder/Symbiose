# SYMBIOSE — tools/bancs/culture_depuis_rien.py
# LE BANC « X DEPUIS RIEN » (D87 tronçon ⑤). Déroule la chaîne moyens-fins complète
# « faire ADVENIR une culture depuis rien » pour N'IMPORTE QUELLE espèce, FORCE chaque
# branche de l'arbre de résolution (banque / magazine / impasse) et compose un RÉCIT à
# partir du LOG FILTRÉ (trace.py + filtre.py). C'est la démo que Nico veut : une matrice
# de test ET un révélateur de bugs bio par espèce (Q8 — une espèce qui meurt tôt ressort
# en `partiel`/`impasse`, ce n'est PAS un bug du banc).
#
# EXTERNE au moteur (invariant H2) : `engine.tick_semaine()` puis `automate.jouer_tick`.
# L'automate n'est JAMAIS dans le tick → golden intact. Instrument de DEV, pas un test
# golden. On ne simule qu'une poignée d'années (JAMAIS 500 ans).
#
# « DEPUIS RIEN » — pour une branche FORCÉE, on remet le monde à plat pour l'espèce :
# on retire ses cultivées vivantes, on repart d'une banque VIDE, puis on ouvre la seule
# porte voulue (graine déposée / offre magazine / rien). Le placement, l'achat et la
# levée restent DÉTERMINISTES (zéro RNG) → deux runs à entrées égales = log identique
# (oracle). `source="auto"` ne force RIEN (ce qui est disponible dans la config).
#
# RÉCIT — on filtre le journal par `objectif_id` (PAS par `espece`) : les gestes CRÉATIFS
# sont tracés en ligne `geste` legacy dont `espece=None` (la position vit dans `cible`) ;
# seul `objectif_id` rattache TOUTE la chaîne (plan/geste/veille/résultat) à l'objectif.
# Les impasses (`objectif_id=None`, cible `sp#id`) sont ramassées à part.
#
# VIGUEUR (dev) — la voie magazine coûte `COUT_MAGAZINE=120` ; or en régime LIBRE le
# solde est plafonné à `MAX_BASE=100` au moment où le planificateur sonde (avant le
# rehaussement de fin de tick). On PROVISIONNE donc le joueur (dev, comme le grant de
# palier) pour que la branche magazine soit ATTEIGNABLE — le banc éprouve la CHAÎNE, pas
# l'économie de Vigueur (cf. finding remonté à Nico).
#
# Usage (depuis data/code/) :
#   python3 -m tools.bancs.culture_depuis_rien [--espece E] [--quantite N]
#       [--source auto|banque|magazine|aucune] [--cout-vigueur] [--nb-plants K]
#       [--annees A] [--config smoke|propre|full] [--matrice]

from __future__ import annotations
import argparse
from dataclasses import replace

from tools.jardinier_auto import (JardinierAutomate, LIBRE, marquer_jardin_cultive,
                                   Objectif, ajouter_objectif, filtrer, trier, rendre)
from tools.jardinier_auto.objectifs import classe_cible, progression, est_accompli
from tools.jardinier_auto.trace import journal
from sim import maitrise, vigueur as V
from sim.magazine import SEUIL_MAGAZINE, COUT_MAGAZINE
from sim.seeds import Seed, PlayerSeedBank

SOURCES = ("auto", "banque", "magazine", "aucune")
# Vigueur provisionnée (dev) pour rendre la branche magazine atteignable (voir en-tête).
VIGUEUR_BANC = COUT_MAGAZINE * 3


def _build_engine(config: str, seed: int):
    """Monte le monde `config` via `SimServer.cmd_init` (fabrique du F5) — même patron
    que les bancs frères (automate_demo, jardin_tenu). `smoke` (2 tuiles) est LÉGER et
    rapide (~5 s / 2 ans) → défaut du banc ; `propre`/`full` sont plus lourds."""
    from tools.simserver.server import SimServer
    srv = SimServer()
    rep = srv.cmd_init({"config": config, "seed": seed})
    if not rep.get("ok"):
        raise RuntimeError(f"cmd_init a échoué : {rep}")
    return srv.engine


def _preparer_depuis_rien(engine, espece: str, source: str, quantite: int) -> None:
    """Met le monde « depuis rien » pour `espece` et OUVRE la seule porte voulue (T4 :
    tout déterministe, zéro RNG). `auto` ne force rien (état de la config). Les autres
    branches : retirent les cultivées vivantes de l'espèce, repartent banque VIDE,
    provisionnent la Vigueur, puis —
      - `banque`   : déposent `quantite` graines (de quoi re-semer) ;
      - `magazine` : accordent le palier 3 à l'espèce (sa famille ouvre l'offre) ;
      - `aucune`   : rien → l'objectif finira en impasse HONNÊTE (chaînon manquant)."""
    if source == "auto":
        return
    gs = engine.game_state
    player = gs["current_player"]
    cls = classe_cible(espece)
    for tile in engine.tiles:
        tile.plants[:] = [p for p in tile.plants if p.plant_class is not cls]
    gs["player_seed_bank"] = PlayerSeedBank()
    V.ensure_player(gs, player)
    gs["vigueur"][player] = {"courante": VIGUEUR_BANC, "max_base": VIGUEUR_BANC}
    if source == "banque":
        for _ in range(quantite):
            gs["player_seed_bank"].add(Seed(species=espece))
    elif source == "magazine":
        st = maitrise.ensure_player_maitrise(gs, player)
        st["objets"][espece] = {"palier": SEUIL_MAGAZINE, "preuves": 0.0}


def _composer_recit(gs: dict, oid: str, espece: str, quantite: int,
                    niveau_max: int) -> dict:
    """Lit le journal FILTRÉ et compose le récit de la chaîne (lecture seule). Rattache
    par `objectif_id` (chaîne) + ramasse les impasses par `cible` (`sp#id`). Renvoie un
    dict consommable par le rendu ET par les tests (matrice / oracle)."""
    jr = journal(gs)
    chaine = trier(filtrer(jr, objectif_id=oid, niveau_max=niveau_max))
    # Impasses `objectif_id=None` mais cible `sp#oid` (planification.py / boucle.py).
    impasses = [l for l in jr if l.get("categorie") == "impasse"
                and str(l.get("cible", "")).endswith(f"#{oid}")]
    gestes: dict[str, int] = {}
    for l in chaine:
        if l.get("categorie") == "geste":
            gestes[l["geste"]] = gestes.get(l["geste"], 0) + 1
    recit = {
        "espece": espece, "quantite": quantite,
        "progression": progression(gs, oid),
        "accompli": est_accompli(gs, oid),
        "fruitier": bool(getattr(classe_cible(espece), "fruitier", False)),
        "chaine": [rendre(l) for l in chaine],
        "gestes": gestes,
        "favoriser": gestes.get("favoriser_auxiliaire", 0),
        "impasses": [l.get("cause") for l in impasses],
    }
    recit["issue"] = _issue(recit)
    return recit


def _issue(recit: dict) -> str:
    """Classe l'issue de la chaîne (ordre : accompli > partiel > geste amorcé > impasse
    honnête > inerte). Les impasses transitoires `objectif_inatteignable` ne masquent
    JAMAIS un geste réellement joué → les gestes priment sur les impasses."""
    q, p = recit["quantite"], recit["progression"]
    if recit["accompli"]:
        return f"accompli {p}/{q}"
    if p > 0:
        return f"partiel {p}/{q}"
    if recit["gestes"].get("planter"):
        return "en_cours:semé (pas de récolte)"
    if recit["gestes"].get("acheter_magazine"):
        return "en_cours:acheté (pas semé)"
    for cause in ("chainon_manquant", "niche_defavorable", "objectif_inatteignable"):
        if cause in recit["impasses"]:
            return f"impasse:{cause}"
    return "inerte"


def banc_culture_depuis_rien(espece: str, quantite: int = 5, source_graine: str = "auto",
                             cout_vigueur: bool = False, nb_plants=None, annees: int = 2,
                             config: str = "smoke", seed: int = 0x5AB1057E,
                             verbose: bool = True) -> dict:
    """Déroule « faire advenir `quantite` × `recolter espece` depuis rien » et renvoie le
    récit (dict). `source_graine ∈ SOURCES` force une branche de l'arbre. `cout_vigueur`
    → `paie_vigueur` (défaut False = coût 0, preset LIBRE). `nb_plants` → surcharge
    `nb_plants_cible` (défaut `min(quantite,3)`). PURE côté golden (hors tick, opt-in)."""
    if source_graine not in SOURCES:
        raise ValueError(f"source_graine ∈ {SOURCES} (reçu {source_graine!r})")
    engine = _build_engine(config, seed)
    gs = engine.game_state
    player = gs["current_player"]
    _preparer_depuis_rien(engine, espece, source_graine, quantite)
    marquer_jardin_cultive(engine, player)
    oid = f"recolter:{quantite}:{espece}"
    ajouter_objectif(gs, Objectif(geste="recolter", quantite=quantite, cible=espece, id=oid))
    profil = replace(LIBRE, paie_vigueur=cout_vigueur, nb_plants_cible=nb_plants)
    automate = JardinierAutomate(profil)
    for _ in range(annees * 52):
        engine.tick_semaine()
        automate.jouer_tick(engine)
    recit = _composer_recit(gs, oid, espece, quantite, niveau_max=profil.verbosite_log)
    if verbose:
        _imprimer(recit, source_graine, cout_vigueur, config, annees)
    return recit


def _imprimer(recit: dict, source: str, cout_vigueur: bool, config: str, annees: int) -> None:
    """Imprime le récit d'un run (chaîne déroulée + issue + note C2 fruitier)."""
    print(f"=== « {recit['espece']} depuis rien » — source={source}, "
          f"quantite={recit['quantite']}, cout_vigueur={cout_vigueur}, "
          f"config={config}, {annees} ans ===")
    print(f"  fruitier={recit['fruitier']} "
          f"→ but satisfait par {'FRUIT mûr' if recit['fruitier'] else 'maturité végétative'} (C2)")
    print(f"  chaîne déroulée ({len(recit['chaine'])} lignes) :")
    for ligne in recit["chaine"][:16]:
        print(f"    {ligne}")
    if len(recit["chaine"]) > 16:
        print(f"    … (+{len(recit['chaine']) - 16} lignes)")
    verbes = ", ".join(f"{v}×{n}" for v, n in sorted(recit["gestes"].items()))
    print(f"  gestes créatifs : {verbes or '(aucun)'}")
    if recit["fruitier"]:
        print(f"  sous-chaîne pollinisation (favoriser_auxiliaire) : "
              f"×{recit['favoriser']} (0 = habitat déjà présent sur la tuile)")
    print(f"  ➜ ISSUE : {recit['issue']}")


# --- Matrice : quelques espèces × sources, tabule les issues (Q8) -----------------

# Défaut : un non-fruitier robuste + un fruitier (chaîne + post-condition organe-typée).
# `tomate` incluse VOLONTAIREMENT (mildiou familial, [[tomate-mort-precoce]]) : elle
# ressort en `partiel`/`impasse` → le banc RÉVÈLE le fait bio, il ne le masque pas.
ESPECES_MATRICE = ("haricot", "basilic", "courgette", "tomate")


def matrice(especes=ESPECES_MATRICE, sources=("banque", "magazine", "aucune"),
            quantite: int = 5, annees: int = 2, config: str = "smoke",
            cout_vigueur: bool = False) -> list:
    """Balaie `especes × sources`, tabule les issues. Une espèce qui meurt tôt ressort
    par ligne (Q8) — c'est de la DONNÉE bio, pas un bug du banc."""
    print(f"=== MATRICE culture-depuis-rien — {len(especes)}×{len(sources)}, "
          f"quantite={quantite}, {annees} ans, config={config} ===")
    print(f"  {'espèce':<11}{'source':<10}{'fruitier':<9}{'issue':<28}gestes")
    lignes = []
    for espece in especes:
        for source in sources:
            r = banc_culture_depuis_rien(espece, quantite=quantite, source_graine=source,
                                         cout_vigueur=cout_vigueur, annees=annees,
                                         config=config, verbose=False)
            verbes = " ".join(f"{v}×{n}" for v, n in sorted(r["gestes"].items()))
            print(f"  {espece:<11}{source:<10}{str(r['fruitier']):<9}{r['issue']:<28}{verbes}")
            lignes.append(r)
    return lignes


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Banc « X depuis rien » — chaîne moyens-fins de l'automate (D87 ⑤).")
    ap.add_argument("--espece", default="haricot", help="espèce à faire advenir")
    ap.add_argument("--quantite", type=int, default=5, help="objectif recolter ×N")
    ap.add_argument("--source", default="banque", choices=SOURCES,
                    help="branche forcée de l'arbre (défaut banque)")
    ap.add_argument("--cout-vigueur", action="store_true",
                    help="paie_vigueur=True (coût normal) ; défaut = coût 0 (LIBRE)")
    ap.add_argument("--nb-plants", type=int, default=None,
                    help="surcharge nb_plants_cible (défaut min(N,3))")
    ap.add_argument("--annees", type=int, default=2, help="années simulées (PAS 500 !)")
    ap.add_argument("--config", default="smoke", choices=["smoke", "propre", "full"])
    ap.add_argument("--matrice", action="store_true",
                    help="balaie ESPECES_MATRICE × sources et tabule les issues (Q8)")
    args = ap.parse_args()
    if args.matrice:
        matrice(quantite=args.quantite, annees=args.annees, config=args.config,
                cout_vigueur=args.cout_vigueur)
    else:
        banc_culture_depuis_rien(args.espece, quantite=args.quantite,
                                 source_graine=args.source, cout_vigueur=args.cout_vigueur,
                                 nb_plants=args.nb_plants, annees=args.annees,
                                 config=args.config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
