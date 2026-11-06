"""
SYMBIOSE — tools/simserver/chronique.py
La CHRONIQUE DES ESPÈCES (D127, sprint chronique des espèces ②) : sur un run de
n'importe quelle longueur, QUAND chaque espèce végétale disparaît ou revient, et
DE QUOI meurent les plantes.

📖 Pourquoi pas le bilan de `perf_annees` ? Il ne garde que 60 ans et le top 3 des
espèces : une espèce minoritaire qui s'éteint y est invisible, et un run de 192 ans
n'en montre que la fin. Ici : TOUTES les espèces, mémoire NON bornée (≈ 40 espèces
× 200 ans, quelques centaines de Ko au pire).

Comment on compte — par IDENTITÉ des plantes, pas par le log seul :
  - À chaque recensement on note l'ensemble des plantes VIVANTES (`id(p)` → p ; on
    garde la référence, donc un `id` ne peut pas être réutilisé tant qu'on la tient).
  - Différence avec le recensement précédent : présentes avant, absentes ou mortes
    maintenant = MORTS ; absentes avant, vivantes maintenant = LEVÉES (germination
    férale, semis du joueur, ramet clonal, semis du parent… toutes voies confondues).
  - Le log du tick ne sert qu'à dire DE QUOI : chaque mort y est appariée à son
    événement `mort` (`sim.evenements`, causes canoniques du tronçon ①) par
    (tuile, plot, espèce).
Deux recensements par semaine, pour ne pas mélanger les morts :
  - `avant_tick` : ce qui a changé ENTRE deux ticks = gestes du joueur ou de
    l'automate (absents du log) → cause `hors_tick` ;
  - `apres_tick` : ce qui a changé PENDANT le tick → cause lue au log, ou
    `non_consignee` si le moteur n'a rien écrit (annélation par le campagnol, qui
    pose `vitalite = 0` sans ligne de log).

Golden NEUTRE : le golden tourne hors serveur, et ce module ne fait que LIRE.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from sim.evenements import evenements

# Clé d'espèce = celle du catalogue (comme `sim.evenements`), jamais `__name__`.
_CLE_DE_CLASSE = {cls: cle for d in (PLANT_CATALOGUE, PERENNIAL_CATALOGUE)
                  for cle, cls in d.items()}

HORS_TICK = "hors_tick"            # mort entre deux ticks (geste joueur / automate)
NON_CONSIGNEE = "non_consignee"    # mort pendant le tick sans ligne de log
PAS_TABLEAU = 10                   # une ligne de tableau tous les 10 ans


def _an(semaine: int) -> int:
    """Année d'une semaine, à la convention des bilans (`perf_annees`) : le bilan
    clos à la semaine 52·k porte le n° k et couvre les semaines 52·(k-1)+1 … 52·k."""
    return -(-semaine // 52)


def _cle(plant) -> str:
    cls = plant.plant_class
    return _CLE_DE_CLASSE.get(cls, getattr(cls, "name", cls.__name__))


def _annee_vierge() -> dict:
    return {"morts": defaultdict(Counter), "levees": Counter(), "autres": Counter()}


class Chronique:
    """Alimentée par `avant_tick` / `apres_tick` (cmd_step_week) ; `texte()` rend
    la section lisible, `brut()` les données."""

    def __init__(self):
        self._vivants: dict[int, tuple] | None = None   # id → (plante, tuile)
        self._effectifs: Counter = Counter()            # vivants par espèce
        self._annee = _annee_vierge()
        self.bilans: list[dict] = []
        self.registre: list[dict] = []
        self._eteintes: set[str] = set()                # espèces disparues à ce jour

    # --- Recensement -------------------------------------------------------
    @staticmethod
    def _recenser(engine) -> dict[int, tuple]:
        return {id(p): (p, t.tile_id) for t in engine.game_state["tiles"]
                for p in t.plants if p.is_alive}

    def avant_tick(self, engine) -> None:
        """Avant `tick_semaine()` : ce qui a bougé depuis le dernier tick vient des
        gestes (joueur, automate). Le tout premier appel pose seulement la base."""
        maintenant = self._recenser(engine)
        if self._vivants is None:
            self._vivants = maintenant
            self._effectifs = Counter(_cle(p) for p, _ in maintenant.values())
            return
        # `week` = la semaine qui VA être simulée : les gestes s'y rattachent (ils
        # tombent dans le même bilan annuel que leur accumulateur).
        self._appliquer(maintenant, {}, engine.game_state["week"], HORS_TICK)

    def apres_tick(self, engine, log: list[str]) -> None:
        """Après `tick_semaine()`, AVANT le vidage du log : morts appariées à leur
        cause, levées comptées, bilan clos la dernière semaine de l'année."""
        if self._vivants is None:          # appel sans avant_tick (test, outil)
            self._vivants, self._effectifs = {}, Counter()
        causes: dict[tuple, list] = defaultdict(list)
        # Tri préalable : toute ligne de mort contient « meurt » (🪦, ✗ → meurt, ❄/✿
        # meurt) ; on garde aussi les en-têtes de tuile `[T0]`. Mêmes événements
        # `mort` qu'un parse complet, ~0,7 ms au lieu de ~13 ms (full an 3, VM, n=10).
        utiles = [l for l in log if "meurt" in l or l.lstrip().startswith("[")]
        for ev in evenements(utiles):
            if ev.kind == "mort":
                causes[(ev.tile_id, ev.pos, ev.espece)].append((ev.cause, ev.raison))
        semaine = engine.game_state["week"] - 1   # `week` est déjà incrémenté
        self._appliquer(self._recenser(engine), causes, semaine, NON_CONSIGNEE)
        if semaine % 52 == 0:
            self._cloturer(semaine)

    def _appliquer(self, maintenant: dict, causes: dict, semaine: int,
                   defaut: str) -> None:
        """Différence entre deux recensements → morts (avec cause), levées, puis
        disparitions et retours d'espèces."""
        avant, an = self._vivants, self._annee
        dernieres: dict[str, dict] = {}            # dernière mort vue par espèce
        for i, (p, tuile) in avant.items():
            if i in maintenant:
                continue
            esp = _cle(p)
            pile = causes.get((tuile, p.position, esp))
            cause, raison = pile.pop(0) if pile else (defaut, None)
            an["morts"][esp][cause] += 1
            if raison:
                an["autres"][raison] += 1
            self._effectifs[esp] -= 1
            dernieres[esp] = {"cause": cause, "age_sem": p.age_weeks, "tuile": tuile}
        for i, (p, _) in maintenant.items():
            if i not in avant:
                esp = _cle(p)
                an["levees"][esp] += 1
                self._effectifs[esp] += 1
        self._vivants = maintenant
        for esp, mort in dernieres.items():
            if self._effectifs[esp] <= 0:
                self._eteintes.add(esp)
                self.registre.append({"semaine": semaine, "espece": esp,
                                      "quoi": "disparition", **mort})
        for esp in list(self._eteintes):
            if self._effectifs[esp] > 0:
                self._eteintes.discard(esp)
                self.registre.append({"semaine": semaine, "espece": esp,
                                      "quoi": "retour"})

    def _cloturer(self, semaine: int) -> None:
        an = self._annee
        n_an = _an(semaine)
        self.bilans.append({
            "an": n_an,
            "vivants": {e: n for e, n in sorted(self._effectifs.items()) if n > 0},
            "morts": {e: dict(c) for e, c in sorted(an["morts"].items())},
            "levees": dict(sorted(an["levees"].items())),
            "autres": dict(an["autres"]),
            "marquante": any(_an(r["semaine"]) == n_an for r in self.registre),
        })
        self._annee = _annee_vierge()

    # --- Restitution -------------------------------------------------------
    def brut(self) -> dict:
        return {"annees": self.bilans, "registre": self.registre}

    def texte(self) -> str:
        """LE formateur (vue C# et outil sans écran l'affichent tel quel) : un bilan
        tous les 10 ans + toute année à disparition/retour + la dernière, puis le
        registre complet."""
        lignes = [f"[chronique] {len(self.bilans)} bilans annuels, "
                  f"{len(self.registre)} disparitions/retours"]
        for i, b in enumerate(self.bilans):
            if b["an"] % PAS_TABLEAU == 0 or b["marquante"] or i == len(self.bilans) - 1:
                lignes += _bloc_annee(b)
        lignes.append("Registre des disparitions et retours :")
        if not self.registre:
            lignes.append("  (aucun)")
        for r in self.registre:
            tete = f"  an {_an(r['semaine'])} (sem {r['semaine']}) : {r['espece']}"
            if r["quoi"] == "retour":
                lignes.append(f"{tete} revient")
            else:
                lignes.append(f"{tete} disparaît, dernière mort : {r['cause']}, "
                              f"{r['age_sem']} sem d'âge, tuile {r['tuile']}")
        return "\n".join(lignes)


def _bloc_annee(b: dict) -> list[str]:
    """Trois lignes par année : vivants, morts par cause, levées (espèces triées)."""
    vivants = b["vivants"]
    out = [f"An {b['an']} : {sum(vivants.values())} plantes, {len(vivants)} espèces"
           + (" *" if b["marquante"] else ""),
           "  vivants : " + (" · ".join(f"{e} {n}" for e, n in vivants.items()) or "-")]
    morts = [f"{e} " + ", ".join(f"{c} {n}" for c, n in sorted(cs.items()))
             for e, cs in b["morts"].items()]
    out.append("  morts   : " + (" · ".join(morts) or "-"))
    out.append("  levées  : " + (" · ".join(f"{e} {n}" for e, n in b["levees"].items())
                                 or "-"))
    if b["autres"]:
        out.append("  autres  : " + " · ".join(f"{r} {n}" for r, n in b["autres"].items()))
    return out
