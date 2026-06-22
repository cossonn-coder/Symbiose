"""
SYMBIOSE — tests/test_plasticite.py
Test ciblé, lancé À LA DEMANDE (hors smoke test).

Couvre le SUBSTRAT de plasticité (sprint plasticité ①) : l'EXPRESSION plastique
des gènes adaptogènes dérive du stress vécu, distincte du génotype figé.
Conception : docs/conception/CONCEPTION_PLASTICITE_EXPRESSION.md (§2.1-2.3).

Au tronçon ① PERSONNE ne lit `expressed_gene` (acclimatation INERTE) ; on teste
donc la TUYAUTERIE en isolation, pas un effet écologique :
  ① expressed_gene = clamp_gene(génotype × expression), == génotype si neutre,
     borné par les limites dures (clamp_gene) ;
  ② acclimatation : sous stress installé (mémoire haute), expression monte vers
     1 + EXPR_GAIN à la vitesse TAU_UP ;
  ③ HYSTÉRÈSE : stress levé → expression redescend à TAU_DOWN < TAU_UP (la plante
     garde un temps son endurcissement) ; bornée [EXPR_MIN, EXPR_MAX].

On appelle directement `engine._update_physiology(tile, eco)` (une étape de mise à
jour des mémoires + expression, sans le reste du tick) en ÉPINGLANT la mémoire de
stress via une surcharge d'`eco.humidite.at_plot` (patron du test stress chronique)
→ pas/peu de RNG, assertions numériques exactes.

Lancement (depuis data/code/) :
  python3 -m tests.test_plasticite
"""

import sys

from world import Tile
from plants import (Zucchini, clamp_gene,
                    EXPR_GAIN, EXPR_MIN, EXPR_MAX, TAU_UP, TAU_DOWN, GENE_HARD_MAX)
from plants.genetics import (DEFENSE_COST, DEFENSE_PLANCHER, ADAPTOGENIC_GENES,
                             PRIMING_FRAC)
from fields import init_eco
from sim.engine import Engine
from sim.reproduction import child_expression
from sim.effects.perturbations import drought_stress_damage, DROUGHT_DAMAGE_THRESHOLD
from sim.growth.phases import shade_tolerance_effective

_GENE = "tolerance_secheresse"   # gène adaptogène ↔ drought_memory (le plus simple à piloter)
_EPS  = 1e-9


