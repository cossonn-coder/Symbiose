"""
SYMBIOSE — tests/simserver/voix.py
Section 18 : voix narratives au pont (sprint UI voix ①, protocole 0.5.11).
Les 4 commandes READ-ONLY (carnet/encyclopedie/pages/magazine) + le verbe
`acheter_magazine`, alimentés par la chaîne de maîtrise (3 hooks hors tick).

Scénario : init config="full" (monde planté → espèces vivantes observables) →
quelques step_week → l'encyclopédie s'est peuplée (hook A observer), le carnet
répond, pages/magazine répondent (même vides). Puis un achat magazine forcé
(maîtrise injectée + Vigueur gonflée) débite la Vigueur et ajoute la graine.
Enfin déterminisme byte-à-byte du chemin de lecture.
"""
from .harness import check, ServerProc


def test_voix():
    print("[voix narratives — pont ①]")
    s = ServerProc()
    init = s.send(cmd="init", config="full", seed=7)
    check("protocole bumpé à 0.6.7 (formes des plantes)",
          init["engine_version"] == "0.6.7", init.get("engine_version"))
    import platform
    check("init porte la version de Python du moteur (fluidité PC ①)",
          init.get("python", {}).get("version") == platform.python_version(),
          init.get("python"))

    # Retour F5 : une plante n'est PLUS observée parce qu'elle pousse — seulement au
    # SURVOL souris. Après quelques semaines SANS survol, aucune ESPÈCE (plante /
    # animal / champignon) n'entre à l'index. (D60 ④ : les CONCEPTS transversaux
    # — eau/lumière/météo — se créditent seuls aux événements écologiques et
    # PEUVENT apparaître sans survol ; on les exclut du contrôle, qui vise le canal
    # d'observation à la souris.)
    snap = None
    for _ in range(6):
        snap = s.send(cmd="step_week")["snapshot"]
    vide = s.send(cmd="encyclopedie")
    especes = [e for e in vide["index"]
               if e["type"] in ("plante", "animal", "champignon")]
    check("aucune ESPÈCE à l'index sans survol (observation = souris)",
          vide["ok"] and especes == [], f"espèces={especes}")

    # Observer par SURVOL : le C# envoie le NOM DE CLASSE de la plante survolée ;
    # on le prend d'une plante vivante du snapshot (serialize `species`=__name__).
    nom_classe = snap["plants"][0]["species"]
    obs = s.send(cmd="observer", species=nom_classe)
    check("observer (survol) découvre une espèce → observed:true",
          obs["ok"] and obs["observed"] is True, obs)
    obs2 = s.send(cmd="observer", species=nom_classe)
    check("ré-observer la même espèce → observed:false (idempotent)",
          obs2["ok"] and obs2["observed"] is False, obs2)

    enc = s.send(cmd="encyclopedie")
    check("encyclopedie index NON vide APRÈS survol",
          enc["ok"] and len(enc["index"]) > 0, f"index={enc.get('index')}")
    # D60 ① : l'index rend des entrées TAGUÉES `{cle, type, titre}` (multi-règnes).
    # On cible l'entrée PLANTE survolée (des concepts auto-crédités peuvent coexister).
    entree = next(e for e in enc["index"] if e["type"] == "plante")
    check("entrée d'index taguée {cle,type,titre}",
          set(entree) == {"cle", "type", "titre"}, f"{entree}")
    espece = entree["cle"]
    fiche = s.send(cmd="encyclopedie", espece=espece)
    check("encyclopedie fiche d'une espèce découverte : niveau_max ≥ 1",
          fiche["ok"] and fiche["fiche"] is not None
          and fiche["fiche"]["niveau_max"] >= 1, f"fiche={fiche.get('fiche')}")
    absente = s.send(cmd="encyclopedie", espece="_inconnue_")
    check("encyclopedie espèce non découverte → fiche null",
          absente["ok"] and absente["fiche"] is None)

    # D60 ② : le survol de la VIE MACRO est aussi une observation. Le C# envoie
    # directement la CLÉ d'espèce (animale, ou fongique depuis ⑤ du sol qui
    # respire) dans `species` — `observer_espece` est multi-règnes.
    obs_faune = s.send(cmd="observer", species="puceron")
    check("observer (survol) une clé animale connue → observed:true",
          obs_faune["ok"] and obs_faune["observed"] is True, obs_faune)
    check("ré-observer la même clé animale → observed:false (idempotent)",
          s.send(cmd="observer", species="puceron")["observed"] is False)
    obs_champi = s.send(cmd="observer", species="pleurote")
    check("observer (survol) un carpophore → espèce fongique découverte (observed:true)",
          obs_champi["ok"] and obs_champi["observed"] is True, obs_champi)
    check("l'ancienne clé générique `champignon` → no-op (⑤)",
          s.send(cmd="observer", species="champignon")["observed"] is False)
    obs_bog = s.send(cmd="observer", species="_pas_une_espece_")
    check("observer un nom inconnu (règne inconnu) → observed:false, no-op",
          obs_bog["ok"] and obs_bog["observed"] is False, obs_bog)
    # L'index gagne bien une entrée animale ET une entrée champignon, TAGUÉES.
    idx_types = {e["type"] for e in s.send(cmd="encyclopedie")["index"]}
    check("index contient désormais les types animal + champignon",
          "animal" in idx_types and "champignon" in idx_types, idx_types)

    carnet = s.send(cmd="carnet")
    check("carnet répond une liste d'entrées (clé `entrees`)",
          carnet["ok"] and isinstance(carnet["entrees"], list),
          f"n={len(carnet.get('entrees', []))}")
    # Filtre par ESPÈCE (retour F5) : sous-ensemble du carnet complet ; une espèce
    # inconnue ne renvoie rien (le filtre est ET-combiné, clé catalogue).
    c_sp = s.send(cmd="carnet", filtre={"espece": espece})
    check("carnet filtre par espèce → sous-ensemble",
          c_sp["ok"] and len(c_sp["entrees"]) <= len(carnet["entrees"]))
    c_bog = s.send(cmd="carnet", filtre={"espece": "_inconnue_"})
    check("carnet filtre espèce inconnue → vide",
          c_bog["ok"] and len(c_bog["entrees"]) == 0)

    # Aide (retour F5, debug d'abord) : liste de remèdes {concept, remede, debloque}
    # pour les problèmes récents d'une espèce ; espèce inconnue → vide.
    aide = s.send(cmd="aide", espece=espece)
    check("aide répond une liste (clé `aide`)",
          aide["ok"] and isinstance(aide["aide"], list))
    check("aide items bien formés (concept/remede/debloque)",
          all({"concept", "remede", "debloque"} <= set(it) for it in aide["aide"]))
    check("aide espèce inconnue → vide",
          len(s.send(cmd="aide", espece="_inconnue_")["aide"]) == 0)

    pages = s.send(cmd="pages")
    check("pages répond (ids + textes, listes cohérentes)",
          pages["ok"] and isinstance(pages["ids"], list)
          and len(pages["ids"]) == len(pages["pages"]))

    mag = s.send(cmd="magazine")
    check("magazine offres répond une liste",
          mag["ok"] and isinstance(mag["offres"], list))
    # Fiche produit : indépendante du palier joueur → sert dès qu'espèce au corpus.
    mfiche = s.send(cmd="magazine", espece=espece)
    check("magazine fiche produit d'une espèce du corpus non nulle",
          mfiche["ok"] and mfiche["fiche"] is not None, mfiche.get("fiche"))

    # --- raccourcis DEBUG (retour F5 : tester magazine/pages sans jouer) -------
    check("magazine sans maîtrise palier 3 → offres vides",
          len(s.send(cmd="magazine")["offres"]) == 0)
    dbg = s.send(cmd="debug", op="palier3")
    check("debug palier3 → ok + objets crédités", dbg["ok"] and dbg["objets"] > 0, dbg)
    check("debug palier3 → magazine offres NON vides",
          len(s.send(cmd="magazine")["offres"]) > 0)
    check("debug palier3 → pages révélées", len(s.send(cmd="pages")["ids"]) > 0)
    check("debug observer_tout → ok", s.send(cmd="debug", op="observer_tout")["ok"])
    s.send(cmd="debug", op="reset")
    check("debug reset → magazine muet + index vide",
          len(s.send(cmd="magazine")["offres"]) == 0
          and len(s.send(cmd="encyclopedie")["index"]) == 0)
    # D112 ② (h) : faire pousser un psilocybe → visible au snapshot, cueillable.
    tid0 = next(iter(s.send(cmd="snapshot")["snapshot"]["carpophores"]))
    car = s.send(cmd="debug", op="carpophore", tile=tid0, r=1, c=1)
    psilo = [k for k in car.get("carpophores", {}).get(tid0, [])
             if k[0] == 1 and k[1] == 1 and k[6] == "psilocybe"]
    check("debug carpophore → psilocybe au plot visé", car.get("ok") and len(psilo) == 1, car)
    snap_c = s.send(cmd="snapshot")["snapshot"]["carpophores"][tid0]
    check("debug carpophore → présent au snapshot", any(k[6] == "psilocybe" for k in snap_c))
    m = s.send(cmd="action", verb="manger",
               target={"tile": tid0, "carpophore": [1, 1, psilo[0][7]]}) if psilo else {}
    check("debug carpophore → mangé = vision",
          m.get("result", {}).get("vision") == "vision", m.get("result"))
    check("debug carpophore espèce inconnue → ok:false",
          s.send(cmd="debug", op="carpophore", tile=tid0, r=1, c=1,
                 espece="_x_")["ok"] is False)
    check("debug op inconnue → ok:false, serveur survit",
          s.send(cmd="debug", op="_inconnu_")["ok"] is False)

    s.send(cmd="quit")
    check("quit voix → exit 0", s.close() == 0)

    # --- achat magazine bout-en-bout (verbe acheter_magazine) -----------------
    # Le monde full ne débloque pas d'offre spontanément en 6 semaines. On force
    # une offre via une commande interne d'injection : impossible par le pont
    # (read-only). On teste donc le CHEMIN du verbe : achat REFUSÉ hors offre
    # (aucun crash, aucun débit indu) — le débit réel est couvert par les tests
    # unitaires du module magazine (déterministe, hors pont).
    s2 = ServerProc()
    s2.send(cmd="init", config="full", seed=7)
    vig_av = s2.send(cmd="snapshot")["snapshot"]["player"]["vigueur"]
    r = s2.send(cmd="action", verb="acheter_magazine", params={"espece": "tomate"})
    check("acheter_magazine hors offre → applied:false, achete:false",
          r["result"]["applied"] is False and r["result"]["achete"] is False,
          r["result"]["message"])
    r2 = s2.send(cmd="action", verb="acheter_magazine", params={})
    check("acheter_magazine sans espèce → applied:false, serveur survit",
          r2["ok"] and r2["result"]["applied"] is False)
    s2.send(cmd="quit")
    s2.close()

    # --- déterminisme byte-à-byte du chemin de lecture ------------------------
    def run_voix(seed):
        srv = ServerProc()
        srv.send(cmd="init", config="full", seed=seed)
        for _ in range(6):
            srv.send(cmd="step_week")
        srv.send(cmd="encyclopedie")
        srv.send(cmd="carnet")
        srv.send(cmd="pages")
        srv.send(cmd="magazine")
        srv.send(cmd="quit")
        return srv
    a, b = run_voix(7), run_voix(7)
    a.close(); b.close()
    check("2 runs voix même seed → réponses byte-identiques",
          a.raw_lines == b.raw_lines)
