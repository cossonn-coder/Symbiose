"""
SYMBIOSE — tests/vigueur/maitrise_seam.py
F. Pont maîtrise → Vigueur (D12·i2) : palier_bonus actif (§4.1) + sources
   ponctuelles (§4.3).
G. Seam cout_action (D12·i3) : la maîtrise allège le coût des gestes
   (CONCEPTION_MAITRISE §4.2/§10.4) — neutre à vide, décroissant, plancher > 0.
Event-driven hors tick, déterministe sans RNG.
"""
from sim import vigueur as V
from sim import actions as ACT
from sim import maitrise as M   # D12·i2 : le pont maîtrise→Vigueur (palier_bonus + gains §4.3)

from .harness import check, _minimal_state


def test_pont_maitrise_vigueur():
    print("\n[F1] pont §4.1 : la maîtrise gonfle vigueur_max & régen (log-saturé)")
    gs = {}
    V.ensure_player(gs, "j")
    vmax0 = V.vigueur_max(gs, "j"); regen0 = V.regen_rate(gs, "j")
    check("sans maîtrise : vigueur_max = MAX_BASE", vmax0 == V.MAX_BASE, f"vmax={vmax0}")
    check("sans maîtrise : regen_rate = REGEN_BASE", regen0 == V.REGEN_BASE)
    # On acquiert de la maîtrise → palier_bonus > 1 → plafond & régen montent.
    M.decouvrir(gs, "j", "tomate")
    for _ in range(20):
        M.enregistrer_preuve(gs, "j", "tomate")
    check("maîtrise acquise → vigueur_max > MAX_BASE", V.vigueur_max(gs, "j") > vmax0,
          f"vmax={V.vigueur_max(gs, 'j')}")
    check("maîtrise acquise → régen plus rapide", V.regen_rate(gs, "j") > regen0,
          f"regen={V.regen_rate(gs, 'j')}")
    check("plafond = MAX_BASE × palier_bonus (le pont, pas un état dupliqué)",
          V.vigueur_max(gs, "j") == V.MAX_BASE * M.palier_bonus(gs, "j"))


def test_gains_ponctuels():
    print("\n[F2] sources ponctuelles §4.3 : découverte (+) idempotente, succès (+) par palier")
    gs = {}
    st = V.ensure_player(gs, "j"); st["courante"] = 0.0
    neuf = ACT.observer(gs, "j", "tomate")
    check("observer découvre ET crédite GAIN_DECOUVERTE",
          neuf and st["courante"] == ACT.GAIN_DECOUVERTE, f"courante={st['courante']}")
    st["courante"] = 0.0
    redite = ACT.observer(gs, "j", "tomate")
    check("ré-observer un connu → False, aucun gain (idempotent)",
          (not redite) and st["courante"] == 0.0, f"courante={st['courante']}")
    # Succès : aucun gain tant qu'aucun palier n'est franchi, +GAIN_SUCCES au seuil.
    st["courante"] = 0.0
    avant = M.palier(gs, "j", "tomate")
    for _ in range(M.preuves_requises(1) - 1):
        ACT.crediter_succes(gs, "j", "tomate")
    check("sous le quota : aucun palier, aucun gain de succès", st["courante"] == 0.0,
          f"courante={st['courante']}")
    pal = ACT.crediter_succes(gs, "j", "tomate")
    check("franchissement de palier → +GAIN_SUCCES",
          pal == avant + 1 and st["courante"] == ACT.GAIN_SUCCES,
          f"palier={pal} courante={st['courante']}")


def test_seam_cout_action():
    print("\n[G] seam cout_action : la maîtrise allège le coût des gestes (§4.2/§10.4)")
    gs = _minimal_state()
    plant = gs["tiles"][0].plants[0]   # Tomato → clé catalogue "tomate"
    V.ensure_player(gs, "joueur_1")
    check("résolution classe→clé d'espèce (reverse catalogue)",
          ACT._cle_espece(plant) == "tomate", f"clé={ACT._cle_espece(plant)}")
    # Neutre à vide : sans maîtrise, cout_action == base (ce qui garde A5–E verts).
    base = ACT.cout_action(gs, "joueur_1", "deraciner",
                           ACT._objets_action("deraciner", plant))
    check("sans maîtrise : cout_action == base (ELEVE)", base == ACT.ELEVE,
          f"cout={base}")
    # On maîtrise la technique d'arrachage ET l'espèce ciblée → le coût baisse
    # (terme 2 par-objet + terme 1 global montent tous deux).
    for _ in range(20):
        M.enregistrer_preuve(gs, "joueur_1", "arrachage")   # technique (terme 2)
        M.enregistrer_preuve(gs, "joueur_1", "tomate")      # espèce ciblée (terme 2 + global)
    avec = ACT.cout_action(gs, "joueur_1", "deraciner",
                           ACT._objets_action("deraciner", plant))
    check("avec maîtrise : coût strictement < base", avec < ACT.ELEVE, f"cout={avec}")
    check("plancher : atténuation jamais ≤ 0 (coût strictement positif)",
          avec > 0.0, f"cout={avec}")
    # Un objet NON maîtrisé n'allège PAS le terme 2 : sur un joueur VIERGE, un geste
    # dont les objets sont tous inconnus reste exactement à sa base.
    gs_vierge = _minimal_state(); V.ensure_player(gs_vierge, "joueur_1")
    check("objet non maîtrisé (joueur vierge) → becher == base (FAIBLE)",
          ACT.cout_action(gs_vierge, "joueur_1", "becher", ACT.OBJETS_TOUCHES["becher"])
          == ACT.FAIBLE)
    # Coût NUL préservé (§10.5) : manger renvoie 0 sans rien lire, même avec maîtrise.
    check("manger : coût NUL préservé (base 0 → 0, même avec maîtrise)",
          ACT.cout_action(gs, "joueur_1", "manger") == 0.0)
    # Effet de bout-en-bout : une vraie récolte coûte MOINS de Vigueur avec maîtrise.
    eco = gs["eco"]["T0"]; plant.current_stage = len(plant.plant_class.growth_stages) - 1
    st = gs["vigueur"]["joueur_1"]; st["max_base"] = 1000.0; st["courante"] = 500.0
    ACT.recolter(gs, "joueur_1", plant, eco)
    debit = 500.0 - st["courante"] + ACT.HARVEST_GAIN_FULL   # net = gain − coût ; on isole le coût
    check("récolte branchée : coût payé < HARVEST_VIGUEUR_COST (maîtrise active)",
          debit < ACT.HARVEST_VIGUEUR_COST, f"coût payé={debit:.3f}")
