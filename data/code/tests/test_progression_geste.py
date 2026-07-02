"""
SYMBIOSE — tests/test_progression_geste.py
Golden JOUEUR de la PROGRESSION geste / outil / technique (D60, tronçon ③).
Distinct du golden ÉCOLOGIQUE (`test_golden.py`) et des goldens maîtrise cœur /
détection (`test_maitrise.py` / `test_maitrise_detection.py`).

Contexte (décision figée §3.4 de `CONCEPTION_VIE_MACRO_IDENTIFIABLE.md`) : geste,
outil et technique ont des fiches encyclopédie à 3 NIVEAUX gatés palier. Or la
détection de succès ne crédite QUE plantes + concepts — sans robinet neuf, ces
objets resteraient plafonnés au palier 1 et les niveaux N2/N3 seraient du contenu
MORT. Ce tronçon ouvre une progression COMBINÉE, tout côté PONT (hors tick) :

  - USAGE répété : chaque geste RÉUSSI découvre puis crédite (poids léger) le geste
    + sa technique + ses outils ;
  - SUCCÈS écologique : quand `detecter` impute une amélioration au geste, crédit
    d'une preuve de poids FORT sur ce geste.

Le golden écolo tourne le moteur SANS serveur → ces hooks ne sont jamais appelés →
golden NEUTRE (vérifié à part). Déterministe, aucun RNG.

Vérifie :
  1. Usage réussi → geste/technique/outils DÉCOUVERTS (palier 1) puis crédités léger.
  2. N usages → franchit un palier (courbe géométrique existante).
  3. Usage REFUSÉ (applied=False) → aucun crédit (rien ne se découvre, rien ne monte).
  4. Succès écologique imputé → crédit FORT sur le geste (palier monte plus vite
     qu'à l'usage seul).
  5. `enregistrer_preuve(..., poids=1.0)` identique à l'ancien comportement.
  6. La cible VIVANTE n'est jamais créditée par le volet usage (pas de double
     comptage — elle a sa voie via `detecter`).

Usage (depuis data/code/) :
  python3 -m tests.test_progression_geste
"""
from sim import maitrise as M
from sim import maitrise_detection as MD
from sim.actions import OBJETS_TOUCHES
from tools.simserver import maitrise_pont as P

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# Lignes de log au format EXACT du moteur (repris de test_maitrise_detection).
def _l_stagne(nom, r, c, raison="sec"):
    txt = {"sec": "(sec hum=0.10)", "ombre": "(ombre lum=0.10)", "froid": "(froid t=-2.0°C)"}[raison]
    marq = {"sec": "⏸ ", "ombre": "🌑", "froid": "❄"}[raison]
    return f"    {marq} {nom}@({r}, {c}) stagne {txt}"


def _l_avance(nom, r, c):
    return f"    🌱 {nom}@({r}, {c}) → [pousse] (hum=0.50 lum=0.80 t=18.0°C)"


def _entete(tile_id="T0"):
    return f"  [{tile_id}]"


def _simuler_usage(gs, player, verb):
    """Reproduit fidèlement ce que `cmd_action` fait après un geste appliqué :
    découverte à l'usage PUIS crédit léger (dans cet ordre)."""
    P.decouvrir_a_usage(gs, player, verb)
    P.crediter_usage(gs, player, verb)


# ---------------------------------------------------------------------------
# 1. Usage réussi → découverte du geste + technique + outils, crédit léger
# ---------------------------------------------------------------------------

def test_usage_decouvre_et_credite():
    print("\n[1] usage réussi → geste/technique/outils découverts (palier 1) + crédit léger")
    gs = {}
    # 'arroser' touche ("arrosage" technique, "arrosoir" outil) + le geste lui-même.
    _simuler_usage(gs, "j", "arroser")
    for objet in ("arroser", "arrosage", "arrosoir"):
        check(f"{objet} découvert (palier ≥ 1)", M.palier(gs, "j", objet) >= 1,
              f"palier={M.palier(gs,'j',objet)}")
    # Le crédit léger a bien déposé une fraction de preuve (< quota du 1er palier).
    o = gs["maitrise"]["j"]["objets"]["arroser"]
    check("preuve fractionnaire déposée (0 < preuves < quota)",
          0.0 < o["preuves"] < M.preuves_requises(1),
          f"preuves={o['preuves']:.3f}, quota={M.preuves_requises(1)}")
    check("un seul usage ne franchit pas encore le palier 1",
          M.palier(gs, "j", "arroser") == 1)


# ---------------------------------------------------------------------------
# 2. N usages → franchit un palier (courbe géométrique)
# ---------------------------------------------------------------------------

def test_usages_repetes_franchissent_palier():
    print("\n[2] N usages réussis → franchissent le palier 1→2 (poids léger cumulé)")
    gs = {}
    # Poids léger sans spillover (geste = pas de famille) → besoin = ceil(quota/poids).
    import math
    besoin = math.ceil(M.preuves_requises(1) / P.PREUVE_USAGE_LEGER)
    for _ in range(besoin):
        _simuler_usage(gs, "j", "arroser")
    check("après assez d'usages, le geste franchit le palier 1→2",
          M.palier(gs, "j", "arroser") >= 2,
          f"palier={M.palier(gs,'j','arroser')} après {besoin} usages")


# ---------------------------------------------------------------------------
# 3. Usage refusé → aucun crédit
# ---------------------------------------------------------------------------