def _lab():
    """Tuile 6×6 terre + plante + Engine ; renvoie (engine, tile, eco, plant)."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=1.2, fertilite=1.2, microbiome=0.3)
    plant = tile.add_plant(Zucchini, 3, 3)
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "j1", "week": 1, "log": []}
    return Engine(gs), tile, eco, plant


def _pin_humidite(eco, hum: float):
    """Épingle l'humidité lue partout → drought_memory pilotée à volonté.
    hum=0   → drought_stress 1.0 (sécheresse sévère, cible mémoire 1.0) ;
    hum≥2.5 → drought_stress 0   (confort, cible mémoire 0)."""
    eco.humidite.at_plot = lambda r, c, _h=hum: _h


def test_expressed_gene_math():
    """expressed_gene = clamp_gene(génotype × expression) : neutre ⇒ == génotype ;
    sur-exprimé ⇒ > génotype ; jamais hors des limites dures (clamp_gene)."""
    _, _, _, p = _lab()
    p.genes = {_GENE: 1.2}
    # Neutre (défaut 1.0) → phénotype = génotype
    assert abs(p.expressed_gene(_GENE) - 1.2) < _EPS, "neutre : expressed ≠ génotype"
    # Sur-expression → phénotype relevé
    p.expression[_GENE] = 1.1
    assert abs(p.expressed_gene(_GENE) - clamp_gene(1.2 * 1.1)) < _EPS
    assert p.expressed_gene(_GENE) > p.gene(_GENE), "sur-expression n'élève pas le phénotype"
    # Borne dure : génotype haut × expression haute → plafonné à GENE_HARD_MAX
    p.genes[_GENE] = 1.5
    p.expression[_GENE] = EXPR_MAX
    assert abs(p.expressed_gene(_GENE) - GENE_HARD_MAX) < _EPS, "clamp_gene ne plafonne pas"
    # Gène NON adaptogène (absent d'expression) → expressed == gene
    p.genes["hauteur"] = 1.3
    assert abs(p.expressed_gene("hauteur") - 1.3) < _EPS, "gène non adaptogène altéré"
    print("[plasticité ①·math] PASS — expressed_gene = clamp(génotype×expression), bornes OK")


def test_acclimatation_vitesse_montee():
    """Sous stress installé (drought_memory épinglée 1.0), l'expression fait UN pas
    vers la cible 1+EXPR_GAIN exactement à la vitesse TAU_UP."""
    engine, tile, eco, p = _lab()
    _pin_humidite(eco, 0.0)              # sécheresse sévère → cible mémoire 1.0
    p.drought_memory = 1.0              # épinglée (hum=0 la maintient)
    p.expression[_GENE] = 1.0
    engine._update_physiology(tile, eco)
    cible = 1.0 + EXPR_GAIN             # 1.30
    attendu = 1.0 + (cible - 1.0) * TAU_UP
    assert abs(p.expression[_GENE] - attendu) < 1e-6, (
        f"montée à TAU_UP fausse : {p.expression[_GENE]:.6f} ≠ {attendu:.6f}")
    # Saturation : après beaucoup de pas, asymptote vers la cible sans la dépasser
    for _ in range(500):
        p.drought_memory = 1.0
        engine._update_physiology(tile, eco)
    assert p.expression[_GENE] <= EXPR_MAX + _EPS, "expression dépasse EXPR_MAX"
    assert abs(p.expression[_GENE] - cible) < 1e-3, "n'asymptote pas vers la cible"
    print(f"[plasticité ①·montée] PASS — un pas = TAU_UP ({TAU_UP}), "
          f"asymptote {p.expression[_GENE]:.4f}≈{cible}")


def test_hysterese_descente_plus_lente():
    """Stress levé : l'expression redescend à TAU_DOWN < TAU_UP (désacclimatation
    plus lente que l'acclimatation, à distance-à-la-cible ÉGALE → hystérèse)."""
    engine, tile, eco, p = _lab()
    gap = EXPR_GAIN                     # même écart 0.30 pour comparer les vitesses
    # MONTÉE : expression EXPR_MIN, cible EXPR_MIN+gap (mémoire 1.0)
    _pin_humidite(eco, 0.0)
    p.drought_memory = 1.0
    p.expression[_GENE] = EXPR_MIN
    engine._update_physiology(tile, eco)
    frac_montee = (p.expression[_GENE] - EXPR_MIN) / gap
    # DESCENTE : expression EXPR_MIN+gap, cible EXPR_MIN (mémoire 0)
    _pin_humidite(eco, 3.0)            # confort → drought_stress 0
    p.drought_memory = 0.0
    p.expression[_GENE] = EXPR_MIN + gap
    engine._update_physiology(tile, eco)
    frac_descente = (EXPR_MIN + gap - p.expression[_GENE]) / gap
    assert abs(frac_montee - TAU_UP) < 1e-6 and abs(frac_descente - TAU_DOWN) < 1e-6, (
        f"fractions ≠ τ : montée {frac_montee:.4f}/{TAU_UP}, descente {frac_descente:.4f}/{TAU_DOWN}")
    assert frac_descente < frac_montee, (
        f"pas d'hystérèse : descente {frac_descente:.4f} ≥ montée {frac_montee:.4f}")
    assert p.expression[_GENE] >= EXPR_MIN - _EPS, "expression sous EXPR_MIN"
    print(f"[plasticité ①·hystérèse] PASS — descente {frac_descente} < montée "
          f"{frac_montee} (TAU_DOWN<TAU_UP)")


def _compte_degats_secheresse(plant, eco, expression: float) -> int:
    """Nombre de tics où drought_stress_damage tape, sur 300 semaines déterministes,
    à drought_memory saturée (1.0) et expression `expression` épinglée. Plus l'expression
    monte, plus expressed_gene monte, plus la proba 1/expressed_gene baisse → moins de
    dégâts. _hash_noise(seed, week·37, r, c) varie par semaine → échantillonnage sans RNG."""
    plant.drought_memory = 1.0                      # > seuil → sévérité 1.0
    plant.expression[_GENE] = expression
    return sum(1 for wk in range(1, 301)
               if drought_stress_damage(plant, eco, seed=42, week=wk))


