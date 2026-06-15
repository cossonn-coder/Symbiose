## 2026-06-04 — Sprint impl. maîtrise D12·i2 : agrégats + ponts Vigueur (Python)

**Deuxième des 4 tronçons** (`sprints/sprint_D12_impl/`). On branche la strate 2
(agrégats dérivés) et la strate 3 (ponts vers la Vigueur §4.1/§4.3). Toujours
couche gameplay **au-dessus du tick**, golden écolo intact.

**A. `sim/maitrise.py`** (étendu, reste pur côté Vigueur — importe désormais
`plants.catalogue` pour la famille). Ajouts :
- **Spillover intra-famille (§3.1)** dans `enregistrer_preuve` : une preuve est
  pondérée par `_facteur_spillover` = `1 + SPILLOVER_RATE · Σ(palier−1 des sœurs
  découvertes de même famille)`. « Être avancé sur la tomate accélère l'aubergine,
  jamais le haricot. » Le seuil « ≥2 espèces découvertes » (§10.1) **tombe
  naturellement** : une sœur juste découverte (palier 1) transfère `palier−1 = 0`.
  Mapping famille **dérivé** de `PLANT_CATALOGUE`+`PERENNIAL_CATALOGUE` (reflète
  `plants/`, ne duplique rien) ; objet sans famille (concept/outil) → facteur 1.0.
- **Agrégats (§3.2, calculés, jamais stockés)** : `accumulation_globale` = Σ paliers
  (pool unique espèces+concepts, brut, avant log) ; `completude_ratio` = Σ /
  (PALIER_MAX × découverts) — **dénominateur = découverts seuls → aucune dilution**
  quand le catalogue grossit. Lecture pure (no-op golden préservé).
- **`palier_bonus(game_state, player)` (§4.1)** = `1 + K·log1p(accumulation)` :
  remplit l'ex-stub, **neutre 1.0** sans savoir (log1p(0)=0), rendements décroissants
  (anti-super-héros §3.2).

**B. `sim/vigueur.py`** — `palier_bonus` **délègue** à `maitrise.palier_bonus`.
**Point ouvert i2 tranché → (a)** : la signature gagne `game_state` (l'accumulation
est par-joueur ; pas d'état caché module-level → déterminisme). 5 sites internes mis
à jour. **Sens de dépendance posé : Vigueur → Maîtrise** (la capacité de Vigueur
dérive du savoir), jamais l'inverse → `maitrise.py` n'importe pas `vigueur.py`.
L'idéal §4.1 « ne pas retoucher vigueur.py » était inatteignable (bonus par-joueur) :
retouche assumée, la *forme* du pont (plafond/régen × `palier_bonus`) est inchangée.

**C. `sim/actions.py`** — sources ponctuelles §4.3 (orchestration, là où vivent déjà
`manger`/`recolter`) : `observer` (découvre + `GAIN_DECOUVERTE`, idempotent) et
`crediter_succes` (preuve + `GAIN_SUCCES` × paliers franchis). Placées ici, pas dans
`maitrise.py`, pour éviter le cycle d'import (actions voit les deux couches).

**Décisions (sobre, signalées) :** dépendance Vigueur→Maîtrise ; gains §4.3 dans la
couche d'orchestration ; `preuves` devient flottant quand le spillover joue
(`0.5×int` → exactement représentable, déterministe). Placeholders nommés
`PALIER_BONUS_K=0.05`, `SPILLOVER_RATE=0.5`, `GAIN_DECOUVERTE`/`GAIN_SUCCES` →
**calibrage D12.4**.

**D. Golden joueur** — `test_maitrise.py` **35/35** (+ agrégats, spillover,
`palier_bonus`), `test_vigueur.py` **96/96** (A4 adaptée à la nouvelle signature
+ section F : pont actif vigueur_max↑ & gains ponctuels).

### Hash golden (journal — AUCUN re-figeage)
Golden engine **`c950f06c…`**, golden de champ **`b005d9ba…`** : **VÉRIFIÉS
INCHANGÉS** avant *et* après (le pont est neutre sans couche maîtrise — golden =
succession pure sans joueur). `main.py` tourne (exit 0). **Prochain : i3** (seam
`cout_action` + table objets-touchés §10.4 sur `actions.py`).
