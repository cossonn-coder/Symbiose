"""
SYMBIOSE — tests/test_quetes.py
Golden JOUEUR du SYSTÈME DE QUÊTES (D79, tronçon ①) — famille de conditions
`recolte_cumulee`, comptée par HOOK sur le geste joueur.

Distinct du golden ÉCOLOGIQUE (`test_golden.py`) : le moteur tourne sans joueur ni
quête → `notifier_geste` n'est jamais appelé → golden NEUTRE (vérifié à part).

Vérifie (kickoff ①) :
  1. `recolte_cumulee(recolter, 3, "tomate")` : 3 récoltes → accomplie + événement
     émis au log (canal ledger).
  2. Une récolte d'une AUTRE espèce n'incrémente pas.
  3. Un geste d'un AUTRE verbe n'incrémente pas.
  4. Ordre déterministe (quêtes actives triées par `id`).
  5. Opt-in strict : aucune quête → aucune clé `quetes` → notifier no-op.

Usage (depuis data/code/) :
  python3 -m tests.test_quetes
"""
from sim import quetes as Q
from plants.catalogue import PLANT_CATALOGUE

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


class _FakePlante:
    """Plante-cible minimale : le hook ne lit que `plant_class` (comme
    `objectifs.sert`). On évite ainsi tout montage de monde. Les conditions d'état
    (②) lisent en plus `is_alive` / `current_height` (cm) / `floraison` — attributs
    plats posés ici en duck-typing (le vrai `PlantInstance` les expose en propriétés)."""

    def __init__(self, cle, is_alive=True, current_height=0.0, floraison=0.0):
        self.plant_class = PLANT_CATALOGUE[cle]
        self.is_alive = is_alive
        self.current_height = current_height
        self.floraison = floraison


class _FakeTile:
    """Tuile-snapshot minimale : `evaluer_etat` n'itère que `tile.plants`."""

    def __init__(self, plants):
        self.plants = list(plants)


# ---------------------------------------------------------------------------
# 1. 3 récoltes de tomate → accomplie + événement émis
# ---------------------------------------------------------------------------

def test_accomplissement_et_evenement():
    print("\n[1] recolte_cumulee(recolter, 3, tomate) : 3 récoltes → accomplie + log")
    gs = {"week": 5, "log": []}
    q = Q.Quete(id="q_patates", donneur="Marcel",
                condition=("recolte_cumulee", "recolter", 3, "tomate"))
    Q.ajouter_quete(gs, q)
    tomate = _FakePlante("tomate")
    for i in range(2):
        Q.notifier_geste(gs, "j", "recolter", tomate)
        check(f"après {i + 1} récolte(s), pas encore accomplie",
              not Q.est_accomplie(gs, "q_patates"),
              f"progression={Q.progression(gs, 'q_patates')}")
    Q.notifier_geste(gs, "j", "recolter", tomate)   # la 3ᵉ
    check("3ᵉ récolte → accomplie", Q.est_accomplie(gs, "q_patates"),
          f"progression={Q.progression(gs, 'q_patates')}")
    check("événement ✉ émis au log", any("✉" in l for l in gs["log"]),
          f"log={gs['log']}")
    check("quête accomplie sortie des actives", Q.quetes_actives(gs) == [])
    # Une récolte SUPPLÉMENTAIRE ne ré-incrémente pas (fenêtre close).
    Q.notifier_geste(gs, "j", "recolter", tomate)
    check("après clôture, la progression est figée",
          Q.progression(gs, "q_patates") == 3,
          f"progression={Q.progression(gs, 'q_patates')}")
    check("un seul événement émis (pas de re-déclenchement)",
          sum("✉" in l for l in gs["log"]) == 1)


# ---------------------------------------------------------------------------
# 2. Autre espèce → pas d'incrément
# ---------------------------------------------------------------------------

