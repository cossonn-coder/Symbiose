## 2026-06-04 — Sprint impl. D31.3 : façades `vigueur_*` + gestes joueur (Python)

**Dernier tronçon de D31 — clôt la dette côté Python.** Au-dessus du tick câblé
en D31.2, on pose la **couche joueur** : des **lectures diégétiques** de la
vitalité des populations et trois **gestes** qui touchent les champs comme donnée
d'entrée. **Contraste assumé avec D31.2 :** ici le golden écolo **NE re-fige PAS**
(exactement comme le sprint Vigueur D11) — tout est event-driven, jamais appelé
par le tick. Les deux hash écolo restent **`c950f06c…`** (engine) et
**`b005d9ba…`** (champ) — **vérifiés inchangés** avant *et* après.

**A. Façades `vigueur_macro.py`** (nouveau module `sim/`, miroir read-only de
`vigueur_plante.py`). Quatre fonctions pures `vigueur_nuisible/auxiliaire/
pollinisateur/ver(r, c, eco)` = `densité(r,c) × qi_local_trophique(r,c)`, où le
`qi_local` n'est PAS le sol racinaire mais la **ressource trophique** de la guilde
— réutilisée telle quelle via `PopulationField.activite()` (déjà mémorisée au
tick, **rien à recalculer**). **Populations, pas individus** (la façade lit une
vitalité de population à un endroit ; les sprites sont des échantillons sans
Vigueur). Descripteur qualitatif `decrire_vigueur_pop` (voix naturaliste :
absente / clairsemée / vigoureuse / florissante, philo #5). Zéro écriture, zéro
nouvel état.

**B. Trois (puis quatre) gestes dans `sim/actions.py`**, granularité **§5 « un
geste = un quantum »** (`DENSITE_PAR_SPRITE = 0.06`) :
- **`favoriser_auxiliaire(gs, player, tile)`** — coût `MODÉRÉ`. Pose une rondelle
  `auxiliaire` (déjà lue par `_stability_grid` comme nectar/refuge → plancher
  d'habitat **persistant**). Le canal vertueux : les auxiliaires s'installent
  **et restent**.
- **`ecraser(gs, player, eco, r, c, urgence=True)`** — **rendu RÉEL** (l'aveu
  « aucune entité nuisible n'existe encore » est levé). Retire un quantum de
  `ravageur` au plot ciblé ; binaire tout-ou-rien, `MODÉRÉ × URGENCE` conservé.
  **Changement d'interface** (ajout `eco, r, c`) — appelants de test adaptés.
- **`becher(gs, player, eco, r, c)`** — coût `FAIBLE`. Tue la faune du sol
  (↓ `vers_de_terre` d'un quantum + ↓ `microbiome` de `BECHAGE_MICROBIOME_MALUS`
  = 0.5, knob sobre, la conception ne chiffrait pas). **Visuel avant santé** : les
  sprites de vers disparaissent *avant* la dette différée `microbiome → uptake`.
- **`grelinette(gs, player)`** — **livré** (point ouvert #2 tranché). Le jumeau
  qui **préserve** : coût `MODÉRÉ`, **ne touche ni vers ni microbiome**. Ancre le
  couple pédagogique becher/grelinette dès maintenant (contraste enseigné à
  l'œil). Son **bonus d'aération attend D30** — d'ici là il ne dépense que la
  Vigueur du travail du sol, sans dette biologique.

**Points ouverts tranchés sobre (signalés) :** (#1) habitat **tuile** (rondelle
existante), pas de champ habitat-par-plot neuf → renvoyé D30/futur ; (#2)
grelinette livrée en jumeau-qui-préserve, aération → D30.

**Hors périmètre tenu :** gain signé « manger un individu » reste **D19** (le
prérequis ciblable est désormais complet : sprite + `ecraser` réel) ; sprites
« vers morts » animés = rendu Godot ; bénéfice structure du sol = D30.

**Validation :** golden joueur `tests/test_vigueur.py` étendu **59 → 87/87**
(façades E1-E3, favoriser E4, becher/grelinette E5, et **E6 « la pression
revient »** : densité de fond installée 0.152 → écrasée 0.092 → remonte 0.130 en
4 ticks, philo #1 prouvée). Hash de trajectoire joueur **inchangé**. `main.py`
tourne (exit 0).

### Hash golden (journal — AUCUN re-figeage)
Golden engine **`c950f06c…`** et golden de champ **`b005d9ba…`** : **inchangés**
(façades read-only, gestes event-driven hors tick). C'est le test du sprint —
réussi.

---