def test_branchement_acclimatation():
    """Tronçon ② : les consommateurs lisent expressed_gene, donc l'acclimatation agit.
      • NON-RÉGRESSION : à expression neutre (1.0) le point de lecture rend EXACTEMENT
        le génotype → dégât et gate identiques au comportement d'avant branchement ;
      • ACCLIMATATION : à expression haute, le dégât (sécheresse) et la gate (ombre)
        sont MESURABLEMENT plus doux."""
    _, _, eco, p = _lab()
    p.genes = {_GENE: 1.0, "tolerance_ombre": 0.8}   # héliophile (tol ombre < 1)

    # — Chemin de DÉGÂT (drought_stress_damage) —
    assert DROUGHT_DAMAGE_THRESHOLD < 1.0            # garde-fou : mémoire 1.0 franchit le seuil
    n_neutre = _compte_degats_secheresse(p, eco, 1.0)
    # Non-régression : à neutre, le point de lecture == génotype brut (expression vient
    # d'être épinglée à 1.0 par le comptage neutre)
    assert abs(p.expressed_gene(_GENE) - p.gene(_GENE)) < _EPS, "neutre ≠ génotype au point de lecture"
    n_endurci = _compte_degats_secheresse(p, eco, EXPR_MAX)
    assert n_neutre > 0, "le test n'exerce pas le dégât (aucun tic touché)"
    assert n_endurci < n_neutre, (
        f"acclimatation n'adoucit pas le dégât : endurci {n_endurci} ≥ neutre {n_neutre}")

    # — GATE (tolérance ombre effective, déterministe) —
    base = p.plant_class.shade_tolerance_base()
    p.expression["tolerance_ombre"] = 1.0
    assert abs(shade_tolerance_effective(p) - base * p.gene("tolerance_ombre")) < _EPS, (
        "neutre : gate ombre ≠ base×génotype")
    p.expression["tolerance_ombre"] = EXPR_MAX
    assert shade_tolerance_effective(p) > base * p.gene("tolerance_ombre"), (
        "acclimatation n'assouplit pas la gate ombre")
    print(f"[plasticité ②·branchement] PASS — neutre=génotype ; endurci {n_endurci} dégât(s) "
          f"< neutre {n_neutre}, gate ombre relevée")


def test_cout_defense():
    """Tronçon ③ : le coût croissance/défense re-route la vigueur.
      • NEUTRE (toutes expressions à 1.0) → facteur 1.0 (non-régression du tick) ;
      • SUR-expression → facteur strictement < 1.0, monotone (plus on durcit, plus
        ça coûte), jamais sous DEFENSE_PLANCHER ;
      • DÉSEXPRESSION (expression < 1.0) → AUCUN coût (seule la part > 1 compte) ;
      • valeur exacte = 1 − DEFENSE_COST × Σ max(0, expr−1)."""
    _, _, _, p = _lab()
    # Neutre : toutes les expressions à 1.0 (défaut) → pas de coût
    assert abs(p.cout_defense() - 1.0) < _EPS, "neutre : coût ≠ 1.0 (régression vigueur)"
    # Une seule sur-expression → coût exact et < 1
    p.expression[_GENE] = 1.20                       # surexpression 0.20
    attendu = 1.0 - DEFENSE_COST * 0.20
    assert abs(p.cout_defense() - attendu) < _EPS, f"coût mono faux : {p.cout_defense()} ≠ {attendu}"
    assert p.cout_defense() < 1.0, "sur-expression ne ronge pas la vigueur"
    # Monotonie : durcir un 2ᵉ gène coûte davantage
    cout1 = p.cout_defense()
    p.expression["tolerance_ombre"] = 1.20
    assert p.cout_defense() < cout1, "durcir un 2ᵉ gène ne coûte pas plus"
    # Désexpression (< 1.0) : ne compte JAMAIS (max(0, expr−1) = 0)
    p.expression = {g: 1.0 for g in ADAPTOGENIC_GENES}
    p.expression[_GENE] = 0.5                        # désexprimé
    assert abs(p.cout_defense() - 1.0) < _EPS, "désexpression pénalisée à tort"
    # Plancher : toutes saturées à EXPR_MAX → facteur ≥ DEFENSE_PLANCHER (jamais nul)
    p.expression = {g: EXPR_MAX for g in ADAPTOGENIC_GENES}
    assert p.cout_defense() >= DEFENSE_PLANCHER - _EPS, "coût sous le plancher"
    assert p.cout_defense() > 0.0, "le coût annule la vigueur (interdit)"
    print(f"[plasticité ③·coût] PASS — neutre=1.0, sur-expression ronge (monotone), "
          f"désexpression gratuite, plancher {DEFENSE_PLANCHER} tenu")