def test_autre_espece_ignoree():
    print("\n[2] récolte d'une AUTRE espèce → pas d'incrément")
    gs = {"week": 1, "log": []}
    Q.ajouter_quete(gs, Q.Quete(id="q", donneur="M",
                    condition=("recolte_cumulee", "recolter", 2, "tomate")))
    Q.notifier_geste(gs, "j", "recolter", _FakePlante("basilic"))
    check("basilic ne sert pas une quête de tomate",
          Q.progression(gs, "q") == 0, f"progression={Q.progression(gs, 'q')}")


# ---------------------------------------------------------------------------
# 3. Autre verbe → pas d'incrément
# ---------------------------------------------------------------------------

def test_autre_verbe_ignore():
    print("\n[3] geste d'un AUTRE verbe → pas d'incrément")
    gs = {"week": 1, "log": []}
    Q.ajouter_quete(gs, Q.Quete(id="q", donneur="M",
                    condition=("recolte_cumulee", "recolter", 2, "tomate")))
    Q.notifier_geste(gs, "j", "manger", _FakePlante("tomate"))
    check("manger ne sert pas une quête de récolte",
          Q.progression(gs, "q") == 0, f"progression={Q.progression(gs, 'q')}")


# ---------------------------------------------------------------------------
# 4. Ordre déterministe des quêtes actives
# ---------------------------------------------------------------------------

def test_ordre_deterministe():
    print("\n[4] quetes_actives triées par id (déterminisme)")
    gs = {"week": 1, "log": []}
    for qid in ("q_c", "q_a", "q_b"):
        Q.ajouter_quete(gs, Q.Quete(id=qid, donneur="M",
                        condition=("recolte_cumulee", "recolter", 1, "tomate")))
    ids = [q.id for q in Q.quetes_actives(gs)]
    check("ordre trié par id", ids == ["q_a", "q_b", "q_c"], f"ids={ids}")


# ---------------------------------------------------------------------------
# 5. Opt-in strict : aucune quête → notifier no-op
# ---------------------------------------------------------------------------

def test_opt_in_strict():
    print("\n[5] opt-in strict : aucune quête → aucune clé, notifier no-op")
    gs = {"week": 1, "log": []}
    Q.notifier_geste(gs, "j", "recolter", _FakePlante("tomate"))
    check("aucune clé 'quetes' créée par le seul hook", "quetes" not in gs)
    check("aucun événement émis", gs["log"] == [])


# ---------------------------------------------------------------------------
# 6. hauteur_min : snapshot, prédicat current_height (cm), mètres → cm
# ---------------------------------------------------------------------------

def _gs_snapshot(plants, week=3):
    return {"week": week, "log": [], "tiles": [_FakeTile(plants)]}


def test_hauteur_min():
    print("\n[6] hauteur_min(tournesol, 2 m) sur snapshot")
    q = Q.Quete(id="q_h", donneur="Léa",
                condition=("hauteur_min", "tournesol", 2.0))
    # En deçà (1 m = 100 cm < 200) → non accomplie, phrase diégétique sans chiffre.
    gs = _gs_snapshot([_FakePlante("tournesol", current_height=100.0)])
    Q.ajouter_quete(gs, q)
    Q.evaluer_etat(gs)
    check("1 m < 2 m → non accomplie", not Q.est_accomplie(gs, "q_h"))
    phrase = Q.avancement(gs, "q_h")
    check("phrase diégétique non vide et sans chiffre",
          phrase and not any(ch.isdigit() for ch in phrase), f"phrase={phrase!r}")
    # Au-delà (2,5 m = 250 cm ≥ 200) → accomplie après évaluation.
    gs = _gs_snapshot([_FakePlante("tournesol", current_height=250.0)])
    Q.ajouter_quete(gs, q)
    Q.evaluer_etat(gs)
    check("2,5 m ≥ 2 m → accomplie", Q.est_accomplie(gs, "q_h"))
    check("événement ✉ émis", any("✉" in l for l in gs["log"]))
    check("avancement d'une quête close = phrase de clôture",
          Q.avancement(gs, "q_h") and not any(c.isdigit() for c in Q.avancement(gs, "q_h")))


