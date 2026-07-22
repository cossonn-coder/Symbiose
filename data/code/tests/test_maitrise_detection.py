"""
SYMBIOSE — tests/test_maitrise_detection.py
Golden JOUEUR de la DÉTECTION DE SUCCÈS (D12, tronçon i4). Distinct des golden
ÉCOLOGIQUE (`test_golden.py`), POPULATION (`test_population.py`), MAÎTRISE cœur
(`test_maitrise.py`) et VIGUEUR (`test_vigueur.py`).

La détection vit AU-DESSUS du tick (`docs/joueur/maitrise/conception_maitrise.md` §9/§6) : elle LIT le
`log` d'un tick + l'état post-tick, et crédite des preuves TOUTE SEULE. Elle ne
fait jamais avancer la simulation → le golden écolo ne bouge pas (vérifié à part).

Stratégie de test :
  - Les règles fines (§9.2/§9.3) sont vérifiées sur des LOGS SCRIPTÉS (chaînes au
    format EXACT du moteur) — déterminisme total, isolation des many systèmes du
    tick.
  - Un test d'INTÉGRATION fait tourner un vrai `Engine` et vérifie que le parser
    reconnaît le format réel du log (compatibilité format ↔ regex).
  - Le tag FÉRAL / la naturalisation (§9.4(b)) sont vérifiés sur un état post-tick
    construit (plante établie en pleine santé).

Vérifie :
  1. Lever une stagnation APRÈS un geste joueur → crédite espèce + concept (§9.2).
  2. Négatif (§9.0) : amélioration ÉMERGENTE (sans geste imputable) → rien.
  3. Concept lié à la cause (sec→eau, ombre→lumière, froid→météo, §9.3).
  4. Gate d'observation (§9.6) : objet non découvert (palier 0) → jamais crédité.
  5. Nature croissante (§9.2) : un succès de mauvaise nature pour le palier courant
     ne crédite pas (impossible de sauter une marche).
  6. Reproduction biparentale + geste → pollinisation (§9.3).
  7. Tag féral / naturalisation (§9.4(b)) : recrue férale établie en pleine santé.
  8. Intégration : le parser reconnaît le format réel d'un `Engine`.

Usage (depuis data/code/) :
  python3 -m tests.test_maitrise_detection
"""
from world import Tile
from plants import Tomato, Basil, Bean
from fields import init_eco
from sim.engine import Engine
from sim import maitrise as M
from sim import maitrise_detection as D

SEED = 0x5AB1057E
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# Lignes de log au format EXACT du moteur (cf. engine._avancer_stades / _reproduction).
def _l_stagne(nom, r, c, raison):
    txt = {"sec": f"(sec hum=0.10)", "ombre": "(ombre lum=0.10)", "froid": "(froid t=-2.0°C)"}[raison]
    marq = {"sec": "⏸ ", "ombre": "🌑", "froid": "❄"}[raison]
    return f"    {marq} {nom}@({r}, {c}) stagne {txt}"


def _l_avance(nom, r, c):
    return f"    🌱 {nom}@({r}, {c}) → [pousse] (hum=0.50 lum=0.80 t=18.0°C)"


def _l_repro(nom, r, c, tag):
    return f"    🌰 Reproduction : {nom} @({r}, {c}) [lum=0.50 h=1.20 {tag}]"


def _entete(tile_id="T0"):
    return f"  [{tile_id}]"


# ---------------------------------------------------------------------------
# 1. Lever une stagnation après un geste → crédite espèce + concept
# ---------------------------------------------------------------------------

def test_lever_stagnation_positif():
    print("\n[1] lever une stagnation après un geste joueur → preuve espèce + concept (auto)")
    gs = {}
    M.decouvrir(gs, "j", "tomate")   # espèce découverte (palier 1)
    M.decouvrir(gs, "j", "eau")      # concept découvert (palier 1)

    # Semaine 1 : la tomate stagne (sec). Semaine 2 : le joueur agit sur le plot
    # (ex. arroser). Semaine 3 : la plante repart → succès imputable.
    D.detecter(gs, "j", [_entete(), _l_stagne("Tomate", 2, 2, "sec")], semaine=1)
    D.noter_geste(gs, "j", 2, ("T0", 2, 2))
    credits = D.detecter(gs, "j", [_entete(), _l_avance("Tomate", 2, 2)], semaine=3)

    objets = {o for o, _ in credits}
    check("preuve créditée sur l'espèce (tomate)", "tomate" in objets, f"credits={credits}")
    check("preuve créditée sur le concept lié (eau)", "eau" in objets, f"credits={credits}")

    # Deux cycles complets franchissent le palier 1→2 (PREUVES_BASE=2) — sans
    # AUCUN appel manuel à enregistrer_preuve.
    D.detecter(gs, "j", [_entete(), _l_stagne("Tomate", 2, 2, "sec")], semaine=5)
    D.noter_geste(gs, "j", 6, ("T0", 2, 2))
    D.detecter(gs, "j", [_entete(), _l_avance("Tomate", 2, 2)], semaine=7)
    check("après 2 cycles, l'espèce franchit le palier 1→2 (toute seule)",
          M.palier(gs, "j", "tomate") == 2, f"palier={M.palier(gs,'j','tomate')}")


