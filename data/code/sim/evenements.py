"""
SYMBIOSE — sim/evenements.py
Le PARSEUR D'ÉVÉNEMENTS partagé (sprint Voix narratives, tronçon ①).
Spec de référence : `docs/narration/voix/conception_voix_narratives.md` §1.2.

Le tick émet déjà, dans son `log` texte, des MARQUEURS lisibles (🌱 ⏸ 🌑 ❄ 🌊
🌰 🪦 ✗ 🍂 🍎 🐛 …). Jusqu'ici, seule la détection de maîtrise
(`maitrise_detection._evenements`) en parsait une PARTIE (avance/stagne/repro)
pour créditer la maîtrise. Ce module EXTRAIT ce parsing dans un endroit commun
et l'ÉLARGIT aux marqueurs que le carnet (tronçon ③) devra consigner.

Deux lecteurs partagent ce socle (doc §1.2) :

    evenements.py     ← parse PURE du log → flux d'événements typés
       ↑            ↑
  maitrise_detection  journal   (lecteurs ; aucun n'est importé par engine)

GARDE-FOU DE COUCHE : `evenements` est au niveau `sim`, AU-DESSUS du tick (comme
`maitrise_detection`). `engine`/`fields`/`plants` ne l'importent JAMAIS. Module
PUR : aucun RNG, aucun effet de bord, aucun import de couche haute — il ne lit
que le `log` texte qu'on lui passe et le retraduit en tuples.

DEUX API, par souci de refactor STRICTEMENT pur (le golden joueur
`test_maitrise_detection` doit rester bit-identique) :

  - `_evenements(log)` — l'HISTORIQUE, déplacé TEL QUEL depuis maitrise_detection.
    Yield `(kind, tile_id, pos, payload)`, `kind ∈ {avance, stagne, repro}`.
    `maitrise_detection` le ré-importe → son comportement est INCHANGÉ.
  - `evenements(log) -> list[Evenement]` — le NOUVEAU, élargi, pour le carnet.
    Renvoie le namedtuple unifié `Evenement(kind, tile_id, pos, espece, cause)`
    avec les kinds riches du doc (germination, stagnation, reproduction, mort,
    nouaison, abscission, ravageur…). Les deux fonctions partagent les regex.
"""
from __future__ import annotations

import re
from collections import namedtuple

from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE

# --- Type partagé (doc §1.2) -------------------------------------------------
# Un événement typé issu d'UNE ligne de log. `pos` = (r, c) plot-foyer ou None ;
# `tile_id` = id de tuile courante (lignes `[T0]`) ou None ; `espece` = clé du
# catalogue (ou None pour un événement sans plante : aléa météo, ravageur de
# saison) ; `cause` = sous-type string (sec/noyé/sénescence/conflit/…) ou None.
Evenement = namedtuple("Evenement", "kind tile_id pos espece cause")

# --- Reverse mappings, DÉRIVÉS des catalogues moteur (jamais dupliqués) -------
_CATALOGUE = {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}
_CLE_DE_NOM = {cls.name: cle for cle, cls in _CATALOGUE.items()}     # log → clé

# --- Parsing du log (les marqueurs que le tick émet déjà) --------------------
_POS = re.compile(r"@\((\d+),\s*(\d+)\)")           # @(r, c) — advance/stagnation/repro/mort/…
_RE_TILE = re.compile(r"^\[([^\]]+)\]$")            # ligne d'en-tête de tuile : [T0]
_RE_AVANCE = re.compile(r"🌱\s+(.+?)@")             # 🌱 <nom>@(r, c) → [...]
_RE_STAGNE = re.compile(r"(?:⏸|🌑|❄|🌊)\s+(.+?)@")  # ⏸/🌑/❄/🌊 <nom>@(r, c) stagne (...)
_RE_REPRO = re.compile(r"Reproduction\s*:\s*(.+?)\s+@")   # 🌰 Reproduction : <nom> @(r, c) [...]
_RE_TAG = re.compile(r"\b(auto|biparental|introgr\.)\b")  # tag de reproduction
# Élargissement carnet (doc §1.2) : marqueurs que la détection ignorait.
_RE_MORT = re.compile(r"🪦\s+(.+?)@")               # 🪦 <nom>@(r, c) meurt …
_RE_CONFLIT = re.compile(r"✗\s+(.+?)@")             # ✗ <nom>@(r, c) meurt (conflit)
_RE_NOUAISON = re.compile(r"🍎\s+Nouaison\s+(.+?)@")  # 🍎 Nouaison <nom>@(r, c) …
_RE_ABSCISSION = re.compile(r"🍂\s+Abscission\s+(.+?)@")  # 🍂 Abscission <nom>@(r, c) …
# Émission clonale (sprint LUXURIANCE ②/④) : 🌿 Ramet (<mode>) : <nom> @(r, c) …
# La cause de l'événement = le MODE clonal (stolon/rhizome/drageon) → le carnet
# distingue le tapissage stolonifère de la colonie rhizomateuse.
_RE_RAMET = re.compile(r"🌿\s+Ramet\s+\((\w+)\)\s*:\s*(.+?)\s+@")


