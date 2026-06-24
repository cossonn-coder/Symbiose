# Tronçon ② — Banc édaphique (chlorose / asphyxie / carence NPK)

> Sprint « bancs d'essai ». État : `00_etat.md`. Pattern posé au ① (paquet
> `bancs/`, registre, cadre d'oracle). Ce tronçon ajoute la famille des stress
> du SOL et tranche les anomalies D47-C2 (asphyxie muette) et D47-C6 (NPK
> uniformément pauvres). **Golden NEUTRE attendu** (branché hors smoke/full).

## Objectif
Trois bancs édaphiques, chacun forçant son signe + un oracle. À la fin on sait,
pour chaque cause, si le moteur l'émet bien (oracle vert) — base du tri D47.

## Périmètre — `bancs/edaphique.py` (3 fabriques, ajoutées au registre)

### 1. `chlorose_acidophile()` — DÉMONSTRATEUR ROI de la fenêtre pH
- 1 tuile avec `myrtille` (`Vaccinium`, `ph_opt=4.8`, calcifuge — cf.
  `plants/species/sauvages.py:57`) posée sur un sol au **pH ALCALIN** :
  forcer `eco.ph.set(r, c, ~7.5)` (> `CHLOROSE_PH`) sur tous les plots via
  `build_banc_tile`. La myrtille acidophile sur sol alcalin subit la chlorose
  (`sim/semiologie.py`, fonction `chlorose`, neutre si `ph_opt ≥ 5.5`).
- Oracle : après N semaines, `"chlorose" in signes(myrtille)`.

### 2. `asphyxie_argile()` — tranche D47-C2
- 1 tuile `argile`, `humidite` initiale HAUTE + maintien d'un excès d'eau
  SOUTENU (la fabrique pré-charge `asphyxie_memory` au seuil via
  `force_memoire`, OU pose une humidité telle que l'excès s'installe seul ;
  préférer le forçage d'humidité, plus diégétique). Plante non hygrophile posée.
- **Diagnostic D47-C2** : au F5 du 2026-06-22, le signe `asphyxie` restait muet
  malgré arrosage répété sur argile. Ce banc répond à la question : l'arrosage
  manuel monte-t-il `asphyxie_memory` ? La fenêtre est-elle trop courte ? Vérifier
  le seuil `ASPHYXIE_HEALTH_SEUIL` (`sim/semiologie.py`, fonction `asphyxie`) et
  combien de semaines d'excès soutenu il faut. NOTER la conclusion dans `00_etat.md`
  (bug réel → dette/correctif, ou simple lenteur → calibrage du banc).
- Oracle : après N semaines, `"asphyxie" in signes(plante)`.

### 3. `carence_npk()` — symptôme de D41
- 1 tuile à `n`/`p`/`k` forcés TRÈS BAS (`init_eco(..., fertilite=0.05)` ou
  `eco.n/p/k.set` faibles). Plante gourmande posée.
- **Limite connue (D41)** : la MORT édaphique chronique est bloquée (qi_local
  épuisé). Ce banc n'a donc PAS vocation à tuer — il rend la **carence observable**
  (heatmaps n/p/k « pauvres », croissance bridée par Liebig, et `chlorose` d'azote
  si le moteur la relie). Oracle MINIMAL : asserter que les champs n/p/k restent
  bas et que la croissance est bridée (pas un signe de mort). **Diagnostic D47-C6** :
  ce banc montre que « heatmaps NPK uniformément pauvres » est le symptôme normal
  de D41, pas un bug de la carte. NOTER.
- Oracle : `eco.n.at_plot(...) < seuil` après N semaines + biomasse < témoin.

## Registre
`bancs/__init__.py` : ajouter `chlorose_acidophile`, `asphyxie_argile`,
`carence_npk` à `BANCS`.

## Vérifs
- Golden inchangé `2ab026ad…`.
- `tests/bancs/test_edaphique.py` : les 3 oracles verts.
- `init config="chlorose_acidophile"` (et les 2 autres) répond `ok`.
- Taille `bancs/edaphique.py` < ~350 lignes pur.

## Sortie
MAJ `00_etat.md` : ② clos, golden NEUTRE confirmé, **conclusions D47-C2 et C6**
(bug vs artefact — verser un correctif/dette si bug réel). Commit. `/clear` avant
`03_climatique.md`.