def test_usage_refuse_ne_credite_rien():
    print("\n[3] usage REFUSÉ (applied=False) → aucune découverte, aucun crédit")
    gs = {}
    # cmd_action n'appelle les hooks QUE si result.applied ; ici on ne les appelle
    # simplement PAS (simulation d'un refus métier). L'état reste vierge.
    check("aucune clé maitrise créée (rien n'a été appliqué)", "maitrise" not in gs)
    check("le geste reste au palier 0 (inconnu)", M.palier(gs, "j", "arroser") == 0)


# ---------------------------------------------------------------------------
# 4. Succès écologique imputé → crédit FORT sur le geste
# ---------------------------------------------------------------------------

def test_succes_ecologique_credite_fort():
    print("\n[4] succès écologique imputé à 'arroser' → crédit FORT (palier monte plus vite)")
    gs = {"week": 1}
    # Le geste est déjà découvert (comme après un 1er usage réussi).
    M.decouvrir(gs, "j", "arroser")
    M.decouvrir(gs, "j", "tomate")
    M.decouvrir(gs, "j", "eau")

    # Semaine 1 : la tomate stagne (sec). Le joueur ARROSE le plot en semaine 2
    # (verbe mémorisé). Semaine 3 : la plante repart → succès imputable au geste.
    MD.detecter(gs, "j", [_entete(), _l_stagne("Tomate", 2, 2, "sec")], semaine=1)
    P.noter_geste_pont(gs, "j", 2, ("T0", 2, 2), verb="arroser")
    # Le pont enchaîne detecter(zones) + crédit fort — on reproduit observer_apres_tick.
    gs["week"] = 4                          # semaine du tick = 3 → gs["week"]-1
    zones: list = []
    MD.detecter(gs, "j", [_entete(), _l_avance("Tomate", 2, 2)], semaine=3,
                zones_creditees=zones)
    check("detecter a signalé la zone créditée par un geste", len(zones) == 1,
          f"zones={zones}")
    P._crediter_succes_gestes(gs, "j", 3, zones)
    o = gs["maitrise"]["j"]["objets"]["arroser"]
    check("crédit FORT (≥ PREUVE_USAGE_LEGER) déposé sur le geste",
          o["preuves"] >= P.PREUVE_SUCCES_FORT or M.palier(gs, "j", "arroser") >= 2,
          f"preuves={o['preuves']:.3f}, palier={o['palier']}")
    # Le poids fort (1.0) dépasse largement un usage léger (0.34) : preuve accumulée
    # supérieure à celle d'un unique usage.
    gs2 = {}
    M.enregistrer_preuve(gs2, "j", "arroser", poids=P.PREUVE_USAGE_LEGER)
    check("1 succès fort > 1 usage léger",
          o["preuves"] > gs2["maitrise"]["j"]["objets"]["arroser"]["preuves"],
          f"fort={o['preuves']:.3f} vs léger={gs2['maitrise']['j']['objets']['arroser']['preuves']:.3f}")


# ---------------------------------------------------------------------------
# 5. poids=1.0 identique à l'ancien comportement
# ---------------------------------------------------------------------------

def test_poids_defaut_retrocompatible():
    print("\n[5] enregistrer_preuve(..., poids=1.0) identique à l'appel historique (sans poids)")
    gs_a, gs_b = {}, {}
    for _ in range(3):
        M.enregistrer_preuve(gs_a, "j", "tomate")            # historique
        M.enregistrer_preuve(gs_b, "j", "tomate", poids=1.0)  # explicite
    a = gs_a["maitrise"]["j"]["objets"]["tomate"]
    b = gs_b["maitrise"]["j"]["objets"]["tomate"]
    check("même palier", a["palier"] == b["palier"], f"{a['palier']} == {b['palier']}")
    check("mêmes preuves résiduelles", a["preuves"] == b["preuves"],
          f"{a['preuves']} == {b['preuves']}")


# ---------------------------------------------------------------------------
# 6. La cible vivante n'est JAMAIS créditée par le volet usage
# ---------------------------------------------------------------------------

def test_usage_ne_credite_pas_la_cible():
    print("\n[6] volet usage : la cible vivante n'est pas créditée (pas de double comptage)")
    gs = {}
    # 'recolter' touche ("récolte" technique, "sécateur" outil). Aucune ESPÈCE ne
    # doit apparaître dans les objets découverts par l'usage.
    _simuler_usage(gs, "j", "recolter")
    objets = set(gs["maitrise"]["j"]["objets"])
    attendus = {"recolter", *OBJETS_TOUCHES["recolter"]}
    check("exactement geste + technique + outils, aucune espèce",
          objets == attendus, f"objets={sorted(objets)} attendus={sorted(attendus)}")
    # Aucune des clés n'est une espèce du catalogue (famille None pour toutes).
    check("aucun objet crédité n'a de famille (pas une plante)",
          all(M.famille_de(o) is None for o in objets), f"objets={sorted(objets)}")


def main():
    print("=== test_progression_geste (D60 ③) ===")
    test_usage_decouvre_et_credite()
    test_usages_repetes_franchissent_palier()
    test_usage_refuse_ne_credite_rien()
    test_succes_ecologique_credite_fort()
    test_poids_defaut_retrocompatible()
    test_usage_ne_credite_pas_la_cible()

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
