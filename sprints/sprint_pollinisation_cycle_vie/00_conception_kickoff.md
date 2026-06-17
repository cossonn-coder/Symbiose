# Kickoff — Arc POLLINISATION & CYCLE DE VIE (conception d'abord)

> **Sprint de CONCEPTION d'abord, MOTEUR.** Aucun code moteur tant que le doc
> n'est pas figé. Livrable de cette phase = `docs/conception/CONCEPTION_POLLINISATION_CYCLE_VIE.md`.
> L'implémentation (MOTEUR → re-fige le golden) sera découpée en sous-sprints
> APRÈS validation de la conception.
>
> **Reprise à froid** : « lis `sprints/sprint_pollinisation_cycle_vie/00_conception_kickoff.md` ».
> Origine : idée Nico (vue·rattrapage 02, gravée 2026-06-16, BACKLOG.md). Mémoire :
> [[design_pollinisation_cycle_vie]], [[regle_interconnexion_acteurs]]. S'appuie
> sur l'horloge `daylength(wiy)` posée au sprint saisonnalité vie macro (2026-06-16).

---

## 1. L'intention (Nico)

Rendre **la vie réaliste et interconnectée** autour du cycle floraison →
pollinisation → fruit → graine, et boucler un cycle de vie inter-guildes :

1. **Fruit = résultat d'une pollinisation** (pas un dû automatique).
2. **Vraie floraison + phénologie** par variété (aujourd'hui les fleurs ne sont
   qu'un proxy de rendu).
3. **Pollinisateurs gagnent de la Vigueur** en butinant (faire croître le champ).
4. **Mélange des pollens** = brassage génétique des graines.
5. **Chenille → papillon** = transition champ `ravageur` → `pollinisateur` (cycle
   de vie inter-guildes).

Tout en respectant **philo #2** (jamais bonus/malus direct sur la plante : flux →
contrainte écologique → réponse biologique émergente) et **philo #6** (apprentissage
diffus, pas de tutoriel). Et la **règle d'interconnexion** : chaque acteur relié
aux autres.

---

## 2. État de l'existant — CE QUI EST DÉJÀ LÀ (ne PAS reconstruire)

Audit du moteur Python au 2026-06-16. **Surprise majeure : le brassage génétique
pollinisé est déjà implémenté et modulé par le champ pollinisateur.**

| Brique | Où | Ce qu'elle fait |
|---|---|---|
| **Génétique biparentale pollinisée** | `sim/reproduction.py` | `find_father` (père compatible à portée, même famille) ; `child_genes` (moyenne parents + mutation, autoféc., introgression) ; **`pollinator_reach(mother,tile,eco)` modulé par la densité LOCALE du champ `pollinisateur`** (D31.2, `POLLINATOR_SAT`=0.40) ; modes `wind`/`insect`/`self`, `pollination_radius_cm` |
| Driver reproduction | `sim/engine/mortalite.py:_reproduction` | appelé en **automne** (`boucle.py:215`) : appariement → graines (gènes hérités) → pool-sol + recrutement direct |
| **Fruits traçables** | `sim/engine/decompo.py:_tick_fruits` | nouaison annuelle à `FRUIT_NOUAISON_WEEK` (= début été, w14) pour `fruitier` ET `age_years ≥ maturity_years` ; `PlantInstance.fruits` (maturité par fruit) ; maturation `FRUIT_DMAT` ; chute des sur-mûrs → litière `fruit` ; `manger` ciblé (absorbe D19) |
| **Champ `pollinisateur`** | `fields/population.py` | guilde `PopulationField` ; **ressource = `_flower_grid`** (proxy : plantes stade ≥ 2) ; habitat = rondelle `pollinisateur` ; **désormais SAISONNIER** (fenêtre 12→14.5 h, sprint 2026-06-16) |
| Vigueur macro | `sim/vigueur_macro.py` | 4 façades pures `densité × qi_local` read-only |
| **Horloge photopériode** | `fields/population.py:daylength(wiy)` | sinusoïde 8↔16 h, pure — **fondation posée exprès pour la phénologie florale** |
| Organes / sites | `plants/base/stades.py` (`organs`), `familles.py` (`organ_site` terminal/lateral), `organ_sites()` | sites reproducteurs où naissent fleurs/fruits |
| Floraison « phase » | `engine/calendrier.py:est_phase_floraison` | **semaine calendaire fixe** (proxy), déclenche un `resolve_plant_turn(...,"floraison")` |
| Fleurs au rendu | `tools/maquette.py:REPRO_BY_SEASON` | **PROXY de RENDU** (organe affiché par saison), pas un état moteur |

