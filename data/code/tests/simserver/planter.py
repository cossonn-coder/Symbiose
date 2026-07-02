"""
SYMBIOSE — tests/simserver/planter.py
Section 12 : planter & arroser (protocole 0.3.3). Gestes sur le MILIEU désignés
par POSITION continue (x_cm/y_cm, locale tuile) résolue en plot-foyer côté
serveur. `planter` dépose une graine de la banque-joueur ; `arroser` mouille le
champ humidité (cap 3, cumulatif). Refus sans coût, banque exposée au snapshot,
déterminisme byte-à-byte.
"""
from .harness import check, ServerProc


def test_planter_arroser():
    print("[planter & arroser]")
    s12 = ServerProc()
    s12.send(cmd="init", seed=42)

    def hum_at(srv, tid, r, c):
        g = srv.send(cmd="fields", field="humidite")["tiles"][tid]
        return g["values"][r * g["cols"] + c]

    snap = s12.send(cmd="snapshot")["snapshot"]
    check("bloc player.seeds présent, vide à l'init (banque non remplie)",
          snap["player"].get("seeds") == {}, f"seeds={snap['player'].get('seeds')}")

    # Refus de planter (vigueur 100, RIEN ne doit bouger) : espèce inconnue,
    # lot vide, position hors tuile, tuile introuvable — tous applied:false.
    PT = {"tile": "T0", "x_cm": 75.0, "y_cm": 75.0}          # plot (1,1) de T0
    r = s12.send(cmd="action", verb="planter",
                 target=PT, params={"species": "licorne"})
    check("planter espèce inconnue → applied:false",
          r["result"]["applied"] is False and "non plantable" in r["result"]["message"],
          r["result"]["message"])
    r = s12.send(cmd="action", verb="planter",
                 target=PT, params={"species": "tomate"})
    check("planter lot vide (espèce valide, banque vide) → applied:false",
          r["result"]["applied"] is False and "lot vide" in r["result"]["message"],
          r["result"]["message"])
    r = s12.send(cmd="action", verb="planter",
                 target={"tile": "T0", "x_cm": 99999.0, "y_cm": 0.0},
                 params={"species": "tomate"})
    check("planter hors tuile → applied:false", r["result"]["applied"] is False,
          r["result"]["message"])
    r = s12.send(cmd="action", verb="planter",
                 target={"tile": "TZZ", "x_cm": 75.0, "y_cm": 75.0},
                 params={"species": "tomate"})
    check("planter tuile introuvable → applied:false",
          r["result"]["applied"] is False)
    check("aucun refus de planter n'a coûté de Vigueur",
          r["result"]["vigueur"] == 100.0, f"vigueur={r['result']['vigueur']}")

    # Arroser : le champ humidité monte de DOSE au plot visé, coût MODÉRÉ (15).
    # Depuis la progression geste/outil/technique (D60 ③), le 1ᵉ arroser DÉCOUVRE le
    # geste + sa technique + ses outils (canal Q3) → petit gain de Vigueur de
    # découverte (§4.3) qui compense le coût de ce 1ᵉ geste. On vérifie donc le `cost`
    # ANNONCÉ (source de vérité du geste, MODÉRÉ=15), pas la Vigueur absolue.
    h0 = hum_at(s12, "T0", 1, 1)
    r = s12.send(cmd="action", verb="arroser", target=PT)
    check("arroser → applied:true, coût MODÉRÉ (15)",
          r["result"]["applied"] is True and r["result"]["cost"] == 15.0,
          f"cost={r['result']['cost']} vigueur={r['result']['vigueur']}")
    v_apres_calme = r["result"]["vigueur"]
    h1 = hum_at(s12, "T0", 1, 1)
    check("le champ humidité monte de DOSE_ARROSAGE (0.5) au plot visé",
          abs((h1 - h0) - 0.5) < 1e-6, f"{h0} → {h1}")
    # Urgence (phase Saison, couture §3.1) : × URGENCE_MULT. Le geste est déjà
    # découvert (pas de nouveau gain) → le débit net EST le coût. Les objets sont
    # remisés par le palier ⇒ on vérifie le RATIO URGENCE_MULT (=1.5) porté par le
    # champ `cost`, stable quel que soit le niveau de remise.
    r = s12.send(cmd="action", verb="arroser", target=PT, params={"urgence": True})
    debit_urgence = v_apres_calme - r["result"]["vigueur"]
    check("arroser en urgence : débit net = cost annoncé, majoré par l'urgence",
          debit_urgence > 15.0 and abs(debit_urgence - r["result"]["cost"]) < 1e-6,
          f"cost={r['result']['cost']} Δ={debit_urgence}")
    # Cumul borné : marteler le même plot → l'humidité PLAFONNE à 3.0 (les
    # arrosages refusés faute de Vigueur ne touchent pas le champ).
    for _ in range(8):
        s12.send(cmd="action", verb="arroser", target=PT)
    check("humidité plafonne à 3.0 (cumul borné, cap Q9)",
          abs(hum_at(s12, "T0", 1, 1) - 3.0) < 1e-6, hum_at(s12, "T0", 1, 1))

    # Planter pour de vrai : avancer jusqu'à ce que la récolte d'automne
    # remplisse la banque-joueur, puis déposer une graine → le lot DÉCROÎT de 1
    # et la Vigueur paie FAIBLE (5). Le passage de saison a remis la Vigueur au
    # plein → on lit un débit propre. La germination différée, elle, est couverte
    # par test_planter (la succession lève le grain au bon moment).
    snap = s12.send(cmd="snapshot")["snapshot"]
    while not snap["player"]["seeds"] and snap["week"] < 20:
        snap = s12.send(cmd="step_week")["snapshot"]
    seeds_av = snap["player"]["seeds"]
    check("la récolte d'automne a rempli la banque-joueur",
          len(seeds_av) > 0, f"seeds={seeds_av} (semaine {snap['week']})")
    espece = next(iter(seeds_av))            # sorted (JSON sort_keys) → déterministe
    r = s12.send(cmd="action", verb="planter",
                 target={"tile": "T0", "x_cm": 25.0, "y_cm": 25.0},
                 params={"species": espece})
    # Maîtrise (voix ①) : le coût nominal (planter FAIBLE=5) est remisé par le
    # palier ⇒ le champ `cost` (≤ 5) reste la source de vérité du geste. Depuis la
    # progression geste/outil (D60 ③), ce 1ᵉ `planter` DÉCOUVRE le geste + sa technique
    # → un gain de Vigueur de découverte (§4.3) se superpose au débit (il peut même le
    # dépasser, la Vigueur nette REMONTE) : on vérifie donc le `cost` annoncé, pas le delta.
    check("planter une graine en banque → applied:true, coût FAIBLE (cost ≤ 5)",
          r["result"]["applied"] is True
          and 0.0 < r["result"]["cost"] <= 5.0,
          f"cost={r['result']['cost']} vigueur={r['result']['vigueur']} "
          f"({r['result']['message']})")
    seeds_ap = r["snapshot"]["player"]["seeds"]
    check("le lot de l'espèce plantée a décru de 1 (graine sortie de la banque)",
          seeds_ap.get(espece, 0) == seeds_av[espece] - 1,
          f"{espece} : {seeds_av[espece]} → {seeds_ap.get(espece, 0)}")
    s12.send(cmd="quit")
    check("quit planter/arroser → exit 0", s12.close() == 0)

    # Déterminisme byte-à-byte (planter/arroser sont des fonctions PURES de
    # l'état : aucun RNG, la levée différée réutilise le hash de niche).
    def run_pa(seed):
        s = ServerProc()
        s.send(cmd="init", seed=seed)
        snap = s.send(cmd="snapshot")["snapshot"]
        while not snap["player"]["seeds"] and snap["week"] < 20:
            snap = s.send(cmd="step_week")["snapshot"]
        sp = next(iter(snap["player"]["seeds"]), None)
        if sp:
            s.send(cmd="action", verb="planter",
                   target={"tile": "T0", "x_cm": 25.0, "y_cm": 25.0},
                   params={"species": sp})
        s.send(cmd="action", verb="arroser",
               target={"tile": "T0", "x_cm": 75.0, "y_cm": 75.0},
               params={"urgence": True})
        s.send(cmd="snapshot")
        s.send(cmd="quit")
        return s
    a12, b12 = run_pa(42), run_pa(42)
    a12.close(); b12.close()
    check("2 runs planter+arroser même seed → byte-identiques",
          a12.raw_lines == b12.raw_lines)
