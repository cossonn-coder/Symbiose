# SYMBIOSE — tools/diag_releve.py
# Diagnostic de la RELÈVE DES LIGNEUX (D130, sprint relève ligneuse ④).
#
# Question : sur un run long, chaque arbre se remplace-t-il (taux de remplacement
# ≥ 1 par fondateur), sans fourré de semis sous les couronnes ?
#
# 📖 Méthode — même chemin que `tools/chronique_run.py` (SimServer.cmd_init puis
# `cmd_step_week`), mais on suit chaque LIGNEUX par IDENTITÉ (`id(p)`, référence
# gardée → l'id ne peut pas être réutilisé) :
#   - fondateurs = ligneux vivants au départ ; recrues = ligneux apparus ensuite ;
#   - voie de naissance : `ramet` si le log du tick porte un événement `ramet` de
#     la même espèce au même plot (clonales : stolon/rhizome/drageon) ; `rejet` si le
#     log porte un événement `rejet` (souche, frein rejets ④) de la même espèce sur la
#     même tuile à ≤ PORTEE_REJET_PLOTS plots de l'arbre (le log ne donne que le plot
#     du 1ᵉʳ rejet et celui de l'arbre ; rayon 60 cm ⇒ ≤ 2 plots) ; sinon `graine` ;
#   - cause de mort : appariée à l'événement `mort` du log (tuile, plot, espèce),
#     comme la chronique du rapport C ;
#   - toutes les 13 semaines : lumière reçue, `shade_memory`, hauteur de chaque
#     recrue vivante, et le FOURRÉ = nombre de ligneux plus petits que `H_GAULE`
#     sous la couronne (distance < rayon de couronne) de chaque adulte.
# « Mûr » = `age_years ≥ maturity_years` de l'espèce (âge de 1ʳᵉ fructification).
#
# Régime HORS-LIGNE, lecture seule : golden INTACT (le golden tourne hors serveur).
#
# Usage (depuis data/code/) :
#   python3 -m tools.diag_releve --config verger_mur --annees 200 [--seed 42] [--sortie DIR]
# Sorties : DIR/releve.json (brut par individu) + DIR/releve.txt (résumé).

from __future__ import annotations
import argparse
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

from sim.effects.perturbations import H_GAULE
from sim.evenements import evenements
from tools.simserver.chronique import _cle

PAS_ECHANTILLON = 13      # semaines entre deux relevés (une saison)
PORTEE_REJET_PLOTS = 2    # ceil(RAYON_REJET_CM 60 / PLOT_CM 50) : plots autour de l'arbre


def _ligneux_vivants(engine) -> dict[int, tuple]:
    return {id(p): (p, t.tile_id) for t in engine.game_state["tiles"]
            for p in t.plants if p.is_alive and p.plant_class.ligneux}


def _voie(tuile, pos, espece, ramets, rejets) -> str:
    """Voie de naissance d'une recrue d'après les événements du tick."""
    if (tuile, pos, espece) in ramets:
        return "ramet"
    for t, (r, c), e in rejets:
        if t == tuile and e == espece and max(abs(pos[0] - r), abs(pos[1] - c)) \
                <= PORTEE_REJET_PLOTS:
            return "rejet"
    return "graine"


class Releve:
    """Suivi par identité des ligneux d'un run (fondateurs + recrues)."""

    def __init__(self, engine):
        self.engine = engine
        self.vivants = _ligneux_vivants(engine)
        self.indiv: dict[int, dict] = {}
        for i, (p, tuile) in self.vivants.items():
            self.indiv[i] = self._fiche(p, tuile, 0, "fondateur")
        self.fourre_max = {"n": 0, "semaine": None, "adulte": None}

    @staticmethod
    def _fiche(p, tuile, semaine, voie) -> dict:
        return {"espece": _cle(p), "tuile": tuile, "pos": list(p.position),
                "x_cm": round(p.x_cm), "y_cm": round(p.y_cm), "ne": semaine,
                "voie": voie, "mort": None, "cause": None, "age_mort_sem": None,
                "mur": None, "echantillons": [], "_p": p}

    def apres_tick(self, semaine: int, log: list[str]) -> None:
        """Naissances (voie), morts (cause), puis relevé saisonnier."""
        evs = evenements(log)
        ramets = {(e.tile_id, e.pos, e.espece) for e in evs if e.kind == "ramet"}
        rejets = [(e.tile_id, e.pos, e.espece) for e in evs if e.kind == "rejet"]
        causes = defaultdict(list)
        for e in evs:
            if e.kind == "mort":
                causes[(e.tile_id, e.pos, e.espece)].append(e.cause)
        maintenant = _ligneux_vivants(self.engine)
        for i, (p, tuile) in self.vivants.items():
            if i not in maintenant:
                f = self.indiv[i]
                pile = causes.get((tuile, p.position, f["espece"]))
                f["mort"], f["age_mort_sem"] = semaine, p.age_weeks
                f["cause"] = pile.pop(0) if pile else "non_consignee"
        for i, (p, tuile) in maintenant.items():
            if i not in self.indiv:
                voie = _voie(tuile, p.position, _cle(p), ramets, rejets)
                self.indiv[i] = self._fiche(p, tuile, semaine, voie)
        self.vivants = maintenant
        for i, (p, _) in maintenant.items():
            f = self.indiv[i]
            if f["mur"] is None and p.age_years >= p.plant_class.maturity_years:
                f["mur"] = semaine
        if semaine % PAS_ECHANTILLON == 0:
            self._echantillonner(semaine)

    def _echantillonner(self, semaine: int) -> None:
        eco_de = self.engine.game_state["eco"]
        hauteurs = {}
        for i, (p, tuile) in self.vivants.items():
            h = p.plant_class.height_at(p)
            hauteurs[i] = h
            f = self.indiv[i]
            if f["voie"] != "fondateur":
                lum = eco_de[tuile].lumiere.light_received(p)
                f["echantillons"].append([semaine, round(lum, 3),
                                          round(p.shade_memory, 3), round(h)])
        # Fourré : petits ligneux sous la couronne de chaque adulte (h ≥ H_GAULE).
        for i, (a, ta) in self.vivants.items():
            if hauteurs[i] < H_GAULE:
                continue
            r = a.plant_class.canopy_radius_at(a)
            n = sum(1 for j, (p, tp) in self.vivants.items()
                    if j != i and tp == ta and hauteurs[j] < H_GAULE
                    and math.hypot(p.x_cm - a.x_cm, p.y_cm - a.y_cm) < r)
            if n > self.fourre_max["n"]:
                self.fourre_max = {"n": n, "semaine": semaine,
                                   "adulte": self.indiv[i]["espece"]}

    def bilan(self) -> dict:
        """Par espèce : fondateurs, recrues (par voie), recrues mûres, morts par
        cause, remplacement (recrues mûres / fondateurs), vivants en fin de run."""
        par = defaultdict(lambda: {"fondateurs": 0, "fondateurs_morts": 0,
                                   "recrues": defaultdict(int), "recrues_mures": 0,
                                   "morts": defaultdict(int), "vivants_fin": 0,
                                   "ages_mort_recrues_ans": []})
        for f in self.indiv.values():
            b = par[f["espece"]]
            fond = f["voie"] == "fondateur"
            if fond:
                b["fondateurs"] += 1
                b["fondateurs_morts"] += f["mort"] is not None
            else:
                b["recrues"][f["voie"]] += 1
                b["recrues_mures"] += f["mur"] is not None
                if f["mort"] is not None:
                    b["ages_mort_recrues_ans"].append(round(f["age_mort_sem"] / 52, 1))
            if f["mort"] is not None:
                b["morts"][f["cause"]] += 1
            else:
                b["vivants_fin"] += 1
        for b in par.values():
            b["remplacement"] = (b["recrues_mures"] / b["fondateurs"]
                                 if b["fondateurs"] else None)
            b["recrues"], b["morts"] = dict(b["recrues"]), dict(b["morts"])
        return {"especes": dict(par), "fourre_max": self.fourre_max}

    def brut(self) -> list[dict]:
        return [{k: v for k, v in f.items() if k != "_p"} for f in self.indiv.values()]


