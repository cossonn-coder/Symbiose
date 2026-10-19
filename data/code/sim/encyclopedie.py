"""
SYMBIOSE — sim/encyclopedie.py
L'ENCYCLOPÉDIE — deuxième des quatre voix narratives (sprint Voix narratives,
tronçon ④, dette « 4ᵉ voix »).
Spec de référence : `docs/narration/voix/conception_voix_narratives.md` §2.2 + §6.

Voix « naturaliste qui observe » (3ᵉ personne, factuelle). L'encyclopédie est un
LECTEUR read-only : elle ne consigne RIEN, n'avance aucun tick, n'utilise aucun
RNG. Contrairement au carnet (③, qui lit le LEDGER d'événements), l'encyclopédie
lit le PALIER de maîtrise de l'ESPÈCE (D12, `sim/maitrise.py`) et renvoie sa fiche
du corpus (`sim/encyclopedie_corpus.py`, donnée §6) tronquée au bon niveau :

  - palier 1 (découverte)     → niveau 1 (silhouette, organes observés) ;
  - palier 2 (investissement) → + niveau 2 (biologie : cycle, besoins, famille) ;
  - palier ≥ 3 (maîtrise)     → + niveau 3 (rôle écosystémique).

« Pas d'état neuf » (kickoff) : une espèce a une fiche SSI `palier(espèce) ≥ 1`.
La maîtrise PORTE déjà la découverte (la détection crédite repro → p2, succès
répétés → p3) ; le palier EST la progression d'observation décrite par CLAUDE.md.
On ne stocke RIEN dans `game_state` — tout dérive de `maitrise` + corpus.

DÉCISION A FIGÉE (doc §0) : seulement 3 niveaux. Les paliers 4 et 5 (expertise /
transcendant) ne débloquent PAS de niveau 4 — on plafonne à `min(palier, 3)` (les
nuances expertise/transcendant sont un enrichissement futur du corpus, doc §8.3).

GARDE-FOU DE COUCHE (identique à `carnet.py` / `journal.py` / `maitrise.py`) :
`encyclopedie` est au niveau `sim`, AU-DESSUS du tick. **`engine`/`fields`/`plants`
ne l'importent JAMAIS.** Pas de joueur / pas de maîtrise → `encyclopedie_index`
renvoie `[]` et `encyclopedie_lire` renvoie `None` (no-op golden, jamais de crash).
"""
from __future__ import annotations

from sim import maitrise
from sim.encyclopedie_corpus import FICHES
from sim.encyclopedie_types import type_de
from sim.champignon_encyclo import CLE_CHAMPIGNON, encyclo_meta as _champignon_meta
from sim.concept_corpus import FICHES_CONCEPT
from sim.technique_corpus import FICHES_TECHNIQUE
from sim.geste_corpus import FICHES_GESTE
from sim.outil_corpus import FICHES_OUTIL
from fields.faune_encyclo import FAUNE_ENCYCLO, encyclo_meta as _faune_meta
from sim.signes_corpus import SIGNES
from sim.signes import signe_appris

# --- Calibrage (décision A, doc §0 — figée, pas un knob de tuning) ------------
# Niveau de fiche maximum : l'encyclopédie n'a que 3 niveaux (basique / bio /
# écosystémique). On tronque toujours à min(palier, NIVEAU_MAX) — un palier 4 ou 5
# ne révèle pas de 4ᵉ niveau (corpus paliers 4-5 = enrichissement futur, doc §8.3).
NIVEAU_MAX = 3

