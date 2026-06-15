# Mini-sprint — Succession écologique (pionnier → prairie)

**Statut** : à faire
**Prérequis** : aucun bloquant — sprint **Python pur** sur le moteur de vérité
(`data/code/`). Suite directe du Sprint sol vivant. Git à jour avant de démarrer.
**Estimation** : 1 à 2 sessions
**Objectif** : faire **mûrir** la végétation spontanée. Aujourd'hui un sol même
redevenu riche reste bloqué en **pionnières annuelles** ; on veut que la
succession progresse vers un **stade prairie** (vivaces : fixatrices, graminées,
composées) à mesure que le sol mûrit — cœur du concept « le jardin qui grandit ».
Tout en Python déterministe, validé sur `main.py`.

> Ce mini-sprint dérive de la **dette D25**, diagnostiquée le 2026-06-02 à la fin
> du Sprint sol vivant (voir `journal.md`). Le diagnostic est déjà posé ; ce
> fichier contient le pourquoi biologique, les décisions à acter et le comment.

---

## Avant de commencer

1. **`CLAUDE.md`** — « Source de vérité » (Python = canon), philosophies #3
   (déterminisme), #4 (sol = mémoire vivante), #6 (sagesse écologique émergente),
   et la section panne sèche (« la succession spontanée ramène des pionnières…
   c'est le fonctionnement normal d'un sol vivant »).
2. **`journal.md`** — entrée « Consolidation sol vivant » (2026-06-02), axe 2 :
   le diagnostic complet de D25.
3. **Memory** — `project_python_source.md`, `project_status.md`, `feedback_design.md`
   (flux > action directe), `feedback_pedagogie_domaine.md`.
4. **Code Python à lire (source de vérité)** :
   - `data/code/fields.py` — `SeedBank` : `SEED_ARCHETYPES` (~l.285),
     `tick_disturbance_enrichment` (~l.328, n'enrichit qu'en `pioneer`),
     `tick_plant_production` (~l.337), `niche_index` (~l.350),
     `germination_candidates` (~l.371).
   - `data/code/engine.py` — `_succession` (~l.199, logique de `chosen`),
     `_spring_flush` (~l.340, idem), `_winter_transition` (~l.287).
   - `data/code/models.py` — les 4 adventices et leur `archetype` /
     `reproduction_rate` / `winter_strategy` (BursaPastoris, MedicagoLupulina,
     PoaAnnua, Taraxacum, ~l.290-493).

---

## Partie 1 — La succession, expliquée pour un ingénieur

**La succession écologique** = remplacement progressif des communautés végétales
après une perturbation. Sur un sol existant (succession secondaire), les stades
classiques :

| Stade | Qui | Stratégie | Rôle |
|---|---|---|---|
| **Pionnier** | annuelles rudérales | r (vite, bcp de graines, jetable) | couvrent le sol nu, enrichissent la MO, meurent |
| **Prairie** | vivaces herbacées (graminées, fixatrices, composées) | intermédiaire | racines profondes, persistent, structurent |
| **Arbustif** | ligneux bas | — | (hors scope : pas d'arbustes au catalogue) |
| **Climax** | arbres | K (lent, compétitif, stable) | canopée dense, sol mûr |

**Le moteur de la transition** : les pionnières **modifient le milieu** (ombre,
MO, microbiome, humidité) → créent des conditions favorables aux suivantes et
**défavorables à elles-mêmes** (elles ont besoin de lumière + sol nu). Les
espèces tardives sont **plus compétitives mais plus lentes/exigeantes** : il leur
faut un sol mûri et leurs **propagules doivent arriver** (vent, oiseaux) — c'est
lent.

**Dans Symbiose** : 4 archétypes existent — `pioneer` (annuelle), et trois
vivaces `nitrogen_fixer` / `grass` / `competitor`. On a donc déjà pionnier +
prairie. **Pas d'arbustif/climax** (ça viendra avec les pérennes ligneuses,
Sprint éclairement D21). **Périmètre réaliste de ce sprint : pionnier → prairie.**

---

## Partie 2 — Le diagnostic (pourquoi ça reste bloqué)

Test : un sol saccagé (même à perturbation réaliste) reste **100 %
Bourse-à-pasteur, 0 vivace, sur 150 ans**, alors qu'il redevient riche
(fertilité 2.8, humus saturé, microbiome 1.5). **Double cause** :

1. **Choix d'archétype** (`_succession`, `_spring_flush`) : `chosen = candidates[0]`
   (= `pioneer`, premier dans `SEED_ARCHETYPES` et densité la plus forte). Les
   vivaces ne sont favorisées que sur sol **pauvre** (`fert<0.3` → nitrogen_fixer).
   Sur sol **mûr**, rien ne fait basculer vers la prairie. C'est l'inverse de la
   biologie.

2. **Amorçage de la banque** : `tick_disturbance_enrichment` n'ajoute que du
   `pioneer` ; `tick_plant_production` n'ajoute l'archétype d'une plante que si
   elle en a un (les cultivées ont `archetype=None`). Après une phase 100 %
   pionnières, la banque **ne contient que `pioneer`** — les vivaces n'ont
   **aucune source** pour démarrer, même si on corrige le choix.

→ Un correctif complet touche **les deux** : le choix (∝ maturité) **et**
l'amorçage de la banque (propagules tardives).

---

## Partie 3 — Décisions à acter (début de sprint, avec Nico)

> Recommandations ci-dessous, **à confirmer/ajuster** avant de coder
> (méthode : on ne tranche pas la bio en silence). Max 3 questions à la fois.

