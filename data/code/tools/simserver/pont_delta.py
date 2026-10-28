"""
SYMBIOSE — tools/simserver/pont_delta.py
Segments des plantes EN DELTA pour la vue (sprint FLUIDITÉ PC LEVIERS ④,
protocole 0.6.0). OPT-IN : seule une requête qui porte `"delta"` reçoit ce format ;
sans la clé, le snapshot reste COMPLET et identique (tests, outils, save).

Constat (VM, s92→s95, monde `full`, ~10 900 segments) : d'une semaine à l'autre
~3 % des segments naissent et ~26 % changent (longueur, épaisseur, apex, parent
après une taille) ; les ~71 % restants ne changent QUE par `age_weeks` (+1). On
transmet donc la SEMAINE DE NAISSANCE (`semaine − age_weeks`, dérivée ici sans
toucher `sim/`) : elle ne bouge pas, et la vue recalcule `age = semaine − naissance`.

Format, par plante du sol (les plantes des CONTENEURS restent au format complet) :
  - `pid`  : identifiant entier stable de la plante pour CE serveur (≠ la clé de
             diff de la vue tile|species|x|y, qui reste inchangée) ;
  - `segd` : liste d'opérations qui reconstruisent la liste de segments à partir
             de celle envoyée la fois précédente pour ce `pid` (curseur `j` = 0) :
               · entier k > 0 → recopier les k anciens segments [j, j+k), j += k ;
               · entier k < 0 → sauter |k| anciens segments (retirés), j += |k| ;
               · liste de 11 → segment LITTÉRAL (nouveau ou changé), j inchangé :
                 [parent, bx, by, bz, dx, dy, dz, longueur, épaisseur, apex 0/1,
                  semaine de naissance] (mêmes arrondis que `segments_pont`) ;
  - `genes` : seulement au PREMIER envoi d'un `pid` (le génome ne change jamais).
Au niveau du snapshot : `delta = {complet, disparues}` — `complet` vrai quand
l'état client a été oublié (la vue vide alors le sien), `disparues` = pids envoyés
la fois précédente et absents de celle-ci (mortes, retirées).

Identité d'un segment : l'OBJET `Segment` (la croissance ajoute en fin de liste ;
la taille / l'élagage reconstruisent la liste en gardant les survivants dans
l'ordre, cf. `sim/growth/geometrie._rebuild`). Une recopie n'est émise que si le
MÊME objet a la MÊME charge utile arrondie → reconstruction EXACTE par construction
(un ordre inattendu dégrade en littéraux, jamais en faux). Vérifié par
`tests/simserver/delta.py` (taille + mort comprises).

📖 Pédagogie (côté embarqué) : c'est la compression d'une trame de télémesure
par « image clé + différences » — on n'envoie que ce qui a bougé depuis la
dernière trame ACQUITTÉE ; ici le tube est fiable et ordonné, donc chaque envoi
vaut acquit. Si le récepteur perd le fil, il demande une image clé (`complet`).
"""
from __future__ import annotations


def mode_delta(server, msg: dict):
    """Le `DeltaPont` du serveur si la requête demande le delta, sinon None
    (snapshot complet historique). `"delta": "complet"` = resynchronisation :
    l'état client est oublié avant la passe."""
    mode = msg.get("delta") if isinstance(msg, dict) else None
    if not mode:
        return None
    d = server._delta
    if mode == "complet":
        d.oublier()
    return d


