# CONCEPTION — Plasticité & expression de gènes adaptogènes

> **Statut : CONCEPTION FIGÉE le 2026-06-21.** Prête à implémenter (5 sous-sprints,
> §6). Le §3 conserve la trace des arbitrages (tous tranchés).
>
> **Arbitrages Nico (2026-06-21) :**
> - **COÛT** = *compromis croissance/défense* (re-routage de vigueur, pas de bonus).
> - **PORTÉE** = *priming transgénérationnel* (la lignée transmet l'état d'expression,
>   pas le génotype — épigénétique).
> - **ARTICULATION** = *remplacer par `expressed_gene`* (point de lecture distinct
>   du génotype ; `stress_memory` se recentre sur la mortalité de fond).
> - **P1 PÉRIMÈTRE** = **5 gènes adaptogènes** (sécheresse, ombre, froid, pathogène,
>   asphyxie) → créer `cold_memory` + `infection_memory`, ajouter le gène
>   `tolerance_asphyxie` (`asphyxie_memory` existe déjà).
> - **P2 OUBLI** = **décroissance émergente** (aucun compteur ; l'oubli découle de
>   la désacclimatation + de `PRIMING_FRAC<1`).
> - **P3 VISIBILITÉ** = **signe diégétique** (mécanique apprenable, pas magique).
> - **P4 MAÎTRISE** = lien carnet interprétatif **OUI** (dette, dépend du système
>   maîtrise).
> - **P5 ACCLIMATATION** = **hystérèse** (montée et descente à vitesses distinctes).
> - **P6 CALIBRAGE** = itératif assumé.
> - **P7 REGISTRE** = double registre darwinien + lamarckien **assumé**.

## 0. Objectif & intuition

Aujourd'hui un gène de Symbiose est un **multiplicateur figé à la naissance**
(`genetics.py`) : la sélection naturelle n'opère que **sur des générations** (les
mauvais génotypes meurent, les bons se reproduisent). Le vivant a une seconde
corde : un même génotype **s'exprime différemment selon le milieu vécu**. Une
plante qui a connu la sécheresse renforce ses défenses *de son vivant*, et peut
même transmettre cet état « d'alerte » à sa descendance **sans modifier son ADN**.