1. **Proxy de maturité du sol** : `soil_memory_deep` (reco — c'est déjà
   l'intégrateur décennal de l'état du sol, parfait pour « depuis combien de
   temps ce sol est-il stable et établi »). Alternative : combinaison
   soil_deep + microbiome + om_stable.

2. **Gradient de succession** (quel archétype à quelle maturité) — reco :
   - sol jeune / perturbé (soil_deep bas, disturbance haut) → `pioneer`
   - sol mûrissant (soil_deep moyen) → `nitrogen_fixer` puis `grass`
   - sol mûr (soil_deep haut) → `competitor` (le plus tardif/compétitif)

3. **Amorçage banque en propagules tardives** : un **trickle léger** de graines
   vivaces ∝ maturité du sol (diégétiquement : dispersion vent/oiseaux qui
   arrive quand le milieu est prêt). Reco : OUI, faible taux à calibrer.

4. **Ampleur** : s'arrêter à **pionnier → prairie** (reco ; climax ligneux =
   Sprint éclairement) ou viser plus loin.

---

## Partie 4 — Tâches dans l'ordre

### Étape 0 — Valider les décisions de la Partie 3 avec Nico

### Étape 1 — Gradient de choix d'archétype ∝ maturité
Dans `engine.py:_succession` et `_spring_flush`, remplacer la logique `chosen`
(qui ne favorise les vivaces que sur sol pauvre) par une **sélection indexée sur
la maturité** (`soil_memory_deep` local). Sur sol mûr, privilégier les vivaces
(`competitor`/`grass`/`nitrogen_fixer`) plutôt que `pioneer`. Garder le tirage
déterministe (`germination_candidates`) ; n'agir que sur le choix parmi les
candidats. Factoriser idéalement la logique commune aux deux méthodes.

**Validation 1** : sur un sol qu'on laisse mûrir, la part de vivaces parmi les
germinations **augmente avec `soil_memory_deep`**.

### Étape 2 — Amorçage de la banque en propagules tardives
Dans `fields.py:SeedBank`, ajouter un enrichissement **en archétypes vivaces**
modulé par la maturité du sol (symétrique de `tick_disturbance_enrichment` qui
n'enrichit qu'en `pioneer`). Faible taux, déterministe ou champ-driven (pas de
RNG hors hash/seed). Brancher l'appel dans `EcoFields.tick_seed_bank` (qui reçoit
déjà l'accès aux champs nécessaires) — passer la maturité requise.

**Validation 2** : après une phase 100 % pionnières, la banque accumule
progressivement des graines vivaces sur les plots mûrs.

### Étape 3 — Vérifier l'inhibition naturelle des pionnières
`niche_index` réduit déjà la niche quand `root_density` monte et `soil_deep`
monte. **Vérifier** qu'une fois les vivaces installées, les pionnières refluent
d'elles-mêmes (moins de niche libre). Ne coder un frein explicite que si le
reflux n'émerge pas.

**Validation 3** (le test clé) : un sol nu/saccagé laissé en friche montre une
**trajectoire de succession** dans le terminal — pionnières d'abord, puis bascule
progressive (décennies) vers un couvert de **prairie vivace**, sans rester bloqué
en pionnières ni osciller.

---

## Pièges connus

- **Déterminisme** : tout reste seedé / `_hash_noise`. Aucune source d'aléa non
  reproductible (philosophie #3).
- **Ne pas casser la succession de début de partie** : sur sol jeune, les
  pionnières doivent toujours coloniser vite (c'est correct aujourd'hui).
- **Bascule douce, pas brutale** : la transition pionnier → prairie doit être
  **progressive** (décennies via `soil_memory_deep` lent, lerp 0.02), pas un
  basculement net d'une saison. Éviter les oscillations.
- **Propagules ex nihilo** : le trickle de graines tardives doit rester **faible
  et diégétique** (dispersion lente) — pas un robinet qui crée de la biomasse.
- **Régression de parité C#** : cette logique de succession n'est pas encore
  portée en C# (elle s'ajoute à la dette de portage D24/Sprint 3). Ne pas porter
  maintenant.

---

## À produire à la fin

- [ ] `data/code/engine.py` — `_succession`/`_spring_flush` : choix d'archétype
      ∝ maturité du sol (gradient pionnier → prairie)
- [ ] `data/code/fields.py` — `SeedBank` : amorçage en propagules vivaces ∝
      maturité ; branchement dans `tick_seed_bank`
- [ ] `data/code/main.py` — logs lisibles de la **composition par archétype**
      dans le temps (pour lire la trajectoire de succession au terminal)
- [ ] **`journal.md`** — entrée datée : D25 traitée, décisions actées, gradient
      de succession ; noter l'ajout à la dette de portage C#
- [ ] **Memory** — `project_status.md` (D25 levée), `project_python_source.md`
- [ ] **Commit** ex : `Mini-sprint succession : gradient pionnier → prairie ∝ maturité du sol`
- [ ] Mettre à jour le **Backlog actif** de `CLAUDE.md` (sprint réalisé, D25 levée)

---

## Critère de fin

`python3 data/code/main.py` simule **plusieurs siècles sans crash**, et on
**observe la trajectoire de succession** au terminal : un sol nu/saccagé est
colonisé par les pionnières, puis — à mesure qu'il mûrit (`soil_memory_deep` ↑) —
bascule progressivement vers un couvert de **prairie vivace** (fixatrices,
graminées, composées), sans rester bloqué en pionnières. Validation **par lecture
du terminal**, déterministe.