class DeltaPont:
    """État « dernier envoyé » du client (un serveur = un client, la vue)."""

    def __init__(self):
        self._etat: dict = {}      # id(plante) → (plante, pid, [(segment, charge, brut)])
        self._vus: dict = {}       # même forme, rempli pendant la passe courante
        self._prochain_pid = 1
        self._complet = True       # rien envoyé encore = la prochaine passe est complète
        self._semaine = 0

    def oublier(self) -> None:
        """Le client repart de zéro (resynchro, nouveau monde) : tout sera renvoyé."""
        self._etat = {}
        self._complet = True

    def debut(self, semaine: int) -> None:
        self._vus = {}
        self._semaine = semaine

    def plante(self, base: dict, p, segv) -> bool:
        """Pose `pid` + `segd` dans `base` (dict plante du snapshot). Renvoie True
        si c'est le premier envoi de la plante (→ l'appelant joint `genes`)."""
        prec = self._etat.get(id(p))
        neuve = prec is None or prec[0] is not p
        if neuve:
            pid = self._prochain_pid
            self._prochain_pid += 1
            ancien = ()
        else:
            pid, ancien = prec[1], prec[2]
        semaine = self._semaine
        actuel = []
        ops = []
        copies = 0               # recopies en attente (fusionnées en UN entier)
        j = 0                    # curseur dans l'ancienne liste
        index = None             # id(segment) → indice ancien, construit au 1er écart
        n_anc = len(ancien)
        for s in p.segments:
            brut = (s.base, s.dir, s.length_cm, s.thickness_cm, s.parent,
                    s.is_apex, semaine - s.age_weeks)
            if j < n_anc and ancien[j][0] is s:
                m = j
            else:
                if index is None:
                    index = {id(o[0]): k for k, o in enumerate(ancien)}
                m = index.get(id(s), -1)
                if m >= 0 and ancien[m][0] is not s:
                    m = -1
            if m >= j:
                if m > j:                                  # anciens retirés
                    if copies:
                        _pousser(ops, copies)
                        copies = 0
                    _pousser(ops, j - m)
                    j = m
                j += 1
                a = ancien[m]
                # Chemin rapide (PARTAGE ①) : grandeurs BRUTES inchangées (base, dir,
                # longueur, épaisseur, parent, apex, naissance — une seule égalité de
                # tuple, faite en C) ⇒ charge arrondie inchangée par construction →
                # recopie, sans arrondi ni passage par le cache de `segments_pont`.
                if a[2] == brut:
                    actuel.append(a)
                    copies += 1
                    continue
                charge = _charge(segv.entree(s), brut)
                actuel.append((s, charge, brut))
                if a[1] == charge:                         # arrondi identique
                    copies += 1
                    continue
                if copies:
                    _pousser(ops, copies)
                    copies = 0
                _pousser(ops, -1)                          # l'ancien changé est sauté
            else:
                charge = _charge(segv.entree(s), brut)
                actuel.append((s, charge, brut))
                if copies:
                    _pousser(ops, copies)
                    copies = 0
            ops.append(list(charge))                       # nouveau ou changé
        if copies:
            _pousser(ops, copies)
        self._vus[id(p)] = (p, pid, actuel)
        base["pid"] = pid
        base["segd"] = ops
        return neuve

    def fin(self) -> dict:
        """Clôt la passe : bloc `delta` du snapshot, puis l'état devient l'envoyé."""
        vus = self._vus
        disparues = sorted(e[1] for k, e in self._etat.items() if k not in vus)
        bloc = {"complet": self._complet, "disparues": disparues}
        self._etat, self._vus = vus, {}
        self._complet = False
        return bloc


def _charge(e: tuple, brut: tuple) -> tuple:
    """Charge utile d'un segment (format d'un littéral `segd`) depuis son entrée de
    cache `segments_pont` (indices 5-8 = base, dir, longueur, épaisseur arrondies)
    et ses grandeurs brutes (indices 4-6 = parent, apex, semaine de naissance)."""
    b, d = e[5], e[6]
    return (brut[4], b[0], b[1], b[2], d[0], d[1], d[2], e[7], e[8],
            1 if brut[5] else 0, brut[6])


def _pousser(ops: list, k: int) -> None:
    """Ajoute une recopie (k > 0) ou un saut (k < 0), fusionné avec le précédent
    de même signe (une plante inchangée tient en UN entier)."""
    if ops and type(ops[-1]) is int and (ops[-1] > 0) == (k > 0):
        ops[-1] += k
    else:
        ops.append(k)