# ---------------------------------------------------------------------------
# 7. floraison_min : compte les pieds EN FLEUR (floraison ≥ SEUIL_FLEURI)
# ---------------------------------------------------------------------------

def test_floraison_min():
    print("\n[7] floraison_min(trefle, 3) : 3 trèfles en fleur")
    q = Q.Quete(id="q_f", donneur="Oncle",
                condition=("floraison_min", "trefle", 3))
    # 2 fleuris + 1 en dessous du seuil → non.
    gs = _gs_snapshot([_FakePlante("trefle", floraison=0.8),
                       _FakePlante("trefle", floraison=0.6),
                       _FakePlante("trefle", floraison=0.2)])
    Q.ajouter_quete(gs, q)
    Q.evaluer_etat(gs)
    check("2 < 3 fleuris → non accomplie", not Q.est_accomplie(gs, "q_f"),
          f"phrase={Q.avancement(gs, 'q_f')!r}")
    # 3 pieds au seuil → oui.
    gs = _gs_snapshot([_FakePlante("trefle", floraison=0.5) for _ in range(3)])
    Q.ajouter_quete(gs, q)
    Q.evaluer_etat(gs)
    check("3 fleuris (≥ 0.5) → accomplie", Q.est_accomplie(gs, "q_f"))


# ---------------------------------------------------------------------------
# 8. nombre_vivant_min : un mort ne compte pas
# ---------------------------------------------------------------------------

def test_nombre_vivant_min():
    print("\n[8] nombre_vivant_min(trefle, 4) : un mort ne compte pas")
    q = Q.Quete(id="q_n", donneur="Léa",
                condition=("nombre_vivant_min", "trefle", 4))
    gs = _gs_snapshot([_FakePlante("trefle") for _ in range(3)]
                      + [_FakePlante("trefle", is_alive=False)])
    Q.ajouter_quete(gs, q)
    Q.evaluer_etat(gs)
    check("3 vivants + 1 mort < 4 → non accomplie", not Q.est_accomplie(gs, "q_n"))
    gs = _gs_snapshot([_FakePlante("trefle") for _ in range(4)])
    Q.ajouter_quete(gs, q)
    Q.evaluer_etat(gs)
    check("4 vivants → accomplie", Q.est_accomplie(gs, "q_n"))


# ---------------------------------------------------------------------------
# 9. Cible absente du catalogue → non accomplie, phrase dédiée
# ---------------------------------------------------------------------------

def test_cible_absente():
    print("\n[9] cible hors catalogue (kiwi, D26) → non accomplie")
    q = Q.Quete(id="q_k", donneur="Enfant",
                condition=("hauteur_min", "kiwi", 5.0))
    gs = _gs_snapshot([])
    Q.ajouter_quete(gs, q)
    Q.evaluer_etat(gs)
    check("cible inconnue → jamais accomplie", not Q.est_accomplie(gs, "q_k"))
    check("phrase 'pas encore trouvé sa place'",
          "place" in Q.avancement(gs, "q_k"), f"phrase={Q.avancement(gs, 'q_k')!r}")


# ---------------------------------------------------------------------------
# 10. evaluer_etat : opt-in strict + n'écrit rien pour recolte_cumulee
# ---------------------------------------------------------------------------

def test_evaluer_etat_neutre():
    print("\n[10] evaluer_etat : opt-in + ignore recolte_cumulee")
    gs = {"week": 1, "log": [], "tiles": []}
    Q.evaluer_etat(gs)                       # aucune quête
    check("aucune clé 'quetes' créée", "quetes" not in gs)
    gs = _gs_snapshot([])
    Q.ajouter_quete(gs, Q.Quete(id="q", donneur="M",
                    condition=("recolte_cumulee", "recolter", 2, "tomate")))
    Q.evaluer_etat(gs)
    check("evaluer_etat ne clôt pas une quête cumulée",
          not Q.est_accomplie(gs, "q"))