def test_priming_transgenerationnel():
    """Tronçon ④ : la MÈRE transmet son état d'expression à ses graines, qui voyage
    avec la graine par la banque-sol ; l'oubli est ÉMERGENT (pas de compteur).
      • child_expression = 1 + PRIMING_FRAC×(mère−1), mère neutre ⇒ enfant neutre ;
      • round-trip banque-sol : add_species(expression) → sample_expression rend la
        valeur héritée déposée (l'expression voyage avec la graine) ;
      • oubli émergent : un enfant né pré-armé, SANS stress, voit son expression
        redescendre vers 1.0 (désacclimatation intra-vie) — second ressort de l'oubli
        avec l'atténuation PRIMING_FRAC<1 à la transmission."""
    engine, tile, eco, mere = _lab()

    # — Math du priming (mère seule) —
    mere.expression["tolerance_ombre"] = 1.25
    mere.expression[_GENE] = 1.0                      # gène resté neutre chez la mère
    e = child_expression(mere)
    attendu = 1.0 + PRIMING_FRAC * 0.25
    assert abs(e["tolerance_ombre"] - attendu) < _EPS, (
        f"priming faux : {e['tolerance_ombre']:.4f} ≠ {attendu:.4f}")
    assert abs(e[_GENE] - 1.0) < _EPS, "gène neutre chez la mère ⇒ enfant non neutre"
    assert e["tolerance_ombre"] < mere.expression["tolerance_ombre"], (
        "PRIMING_FRAC<1 n'atténue pas l'alerte à la transmission")

    # — Round-trip banque-sol : l'expression voyage AVEC la graine —
    sb, cls = eco.seed_bank, mere.plant_class
    sb.add_species(3, 3, cls, density=0.5, genes={"hauteur": 1.0}, expression=e)
    lu = sb.sample_expression(3, 3, cls)
    assert abs(lu["tolerance_ombre"] - attendu) < 1e-6, (
        f"l'expression ne voyage pas par la banque : {lu.get('tolerance_ombre')} ≠ {attendu}")
    # Dépôt SANS expression (mère d'avant ④) → aucune expression stockée
    assert sb.sample_expression(0, 0, cls) == {}, "expression fantôme sur plot vierge"

    # — Oubli émergent : enfant né pré-armé, sans stress → redescend vers 1.0 —
    enfant = tile.add_plant(Zucchini, 1, 1)
    enfant.expression.update(e)                       # pré-armé à la germination
    _pin_humidite(eco, 3.0)                           # confort → aucune mémoire ne recharge
    enfant.drought_memory = enfant.shade_memory = 0.0
    avant = enfant.expression["tolerance_ombre"]
    for _ in range(5):
        enfant.shade_memory = 0.0
        engine._update_physiology(tile, eco)
    assert enfant.expression["tolerance_ombre"] < avant, (
        "l'expression héritée ne s'oublie pas sans stress (oubli non émergent)")
    assert enfant.expression["tolerance_ombre"] >= EXPR_MIN - _EPS, "sous EXPR_MIN"
    print(f"[plasticité ④·priming] PASS — mère 1.25→enfant {attendu:.3f} (PRIMING_FRAC), "
          f"voyage par la banque, oubli émergent sans stress")