On veut câbler cette **plasticité phénotypique** : le stress *vécu* régule à la
hausse l'**expression effective** des gènes de tolérance, **à un coût** (la
défense se paie en croissance). C'est du **flux → contrainte → réponse biologique
émergente** (philo #2) à l'état pur : pas de bonus direct, c'est la contrainte
qui *induit* la réponse.

Trois échelles d'adaptation coexisteront alors — comme dans le vivant :

| Échelle | Vitesse | Réversible ? | Support |
|---|---|---|---|
| **Génotype** (darwinien) | lente, sur générations | non — gravé dans l'ADN | `genes[g]` (existe) |
| **Expression** (épigénétique / plastique) | rapide, intra-vie | **oui** — s'efface si le stress cesse | `expression[g]` (nouveau) |
| **Mortalité de fond** (hormèse brute) | — | — | `stress_memory` (existe, recentré) |

Le génotype est la **partition** ; l'expression est l'**interprétation** que le
milieu impose. La distinction lamarckien/darwinien est ici *mécaniquement réelle*
et non cosmétique.

## 1. État de départ (briques déjà là)

| Brique | Où | Rôle pour nous |
|---|---|---|
| `GENE_NAMES`, `clamp_gene`, `GENE_HARD_MAX = 1.6` | `plants/genetics.py:30,43,40` | définit les gènes ; borne dure réutilisée comme plafond d'expression |
| `gene(name)` lecture du génotype | `plants/base/instance.py:115` | **point pivot** : `expressed_gene` se branche à côté |
| `shade_memory`, `drought_memory`, `asphyxie_memory` | `plants/base/instance.py:35-38` | **substrat tout prêt** : intégrations lentes du stress vécu, déterministes |
| `_update_physiology` (intègre les mémoires par tick) | `sim/engine/croissance.py:175` | où la dynamique d'expression vivra |
| décroissance `shade_memory` quand l'ombre lève | `sim/engine/mortalite.py:239` | preuve que les mémoires sont déjà réversibles |
| `drought_stress_damage` / `shade_stress_damage` lisent `gene("tolerance_…")` | `sim/effects/perturbations.py:171,210` | **consommateurs n°1** : liront `expressed_gene` |
| gates de croissance `ok_hum` / ombre lisent `gene("tolerance_…")` | `sim/engine/croissance.py:76,211`, `sim/growth/phases.py:160` | **consommateurs n°2** |
| vigueur = `sante × maturite × qi_local × gene("vigueur")` | `sim/vigueur_plante.py:91` | où le **coût croissance/défense** s'applique |
| `child_genes` (hérédité génotype + mutation) | `sim/reproduction.py:108` | où le **priming** se greffe (transmettre l'expression) |
| `stress_memory` (endurcissement générique → mortalité) | `sim/effects/perturbations.py:401` | **recentré** sur background_mortality / herbivory, plus de rôle adaptogène par-gène |
| `symptom_marks` + `decay_symptoms` (état per-plante décroissant) | `plants/base/instance.py:119` | **patron** d'implémentation pour l'état `expression` |

Rien n'existe sur la plasticité elle-même (`grep` plasticité/expression/acclimat
= vide). Terrain vierge, mais **tout le substrat de mémoire est déjà là**.

## 2. Le modèle proposé

### 2.1 `expressed_gene(g)` — phénotype = génotype × plasticité

```
expressed_gene(g) = clamp_gene( genes[g] × expression[g] )
```

- `genes[g]` : génotype figé (inchangé).
- `expression[g]` : facteur plastique ∈ [`EXPR_MIN`, `EXPR_MAX`] autour de 1.0,
  piloté par la mémoire de stress. Neutre 1.0 = phénotype = génotype.
- `clamp_gene` borne le tout aux **limites dures** existantes (`[0.40, 1.60]`) :
  la plasticité ne peut pas faire sortir une plante de sa physiologie possible.

Tous les sites qui lisent `gene("tolerance_secheresse")` / `gene("tolerance_ombre")`
(consommateurs n°1 & n°2, table §1) passent à `expressed_gene(...)`. Les sites
lisant `gene("vigueur")` / `gene("hauteur")` **ne changent pas** (non adaptogènes).

### 2.2 Quels gènes sont adaptogènes ? (5 gènes — P1 acté)

Sous-ensemble **défensif** complet — chaque gène apparié à une **mémoire
d'exposition** déterministe :

```python
ADAPTOGENIC_GENES = ("tolerance_secheresse",  # ↔ drought_memory   (existe)
                     "tolerance_ombre",        # ↔ shade_memory     (existe)
                     "rusticite_froid",        # ↔ cold_memory      (À CRÉER)
                     "resistance_pathogene",   # ↔ infection_memory (À CRÉER)
                     "tolerance_asphyxie")     # ↔ asphyxie_memory  (existe ; gène À CRÉER)
```

`hauteur`/`vigueur` **ne sont pas** adaptogènes (traits constitutifs, pas défensifs).

**Deux mémoires à créer** (leur signal existe déjà dans le moteur) :
- **`cold_memory`** — intègre l'exposition au froid sub-létal (température sous un
  seuil via `weather_at`). Modèle bio : *cold hardening* (acclimatation au gel).
- **`infection_memory`** — intègre la pression pathogène vécue (issue de
  `fungal_disease` / `disease_probability`). Modèle bio : *SAR* (résistance
  systémique acquise), priming immunitaire.

**Un gène à créer** : `tolerance_asphyxie` — ajouté **en fin de `GENE_NAMES`**
(`genetics.py`) pour **préserver les canaux de hash** des gènes existants
(`child_genes` indexe par position) → ajout golden-neutre attendu au ① (à
vérifier : aucun site ne le lit encore). Il modulera ensuite le dégât d'asphyxie
(`engine/mortalite.py:69`), aujourd'hui non médié par le génotype.

### 2.3 Dynamique d'expression (dans `_update_physiology`)