def _raison_stagnation(line: str) -> str | None:
    """Cause d'une stagnation (`sec`/`ombre`/`froid`/`noyé`) lue dans la ligne de
    log, ou None si la ligne n'est pas une stagnation reconnue. Élargi à `noyé`
    (🌊, marqueur croissance.py) pour le carnet — la détection de maîtrise n'en a
    pas l'usage mais le partage est inoffensif (elle ne consomme que sec/ombre/
    froid via `CONCEPT_PAR_STAGNATION`)."""
    if "stagne (sec" in line:
        return "sec"
    if "stagne (ombre" in line:
        return "ombre"
    if "stagne (froid" in line:
        return "froid"
    if "stagne (noyé" in line:
        return "noyé"
    return None


def _raison_mort(line: str) -> str | None:
    """Cause d'une mort 🪦 lue dans le texte qui suit (sénescence/asphyxie). Les
    morts par conflit portent un marqueur distinct (✗) traité à part ; la mort
    hivernale annuelle (❄ … (annual)) et la monocarpie bisannuelle (✿) n'ont pas
    de cause au sens du carnet (§5.0) → non parsées ici (cf. TODO)."""
    if "meurt de sénescence" in line:
        return "sénescence"
    if "meurt asphyxié" in line:
        return "asphyxie"
    return None


def _evenements(log: list[str]):
    """API HISTORIQUE — déplacée TELLE QUELLE de maitrise_detection (refactor pur).
    Génère les transitions §9.1 lues dans le `log` d'UN tick, en suivant la tuile
    courante (lignes d'en-tête `[T0]`). Chaque événement est un tuple
    `(kind, tile_id, (r, c), payload)` — `kind ∈ {avance, stagne, repro}`.
    Lecture PURE (aucun effet de bord) : la détection de maîtrise consomme ce
    flux. Ne PAS toucher : sa stabilité fait passer `test_maitrise_detection`."""
    tile_id = None
    for line in log:
        stripped = line.strip()
        m_tile = _RE_TILE.match(stripped)
        if m_tile:
            tile_id = m_tile.group(1)
            continue
        m_pos = _POS.search(line)
        if not m_pos:
            continue
        pos = (int(m_pos.group(1)), int(m_pos.group(2)))
        if "🌱" in line:
            m = _RE_AVANCE.search(line)
            if m:
                yield ("avance", tile_id, pos, _CLE_DE_NOM.get(m.group(1).strip()))
        elif "🌰" in line:
            m = _RE_REPRO.search(line)
            tag = _RE_TAG.search(line)
            if m:
                yield ("repro", tile_id, pos,
                       (_CLE_DE_NOM.get(m.group(1).strip()),
                        tag.group(1) if tag else None))
        else:
            raison = _raison_stagnation(line)
            if raison in ("sec", "ombre", "froid"):
                m = _RE_STAGNE.search(line)
                if m:
                    yield ("stagne", tile_id, pos, raison)