# ---------------------------------------------------------------------------
# 2. Négatif (§9.0) : amélioration émergente sans geste → rien
# ---------------------------------------------------------------------------

def test_emergent_negatif():
    print("\n[2] amélioration émergente (« ça pousse tout seul », sans geste) → rien (§9.0)")
    gs = {}
    M.decouvrir(gs, "j", "tomate")
    M.decouvrir(gs, "j", "eau")

    # Stagnation puis levée, mais AUCUN geste joueur dans la fenêtre.
    D.detecter(gs, "j", [_entete(), _l_stagne("Tomate", 2, 2, "sec")], semaine=1)
    credits = D.detecter(gs, "j", [_entete(), _l_avance("Tomate", 2, 2)], semaine=3)
    check("aucune preuve sans geste imputable", credits == [], f"credits={credits}")
    check("le palier de l'espèce n'a pas bougé", M.palier(gs, "j", "tomate") == 1)

    # Avance SANS stagnation préalable (croissance normale) + sans geste → rien.
    credits2 = D.detecter(gs, "j", [_entete(), _l_avance("Tomate", 4, 4)], semaine=4)
    check("avance normale (sans stress levé) → rien", credits2 == [], f"credits={credits2}")


# ---------------------------------------------------------------------------
# 3. Concept lié à la cause de stagnation (§9.3)
# ---------------------------------------------------------------------------

def test_concept_par_cause():
    print("\n[3] le concept crédité dépend de la cause : sec→eau, ombre→lumière, froid→météo")
    for raison, concept in (("sec", "eau"), ("ombre", "lumière"), ("froid", "météo")):
        gs = {}
        M.decouvrir(gs, "j", "tomate")
        M.decouvrir(gs, "j", concept)
        D.detecter(gs, "j", [_entete(), _l_stagne("Tomate", 2, 2, raison)], semaine=1)
        D.noter_geste(gs, "j", 1, ("T0", 2, 2))
        credits = D.detecter(gs, "j", [_entete(), _l_avance("Tomate", 2, 2)], semaine=2)
        objets = {o for o, _ in credits}
        check(f"{raison} → concept {concept} crédité", concept in objets, f"credits={credits}")


# ---------------------------------------------------------------------------
# 4. Gate d'observation (§9.6) : objet non découvert → jamais crédité
# ---------------------------------------------------------------------------

def test_gate_observation():
    print("\n[4] gate d'observation : un objet non découvert (palier 0) n'est jamais crédité")
    gs = {}   # rien de découvert
    D.detecter(gs, "j", [_entete(), _l_stagne("Tomate", 2, 2, "sec")], semaine=1)
    D.noter_geste(gs, "j", 1, ("T0", 2, 2))
    credits = D.detecter(gs, "j", [_entete(), _l_avance("Tomate", 2, 2)], semaine=2)
    check("succès réel mais objet non observé → rien crédité", credits == [], f"credits={credits}")
    check("aucune auto-découverte par la détection (le gate l'interdit)",
          M.palier(gs, "j", "tomate") == 0 and M.palier(gs, "j", "eau") == 0)


# ---------------------------------------------------------------------------
# 5. Nature croissante (§9.2) : mauvaise marche → pas de crédit
# ---------------------------------------------------------------------------

def test_nature_croissante():
    print("\n[5] nature croissante : lever une stagnation ne compte QUE pour le palier 1→2")
    gs = {}
    # Tomate poussée au palier 2 par injection (i1) — la nature requise pour 2→3
    # est « reproduction », pas « stagnation ».
    M.decouvrir(gs, "j", "tomate")
    for _ in range(M.preuves_requises(1)):
        M.enregistrer_preuve(gs, "j", "tomate")
    check("tomate au palier 2 (support)", M.palier(gs, "j", "tomate") == 2)

    D.detecter(gs, "j", [_entete(), _l_stagne("Tomate", 2, 2, "sec")], semaine=1)
    D.noter_geste(gs, "j", 1, ("T0", 2, 2))
    credits = D.detecter(gs, "j", [_entete(), _l_avance("Tomate", 2, 2)], semaine=2)
    objets = {o for o, _ in credits}
    check("au palier 2, une stagnation levée ne crédite PAS l'espèce (mauvaise nature)",
          "tomate" not in objets, f"credits={credits}")

    # En revanche, une reproduction avec geste crédite bien (bonne nature pour 2→3).
    gs2 = {}
    M.decouvrir(gs2, "j", "tomate")
    for _ in range(M.preuves_requises(1)):
        M.enregistrer_preuve(gs2, "j", "tomate")
    D.noter_geste(gs2, "j", 1, ("T0", 3, 3))
    credits2 = D.detecter(gs2, "j", [_entete(), _l_repro("Tomate", 3, 3, "biparental")], semaine=1)
    check("au palier 2, une reproduction avec geste CRÉDITE l'espèce (bonne nature)",
          "tomate" in {o for o, _ in credits2}, f"credits={credits2}")


