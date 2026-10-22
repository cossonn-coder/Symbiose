# ⑤ Voix des 13 champignons — une fiche par espèce

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §3.4,
`docs/narration/voix/conception_voix_narratives.md` (les 5 voix).
**Golden** : NEUTRE (narration, hors tick).

## Objectif
Renverser la fiche générique unique (`sim/champignon_encyclo.py`, `CLE_CHAMPIGNON`) :
chaque espèce du registre ③ a ses 5 voix.
- **Encyclopédie** 3 niveaux par espèce (voir → cycle → effets écosystémiques), voix
  « naturaliste qui observe ». Clés : à harmoniser avec `sim/encyclopedie_types.type_de`,
  `tools/simserver/maitrise_pont.py` (~l.167-181), `tools/simserver/maitrise_cmds.py`
  (~l.90, `SC.CHAMPIGNON_VU`), `sim/signes.py` (~l.97, `vivants`). Inventaire exhaustif des
  lecteurs de `CLE_CHAMPIGNON` au `grep` AVANT de toucher (ne pas le déléguer).
- **Crédit d'observation** : `sim/signes.crediter_saison` par ESPÈCE (nommée après 3
  saisons d'observation, comme la faune).
- **Carnet** : concepts saprophytie, mycorhize, parasitisme de faiblesse, sosies
  (`CONCEPT_DE`), descriptif → interprétatif au seuil de maîtrise.
- **Pages secrètes** (si lore) : polypore du bouleau/Ötzi et l'amadou, psilocybe,
  amanite tue-mouches, morille des vieux vergers, ronds de sorcière du clitocybe.
- **Magazine** : rattachement (article, pas de nouveau geste d'inoculation).
- **Événements** : fructification consignée au ledger (`sim/evenements.py`).
- Info-bulle (`sim/signes_corpus.py`) : ligne carpophore nommée par espèce + comestibilité
  dite seulement une fois l'espèce nommée.
- Tests narratifs existants verts + test : chaque espèce du registre a ses voix.

## Ne PAS faire
Pas de manger/vision (⑥). Pas de dessin (⑧). Ne pas révéler la comestibilité avant le nom.