**Conclusion** : le point 4 (brassage génétique) est **essentiellement fait** et
déjà branché sur le champ pollinisateur. Il deviendra un *raffinement* éventuel,
pas un gros morceau.

---

## 3. LE VRAI GAP — ce que l'arc doit ajouter

1. **Floraison RÉELLE + phénologie** (préalable). Aujourd'hui « fleur » = proxy de
   rendu + une semaine calendaire. Il manque un **état floral moteur** (la plante
   fleurit vraiment, dans une **fenêtre par variété** ancrée sur `daylength`/stade)
   sur lequel tout le reste s'appuie. La ressource du champ pollinisateur
   (`_flower_grid`) devrait lire CETTE floraison, pas le proxy stade ≥ 2.

2. **Nouaison CONDITIONNÉE à la pollinisation** (cœur « fruit = résultat »).
   `_tick_fruits` noue aujourd'hui **inconditionnellement** (gate = âge seulement).
   Il ne lit PAS le champ pollinisateur. L'arc **gate la mise à fruit** (quantité
   nouée) par la pollinisation reçue pendant la floraison — flux → contrainte →
   émergence (philo #2). Nuance : le champ module déjà le BRASSAGE (reach
   génétique) ; l'arc ajoute le gate **quantitatif** (combien de fruits).
   Autogames (`self`) / anémophiles (`wind`) à traiter à part.

3. **Rétroaction floraison ↔ Vigueur du champ pollinisateur**. « Les pollinisateurs
   gagnent de la Vigueur en butinant » = **faire croître le champ** quand il y a
   de la floraison (à trancher : c'est déjà partiellement le cas via
   `_flower_grid` = ressource ; reste à décider si la floraison réelle renforce
   le couplage et/ou crédite une Vigueur joueur quand SES plantes sont butinées).