def evenements(log: list[str]) -> list[Evenement]:
    """API PUBLIQUE ÉLARGIE — flux d'`Evenement` typés pour le carnet (tronçon ③).
    Lit le MÊME `log`, suit la tuile courante, et reconnaît les marqueurs RÉELS
    du moteur (déjà grepés). Disambiguation des emojis POLYSÉMIQUES :
      - 🍂 sert à `Abscission` MAIS aussi à `Nécromasse` / `Chute fruit` → on ne
        retient que les lignes contenant le mot `Abscission`.
      - 🍎 sert à `Nouaison` MAIS aussi au header `Récolte :` → on ne retient que
        les lignes contenant le mot `Nouaison`.
      - ❄ sert à la stagnation `froid`, MAIS aussi au header `gel [tile]` (sans
        @pos) et à la mort hivernale `(annual)` → seul `stagne (froid)` est gardé.
    Toute cause sans source claire reste un TODO nommé (pas de parsing inventé).

    Pur (aucun effet de bord, aucun RNG). Renvoie une LISTE (≠ générateur) car le
    carnet et ses tests itèrent plusieurs fois dessus."""
    out: list[Evenement] = []
    tile_id = None
    for line in log:
        stripped = line.strip()
        m_tile = _RE_TILE.match(stripped)
        if m_tile:
            tile_id = m_tile.group(1)
            continue

        # Ravageur de saison : header global, SANS @pos ni espèce (aléa) — §5.0.
        if "🐛" in line:
            out.append(Evenement("ravageur", tile_id, None, None, None))
            continue

        # Rosée / gelée blanche (sprint météo→champs ⑤) : marqueurs nocturnes de
        # TUILE émis par `rosee.tick_rosee` (💧 rosée / ❄ gelée blanche), SANS @pos
        # ni espèce (un aléa climatique, comme le ravageur de saison). On les teste
        # AVANT le `❄`-stagnation (le `❄` est polysémique : gel/stagnation/mort
        # hivernale) en exigeant le texte explicite « gelée blanche » → pas de
        # collision avec `stagne (froid)` (qui ne contient pas ce mot).
        if "💧" in line and "rosée" in line:
            out.append(Evenement("rosee", tile_id, None, None, None))
            continue
        if "❄" in line and "gelée blanche" in line:
            out.append(Evenement("gelee_blanche", tile_id, None, None, None))
            continue
        # Transport éolien de la litière (sprint VENT ⑦, §5.6) : marqueur de TUILE
        # 🍃 émis par `transport.tick_transport` les semaines de vent fort, SANS @pos
        # ni espèce (un phénomène de milieu, comme la rosée). On le teste AVANT le
        # `❄`-stagnation déjà passé ; 🍃 est polysémique (Abscission/Chute fruit en
        # portent un AVEC @pos) → on exige le mot « charrie » (jamais dans les autres
        # lignes 🍃) pour ne capter QUE le transport. Voix : concept « décomposition ».
        if "🍃" in line and "charrie" in line:
            out.append(Evenement("transport_litiere", tile_id, None, None, None))
            continue

        m_pos = _POS.search(line)
        if not m_pos:
            # TODO(voix): floraison — `🌸 Floraison :` n'est qu'un HEADER de
            # section (boucle.py:258), aucune ligne per-plante avec @pos sous lui
            # → pas de source à parser ici. À brancher si le moteur émet un jour
            # un marqueur de floraison par plante.
            # TODO(voix): acclimatation — signe DIÉGÉTIQUE calculé par
            # sim/semiologie.py (rendu), JAMAIS émis dans le log du tick → pas de
            # marqueur source. À brancher si un marqueur d'acclimatation apparaît.
            continue
        pos = (int(m_pos.group(1)), int(m_pos.group(2)))

        if "🌱" in line:
            m = _RE_AVANCE.search(line)
            if m:
                # germination/levée — le moteur n'émet qu'un seul marqueur 🌱
                # d'avance de stade ; on l'expose en `germination` (le carnet ne
                # distingue pas finement levée vs germination, doc §5.0).
                out.append(Evenement("germination", tile_id, pos,
                                     _CLE_DE_NOM.get(m.group(1).strip()), None))
        elif "🌰" in line:
            m = _RE_REPRO.search(line)
            tag = _RE_TAG.search(line)
            if m:
                out.append(Evenement("reproduction", tile_id, pos,
                                     _CLE_DE_NOM.get(m.group(1).strip()),
                                     tag.group(1) if tag else None))
        elif "🪦" in line:
            m = _RE_MORT.search(line)
            if m:
                out.append(Evenement("mort", tile_id, pos,
                                     _CLE_DE_NOM.get(m.group(1).strip()),
                                     _raison_mort(line)))
        elif "✗" in line:
            m = _RE_CONFLIT.search(line)
            if m:
                out.append(Evenement("mort", tile_id, pos,
                                     _CLE_DE_NOM.get(m.group(1).strip()), "conflit"))
        elif "🍎" in line and "Nouaison" in line:
            m = _RE_NOUAISON.search(line)
            if m:
                out.append(Evenement("nouaison", tile_id, pos,
                                     _CLE_DE_NOM.get(m.group(1).strip()), None))
        elif "🍂" in line and "Abscission" in line:
            m = _RE_ABSCISSION.search(line)
            if m:
                out.append(Evenement("abscission", tile_id, pos,
                                     _CLE_DE_NOM.get(m.group(1).strip()), None))
        elif "🌿" in line and "Ramet" in line:
            # Émission clonale (luxuriance ②/④) : espèce = groupe 2, cause = mode
            # clonal (groupe 1). Le carnet gate ce fait sous le concept
            # « reproduction » (la colonie perpétue la lignée sans graine).
            m = _RE_RAMET.search(line)
            if m:
                out.append(Evenement("ramet", tile_id, pos,
                                     _CLE_DE_NOM.get(m.group(2).strip()), m.group(1)))
        else:
            raison = _raison_stagnation(line)
            if raison:
                m = _RE_STAGNE.search(line)
                if m:
                    out.append(Evenement("stagnation", tile_id, pos,
                                         _CLE_DE_NOM.get(m.group(1).strip()), raison))
    return out
