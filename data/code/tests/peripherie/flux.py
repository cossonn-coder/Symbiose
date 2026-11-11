"""
SYMBIOSE — tests/peripherie/flux.py
TRONÇON ③ — pluie de graines, nappe de berge, corridor de lisière : ce que la
ceinture fait TRAVERSER la limite du jardin. Spec
`docs/champs/peripherie/conception_peripherie.md` §3.4/§4.2 + kickoff
`sprints/champs/peripherie/sprint_peripherie/03_graines_eau_corridor.md`.

  I. GRAINES      — un secteur `friche` ensemence la rangée de SON bord en `pioneer`,
                    décroissant avec la distance, NUL au-delà de la portée ; le bord
                    opposé est intact et, sans ceinture, la banque ne bouge pas ;
  J. BERGE        — `ligne_eau > 0` gorge la rangée du bord (pores puis lame de
                    surface) et fait ÉMERGER le marécage ; `< 0` l'assèche ; sans
                    ceinture, hydrologie bit-identique ;
  K. CORRIDOR     — `eco.lisiere` est un champ DU MILIEU (gradient, max entre bords,
                    mémoïsé, None au repos) et une guilde à `lisiere_w = 0.0` est
                    inchangée AU BIT PRÈS — c'est ce qui distingue un champ écologique
                    d'un bonus d'habitat (philo #2).

Plus la géométrie PARTAGÉE par les trois flux (`plots_de_bord`) : c'est elle qui
garantit qu'on ne balaie jamais la grille entière pour un effet de bord.
"""
from fields.seedbank import SeedBank
from fields.ecofields import init_eco
from fields.population import PopulationField, build_population_specs
from fields.population.registry import build_pollinator_specs
from fields.population.spec import TrophicSpec
from fields.peripherie import (
    COTES, NORD, SUD, OUEST, secteur_neutre, plots_de_bord,
)

from tests.peripherie.harness import check, COTE_PLOTS, _neutre, _foret, _secteur


# --- I. Pluie de graines (§4.2) --------------------------------------------
def test_graines():
    print("\n[I] Pluie de graines — la matrice ensemence les bords (canal #3)")
    friche_nord = _secteur(NORD, type="friche", densite_ligneuse=0.15)

    # Grille au coin nord-ouest du monde : elle touche le bord NORD (r=0) et,
    # latéralement, le bord OUEST — on lit donc une colonne assez à l'est (c=8)
    # pour ne mesurer QUE l'apport du nord.
    banque = SeedBank(12, 12)
    temoin = SeedBank(12, 12)
    for _ in range(300):
        banque.tick_aging()
        banque.tick_apport_peripherie(friche_nord)
        temoin.tick_aging()                       # même vieillissement, aucun apport
    col = 8
    profil = [banque.get(r, col, "pioneer") for r in range(6)]
    fond = temoin.get(0, col, "pioneer")

    check("friche au NORD ⇒ pioneer enrichi sur la rangée du bord",
          profil[0] > 5.0 * fond, f"{profil[0]:.4f} contre un fond de {fond:.4f}")
    check("décroissance STRICTE avec la distance au bord",
          all(profil[i] > profil[i + 1] for i in range(3)),
          " > ".join(f"{v:.4f}" for v in profil[:4]))
    check("NUL au-delà de la portée (4 plots) — pas de balayage de grille",
          profil[4] == fond and profil[5] == fond, f"r4 = {profil[4]:.4f}")
    check("bord OPPOSÉ (sud) intact : la friche du nord ne sème pas partout",
          banque.get(11, col, "pioneer") == fond)
    check("aucun autre archétype touché (une friche sème du pionnier)",
          banque.get(0, col, "grass") == temoin.get(0, col, "grass")
          and banque.get(0, col, "competitor") == temoin.get(0, col, "competitor"))

    # Neutralité : sans ceinture l'apport n'est même pas appelé (golden). MÊME
    # `tile_id` de part et d'autre — `init_eco` hétérogénéise om_stable/altitude
    # depuis le tile_id, deux identités donneraient deux sols différents.
    eco_a, eco_b = init_eco("neutre", 12, 12), init_eco("neutre", 12, 12)
    for _ in range(6):
        eco_a.tick_seed_bank([])
        eco_b.tick_seed_bank([], ceinture=None)
    check("sans ceinture ⇒ banque de graines bit-identique",
          eco_a.seed_bank.data == eco_b.seed_bank.data)

    # Une forêt sème du competitor ∝ sa densité (une lisière claire sème peu).
    dense = SeedBank(12, 12)
    claire = SeedBank(12, 12)
    for _ in range(50):
        dense.tick_apport_peripherie(_secteur(NORD, type="foret", essence="hetre",
                                              hauteur_canopee=1500.0,
                                              densite_ligneuse=0.95))
        claire.tick_apport_peripherie(_secteur(NORD, type="foret", essence="hetre",
                                               hauteur_canopee=1500.0,
                                               densite_ligneuse=0.55))
    check("forêt ⇒ competitor, apport ∝ densite_ligneuse",
          dense.get(0, col, "competitor") > claire.get(0, col, "competitor") > 0.01,
          f"dense {dense.get(0, col, 'competitor'):.4f} > "
          f"claire {claire.get(0, col, 'competitor'):.4f}")
    check("rivière/falaise ne sèment RIEN",
          _apport_nul(dict(secteur_neutre(NORD), type="riviere", ligne_eau=30.0))
          and _apport_nul(dict(secteur_neutre(NORD), type="falaise",
                               altitude_relative=800.0)))


