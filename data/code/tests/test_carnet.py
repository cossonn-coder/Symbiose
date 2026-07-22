"""
SYMBIOSE — tests/test_carnet.py
Test du CARNET AUTO (sprint Voix narratives, tronçon ③, D14 + D43).
Spec : `docs/narration/voix/conception_voix_narratives.md` §2.1/§5 + kickoff
`sprints/sprint_voix_narratives/03_carnet.md`.

Propriétés exigées (« Définition de done » du kickoff) :
  A. SANS JOUEUR → `[]` (golden-safe, lecture pure).
  B. BASCULE DE REGISTRE — même événement, palier<3 = descriptif, palier≥3 =
     interprétatif. Le palier lu est celui du CONCEPT (pas de l'espèce).
  C. RÉGLAGE ANTICIPÉ — force interprétatif dès palier 1.
  D. D43 — `acclimatation` rattaché au concept `adaptation`.
  E. FILTRE — par concept / zone / saison.

On consigne via le vrai ledger ② (`journal.consigner`) à partir de logs jouets
au format réel, puis on crédite la maîtrise via l'API `maitrise` (palier posé
directement pour un test net). Lecture pure → déterminisme total.

Usage (depuis data/code/) :
  python3 -m tests.test_carnet
"""
from sim import carnet
from sim import journal as J
from sim import maitrise

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# --- Fabriques de lignes au FORMAT RÉEL du moteur (cf. test_journal/evenements)
def _entete(tid="T0"):
    return f"  [{tid}]"


def _l_avance(nom, r, c):
    return f"    🌱 {nom}@({r}, {c}) → [pousse] (hum=0.50 lum=0.80 t=18.0°C)"


def _l_stagne_sec(nom, r, c):
    return f"    ⏸  {nom}@({r}, {c}) stagne (sec hum=0.10)"


def _poser_palier(gs, player, concept, p):
    """Pose DIRECTEMENT le palier d'un concept (raccourci de test) : passe par
    l'API publique de découverte puis écrit le palier dans la tranche — évite de
    compter les preuves de la courbe géométrique, hors sujet ici."""
    maitrise.decouvrir(gs, player, concept)
    gs["maitrise"][player]["objets"][concept]["palier"] = p


# ---------------------------------------------------------------------------
# A. Sans joueur → []
# ---------------------------------------------------------------------------

def test_sans_joueur():
    print("\n[A] sans joueur consigné → carnet vide (golden-safe)")
    gs = {}
    check("game_state vierge → []", carnet.carnet_lire(gs, "joueur_1") == [])
    # Un joueur avec une tranche journal VIDE → liste vide aussi, sans crash.
    J.ensure_player(gs, "joueur_1")
    check("tranche journal vide → []", carnet.carnet_lire(gs, "joueur_1") == [])


# ---------------------------------------------------------------------------
# B. Bascule de registre (palier du CONCEPT)
# ---------------------------------------------------------------------------

def test_bascule_registre():
    print("\n[B] bascule descriptif → interprétatif au palier 3 du CONCEPT")
    gs = {}
    log = [_entete("T0"), _l_stagne_sec("Tomate", 2, 2)]
    J.consigner(gs, "joueur_1", log, 10)          # 1 entrée : stagnation/sec → concept eau

    # Palier 0 sur "eau" → descriptif.
    notes = carnet.carnet_lire(gs, "joueur_1")
    check("1 entrée formatée", len(notes) == 1, f"{len(notes)}")
    check("concept déduit = eau", notes[0]["concept"] == "eau", f"{notes[0]['concept']}")
    check("palier 0 → descriptif", notes[0]["registre"] == "descriptif")
    check("texte descriptif (grise mine)",
          "grise mine" in notes[0]["texte"], notes[0]["texte"])

    # Palier 2 sur "eau" → encore descriptif (sous le seuil 3).
    _poser_palier(gs, "joueur_1", "eau", 2)
    notes = carnet.carnet_lire(gs, "joueur_1")
    check("palier 2 → toujours descriptif", notes[0]["registre"] == "descriptif")

    # Palier 3 sur "eau" → interprétatif (révélation rétroactive).
    _poser_palier(gs, "joueur_1", "eau", 3)
    notes = carnet.carnet_lire(gs, "joueur_1")
    check("palier 3 → interprétatif", notes[0]["registre"] == "interprétatif")
    check("texte interprétatif (la soif / draine trop vite)",
          "draine trop vite" in notes[0]["texte"], notes[0]["texte"])

    # Le concept lu est bien celui de l'EAU, pas de l'espèce tomate : maîtriser
    # "tomate" ne bascule PAS la note (décision B).
    gs2 = {}
    J.consigner(gs2, "joueur_1", log, 10)
    _poser_palier(gs2, "joueur_1", "tomate", 5)   # maîtrise de l'espèce, pas du concept
    notes2 = carnet.carnet_lire(gs2, "joueur_1")
    check("maîtriser l'espèce ne bascule pas la note (concept ≠ espèce)",
          notes2[0]["registre"] == "descriptif", notes2[0]["texte"])