# ---------------------------------------------------------------------------
# 11. Déclenchement : palier de maîtrise ouvre la bonne lettre
# ---------------------------------------------------------------------------

def test_declencheur_palier():
    print("\n[11] déclencheur palier : lavande palier 1 ouvre la lettre lavande")
    from sim import maitrise
    gs = {"week": 0, "log": []}
    ouverts = Q.evaluer_declencheurs(gs, "j")
    check("sans maîtrise, la lettre lavande (palier lavande 1) reste fermée",
          "lettre_lavande_amelie" not in ouverts, f"ouverts={ouverts}")
    check("la lettre d'emblée (déclencheur None) s'ouvre",
          "lettre_cageot_tomates" in ouverts)
    maitrise.decouvrir(gs, "j", "lavande")               # palier 0→1
    ouverts2 = Q.evaluer_declencheurs(gs, "j")
    check("lavande palier 1 → la lettre lavande s'ouvre",
          "lettre_lavande_amelie" in ouverts2, f"ouverts2={ouverts2}")
    check("une lettre déjà ouverte n'est pas reposée",
          "lettre_cageot_tomates" not in ouverts2)


# ---------------------------------------------------------------------------
# 12. Déclenchement : jalon de saison
# ---------------------------------------------------------------------------

def test_declencheur_saison():
    print("\n[12] déclencheur saison : tournesol s'ouvre à partir de la semaine 4")
    gs = {"week": 2, "log": []}
    check("semaine 2 < 4 → tournesol fermé",
          "lettre_tournesol_geant" not in Q.evaluer_declencheurs(gs, "j"))
    gs = {"week": 5, "log": []}
    check("semaine 5 ≥ 4 → tournesol ouvert",
          "lettre_tournesol_geant" in Q.evaluer_declencheurs(gs, "j"))


# ---------------------------------------------------------------------------
# 13. Plafond : aucune lettre n'arrive quand le plafond est plein
# ---------------------------------------------------------------------------

def test_plafond_bloque():
    print("\n[13] plafond plein → la (N+1)ᵉ lettre n'arrive pas")
    gs = {"week": 0, "log": []}
    # Sature le registre de PLAFOND quêtes actives factices (ids hors corpus).
    for i in range(Q.PLAFOND_QUETES_ACTIVES):
        Q.ajouter_quete(gs, Q.Quete(id=f"factice_{i}", donneur="M",
                        condition=("recolte_cumulee", "recolter", 1, "tomate")))
    ouverts = Q.evaluer_declencheurs(gs, "j")
    check("plafond plein → aucune lettre du corpus ne s'ouvre",
          ouverts == [], f"ouverts={ouverts}")
    check("aucune lettre du corpus n'a été posée",
          all(qid.startswith("factice_") for qid in gs["quetes"]))


# ---------------------------------------------------------------------------
# 14. Déterminisme : même état → même séquence d'ouverture
# ---------------------------------------------------------------------------

def test_declenchement_deterministe():
    print("\n[14] même état → même séquence de lettres")
    a = Q.evaluer_declencheurs({"week": 6, "log": []}, "j")
    b = Q.evaluer_declencheurs({"week": 6, "log": []}, "j")
    check("séquence d'ouverture reproductible", a == b, f"a={a} b={b}")
    check("triée par id (déterminisme)", a == sorted(a), f"a={a}")


# ---------------------------------------------------------------------------
# 15. Récompense graine : la banque est créditée, une seule fois
# ---------------------------------------------------------------------------