def _apport_nul(secteur):
    """Vrai si ce SEUL secteur ne dépose STRICTEMENT rien dans une banque neuve.
    On lui passe une ceinture d'un seul élément : sur une ceinture complète, les
    trois autres bords sont des prairies — qui, elles, sèment (à raison)."""
    a, b = SeedBank(8, 8), SeedBank(8, 8)
    a.tick_apport_peripherie([secteur])
    return a.data == b.data


# --- J. Nappe de berge (§3.4) ---------------------------------------------
def _berge(ligne_eau, ticks=80):
    """Une tuile-monde soumise à une rivière au NORD, après N ticks d'hydrologie
    complète (berge → hydro → ruissellement → marais), sol de départ mi-humide."""
    eco = init_eco("b", COTE_PLOTS, COTE_PLOTS)
    for r in range(COTE_PLOTS):
        for c in range(COTE_PLOTS):
            eco.humidite.set(r, c, 0.6)
    ceinture = _secteur(NORD, type="riviere", ligne_eau=ligne_eau)
    for _ in range(ticks):
        eco.tick_berge(ceinture)
        eco.tick_hydrology("terre")
        eco.tick_ruissellement()
        eco.tick_marais()
    return eco


def test_berge():
    print("\n[J] Nappe de berge — condition aux limites, marécage ÉMERGENT")
    c = COTE_PLOTS // 2
    haute = _berge(40.0)
    basse = _berge(-40.0)
    loin = haute.humidite.at_plot(10, c)          # hors portée (3 plots)

    check("ligne d'eau HAUTE ⇒ le bord se gorge",
          haute.humidite.at_plot(0, c) > 3.0 * loin,
          f"bord {haute.humidite.at_plot(0, c):.3f} contre {loin:.3f} à 5 m")
    check("ligne d'eau BASSE ⇒ le bord s'assèche (le lit appelle l'eau)",
          basse.humidite.at_plot(0, c) < 0.2 * loin,
          f"bord {basse.humidite.at_plot(0, c):.3f} contre {loin:.3f} à 5 m")
    check("pores saturés ⇒ l'eau AFFLEURE en lame de surface",
          haute.eau_surface.at_plot(0, c) > 0.0,
          f"lame {haute.eau_surface.at_plot(0, c):.3f}")
    check("MARÉCAGE émergent près du bord (aucun script : lame → mémoire → état)",
          haute.est_marais(0, c) and not haute.est_marais(10, c))
    check("hors portée (au-delà de 3 plots) : humidité inchangée par la berge",
          abs(haute.humidite.at_plot(10, c) - basse.humidite.at_plot(10, c)) < 1e-12)

    # Neutralité : sans ceinture (ou sans rivière) l'hydrologie est bit-identique.
    # MÊME `tile_id` : le sol d'init dépend de l'identité de la tuile.
    eco_a, eco_b = init_eco("neutre", 12, 12), init_eco("neutre", 12, 12)
    for _ in range(10):
        eco_a.tick_hydrology("terre")
        eco_b.tick_berge(None)
        eco_b.tick_berge(_neutre())               # 4 prairies : aucune rivière
        eco_b.tick_hydrology("terre")
    check("sans ceinture / sans rivière ⇒ humidité bit-identique",
          eco_a.humidite.data == eco_b.humidite.data
          and eco_a.eau_surface.data == eco_b.eau_surface.data)