4. **Chenille → papillon** : **transfert de densité `ravageur` → `pollinisateur`**
   (cycle de vie inter-guildes, philo #6). Nouveau couplage entre deux
   `PopulationField`. Le champ ravageur est générique (pas d'espèces) → on modélise
   une **fraction** qui se métamorphose, déclenchée par photopériode/saison.
   Effet secondaire écologique : moins de ravageur = répit d'herbivorie + plus de
   pollinisateurs → boucle vertueuse émergente.

---

## 4. Axes de conception à trancher (groupés par volet)

> Pédagogie domaine (cf. [[feedback_pedagogie_domaine]]) : la bio (phénologie,
> métamorphose) sera présentée en DOC à étudier ; Nico tranche les choix de
> **modélisation/simulation** (son domaine). Questions posées ≤ 3 à la fois.

- **A — Floraison réelle** : état floral discret (bourgeon → ouvert → fané) ou
  scalaire `floraison ∈ [0,1]` ? Fenêtre par espèce ancrée sur `daylength`
  (seuils h de jour, comme les guildes) ou sur stade + saison ? Durée de floraison
  par variété ? Lien à l'abscission/au caduc ?
- **B — Nouaison pollinisée** : gate DUR (0 pollinisateur → 0 fruit) ou CONTINU
  (fraction nouée ∝ pollinisation intégrée sur la fenêtre de floraison) ? Comment
  exempter `self`/`wind` ? Où vit l'« intégrale de pollinisation » (sur le fruit ?
  la plante ? un champ) ? Interaction avec `maturity_years`.
- **C — Vigueur pollinisateur** : la floraison réelle remplace-t-elle
  `_flower_grid` comme ressource du champ ? Un gain de **Vigueur joueur** quand ses
  plantes mellifères sont butinées, ou rien (le joueur n'est pas l'insecte) ?
- **D — Chenille → papillon** : taux/fraction métamorphosée, déclencheur
  (photopériode ? maturité du champ ravageur ?), conservation de masse (transfert),
  saisonnalité. Toutes les « chenilles » ou une part ?
- **E — Brassage (raffinement)** : l'existant suffit-il, ou veut-on un mélange
  multi-pères proportionnel à la densité pollinisateur (pollen mix) ?

---

## 5. Découpe d'IMPLÉMENTATION — voir le doc §L (élargie le 2026-06-17)

> Cette section pressentie est **superséd​ée** par la découpe finale du doc de
> conception (`§L`). Résumé : **7 tronçons** — ①→⑤ MOTEUR (re-fige le golden
> isolé), ⑥⑦ COUCHE JOUEUR (golden neutre, sprint distinct) :
>
> 1. **① Floraison réelle + phénologie** (A) — golden visé NEUTRE.
> 2. **② Registre + champs par type + nectar** (C/E) — golden re-figé MAÎTRISÉ.
> 3. **③ Butineurs déterministes** (F) — golden probablement neutre (smoke).
> 4. **④ Nouaison pollinisée** (B) — golden probablement neutre (tomate/pommier).
> 5. **⑤ Ponts de cycle de vie** (D : chenille→papillon, syrphe_larve→syrphe) —
>    golden re-figé MAÎTRISÉ (invariant larves=0 ⇒ herbivorie/prédation inchangées).
> 6. **⑥ Ruche & miel** (H/I) — golden neutre. 7. **⑦ Piqûre/alarme** (J) — golden neutre.
>
> Brassage multi-pères (ancien ⑤) **non retenu**.

---

## 6. Garde-fous

- **Philo #2** : la pollinisation est un FLUX (densité pollinisateur × floraison) →
  CONTRAINTE (taux de nouaison) → RÉPONSE émergente (moins de fruits). Jamais
  « −X fruits » en dur.
- **Philo #6** : aucun chiffre en HUD ; l'apprentissage passe par l'observation
  (peu d'abeilles → peu de pommes l'an prochain).
- **Interconnexion** ([[regle_interconnexion_acteurs]]) : fleurs ↔ pollinisateurs
  ↔ fruits ↔ graines ↔ génétique ↔ ravageurs (chenilles) — tout coexiste.
- **Déterminisme** (philo #3) : tout dérivé de `seed` + `_hash_noise` + `daylength`,
  jamais de RNG vivant.
- **Golden** : re-figeage MOTEUR attendu surtout sur ④ — **maîtrisé et annoncé**.
- **Couches** : `plants ← fields ← sim`. La floraison touche `plants` (état) +
  `sim/engine` (tick) ; la nouaison `sim/engine/decompo` ; le transfert de guilde
  `fields/population`.
- **Taille fichiers** (~350 l code pur), **un fichier modifié à la fois** hors
  synchro de commit, **doc d'abord**.

---

## 7. Prochaine étape

~~Démarrer la conversation de conception~~ — **FAIT le 2026-06-16, ÉLARGI &
RE-FIGÉ le 2026-06-17.** La 1ʳᵉ passe était incomplète (manquaient : catalogue
d'acteurs pollinisateurs multi-rôles, trajectoire de butinage, couche joueur
ruche/miel). Conception complète :
`docs/conception/CONCEPTION_POLLINISATION_CYCLE_VIE.md`, réorganisée en
**Partie I (moteur, re-fige le golden) / Partie II (couche joueur)**.
Décisions clés :
- **A** floraison = scalaire `floraison ∈[0,1]`, double porte **GDD + photopériode**,
  fenêtre par espèce (estivale).
- **B** nouaison **continue** ∝ `pollen_recu` (dépôts d'agents conspécifiques),
  **fin de floraison par plante** (remplace `FRUIT_NOUAISON_WEEK`), `self`/`wind`
  pleins, entomophiles **sans plancher**.
- **C/E** **champs pollinisateurs PAR TYPE** + **registre data-driven**
  `PollinatorSpec` (abeille/syrphe/papillon au départ, extensible) ; ressource =
  `floraison × attractivite(type)` ; **pas de Vigueur joueur** pour le butinage.
- **D** **ponts de cycle de vie** (patron généralisé) : chenille→papillon (larve
  +herbivorie) **et** syrphe_larve→syrphe (larve −ravageur, prédatrice puceron) ;
  ponte/maturation/**famine→mortalité**/métamorphose.
- **F** **butineurs déterministes MÉCANIQUES** : trajectoire fleur-en-fleur,
  **constance florale** (pollen conspécifique), simulés en Python + exposés
  snapshot (bascule actée des sprites perceptifs → load-bearing).
- **G** brassage multi-pères **non retenu** (l'existant suffit).
- **H/I/J** (couche joueur) : **ruche** capture un essaim sauvage ; **miel** =
  intégrale du nectar butiné → Vigueur via `recolter_miel`, **équipement débloqué
  par maîtrise** ; **piqûre** = alarme émergente (écraser/récolter sans gear →
  phéromone → piqûre au curseur, philo #1).

**PROCHAINE étape = implémentation.** Découpe **7 tronçons** (cf doc §L) :
①→⑤ MOTEUR (re-fige le golden isolé), ⑥⑦ COUCHE JOUEUR (golden neutre, sprint
distinct APRÈS le moteur). Ordre conseillé ①→⑤. Écrire les kickoffs d'impl
`01_*.md`…au démarrage. **Reprise à froid** : « lis
`docs/conception/CONCEPTION_POLLINISATION_CYCLE_VIE.md` §K-§L puis lance le
tronçon ① (Floraison réelle + phénologie, golden visé NEUTRE) ».