def test_recompense_graine():
    print("\n[15] récompense graine → banque créditée (idempotent)")
    from sim.seeds import PlayerSeedBank
    gs = {"week": 1, "log": [], "player_seed_bank": PlayerSeedBank()}
    q = Q.Quete(id="q_g", donneur="Léa",
                condition=("recolte_cumulee", "recolter", 1, "tournesol"),
                recompense=("graine", "tournesol"))
    Q.ajouter_quete(gs, q)
    avant = gs["player_seed_bank"].count("tournesol")
    Q.notifier_geste(gs, "j", "recolter", _FakePlante("tournesol"))  # accomplit
    Q.remettre_recompenses(gs, "j")
    check("banque +1 graine de tournesol",
          gs["player_seed_bank"].count("tournesol") == avant + 1)
    Q.remettre_recompenses(gs, "j")                                  # rappel
    check("récompense versée une seule fois (idempotent)",
          gs["player_seed_bank"].count("tournesol") == avant + 1)


# ---------------------------------------------------------------------------
# 16. Récompense Vigueur : crédit joueur (pas un buff plante)
# ---------------------------------------------------------------------------

def test_recompense_vigueur():
    print("\n[16] récompense vigueur → crédit joueur")
    from sim import vigueur
    gs = {"week": 1, "log": []}
    vigueur.spend(gs, "j", 50.0)                     # descend sous le plafond
    avant = vigueur.ensure_player(gs, "j")["courante"]
    q = Q.Quete(id="q_v", donneur="M",
                condition=("recolte_cumulee", "recolter", 1, "tomate"),
                recompense=("vigueur", 30.0))
    Q.ajouter_quete(gs, q)
    Q.notifier_geste(gs, "j", "recolter", _FakePlante("tomate"))
    Q.remettre_recompenses(gs, "j")
    check("Vigueur créditée de +30",
          vigueur.ensure_player(gs, "j")["courante"] == avant + 30.0,
          f"avant={avant} après={vigueur.ensure_player(gs, 'j')['courante']}")


# ---------------------------------------------------------------------------
# 17. Atteignabilité : une lettre peut viser une espèce absente (kiwi, D26)
# ---------------------------------------------------------------------------

def test_est_atteignable():
    print("\n[17] est_atteignable : kiwi non, tomate oui")
    check("cible kiwi (absente) → inatteignable",
          not Q.est_atteignable(("hauteur_min", "kiwi", 5.0)))
    check("cible tomate (récolte) → atteignable",
          Q.est_atteignable(("recolte_cumulee", "recolter", 3, "tomate")))


# ---------------------------------------------------------------------------
# 18. remettre_recompenses : opt-in strict + plaisir pur (None) sans effet
# ---------------------------------------------------------------------------

def test_remettre_opt_in():
    print("\n[18] remettre_recompenses : opt-in + plaisir pur no-op")
    gs = {"week": 1, "log": []}
    check("aucune quête → no-op, aucune clé créée",
          Q.remettre_recompenses(gs, "j") == [] and "quetes" not in gs)
    q = Q.Quete(id="q_p", donneur="M",
                condition=("recolte_cumulee", "recolter", 1, "tomate"))  # recompense None
    Q.ajouter_quete(gs, q)
    Q.notifier_geste(gs, "j", "recolter", _FakePlante("tomate"))
    check("plaisir pur (None) → quête honorée sans effet",
          Q.remettre_recompenses(gs, "j") == ["q_p"])


# ---------------------------------------------------------------------------
# 19. Récompense MATÉRIELLE : vivace enracinée (④) — un ACTEUR neuf, pas un buff
# ---------------------------------------------------------------------------

def _monde_cadeau():
    """Monde MINIMAL mais RÉEL (tuile + eco) : les cadeaux matériels ont besoin d'une
    destination (`tiles` / `eco`), contrairement aux conditions d'état factices."""
    from world import Tile
    from fields import init_eco
    tile = Tile(tile_id="t0", soil_type="terre")
    eco = init_eco(tile.tile_id, tile.grid_rows, tile.grid_cols)
    return {"week": 3, "seed": 42, "log": [],
            "tiles": [tile], "eco": {tile.tile_id: eco}}


def _accomplir_et_remettre(gs, quete):
    Q.ajouter_quete(gs, quete)
    Q.notifier_geste(gs, "j", "recolter", _FakePlante("tomate"))  # 1 récolte suffit
    Q.remettre_recompenses(gs, "j")