Chaque tick, pour chaque gène adaptogène, l'expression glisse en **lerp lent**
vers une **cible** fixée par la mémoire de stress correspondante :

```
cible(g)        = 1.0 + EXPR_GAIN × memoire(g)              # memoire ∈ [0,1]
tau             = TAU_UP  si cible(g) > expression[g]       # acclimatation
                  TAU_DOWN sinon                            # désacclimatation
expression[g]  += ( cible(g) − expression[g] ) × tau
```

- Appariement mémoire↔gène : `tolerance_secheresse↔drought_memory`,
  `tolerance_ombre↔shade_memory`, `rusticite_froid↔cold_memory`,
  `resistance_pathogene↔infection_memory`, `tolerance_asphyxie↔asphyxie_memory`.
- Stress installé → mémoire haute → cible > 1 → l'expression **monte** (défense).
- Stress levé → la mémoire redescend (déjà câblé, `mortalite.py:239`) → la cible
  retombe → l'expression **redescend** : **acclimatation réversible**.
- **Hystérèse (P5 acté)** : deux vitesses, `TAU_UP` ≠ `TAU_DOWN`. La plante
  **garde un temps** son endurcissement après la fin du stress (`TAU_DOWN` <
  `TAU_UP` → désacclimatation plus lente) — mémoire de stress réaliste, évite le
  yo-yo. Knobs de calibrage (P6).

**La boucle d'endurcissement émerge gratuitement** : sécheresse →
`drought_memory ↑` → `expression[tolerance_secheresse] ↑` → `drought_stress_damage`
(qui lit `expressed_gene`) tape **moins fort**. Lent **exprès** (`tau` petit) : un
coup brutal sur une plante non-acclimatée tue encore — c'est la leçon permaculture
du **durcissement des semis** (hardening off).

### 2.4 Le coût : compromis croissance/défense (choix acté)

La sur-expression (expression > 1) **re-route** la vigueur vers la défense — elle
ne s'ajoute pas. Dans `vigueur_plante.py` :

```
surexpression = Σ_g max(0, expression[g] − 1)        # « budget défense » mobilisé
cout_defense  = 1 − DEFENSE_COST × surexpression       # ∈ ]0,1], borné
vigueur      *= cout_defense
```

Une plante qui blinde sa tolérance sécheresse **croît moins et fait moins de
graines**. C'est ce qui empêche le buff gratuit (philo #2) et crée l'arbitrage :
survivre au stress *coûte* de la performance. Le coût ne s'applique qu'à la
**sur**-expression (expression ≤ 1 → coût nul) — désexprimer n'est jamais pénalisé.

### 2.5 Priming transgénérationnel (choix acté)

À la production de graine, l'enfant naît avec une expression **initiale héritée**
de la mère (pas neutre), **sans toucher son génotype** :

```
child.expression[g] = 1.0 + PRIMING_FRAC × ( mother.expression[g] − 1.0 )
```

- `PRIMING_FRAC ∈ ]0,1[` : fraction de l'état d'alerte maternel transmis. **Mère
  seule** (voie épigénétique dominante chez les plantes ; le père est parfois
  `None` en autofécondation).
- Une lignée éprouvée naît **pré-armée** → avantage de survie immédiat sous stress
  récurrent.
- **Oubli ÉMERGENT (P2 acté) — aucun compteur de générations.** L'effacement n'est
  pas programmé, il *découle* des règles déjà posées. Si le stress cesse : la
  mémoire de l'enfant ne se recharge pas → son expression retombe vers 1.0 *de son
  vivant* (désacclimatation) → quand il grène, il transmet un priming déjà affaibli,
  encore atténué par `PRIMING_FRAC<1`. **Double extinction** (désacclimatation
  intra-vie + atténuation à la transmission) → retour au neutre en 2-3 générations
  sans stress, automatiquement. Si le stress **persiste**, chaque génération
  recharge sa propre mémoire → le priming se maintient. Fidèle à l'épigénétique
  réelle (la déméthylation survient *parce que* le signal disparaît) et à la
  philo #2/#4 (*le sol et la lignée se souviennent, mais l'oubli existe*). La
  *durée* d'oubli se règle via `PRIMING_FRAC` / `TAU_DOWN`, pas par un minuteur ad hoc.