# Registre (D60 §5) des corpus 3-niveaux des types NEUFS (concept · technique ·
# outil · geste). Le dispatch consulte ce registre pour ces types ; tant qu'un
# type/clé n'y est pas, on renvoie `None` proprement (pas de crash). Structure :
# `{type: {cle: {1,2,3}}}`. ④ a branché concept + technique ; ⑤ branche outil +
# geste. Les 4 types NEUFS ont désormais leur corpus 3-niveaux. L'alignement
# clé↔classification (zéro trou, zéro surplus) est vérifié par le test.
CORPUS_PAR_TYPE: dict[str, dict[str, dict[int, str]]] = {
    "concept":   FICHES_CONCEPT,
    "technique": FICHES_TECHNIQUE,
    "outil":     FICHES_OUTIL,
    "geste":     FICHES_GESTE,
}


def _decouverte(game_state: dict, player: str, cle: str) -> bool:
    """Une clé est « découverte » (donc a une entrée) SSI son palier de maîtrise
    est ≥ 1 (kickoff : « pas d'état neuf, palier ≥ 1 ⇒ fiche »). Lecture pure de
    `maitrise.palier` (ne crée AUCUNE clé → no-op golden)."""
    return maitrise.palier(game_state, player, cle) >= 1


# Ordre STABLE d'énumération de l'index : d'abord par type (ordre des onglets),
# puis, à l'intérieur d'un type, l'ordre de son corpus source. Les plantes gardent
# l'ordre de `FICHES`, la faune celui de `FAUNE_ENCYCLO`, etc.
# `signe` (PLANTE ASSEMBLÉE ⑥) : 8ᵉ type, HORS `encyclopedie_types` — un signe n'est
# pas une clé de maîtrise ; sa fiche s'ouvre quand il est APPRIS (`sim/signes.py`).
_ORDRE_TYPES = ("plante", "animal", "champignon", "concept", "technique", "outil", "geste",
                "signe")


def _cles_du_type(nom_type: str) -> list[str]:
    """Clés d'un type dans l'ordre de son corpus source (stable, déterministe).
    Concept/technique/outil/geste tirent leur ordre de `CORPUS_PAR_TYPE` (vide
    d'ici ④⑤) → aucune entrée servie tant que le corpus n'existe pas."""
    if nom_type == "plante":
        return list(FICHES)
    if nom_type == "animal":
        return list(FAUNE_ENCYCLO)
    if nom_type == "champignon":
        return [CLE_CHAMPIGNON]
    if nom_type == "signe":
        return list(SIGNES)
    return list(CORPUS_PAR_TYPE.get(nom_type, {}))


def encyclopedie_index(game_state: dict, player: str,
                       type_filtre: str | None = None) -> list[dict]:
    """Index des entrées DÉCOUVERTES (palier ≥ 1), TAGUÉES par type (D60 §5) :
    liste de `{cle, type, titre}`. `type_filtre` optionnel restreint à un onglet
    (les 7 types) — sinon toutes les entrées, dans l'ordre stable des types puis
    des corpus. Sans couche maîtrise ni joueur → `[]` (golden-safe). PUR.

    `titre` = la clé lisible (le joli libellé viendra du corpus au ④⑤ ; ici la clé
    suffit — l'UI ⑥ affichera le titre). Une clé découverte hors corpus (type
    `None`) est ignorée (pas de crash)."""
    entrees: list[dict] = []
    for nom_type in _ORDRE_TYPES:
        if type_filtre is not None and nom_type != type_filtre:
            continue
        for cle in _cles_du_type(nom_type):
            ouverte = (signe_appris(game_state, player, cle) if nom_type == "signe"
                       else _decouverte(game_state, player, cle))
            if ouverte:
                entrees.append({"cle": cle, "type": nom_type, "titre": cle})
    return entrees


def _lire_plante(cle: str, palier: int) -> dict | None:
    """Fiche PLANTE (comportement inchangé) : tronquée à `min(palier, 3)`, corpus
    `FICHES`. Clé hors corpus → `None`."""
    fiche = FICHES.get(cle)
    if fiche is None:
        return None
    niveau_max = min(palier, NIVEAU_MAX)
    niveaux = {n: fiche[n] for n in range(1, niveau_max + 1)}
    return {"cle": cle, "type": "plante", "niveau_max": niveau_max, "niveaux": niveaux}


