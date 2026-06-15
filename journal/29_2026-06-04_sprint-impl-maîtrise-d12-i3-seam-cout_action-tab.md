## 2026-06-04 — Sprint impl. maîtrise D12·i3 : seam `cout_action` + table objets-touchés (Python)

**Troisième des 4 tronçons** (`sprints/sprint_D12_impl/`). On pose le **second
seam** de la maîtrise (le premier, `palier_bonus`, fait en i2) : la **réduction
du coût d'action**. La maîtrise rend les gestes moins chers en Vigueur,
*contextuellement* — geste par geste, selon ce que l'action touche. Tout dans
`sim/actions.py`, la couche d'orchestration qui voit Vigueur **et** Maîtrise ;
`maitrise.py` reste **pur** (sens de dépendance acté i2).

**A. `cout_action(game_state, player, action, objets_touches)` (§4.2)** =
`base × f_globale × f_objets`, atténuation ∈ ]0,1].
- **`f_globale`** (terme 1, connaissance écologique générale) lit la
  **complétude-ratio** de i2 (∈ [0,1], borné → pas de log) : `1 − ATT_GLOBALE_MAX
  · completude_ratio`, décroissant vers le plancher `1−ATT_GLOBALE_MAX > 0`.
- **`f_objets`** (terme 2, objets concrets touchés) = **moyenne** des
  `1 − ATT_OBJET_MAX · palier/PALIER_MAX` ; objet inconnu (palier 0) → neutre 1.0.
  Moyenne choisie (sobre, bornée : reste ∈ [plancher, 1], jamais →0 même avec
  beaucoup d'objets). `None`/`[]` → 1.0.
- **Coût NUL préservé** (§10.5) : `base == 0` (`manger`) → 0 sans rien lire.

**B. Tables data-driven.** `COUTS` regroupe les littéraux d'avant (ils deviennent
la `base` — constantes conservées, rien supprimé). `OBJETS_TOUCHES` reflète §10.4
**telle quelle** (objets STATIQUES : technique + outil/structure ; la cible vivante
est dynamique). Helpers : `_cle_espece` (reverse classe→clé catalogue, dégradation
gracieuse si introuvable) + `_objets_action` (statique ∪ clé d'espèce cible → le
**spillover famille** vient gratuitement, la maîtrise de l'espèce monte déjà via i2).

**C. Branchement des 6 gestes payants.** `recolter`/`deraciner` ajoutent la clé
d'espèce ; `ecraser`/`becher`/`grelinette`/`favoriser_auxiliaire` (actions milieu,
philo #2) = statique seule. **`ecraser`** : l'`URGENCE_MULT` reste un facteur
**séparé** appliqué par-dessus le seam (l'urgence est la phase saison, pas de la
maîtrise). `manger` inchangé (base NUL, aucun `spend`). Aucune signature publique
touchée.

**Dégradation gracieuse (§10.5).** Outils/structures/techniques n'ont **aucun état
moteur** aujourd'hui → `M.palier == 0` → contribution neutre 1.0. La table les
**nomme** pour quand leur sprint (D29/D30/D31) les câblera. Aujourd'hui seuls les
**espèces** (cible vivante) et la **complétude globale** allègent réellement.

**Décisions (sobre, signalées) :** `completude_ratio` pour le terme global (borné,
propre) ; moyenne pour le terme objets ; urgence séparée. Atténuations
`ATT_GLOBALE_MAX`/`ATT_OBJET_MAX = 0.5` = **placeholders nommés → calibrage D12.4**.

**D. Golden joueur** — `test_vigueur.py` **103/103** : A5–E **inchangés** (sans
maîtrise, `cout_action == base` → non-régression gratuite) + **section G** nouvelle
(avec maîtrise : `deraciner` coûte strictement < ELEVE ; plancher > 0 ; objet non
maîtrisé reste à base ; `manger` NUL préservé ; récolte branchée bout-en-bout).
`test_maitrise.py` **35/35** (i1/i2 intacts).

### Hash golden (journal — AUCUN re-figeage)
Golden engine **`c950f06c…`**, golden de champ **`b005d9ba…`** : **VÉRIFIÉS
INCHANGÉS** avant *et* après (le coût d'action vit au-dessus du tick — golden =
succession pure sans joueur). `main.py` tourne (exit 0). **Prochain : i4**
(détection automatique de succès §9 : signaux du tick, fenêtre d'imputation, tag
féral, gate d'observation).
