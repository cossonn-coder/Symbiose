# Tronçon ③ — Déclenchement déterministe + table de quêtes + voix + récompenses simples

> Sprint QUÊTES (D79). Lire d'abord : `CLAUDE.md`, `00_etat.md`,
> `docs/joueur/automate/conception_quetes.md`, tronçons ①② (faits).
> Golden : **INCHANGÉ**.

## Objectif
Transformer le moteur nu (①②) en **quêtes qui arrivent d'elles-mêmes**, incarnées
par des **lettres**, avec leurs **récompenses simples** et le **garde-fou #6**.

## À implémenter
1. **Table déclarative de quêtes** (`sim/quetes_corpus.py`, sur le modèle de
   `sim/concept_corpus.py` / `pages_corpus.py`) : chaque entrée =
   `(id, donneur, texte_lettre, condition, recompense, declencheur)`.
   Corpus de départ modeste (≈ 5-8 lettres) démontrant les deux familles de
   conditions : au moins une `recolte_cumulee`, une `hauteur_min`
   (pommier/tournesol), une `floraison_min` (trèfle). Une lettre peut cibler le
   « kiwi » → cible `inatteignable` (assumé, F3).
2. **Voix des donneurs (V1 — lettres ANONYMES)** : registre épistolaire
   chaleureux, **jamais directif** (désir sans méthode, #6). Signature = prénom
   sans figure ni récurrence. Cf. §7 conception pour le ton.
3. **Déclenchement déterministe (#3, zéro RNG)** : une quête `declencheur`
   s'ouvre quand une condition d'ouverture est remplie — **palier de maîtrise**
   (`sim.maitrise.palier(gs, player, objet) >= seuil`) et/ou **jalon de saison**
   (`game_state["week"]`/saison). AUCUN `random`. Évaluer les déclencheurs au
   **passage de saison** (hors tick).
4. **Plafond de quêtes actives (#6)** : constante `PLAFOND_QUETES_ACTIVES`
   (ex. 3). Tant que le plafond est plein, aucune nouvelle lettre n'arrive
   (anti-checklist). Les quêtes en attente restent en file déterministe (tri
   `id`).
5. **Récompenses simples (V3)** à l'accomplissement : `graine` (banque-joueur),
   `page` (page secrète débloquée), `vigueur` (crédit Vigueur joueur, PAS un buff
   plante — #2), `maitrise` (crédit de maîtrise). Repérer les API existantes
   (banque de graines, pages secrètes, Vigueur D11, maîtrise) et les appeler ;
   NE PAS inventer de canal. `recompense=None` → plaisir pur (base).

## Tests
- Étendre `tests/test_quetes.py` : un déclencheur « palier X atteint » ouvre la
  bonne lettre ; le plafond bloque la (N+1)ᵉ ; une récompense `graine` crédite
  bien la banque ; déterminisme (même seed → même séquence de lettres).
- `python3 -m tests.test_golden` → **hash INCHANGÉ** (déclenchement hors tick,
  opt-in ; le golden n'ouvre aucune quête).

## Ne PAS faire
- Aucun tirage aléatoire vivant (#3). Aucune voix directive (« plante ici »,
  « arrose 3 fois ») — désir seulement (#6).
- Pas de récompense matérielle rare (vivace/structure/outil = ④). Pas de vue (⑤).
- Pas de buff direct sur plante (#2).

## Fin de tronçon
Golden inchangé → maj `00_etat.md` → commit.