def _lire_mono(cle: str, nom_type: str, meta: dict) -> dict:
    """Fiche MONO-niveau (animal, champignon) : blurb + graphe d'interconnexions,
    plafonnée à palier 1 (la détection ne les crédite pas). `meta` = `{blurb,
    interconnexions}` de la source (`faune_encyclo` / `champignon_encyclo`)."""
    return {
        "cle": cle, "type": nom_type, "niveau_max": 1,
        "niveaux": {1: meta["blurb"]},
        "interconnexions": list(meta["interconnexions"]),
    }


def _lire_corpus_3n(cle: str, nom_type: str, palier: int) -> dict | None:
    """Fiche 3-niveaux d'un type NEUF (concept/technique/outil/geste), lue dans
    `CORPUS_PAR_TYPE`. VIDE d'ici ④⑤ → `None` propre (point d'extension posé)."""
    fiche = CORPUS_PAR_TYPE.get(nom_type, {}).get(cle)
    if fiche is None:
        return None
    niveau_max = min(palier, NIVEAU_MAX)
    niveaux = {n: fiche[n] for n in range(1, niveau_max + 1)}
    return {"cle": cle, "type": nom_type, "niveau_max": niveau_max, "niveaux": niveaux}


def encyclopedie_lire(game_state: dict, player: str, cle: str) -> dict | None:
    """Fiche d'une clé, DISPATCHÉE par `type_de(cle)` (D60 §5). Renvoie `None` si
    la clé n'est pas découverte (palier 0) ou si son type n'a pas (encore) de
    corpus. Structure de retour (miroir plante enrichi d'un `type`) :

        {"cle": …, "type": …, "niveau_max": …, "niveaux": {1:…, …},
         "interconnexions": [...]}   # présent seulement pour animal/champignon

    - plante                      → 3 niveaux, `min(palier, 3)` (inchangé) ;
    - animal / champignon         → mono-niveau (blurb + graphe), cap palier 1 ;
    - concept/technique/outil/geste → corpus 3-niveaux quand il existe (④⑤), sinon
      `None` proprement.

    - signe (⑥)                   → corpus 3-niveaux des signes, ouvert quand le
      signe est APPRIS ; niveau = `min(palier(concept), 3)`.

    PUR : lit `maitrise.palier` + les corpus, n'écrit RIEN. Clé de type inconnu
    (`type_de` → `None`) → `None` (jamais de crash)."""
    if cle in SIGNES and type_de(cle) is None:
        return _lire_signe(game_state, player, cle)
    p = maitrise.palier(game_state, player, cle)
    if p < 1:
        return None
    nom_type = type_de(cle)
    if nom_type == "plante":
        return _lire_plante(cle, p)
    if nom_type == "animal":
        return _lire_mono(cle, "animal", _faune_meta(cle))
    if nom_type == "champignon":
        return _lire_mono(cle, "champignon", _champignon_meta())
    if nom_type in CORPUS_PAR_TYPE:
        return _lire_corpus_3n(cle, nom_type, p)
    return None


def _lire_signe(game_state: dict, player: str, cle: str) -> dict | None:
    """Fiche « signe » (⑥) : fermée tant que le signe n'est pas appris (même bascule
    que le carnet). Ouverte, elle est tronquée au palier du CONCEPT du signe (au
    seuil normal 3 → les 3 niveaux ; option « anticipé » → selon le palier)."""
    if not signe_appris(game_state, player, cle):
        return None
    p = maitrise.palier(game_state, player, SIGNES[cle]["concept"])
    niveau_max = max(1, min(p, NIVEAU_MAX))
    fiche = SIGNES[cle]["fiche"]
    niveaux = {n: fiche[n] for n in range(1, niveau_max + 1)}
    return {"cle": cle, "type": "signe", "niveau_max": niveau_max, "niveaux": niveaux}