# --- K. Corridor de lisière (§4.2) ----------------------------------------
def _grille_nulle(eco, tile, plants):
    """resource_fn / habitat_fn qui ne rapportent RIEN : la capacité mesurée ne
    vient alors QUE du terme de lisière (isolement de la variable testée)."""
    return [[0.0] * eco.cols for _ in range(eco.rows)]


def _spec_temoin(lisiere_w):
    return TrophicSpec(name="temoin", category="test", salt=7,
                       resource_fn=_grille_nulle, habitat_fn=_grille_nulle,
                       lisiere_w=lisiere_w)


def test_corridor():
    print("\n[K] Corridor de lisière — un champ DU MILIEU, pas un bonus (#2)")
    foret_nord = _foret(NORD, hauteur=1500.0, densite=0.9)

    # 1. Le champ : gradient depuis le bord, MAX entre bords, mémoïsé, lazy.
    eco = init_eco("l", COTE_PLOTS, COTE_PLOTS)
    check("sans ceinture : eco.lisiere reste None (aucune allocation)",
          eco.lisiere is None)
    eco.maj_lisiere(foret_nord)
    col = COTE_PLOTS // 2
    grad = [eco.lisiere.at_plot(r, col) for r in range(10)]
    check("gradient décroissant depuis le bord boisé",
          all(grad[i] > grad[i + 1] for i in range(7)),
          " > ".join(f"{v:.2f}" for v in grad[:4]))
    check("borné [0,1] et nul loin du bord",
          max(grad) <= 1.0 and eco.lisiere.at_plot(COTE_PLOTS // 2, col) == 0.0)
    # Combinaison par MAX : un coin forêt+forêt ne vaut pas deux lisières.
    deux = _foret(NORD, densite=0.9)
    deux[OUEST].update(type="foret", essence="charme",
                       hauteur_canopee=1500.0, densite_ligneuse=0.9)
    eco_deux = init_eco("d", COTE_PLOTS, COTE_PLOTS)
    eco_deux.maj_lisiere(deux)
    check("deux bords boisés : le coin est un MAX, jamais une somme",
          abs(eco_deux.lisiere.at_plot(0, 0) - eco.lisiere.at_plot(0, col)) < 1e-12,
          f"coin {eco_deux.lisiere.at_plot(0, 0):.3f}")
    # Mémoïsation : ceinture figée ⇒ pas de reconstruction (marque conservée).
    eco.lisiere.data[0][0] = -42.0
    eco.maj_lisiere(foret_nord)
    check("ceinture figée ⇒ champ mémoïsé (aucun recalcul dans le tick)",
          eco.lisiere.data[0][0] == -42.0)
    coupe = [dict(s) for s in foret_nord]
    coupe[NORD]["type"] = "prairie"
    eco.maj_lisiere(coupe)
    check("type de secteur changé ⇒ recalcul (une coupe du ④ sera VUE)",
          eco.lisiere.data[0][0] != -42.0)
    eco.maj_lisiere(None)
    check("ceinture retirée ⇒ eco.lisiere repasse à None", eco.lisiere is None)

    # 2. La réponse : elle est DÉCLARÉE par guilde, pas offerte à toutes.
    eco_l = init_eco("g", COTE_PLOTS, COTE_PLOTS)
    eco_l.maj_lisiere(foret_nord)
    eco_0 = init_eco("g", COTE_PLOTS, COTE_PLOTS)      # même tuile, sans lisière
    r_bord, r_loin = 0, COTE_PLOTS // 2

    sensible_l = PopulationField(_spec_temoin(0.30), COTE_PLOTS, COTE_PLOTS)
    sensible_0 = PopulationField(_spec_temoin(0.30), COTE_PLOTS, COTE_PLOTS)
    sourde_l = PopulationField(_spec_temoin(0.0), COTE_PLOTS, COTE_PLOTS)
    sourde_0 = PopulationField(_spec_temoin(0.0), COTE_PLOTS, COTE_PLOTS)
    for _ in range(40):
        sensible_l.tick(eco_l, None, [], [])
        sensible_0.tick(eco_0, None, [], [])
        sourde_l.tick(eco_l, None, [], [])
        sourde_0.tick(eco_0, None, [], [])

    check("guilde à lisiere_w > 0 : capacité gagnée PRÈS du bord boisé",
          sensible_l.at_plot(r_bord, col) > sensible_l.at_plot(r_loin, col),
          f"bord {sensible_l.at_plot(r_bord, col):.4f} > "
          f"centre {sensible_l.at_plot(r_loin, col):.4f}")
    check("… et rien au centre : la lisière n'arrose pas tout le jardin",
          sensible_l.at_plot(r_loin, col) == sensible_0.at_plot(r_loin, col))
    check("guilde à lisiere_w = 0.0 : INCHANGÉE AU BIT PRÈS (golden)",
          sourde_l.data == sourde_0.data)

    # 3. Le registre : les bons noms, et surtout PAS les ravageurs (#2).
    poids = {s.name: s.lisiere_w
             for s in build_population_specs() + build_pollinator_specs()}
    attendus = ("carabe", "merle", "herisson", "chrysope", "coccinelle", "syrphe",
                "geai", "ecureuil")   # zoochorie ⑤ : disperseurs venus du bois
    check("les auxiliaires liés au bord portent un poids de lisière",
          all(poids[n] > 0.0 for n in attendus),
          " · ".join(f"{n} {poids[n]}" for n in attendus))
    muets = [n for n, w in poids.items() if n not in attendus and w != 0.0]
    check("toutes les autres guildes restent à 0.0 (pucerons compris)",
          not muets, f"{len(poids) - len(attendus)} guildes muettes")


# --- Géométrie partagée des trois flux ------------------------------------
def test_plots_de_bord():
    print("\n[③bis] plots_de_bord — la bande, jamais la grille entière")
    for cote in COTES:
        atteints = list(plots_de_bord(cote, COTE_PLOTS, COTE_PLOTS,
                                      (0.0, 0.0), 200.0))
        rangs = {(r if cote in (NORD, SUD) else c) for r, c, _ in atteints}
        check(f"côté {cote} : 4 rangées atteintes sur {COTE_PLOTS}",
              len(rangs) == 4, f"rangs {sorted(rangs)}")
    poids = [p for _, _, p in plots_de_bord(NORD, COTE_PLOTS, COTE_PLOTS,
                                            (0.0, 0.0), 200.0)]
    check("poids ∈ ]0,1] et décroissants", max(poids) <= 1.0 and min(poids) > 0.0)
    # Une tuile trop loin du bord ne reçoit RIEN (la ceinture n'agit qu'aux bords).
    loin = list(plots_de_bord(NORD, 4, 4, (900.0, 900.0), 200.0))
    check("tuile au centre du jardin : aucun plot atteint", loin == [])
    check("portée nulle : générateur vide (aucun coût)",
          list(plots_de_bord(SUD, 4, 4, (0.0, 0.0), 0.0)) == [])
