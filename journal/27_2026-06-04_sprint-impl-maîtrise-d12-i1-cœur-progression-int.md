## 2026-06-04 — Sprint impl. maîtrise D12·i1 : cœur + progression intra-objet (Python)

**Premier des 4 tronçons de l'implémentation D12** (`sprints/sprint_D12_impl/`).
On pose le **cœur** de la maîtrise — l'état par avatar, la découverte, la
progression de palier par preuves — **sans** agrégats, ponts Vigueur, seam de
coût ni détection auto (tout ça vient en i2/i3/i4). Miroir structurel exact de la
couche Vigueur D11 : couche gameplay **au-dessus du tick**, opt-in, golden écolo
intact.

**A. `sim/maitrise.py`** (nouveau, pur — lib std `math` seule, n'importe ni
`vigueur.py` ni le tick). État `game_state["maitrise"][player] = {"objets":
{<objet>: {"palier": 0..5, "preuves": int}}}`, catalogue-agnostique (un objet =
une clé string). Cinq fonctions :
- `ensure_player_maitrise` — opt-in (geste identique à `vigueur.ensure_player`).
- `palier(gs, player, objet)` — lecture pure, `0` si inconnu, ne crée rien.
- `decouvrir` — 0→1 gratuit (§2.1), idempotent, renvoie `True` ssi nouvelle.
- `preuves_requises(k)` — `ceil(BASE·R**(k-1))` (§2.3).
- `enregistrer_preuve` — crédite une preuve, franchit autant de paliers que le
  crédit le permet, renvoie le palier courant. **Monotone** (§2.4, aucun
  décrément exposé), plafonné à 5.

**Décisions i1 (sobre, signalées) :** (1) **invariant** « un objet n'entre dans le
dict qu'au palier ≥ 1 » → l'**absence** du dict EST le palier 0 (inconnu) ; lecture
d'un inconnu ne crée aucune clé (pas d'opt-in parasite). (2) **Auto-découverte** :
`enregistrer_preuve` sur un inconnu le découvre d'abord (une preuve implique qu'on
l'a observé). (3) **Consommation cumulative** : une grosse fournée franchit
plusieurs paliers d'un coup, le reliquat reste au crédit du palier suivant.
(4) **Placeholders nommés** `PREUVES_BASE=2`/`PREUVES_R=2` (courbe 2,4,8,16, visible
et croissante) → vrai calibrage `K`/`BASE`/`R` en **D12.4 post-test**.

**B. Golden joueur `tests/test_maitrise.py`** (nouveau, déterministe sans RNG,
preuves injectées). **18/18** : no-op golden (clone de `test_vigueur` — 20 ticks
engine, `"maitrise" not in gs`), découverte/idempotence/inconnu=0, courbe
croissante, progression + reliquat + auto-découverte, plafond (sur-injection 10 000
preuves → reste 5), monotonie (200 preuves non décroissantes), déterminisme.

### Hash golden (journal — AUCUN re-figeage)
Golden engine **`c950f06c…`**, golden de champ **`b005d9ba…`**, golden joueur
Vigueur **87/87** : **tous VÉRIFIÉS INCHANGÉS** avant *et* après (la maîtrise n'a
aucun point d'entrée depuis le tick — c'est le test du tronçon). `main.py` tourne
(exit 0).

---