def test_priming_canal_joueur():
    """Tronçon ④ (canal JOUEUR) : le priming voyage par TOUS les canaux de graine,
    pas seulement la banque-sol autonome. Chaîne récolte → `Seed` (child_expression,
    filtré non-neutre) → sérialisation save → `planter` (`GrainEnAttente`) →
    germination : la levée naît pré-armée, exactement comme par le canal féral."""
    from sim.seeds import Seed, PlayerSeedBank
    from sim import actions as ACT
    from sim import vigueur as V
    from sim.succession import succession

    # Graine récoltée d'une mère acclimatée (expression primée, filtrée non-neutre).
    e = {"tolerance_ombre": 1.1}
    bank = PlayerSeedBank()
    bank.add(Seed(species="tomate", genes={"hauteur": 1.42}, expression=dict(e)))

    # — Sérialisation round-trip (save lisible JSON) : l'expression survit —
    bank2 = PlayerSeedBank.from_json(bank.to_json())
    assert bank2.lots["tomate"][0].expression == e, (
        f"la sérialisation perd l'expression : {bank2.lots['tomate'][0].expression}")

    # — planter → le GrainEnAttente porte l'expression —
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=8)
    eco = init_eco("T0", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    eco.lumiere.fill(1.0); eco.disturbance.fill(1.0); eco.soil_memory_deep.fill(0.0)
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {}, "current_player": "j1",
          "week": 3, "log": [], "seed": 0x5EED, "player_seed_bank": bank2}
    V.ensure_player(gs, "j1")
    assert ACT.planter(gs, "j1", tile, eco, "tomate", 2, 2), "planter a échoué"
    grain = tile.grains_en_attente[(2, 2)][0]
    assert grain.expression == e, f"planter ne transmet pas l'expression : {grain.expression}"

    # — germination : la levée naît pré-armée —
    germ = None
    for w in range(3, 15):
        gs["week"] = w
        succession(gs, tile, eco, w)
        alive = [p for p in tile.plants if p.is_alive and p.position == (2, 2)]
        if alive:
            germ = alive[0]; break
    assert germ is not None, "la graine plantée n'a pas levé"
    assert abs(germ.expression["tolerance_ombre"] - 1.1) < _EPS, (
        f"semis non pré-armé : {germ.expression.get('tolerance_ombre')}")
    print("[plasticité ④·canal joueur] PASS — récolte→Seed→save→planter→germination pré-armée")


def test_signe_acclimatation():
    """⑤ Signe diégétique : une plante endurcie (expression > EXPR_MIN) sort bien la
    cause `acclimatation` dans leaf_symptoms, triée APRÈS un vrai dégât ; une plante
    au génotype nu n'en sort AUCUNE (lecture pure, golden NEUTRE)."""
    from sim import semiologie
    from plants.genetics import EXPR_MIN, EXPR_MAX

    _, _, eco, p = _lab()
    # Plante neutre : expression au plancher → pas de signe d'acclimatation.
    for g in ADAPTOGENIC_GENES:
        p.expression[g] = EXPR_MIN
    causes = [s["cause"] for s in semiologie.leaf_symptoms(p, eco, "ete")]
    assert "acclimatation" not in causes, f"signe parasite sur plante nue : {causes}"

    # Acclimatation maximale d'UN gène → intensité = 1.0 (rampe pleine à EXPR_MAX).
    p.expression["tolerance_secheresse"] = EXPR_MAX
    i = semiologie.acclimatation(p, eco, "ete")
    assert abs(i - 1.0) < _EPS, f"rampe non pleine à EXPR_MAX : {i}"
    # Acclimatation partielle (à mi-plage) → intensité ≈ 0.5.
    p.expression["tolerance_secheresse"] = EXPR_MIN + 0.5 * (EXPR_MAX - EXPR_MIN)
    assert abs(semiologie.acclimatation(p, eco, "ete") - 0.5) < _EPS, "rampe non linéaire"

    # Tri : à acclimatation forte + dégât d'ombre PLUS fort, l'ombre passe devant
    # (le durcissement est le moins urgent à diagnostiquer, priorité 9).
    p.expression["tolerance_secheresse"] = EXPR_MAX           # acclim intensité 1.0
    from sim.effects.perturbations import SHADE_DAMAGE_THRESHOLD
    p.shade_memory = 1.0                                      # ombre saturée → intensité 1.0
    syms = semiologie.leaf_symptoms(p, eco, "ete")
    causes = [s["cause"] for s in syms]
    assert "acclimatation" in causes and "ombre" in causes, f"signes manquants : {causes}"
    assert causes.index("ombre") < causes.index("acclimatation"), (
        f"à intensité égale l'ombre (dégât) doit précéder l'acclimatation : {causes}")
    print("[plasticité ⑤·signe] PASS — acclimatation visible, absente si nue, triée après le dégât")


if __name__ == "__main__":
    try:
        test_expressed_gene_math()
        test_acclimatation_vitesse_montee()
        test_hysterese_descente_plus_lente()
        test_branchement_acclimatation()
        test_cout_defense()
        test_priming_transgenerationnel()
        test_priming_canal_joueur()
        test_signe_acclimatation()
    except AssertionError as e:
        print(f"[plasticité ①] FAIL — {e}")
        sys.exit(1)
    sys.exit(0)