### 2.6 État ajouté sur `PlantInstance`

Sur le patron de `symptom_marks` (§1) :

```python
expression: dict[str, float]   # {gène adaptogène: facteur}, défaut 1.0
```

Initialisé à 1.0 (ou par priming via `child_genes`). **Moteur Python d'abord**
(feedback Nico) ; exposition au pont Godot = tronçon ultérieur si on veut un signe
visuel (cf. §3-P3).

## 3. ARBITRAGES DE PHILOSOPHIE & DESIGN (tous tranchés — 2026-06-21)

### P1 — Périmètre des gènes adaptogènes — **ACTÉ : 5 gènes**
Sécheresse, ombre, froid, pathogène, asphyxie. Création de `cold_memory` +
`infection_memory` (signaux existants) + gène `tolerance_asphyxie` (réutilise
`asphyxie_memory`). Critère retenu : *toute mémoire biologique réelle qui
s'implémente déjà dans le moteur*. Détail §2.2.

### P2 — Mécanisme du priming — **ACTÉ : mère seule, oubli émergent**
- Transmission par la **mère seule** (épigénétique maternelle dominante).
- `PRIMING_FRAC` : knob de calibrage (~0.3–0.5).
- **Oubli ÉMERGENT, pas de compteur** : retombe seul si le stress cesse, se
  maintient s'il persiste. Mécanisme détaillé §2.5.

### P3 — Visibilité joueur (PHILO #5/#6) — **ACTÉ : signe diégétique**
Mécanique **apprenable, pas magique**. Signe d'acclimatation branché sur la
sémiologie foliaire (`sim/semiologie.py`) — ex. feuillage coriace/glauque (cire)
pour une forte acclimatation sécheresse. Tronçon ⑤. (Forme exacte du signe :
calage au tronçon, cf. §4.) Sans ça le joueur subirait une mécanique invisible →
viole la boucle action → conséquence → observation → hypothèse.

