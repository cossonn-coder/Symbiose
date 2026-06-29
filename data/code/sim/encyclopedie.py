"""
SYMBIOSE — sim/encyclopedie.py
L'ENCYCLOPÉDIE — deuxième des quatre voix narratives (sprint Voix narratives,
tronçon ④, dette « 4ᵉ voix »).
Spec de référence : `docs/conception/CONCEPTION_VOIX_NARRATIVES.md` §2.2 + §6.

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

# --- Calibrage (décision A, doc §0 — figée, pas un knob de tuning) ------------
# Niveau de fiche maximum : l'encyclopédie n'a que 3 niveaux (basique / bio /
# écosystémique). On tronque toujours à min(palier, NIVEAU_MAX) — un palier 4 ou 5
# ne révèle pas de 4ᵉ niveau (corpus paliers 4-5 = enrichissement futur, doc §8.3).
NIVEAU_MAX = 3


def _decouverte(game_state: dict, player: str, espece: str) -> bool:
    """Une espèce est « découverte » (donc a une fiche) SSI son palier de maîtrise
    est ≥ 1 (kickoff : « pas d'état neuf, palier ≥ 1 ⇒ fiche »). Lecture pure de
    `maitrise.palier` (ne crée AUCUNE clé → no-op golden)."""
    return maitrise.palier(game_state, player, espece) >= 1


def encyclopedie_index(game_state: dict, player: str) -> list[str]:
    """Liste des espèces DÉCOUVERTES par ce joueur (palier ≥ 1), dans l'ordre
    STABLE du corpus (= ordre du catalogue recopié au §6). Sans couche maîtrise ni
    joueur → `[]` (golden-safe). PUR : aucune écriture, aucun RNG.

    On itère `FICHES` (et non la tranche maîtrise) pour garantir un tri stable et
    indépendant de l'ordre d'insertion des découvertes dans `game_state` ; toute
    espèce maîtrisée hors corpus (ne devrait pas arriver, l'alignement des clés est
    testé) est simplement ignorée à l'affichage — pas de fiche, pas de crash."""
    return [esp for esp in FICHES if _decouverte(game_state, player, esp)]


def encyclopedie_lire(game_state: dict, player: str, espece: str) -> dict | None:
    """Fiche d'une espèce, TRONQUÉE au niveau `min(palier, NIVEAU_MAX)` (doc §2.2).
    Renvoie `None` si l'espèce n'est pas découverte (palier 0) — elle n'a pas
    encore d'entrée. Structure de retour :

        {
          "espece":      "tomate",
          "niveau_max":  2,                 # = min(palier, 3) ∈ {1, 2, 3}
          "niveaux":     {1: "…N1…", 2: "…N2…"},   # 1..niveau_max, du corpus §6
        }

    PUR : lit `maitrise.palier` (D12) + le corpus, n'écrit RIEN. Espèce absente du
    corpus (clé inconnue) → `None` (jamais de KeyError ; l'alignement clés/catalogue
    est garanti par `tests/test_encyclopedie.py`)."""
    p = maitrise.palier(game_state, player, espece)
    if p < 1:
        return None
    fiche = FICHES.get(espece)
    if fiche is None:                       # clé hors corpus : pas de fiche à servir
        return None
    niveau_max = min(p, NIVEAU_MAX)
    niveaux = {n: fiche[n] for n in range(1, niveau_max + 1)}
    return {"espece": espece, "niveau_max": niveau_max, "niveaux": niveaux}