def test_recompense_vivace():
    print("\n[19] récompense vivace : un pommier de 6 ans apparaît, poussé & cohérent")
    from plants.perennials import AppleTree
    q = Q.Quete(id="q_vivace", donneur="Gaston",
                condition=("recolte_cumulee", "recolter", 1, "tomate"),
                recompense=("vivace", "pommier", 6))
    gs = _monde_cadeau()
    _accomplir_et_remettre(gs, q)
    plants = gs["tiles"][0].plants
    check("une plante ajoutée à la tuile", len(plants) == 1, f"n={len(plants)}")
    p = plants[0]
    check("c'est un pommier VIVANT",
          p.is_alive and p.plant_class is AppleTree, f"class={p.plant_class}")
    check("âge = 6 ans (cohérent avec la croissance)", abs(p.age_years - 6.0) < 1e-9,
          f"age={p.age_years}")
    check("structure réellement poussée (>1 segment)", len(p.segments) > 1,
          f"segments={len(p.segments)}")
    check("arbre établi (hauteur > 1 m, pas un collet)", p.current_height > 100.0,
          f"h={p.current_height:.0f}cm")
    # Déterminisme : même seed → même arbre.
    gs2 = _monde_cadeau()
    _accomplir_et_remettre(gs2, q)
    p2 = gs2["tiles"][0].plants[0]
    check("déterministe : hauteur identique",
          abs(p.current_height - p2.current_height) < 1e-9,
          f"{p.current_height:.4f} vs {p2.current_height:.4f}")
    # Idempotent : un rappel ne re-offre pas l'arbre.
    Q.remettre_recompenses(gs, "j")
    check("cadeau versé une seule fois (idempotent)", len(plants) == 1)


# ---------------------------------------------------------------------------
# 20. Récompense MATÉRIELLE : structure permanente (④) — gratuite, unique
# ---------------------------------------------------------------------------

def test_recompense_structure():
    print("\n[20] récompense structure : un bac à compost posé (gratuit, unique)")
    from sim import vigueur
    q = Q.Quete(id="q_struct", donneur="Odette",
                condition=("recolte_cumulee", "recolter", 1, "tomate"),
                recompense=("structure", "bac"))
    gs = _monde_cadeau()
    vig_avant = vigueur.ensure_player(gs, "j")["courante"]
    _accomplir_et_remettre(gs, q)
    eco = gs["eco"]["t0"]
    check("un bac posé sur la tuile", any(s.kind == "bac" for s in eco.structures))
    check("cadeau GRATUIT (aucune Vigueur prélevée)",
          vigueur.ensure_player(gs, "j")["courante"] == vig_avant,
          f"avant={vig_avant} après={vigueur.ensure_player(gs, 'j')['courante']}")
    # Idempotent + unicité tuile : un rappel ne pose pas un 2ᵉ bac.
    Q.remettre_recompenses(gs, "j")
    check("un seul bac (idempotent + unicité tuile)",
          sum(s.kind == "bac" for s in eco.structures) == 1)


def main():
    print("=== test_quetes (D79 ①②③④) ===")
    test_accomplissement_et_evenement()
    test_autre_espece_ignoree()
    test_autre_verbe_ignore()
    test_ordre_deterministe()
    test_opt_in_strict()
    test_hauteur_min()
    test_floraison_min()
    test_nombre_vivant_min()
    test_cible_absente()
    test_evaluer_etat_neutre()
    test_declencheur_palier()
    test_declencheur_saison()
    test_plafond_bloque()
    test_declenchement_deterministe()
    test_recompense_graine()
    test_recompense_vigueur()
    test_est_atteignable()
    test_remettre_opt_in()
    test_recompense_vivace()
    test_recompense_structure()

    total = len(_results)
    ok = sum(1 for _, c in _results if c)
    print(f"\n{ok}/{total} checks OK")
    if ok != total:
        for name, c in _results:
            if not c:
                print(f"  ÉCHEC : {name}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
