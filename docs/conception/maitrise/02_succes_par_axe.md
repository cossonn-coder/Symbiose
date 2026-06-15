# Maîtrise — §9 · Le succès, définition par axe (D12.1)

> Partie 2/3 de la conception des paliers de maîtrise. Index :
> [`../CONCEPTION_MAITRISE.md`](../CONCEPTION_MAITRISE.md).
> Amont : [`01_modele.md`](01_modele.md) (le modèle). Aval :
> [`03_taxonomie_objets.md`](03_taxonomie_objets.md) (la taxonomie, D12.3).

> **Sous-sprint D12.1 (2026-06-04), conception seule.** Remplit le point §8.1.
> Précédé d'une **lecture moteur** (les signaux que le tick émet déjà) — le point
> de vigilance acté. Reste ouvert : les **Nᵢ** (répétitions/palier) → calibrage
> D12.4 ; le **câblage par objet** → taxonomie D12.3.

## 9.0 Le pivot — ce qu'est un « succès » (décisions Nico, 4 juin 2026)

> **Un succès = une action joueur dont l'effet émergent améliore le résultat
> au-delà du cours spontané — et qui est observée.**

Ce n'est **ni** un événement émergent sur le terrain (*une tomate qui pousse seule
= bonnes conditions, pas maîtrise*), **ni** une action simplement payée (*cliquer
ne suffit pas*). C'est l'**intervention qui change la trajectoire pour le mieux** —
le geste du jardinier qui obtient un résultat que le milieu n'aurait pas produit
seul (ex. *tailler les gourmands d'une tomate indéterminée → plus de récolte*).

**Opérationnalisation (moteur déterministe, donc pas de contrefactuel calculable) :**
« améliorer au-delà du cours spontané » se mesure par des signaux **déjà émis** —
soit *un stress présent que l'action lève*, soit *un stress qui frappe les
non-protégés et que la préparation prévient*. La couche maîtrise **lit** ces
signaux ; elle n'ajoute aucun état au tick (cf. §6 — golden intact).

## 9.1 Les signaux que le tick émet déjà (lecture moteur)

Transitions discrètes lisibles depuis la couche gameplay (au-dessus du tick) :

| Famille | Signal concret | Source |
|---|---|---|
| Stade | `advance_stage()→True` ; atteinte du **dernier stade** (`maturite==1`, `is_seed_bearing`) | `engine._avancer_stades`, `vigueur_plante`, `reproduction` |
| Santé | `health` 3→…→0 (déclin/mort) ; +1 (convalescence) | `_tick_senescence_health` |
| Mort (par cause) | sénescence · conflit · hiver (annuelle/bisannuelle) · dégât médié (gel/grêle) | `_tick_senescence_health`, `_resoudre_conflits`, `_winter_transition`, `_mediated_damage` |
| Reproduction | parent fructifie → gènes enfant en banque-sol ; recrue 🌰 ; **tag** `auto`/`biparental`/`introgr.` | `engine._reproduction`, `reproduction.py` |
| Floraison/Récolte | phases déclenchées ; graine → `player_seed_bank` si `is_seed_bearing` | `engine.tick_semaine` |
| Météo/aléa | `event.kind`+`intensity` ; **dégât médié renvoie un log VIDE si zéro perte** | `weather_at`, `_mediated_damage`, `appliquer_alea` |
| Stagnation | `⏸ sec` (`ok_hum` faux) · `🌑 ombre` · `❄ froid` | `_avancer_stades` |
| Succession | recrue **férale** issue de la banque-sol qui s'établit | `sim/succession.py`, `eco.tick_seed_bank` |
| Champs (trajectoire) | `microbiome`, `soil_memory`, `fertilite`, `vitalite`, `om_*` (continus, échantillon fin de saison) | `eco.summary()` |
| Actions joueur | `recolter→ratio` (1.0 = payé) · `manger→gain` · `deraciner/ecraser→bool` | `sim/actions.py` |

**Constat structurant :** le moteur possède *tous* les signaux pour les **êtres
vivants** et les **concepts transversaux**. En revanche **outils, structures et
techniques n'existent pas encore** (seuls 4 gestes sur le vivant codés ; le
catalogue d'actions-milieu de `CONCEPTION_VIGUEUR.md` §3.2 est conçu mais non
codé). Leur succès est donc fixé ici comme **patron**, pas comme table calibrable
(câblage → D12.3 + sprints d'action).

## 9.2 Être vivant (espèce) — nature de preuve croissante

| Palier | Preuve = une intervention qui… | Signal lu |
|---|---|---|
| 0→1 **découverte** | …rien : **observer** l'espèce (gratuit, §2.1) | germination vue |
| 1→2 **investissement** | …fait franchir un cap **non franchi seul** (lever une stagnation sec/ombre/froid → reprise de croissance) | flag `⏸/🌑/❄` qui se lève après le geste |
| 2→3 **maîtrise** | …amène à **reproduction** (favoriser pollinisateurs → croisement ; tailler → mise à fruit) | tag `biparental`, `advance_stage` post-geste |
| 3→4 **expertise** | …**optimise** récolte/repro de façon **répétée, fiable, en pleine santé** (tailler les gourmands → récolte ↑) | récolte/repro + `health==3`, répété |
| 4→5 **transcendant** | **conjonction** (§9.4) | voir §9.4 |

## 9.3 Concept transversal — toujours « grâce à ton intervention »

Jamais émergent pur : le stress doit être **levé/prévenu par une action**.

| Concept | Succès |
|---|---|
| météo/climat | **préparation** (paillage/voile/brise-vent) → sujets protégés traversent l'aléa **sans perte** *là où les exposés souffrent* (`_mediated_damage` vide sous protection) |
| sol/microbiome | amender/inoculer/grelinette → `microbiome`/`soil_memory` ↑ et uptake/vigueur suit |
| eau | pailler/drainer → **aucune stagnation hydrique** en saison sèche sur la zone traitée |
| lumière | tailler/éclaircir → strate basse qui repart (un `🌑` chronique qui se lève) |
| pollinisation | favoriser auxiliaires → **croisement biparental** (tag, vs autofécondation) |
| succession | semer/bouturer au bon endroit → recrue **établie** (atteint jeune/adulte) |

## 9.4 Palier 5 (transcendant) = conjonction action **+** naturalisation

Décision Nico : la transcendance est **très dure** car elle exige **les deux** à la
fois (les deux principes de CLAUDE.md cessent de s'opposer — l'action est la
**preuve**, l'auto-suffisance est l'**état atteint**) :

- **(a) Action experte/extraordinaire réussie** (Nₐ fois) — gérer le cas le plus
  dur : un aléa du **~20 % imprévisible** (météo), une intervention de **sauvetage**
  réussie, une optimisation de pointe. *La maîtrise résulte d'actions du joueur.*
- **ET (b) Naturalisation** — une **génération férale** (auto-semée depuis la
  banque-sol, **non replantée** par le joueur) **boucle son cycle en pleine santé**
  dans le sol/microbiome que le joueur a façonné : « le sol et l'environnement
  l'accueillent **comme si elle était native** ». *L'écosystème tient seul.*

C'est le **seul** endroit où le « ça pousse tout seul » compte — uniquement
**conjoint** à (a). Seul, l'auto-semis reste « bonnes conditions », pas maîtrise.

> Les concepts transcendent par analogie : (a) une action experte sur le concept
> (météo : le ~20 % imprévisible géré) **ET** (b) le domaine s'auto-régule sans
> intervention (le sol auto-entretient son microbiome, le cycle de l'eau
> s'auto-tamponne).

## 9.5 Outil / Structure / Technique — patron (câblage D12.3)

Action par nature → succès = l'action via l'objet **produit son effet visé**,
observé dans une fenêtre :

- **outil** : `arroser`→`ok_hum` restauré ; `grelinette`→infiltration ↑ ;
  `sécateur`/`tailler`→empreinte réduite → lumière livrée.
- **structure** : prouve sa fonction **pendant un stress** (`voile` au gel → semis
  intact ; `tuteur` → grand sujet ne verse pas).
- **technique** : son issue émergente (`bouture` reprend N semaines ;
  `inoculer`→microbiome ↑).

v1 minimal acceptable : « action payée **et** effet visé observé = 1 preuve ». Le
détail « quels objets chaque action touche » est la donnée que lit `cout_action`
(§4.2) → **taxonomie D12.3**.

## 9.6 Implications pour la couche maîtrise (sans toucher au tick)

- **État gameplay nouveau, minimal** (au-dessus du tick, par avatar, §6) :
  (i) un **tag de provenance** par plante (*féral* vs *replanté par le joueur*) pour
  distinguer la naturalisation §9.4(b) ; (ii) une **fenêtre d'imputation** liant un
  geste joueur à l'amélioration qu'il produit (le stress levé/prévenu). Aucun de ces
  états ne vit dans le tick déterministe → **golden intact** (§6).
- **Gate d'observation** : un succès se **registre quand il est observé** (carnet
  auto / notification) — cohérent avec « émergent sur le terrain *si c'est observé
  par le joueur* » et avec les trois voix narratives (CLAUDE.md).
- **Répétition (Nᵢ)** : la *nature* de la preuve est fixée ici ; le *nombre* par
  palier suit la courbe log §2.3 et se **calibre post-test** (D12.4).