### P4 — Lien avec la Maîtrise — **ACTÉ : oui (dette)**
Au palier de maîtrise « adaptation/génétique », le carnet passe de descriptif
(« feuillage coriace ») à interprétatif (« cette lignée s'est acclimatée à la
sécheresse »). Dépend du système de maîtrise → **inscrit en dette**, hors de ce
sprint (le moteur d'abord).

### P5 — Asymétrie montée/descente — **ACTÉ : hystérèse**
Deux vitesses `TAU_UP` / `TAU_DOWN` (`TAU_DOWN` plus lent → la plante garde un
temps son endurcissement). Détail §2.3.

### P6 — Garde-fou anti-emballement / anti-sélection — **ACTÉ : calibrage itératif**
Risques : (a) emballement → plus de mort par stress ; (b) coût défense trop lourd
→ acclimatés non-compétitifs (anti-sélection). Garde-fous : plafond `EXPR_MAX`
modeste (ex. 1.3) + `clamp_gene` dur (1.6) ; coût défense modéré pour que survivre
reste gagnant sous stress, payant sous abondance. **Réglage itératif assumé** (le
golden bougera, §5).

### P7 — Double registre darwinien + lamarckien — **ACTÉ : assumé**
Génotype (darwinien, lent, irréversible) **+** expression (lamarckien, rapide,
réversible) coexistent. Parti-pris thématique fort, cohérent philo #4 (le sol porte
la mémoire) et **déterministe** (tout dérive de mémoires déterministes, règle #3).

## 4. Synthèse biologique (à étudier — Nico)

Repères naturalistes, pour caler le modèle et un éventuel signe (P3) :

- **Plasticité phénotypique** : un même génotype produit des phénotypes
  différents selon l'environnement (feuilles de soleil épaisses vs feuilles
  d'ombre larges et minces, sur le *même* arbre). Réversible, non héritable au
  sens génétique.
- **Acclimatation / endurcissement** : exposition graduelle à un stress doux →
  montée des défenses *avant* le coup dur (synthèse d'osmoprotecteurs,
  épaississement cuticulaire, fermeture stomatique anticipée). C'est le
  **durcissement des semis** : on sort les plants progressivement avant repiquage,
  sinon ils grillent. Leçon permaculture directe.
- **Compromis croissance/défense** (*growth–defense tradeoff*) : les ressources
  allouées à la défense (métabolites, parois) ne le sont plus à la croissance/
  reproduction. Une plante très défendue croît moins vite. C'est le fondement
  biologique de notre §2.4.
- **Hormèse** : une petite dose de stress protège d'une grosse dose ultérieure
  (≈ `stress_memory` actuel, en plus brut).
- **Priming / mémoire de stress transgénérationnelle** : marques épigénétiques
  (méthylation de l'ADN, modifications de chromatine) induites par le stress
  maternel, transmises aux graines → descendance « pré-alertée ». **Réversible
  sur quelques générations** si le stress disparaît — d'où la distinction nette
  avec une mutation génétique, qui, elle, persiste.

## 5. Impact golden — à plat

- **Tronçon ① (substrat seul) : golden NEUTRE.** Tant que personne ne *lit*
  `expressed_gene` et que `expression` reste à 1.0 partout, le calcul est inchangé
  (même propriété que la sémiologie ① ou le ⑨). Lecture seule.
- **Tronçons ②–④ : re-figeage MAÎTRISÉ et annoncé.** Brancher `expressed_gene` sur
  les dégâts (②), le coût sur la vigueur (③) et le priming (④) modifie croissance
  ET mortalité → le hash bouge. Dérive **localisée, expliquée, annoncée** (règle de
  design #3, garde-fou golden CLAUDE.md). Calibrage itératif assumé (P6).

## 6. Tronçonnage (sprint GROS → 5 sous-sprints autosuffisants)

| # | Contenu | Golden |
|---|---|---|
| ① | **Substrat (le plus gros).** Gène `tolerance_asphyxie` (fin de `GENE_NAMES`) ; mémoires `cold_memory` + `infection_memory` (intégration dans `_update_physiology`, **lues par personne**) ; `ADAPTOGENIC_GENES` + `expression` sur `PlantInstance` + `expressed_gene()` + dynamique lerp à hystérèse. **Rien ne lit encore `expressed_gene`.** Tests d'unité sur la dynamique. | **NEUTRE** (à vérifier) |
| ② | Tous les consommateurs passent `gene(…)`→`expressed_gene(…)` : dégâts sécheresse/ombre/asphyxie + gates croissance + susceptibilités fongiques/gel. Acclimatation **active**. | re-figeage annoncé |
| ③ | Coût croissance/défense dans `vigueur_plante.py` (somme des sur-expressions → vigueur). Le compromis émerge. | re-figeage annoncé |
| ④ | Priming dans `child_genes` (mère → enfant, `PRIMING_FRAC`). | re-figeage annoncé |
| ⑤ | Signe diégétique d'acclimatation dans `sim/semiologie.py` (nouvelle `cause`) + consommation vue C# + entrée journal + dette (froid/pathogène déjà couverts ; **lien Maîtrise P4**). | NEUTRE (lecture) |

Boucle CLAUDE.md : `0N` → travailler → vérifier golden → MAJ `00_etat.md` →
commit → `/clear` → `0N+1`.

## 7. Dette / liens

- **Crée la dette** (à inscrire dans `DETTE.md` en fin de sprint) : lien Maîtrise →
  carnet interprétatif (P4, dépend du système maîtrise). *(Froid/pathogène ne sont
  plus une dette : intégrés au périmètre v1, P1 acté.)*
- **Recoupe** : `genetics.py`/D22 (génotype, introgression), sémiologie foliaire
  D33 (signe d'acclimatation P3), Vigueur/D11 (coût défense ↔ Vigueur universelle),
  stress chronique (sécheresse/ombre → santé, base sur laquelle on se branche),
  D41 (carence édaphique reportée — futur 3ᵉ gène adaptogène potentiel).
- **Extensible sans refactor** : ajouter un gène adaptogène = l'ajouter à
  `ADAPTOGENIC_GENES` + lui fournir une mémoire d'exposition.