def _texte(bilan: dict, annees: int) -> str:
    out = [f"[diag_releve] {annees} ans, H_GAULE {H_GAULE:.0f} cm"]
    for esp, b in sorted(bilan["especes"].items()):
        ages = b["ages_mort_recrues_ans"]
        rem = "-" if b["remplacement"] is None else f"{b['remplacement']:.2f}"
        out.append(f"  {esp} : fondateurs {b['fondateurs']} (morts {b['fondateurs_morts']})"
                   f" · recrues {b['recrues']} · mûres {b['recrues_mures']}"
                   f" · remplacement {rem} · vivants fin {b['vivants_fin']}")
        out.append(f"      morts {b['morts']} · âge de mort des recrues (ans) "
                   f"min {min(ages) if ages else '-'} méd "
                   f"{sorted(ages)[len(ages) // 2] if ages else '-'} max "
                   f"{max(ages) if ages else '-'}")
    fm = bilan["fourre_max"]
    out.append(f"  fourré max : {fm['n']} petits ligneux sous une couronne "
               f"({fm['adulte']}, sem {fm['semaine']})")
    return "\n".join(out)


def lancer(config: str, annees: int, seed: int | None, sortie: Path) -> dict:
    from tools.simserver.server import SimServer
    srv = SimServer()
    msg = {"config": config} if seed is None else {"config": config, "seed": seed}
    if not srv.cmd_init(msg).get("ok"):
        raise RuntimeError("cmd_init a échoué")
    rel = Releve(srv.engine)
    # `cmd_step_week` VIDE le log avant de rendre la main : on se greffe sur la
    # lecture de la chronique (même instant, log encore plein), sans rien modifier.
    chro_apres = srv._chronique.apres_tick

    def _greffe(engine, log):
        chro_apres(engine, log)
        rel.apres_tick(engine.game_state["week"] - 1, log)
    srv._chronique.apres_tick = _greffe
    t0 = time.perf_counter()
    for semaine in range(1, annees * 52 + 1):
        rep = srv.cmd_step_week({})
        if not rep.get("ok"):
            raise RuntimeError(f"step_week a échoué semaine {semaine} : {rep}")
        if semaine % 520 == 0:
            print(f"[diag_releve] an {semaine // 52} : {len(rel.vivants)} ligneux, "
                  f"{(time.perf_counter() - t0) / 60:.1f} min", file=sys.stderr, flush=True)
    bilan = rel.bilan()
    sortie.mkdir(parents=True, exist_ok=True)
    with open(sortie / "releve.json", "w", encoding="utf-8") as f:
        json.dump({"bilan": bilan, "individus": rel.brut()}, f, ensure_ascii=False)
    (sortie / "releve.txt").write_text(_texte(bilan, annees) + "\n", encoding="utf-8")
    return bilan


def main() -> int:
    ap = argparse.ArgumentParser(description="Relève des ligneux : remplacement, fourré.")
    ap.add_argument("--config", default="verger_mur")
    ap.add_argument("--annees", type=int, default=200)
    ap.add_argument("--seed", type=lambda s: int(s, 0), default=None)
    ap.add_argument("--sortie", type=Path, default=Path("."))
    args = ap.parse_args()
    print(_texte(lancer(args.config, args.annees, args.seed, args.sortie), args.annees))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