# ---------------------------------------------------------------------------
# 6. Reproduction biparentale + geste → pollinisation (§9.3)
# ---------------------------------------------------------------------------

def test_pollinisation():
    print("\n[6] reproduction biparentale avec geste → concept pollinisation (§9.3)")
    gs = {}
    M.decouvrir(gs, "j", "tomate")
    for _ in range(M.preuves_requises(1)):
        M.enregistrer_preuve(gs, "j", "tomate")   # palier 2 (rung reproduction)
    M.decouvrir(gs, "j", "pollinisation")
    D.noter_geste(gs, "j", 1, ("T0", 3, 3))       # favoriser_auxiliaire au plot
    credits = D.detecter(gs, "j", [_entete(), _l_repro("Tomate", 3, 3, "biparental")], semaine=1)
    objets = {o for o, _ in credits}
    check("pollinisation créditée (croisement biparental)", "pollinisation" in objets,
          f"credits={credits}")

    # Autofécondation (tag `auto`) sans geste → pas de pollinisation.
    gs2 = {}
    M.decouvrir(gs2, "j", "pollinisation")
    credits2 = D.detecter(gs2, "j", [_entete(), _l_repro("Tomate", 3, 3, "auto")], semaine=1)
    check("autofécondation sans geste → pas de pollinisation",
          "pollinisation" not in {o for o, _ in credits2}, f"credits={credits2}")


# ---------------------------------------------------------------------------
# 7. Tag féral / naturalisation (§9.4(b))
# ---------------------------------------------------------------------------

def test_naturalisation_ferale():
    print("\n[7] naturalisation férale : recrue auto-semée établie en pleine santé (§9.4(b))")
    tile = Tile(tile_id="T0", soil_type="terre")
    p = tile.add_plant(Tomato, 2, 2)
    p.current_stage = D.STAGE_NATURALISATION   # établie (≥ seuil jeune/adulte)
    p.vitalite = 1.0                           # pleine santé (etat == "sain")
    gs = {"tiles": [tile]}
    M.decouvrir(gs, "j", "tomate")
    D.detecter(gs, "j", [], semaine=1)         # log vide : seul le balayage d'état joue
    det = gs["maitrise"]["j"]["_detection"]
    check("la recrue NON marquée est traitée comme férale → naturalisation détectée",
          "tomate" in det["naturalise"], f"naturalise={det['naturalise']}")

    # Une zone marquée `replante` (futur geste planter) est EXCLUE de la naturalisation.
    tile2 = Tile(tile_id="T1", soil_type="terre")
    p2 = tile2.add_plant(Tomato, 1, 1)
    p2.current_stage = D.STAGE_NATURALISATION
    p2.vitalite = 1.0
    gs2 = {"tiles": [tile2]}
    M.decouvrir(gs2, "j", "tomate")
    D.marquer_replante(gs2, "j", "T1", 1, 1)
    D.detecter(gs2, "j", [], semaine=1)
    det2 = gs2["maitrise"]["j"]["_detection"]
    check("une zone replantée par le joueur n'est PAS comptée comme naturalisée",
          "tomate" not in det2["naturalise"], f"naturalise={det2['naturalise']}")


# ---------------------------------------------------------------------------
# 8. Intégration : le parser reconnaît le format réel d'un Engine
# ---------------------------------------------------------------------------

def test_integration_format_reel():
    print("\n[8] intégration : le parser reconnaît le format de log d'un vrai Engine")
    tile = Tile(tile_id="T0", soil_type="terre")
    eco = init_eco("T0", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    tile.add_plant(Tomato, 2, 2)
    tile.add_plant(Basil, 2, 4)
    tile.add_plant(Bean, 4, 2)
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "joueur_1", "week": 1, "log": [], "seed": SEED}
    eng = Engine(gs)

    avances = 0
    crash = False
    try:
        for _ in range(30):
            log = eng.tick_semaine()
            for kind, *_ in D._evenements(log):
                if kind == "avance":
                    avances += 1
    except Exception as e:           # noqa: BLE001 — on veut justement attraper tout
        crash = True
        print(f"      exception: {e!r}")
    check("le parser ne plante pas sur un log réel", not crash)
    check("le parser extrait des avances de stade réelles (format compatible)",
          avances > 0, f"avances={avances}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Golden JOUEUR Détection de succès (D12, tronçon i4)")
    print("=" * 60)
    test_lever_stagnation_positif()
    test_emergent_negatif()
    test_concept_par_cause()
    test_gate_observation()
    test_nature_croissante()
    test_pollinisation()
    test_naturalisation_ferale()
    test_integration_format_reel()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