# ---------------------------------------------------------------------------
# C. Réglage « interprétatif anticipé »
# ---------------------------------------------------------------------------

def test_reglage_anticipe():
    print("\n[C] réglage anticipé → interprétatif dès le palier 1")
    gs = {}
    log = [_entete("T0"), _l_stagne_sec("Tomate", 2, 2)]
    J.consigner(gs, "joueur_1", log, 10)
    _poser_palier(gs, "joueur_1", "eau", 1)       # palier 1 seulement

    check("sans réglage, palier 1 → descriptif",
          carnet.carnet_lire(gs, "joueur_1")[0]["registre"] == "descriptif")

    # Active le flag d'aide (posé par le driver/options).
    gs.setdefault("options", {})["joueur_1"] = {"carnet_anticipe": True}
    check("avec réglage anticipé, palier 1 → interprétatif",
          carnet.carnet_lire(gs, "joueur_1")[0]["registre"] == "interprétatif")


# ---------------------------------------------------------------------------
# D. D43 — acclimatation → concept adaptation
# ---------------------------------------------------------------------------

def test_d43_acclimatation():
    print("\n[D] D43 : acclimatation rattachée au concept adaptation")
    # `acclimatation` n'est pas émis par le parseur (signe de rendu) → on injecte
    # l'entrée directement dans le ledger pour valider la TABLE + le gabarit.
    gs = {}
    st = J.ensure_player(gs, "joueur_1")
    st["entries"].append({"semaine": 20, "zone": ("T0", 4, 4),
                          "kind": "acclimatation", "cause": None, "espece": "lavande"})

    notes = carnet.carnet_lire(gs, "joueur_1")
    check("acclimatation → concept adaptation",
          notes[0]["concept"] == "adaptation", f"{notes[0]['concept']}")
    check("palier 0 adaptation → descriptif (éclat cireux)",
          notes[0]["registre"] == "descriptif" and "cireux" in notes[0]["texte"],
          notes[0]["texte"])

    _poser_palier(gs, "joueur_1", "adaptation", 3)
    notes = carnet.carnet_lire(gs, "joueur_1")
    check("palier 3 adaptation → interprétatif (descendants pré-armés)",
          notes[0]["registre"] == "interprétatif"
          and "pré-armés" in notes[0]["texte"], notes[0]["texte"])


# ---------------------------------------------------------------------------
# E. Filtre (concept / zone / saison)
# ---------------------------------------------------------------------------

def test_filtre():
    print("\n[E] filtre par concept / zone / saison")
    gs = {}
    log_s10 = [_entete("T0"), _l_avance("Tomate", 2, 2), _l_stagne_sec("Basilic", 3, 1)]
    J.consigner(gs, "joueur_1", log_s10, 10)      # germination@(2,2) + stagnation sec@(3,1)
    log_s11 = [_entete("T1"), _l_avance("Haricot", 0, 0)]
    J.consigner(gs, "joueur_1", log_s11, 11)      # germination@(T1,0,0)

    tout = carnet.carnet_lire(gs, "joueur_1")
    check("3 entrées sans filtre", len(tout) == 3, f"{len(tout)}")

    par_eau = carnet.carnet_lire(gs, "joueur_1", {"concept": "eau"})
    check("filtre concept=eau → 1 (la stagnation sec)",
          len(par_eau) == 1 and par_eau[0]["concept"] == "eau", f"{par_eau}")

    par_zone = carnet.carnet_lire(gs, "joueur_1", {"zone": ("T1", 0, 0)})
    check("filtre zone=(T1,0,0) → 1 (le haricot)",
          len(par_zone) == 1 and par_zone[0]["zone"] == ("T1", 0, 0), f"{par_zone}")

    par_saison = carnet.carnet_lire(gs, "joueur_1", {"saison": 11})
    check("filtre saison=11 → 1 (semaine 11)",
          len(par_saison) == 1 and par_saison[0]["semaine"] == 11, f"{par_saison}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Carnet auto (Voix narratives ③)")
    print("=" * 60)
    test_sans_joueur()
    test_bascule_registre()
    test_reglage_anticipe()
    test_d43_acclimatation()
    test_filtre()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
