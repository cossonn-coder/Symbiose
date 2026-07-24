"""
SYMBIOSE — tests/simserver/conteneurs.py
Section 17 : conteneurs pots/bacs au pont (④, protocole 0.5.7). Snapshot du bloc
`containers` (VIDE à l'init = golden NEUTRE), pose pot/bac par POSITION monde
(Vigueur débitée, conteneur exposé, index = `target.container`), `deplacer_pot`
(change x_cm/y_cm + lumière recalculée ; bac REFUSE sans coût), `planter_conteneur`
(place une plante du banc-graines dans le mini-sol), refus de désignation
(substrat/volume/index/espèce invalides) SANS coût + serveur survivant.
"""
from .harness import check, ServerProc


def test_conteneurs():
    print("\n[17] conteneurs pots/bacs : pose/déplace/plante + snapshot (0.5.7)")
    s = ServerProc()
    # "full" : monde réel (maison → ombre) + banque de départ (planter_conteneur).
    init = s.send(cmd="init", config="full", seed=42)
    check("engine_version 0.5.40", init.get("engine_version") == "0.5.40",
          init.get("engine_version"))
    snap0 = s.send(cmd="snapshot")["snapshot"]
    check("snapshot expose `containers` VIDE à l'init (golden neutre)",
          snap0.get("containers") == [], snap0.get("containers"))
    # LOD émetteurs d'ombre (D67, 0.5.21) : chaque plante VIVANTE porte `emitteur`
    # (bool dérivé du pouvoir ombrageant). En config full à l'init on a un mélange de
    # semis sous-seuil (emitteur false) et de plantes plus vigoureuses (true).
    vivantes = [p for p in snap0.get("plants", []) if not p.get("dead")]
    check("chaque plante vivante porte `emitteur` (bool)",
          vivantes and all(isinstance(p.get("emitteur"), bool) for p in vivantes),
          [p.get("emitteur") for p in vivantes[:5]])
    check("le LOD sépare émetteurs et non-émetteurs (au moins un de chaque)",
          any(p["emitteur"] for p in vivantes)
          and any(not p["emitteur"] for p in vivantes),
          {p["name"]: p["emitteur"] for p in vivantes})
    # Épaisseur de sol (D57 ②, 0.5.16) : bloc `epaisseur` = grille 2D dense par
    # tuile (cm). Présent dès l'init, valeurs finies ≥ 0 (init AU REPOS sur l'humus
    # de fond D56, donc hétérogène mais non nul). Le relief C# l'extrude.
    ep = snap0.get("epaisseur")
    check("snapshot expose `epaisseur` (grille par tuile)",
          isinstance(ep, dict) and len(ep) > 0, type(ep).__name__)
    if isinstance(ep, dict) and ep:
        grid0 = next(iter(ep.values()))
        flat = [v for row in grid0 for v in row]
        check("épaisseur : grille 2D dense de valeurs ≥ 0",
              bool(flat) and all(isinstance(v, (int, float)) and v >= 0.0
                                 for v in flat),
              f"{len(grid0)}×{len(grid0[0]) if grid0 else 0}")
    # Altitude (hydrologie & marécages ①, 0.5.17) : bloc `altitude` = grille 2D dense
    # par tuile (cm de micro-relief). Présent dès l'init, valeurs finies ≥ 0 (posée
    # hétérogène par `init_eco` sur un canal de hash décorrélé de l'humus). Le relief
    # C# l'extrude ; ce tronçon ne fait que la POSER + l'exposer (aucun tick, golden neutre).
    alt = snap0.get("altitude")
    check("snapshot expose `altitude` (grille par tuile)",
          isinstance(alt, dict) and len(alt) > 0, type(alt).__name__)
    if isinstance(alt, dict) and alt:
        grid_a = next(iter(alt.values()))
        flat_a = [v for row in grid_a for v in row]
        check("altitude : grille 2D dense de valeurs ≥ 0",
              bool(flat_a) and all(isinstance(v, (int, float)) and v >= 0.0
                                   for v in flat_a),
              f"{len(grid_a)}×{len(grid_a[0]) if grid_a else 0}")
    # Marais (hydrologie & marécages ③, 0.5.27) : bloc `marais` = liste CREUSE par
    # tuile des plots dont `marais_memory > MARAIS_OFF`. VIDE à l'init (aucune flaque
    # durable) → golden neutre. La vue « noircit » le sol ∝ intensité (philo #5).
    marais = snap0.get("marais")
    check("snapshot expose `marais` (bloc par tuile)",
          isinstance(marais, dict) and len(marais) > 0, type(marais).__name__)
    check("marais : liste creuse VIDE à l'init (aucune flaque durable)",
          isinstance(marais, dict)
          and all(v == [] for v in marais.values()),
          {k: len(v) for k, v in (marais or {}).items()})

    # --- poser_pot par position monde --------------------------------------
    rp = s.send(cmd="action", verb="poser_pot",
                target={"x_cm": 1000.0, "y_cm": 400.0},
                params={"substrat": "terreau", "volume": 10.0})
    check("poser_pot → applied + coût > 0",
          rp["result"]["applied"] and rp["result"]["cost"] > 0.0)
    # Le `cost` (> 0, ci-dessus) reste la source de vérité du geste. Depuis la
    # progression geste/outil (D60 ③), ce 1ᵉ `poser_pot` DÉCOUVRE le geste + sa
    # technique + son outil → un gain de Vigueur de découverte (§4.3) compense le débit
    # (voire le plafonne à la Vigueur max) : le delta net n'est plus le coût. On vérifie
    # à la place que le pont a bien RAFRAÎCHI la Vigueur du result après ce gain — elle
    # doit coïncider avec celle du snapshot joint (invariant que touche ③).
    check("Vigueur cohérente result ↔ snapshot (gain de découverte D60 ③ inclus)",
          rp["result"]["vigueur"] == rp["snapshot"]["player"]["vigueur"],
          (rp["result"]["vigueur"], rp["snapshot"]["player"]["vigueur"]))
    cont = rp["snapshot"]["containers"]
    check("snapshot expose le pot (kind/substrat/mobile/eco_summary)",
          len(cont) == 1 and cont[0]["kind"] == "pot"
          and cont[0]["substrat"] == "terreau" and cont[0]["mobile"] is True
          and cont[0]["x_cm"] == 1000.0 and "eco_summary" in cont[0], cont)

    # --- poser_bac immobile N×M --------------------------------------------
    rb = s.send(cmd="action", verb="poser_bac_culture",
                target={"x_cm": 800.0, "y_cm": 800.0},
                params={"substrat": "compost", "volume": 200.0,
                        "rows": 2, "cols": 2})
    check("poser_bac_culture → applied", rb["result"]["applied"])
    bac = rb["snapshot"]["containers"][1]
    check("le bac est immobile N×M (mobile false, rows/cols 2, fond_ouvert)",
          bac["kind"] == "bac" and bac["mobile"] is False
          and bac["rows"] == 2 and bac["cols"] == 2
          and bac["fond_ouvert"] is True, bac)

    # --- substrat / volume invalides → refus SANS coût ---------------------
    rbadsub = s.send(cmd="action", verb="poser_pot",
                     target={"x_cm": 0.0, "y_cm": 0.0},
                     params={"substrat": "n_existe_pas", "volume": 5.0})
    check("substrat inconnu → applied false, coût 0 (refus de désignation)",
          rbadsub["result"]["applied"] is False and rbadsub["result"]["cost"] == 0.0)
    rbadvol = s.send(cmd="action", verb="poser_pot",
                     target={"x_cm": 0.0, "y_cm": 0.0},
                     params={"substrat": "terreau", "volume": -5.0})
    check("volume ≤ 0 → applied false sans coût",
          rbadvol["result"]["applied"] is False and rbadvol["result"]["cost"] == 0.0)
    check("toujours 2 conteneurs après refus (rien posé)",
          len(rbadvol["snapshot"]["containers"]) == 2)

    # --- deplacer_pot : position + lumière recalculée ----------------------
    # Le pot #0 est sous l'ombre maison (1000,400). On le déplace au plein soleil
    # (loin) → le snapshot reflète la nouvelle position (la lumière se recalcule au
    # tick — ici on prouve la MOBILITÉ + l'exposition de la position).
    rm = s.send(cmd="action", verb="deplacer_pot",
                target={"container": 0, "x_cm": 2500.0, "y_cm": 2500.0})
    check("deplacer_pot → applied + coût > 0",
          rm["result"]["applied"] and rm["result"]["cost"] > 0.0)
    moved = rm["snapshot"]["containers"][0]
    check("position du pot mise à jour au snapshot",
          moved["x_cm"] == 2500.0 and moved["y_cm"] == 2500.0, moved)

    # --- bac REFUSE le déplacement (immobile, sans coût) -------------------
    rbacmove = s.send(cmd="action", verb="deplacer_pot",
                      target={"container": 1, "x_cm": 50.0, "y_cm": 50.0})
    check("déplacer un bac → applied false, coût 0 (immobile)",
          rbacmove["result"]["applied"] is False
          and rbacmove["result"]["cost"] == 0.0)
    check("la position du bac est INTACTE après refus",
          rbacmove["snapshot"]["containers"][1]["x_cm"] == 800.0)

    # --- index de conteneur invalide → refus -------------------------------
    rbadidx = s.send(cmd="action", verb="deplacer_pot",
                     target={"container": 9, "x_cm": 0.0, "y_cm": 0.0})
    check("container hors liste → applied false (refus)",
          rbadidx["result"]["applied"] is False)

    # --- planter_conteneur : place une plante du banc-graines --------------
    rplant = s.send(cmd="action", verb="planter_conteneur",
                    target={"container": 0}, params={"species": "tomate"})
    check("planter_conteneur (tomate) → applied + coût > 0",
          rplant["result"]["applied"] and rplant["result"]["cost"] > 0.0)
    pot0 = rplant["snapshot"]["containers"][0]
    check("le mini-sol du pot porte la plante au snapshot",
          len(pot0["plants"]) == 1 and pot0["plants"][0]["species"] == "Tomato",
          pot0["plants"])
    # espèce non plantable → refus sans coût
    rbadsp = s.send(cmd="action", verb="planter_conteneur",
                    target={"container": 0}, params={"species": "licorne"})
    check("espèce non plantable → applied false, coût 0",
          rbadsp["result"]["applied"] is False and rbadsp["result"]["cost"] == 0.0)

    # --- serveur survivant après tous ces refus ----------------------------
    rsurv = s.send(cmd="snapshot")
    check("serveur survit à tous les refus (snapshot encore ok)", rsurv["ok"])
    s.send(cmd="quit")
    check("quit conteneurs → exit 0", s.close() == 0)
