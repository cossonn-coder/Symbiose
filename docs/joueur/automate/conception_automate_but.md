# CONCEPTION — Automate dirigé par le but (D87)

> **FIGÉE le 2026-07-23** (`/conception`, sur repo). Étend le **jardinier automate
> réactif** (D78, `conception_jardinier_automate.md`) d'un **étage de planification
> moyens-fins** déterministe. Prêt pour `/sprint-auto sprint_automate_but`.
>
> Amorce d'origine (écrite SANS accès repo, recadrée ici par la lecture du code) :
> `brief_amorce_automate_but_D87.md`. Retour d'aval (C1-C4 + exigences A/B + log)
> intégré. Carnet de bord vivant : `sprints/joueur/automate/sprint_automate_but/00_etat.md`.

## 0. Intention

Aujourd'hui, l'automate est **purement réactif** (loi de Liebig : il lève le
facteur limitant dominant de chaque cultivée, tick par tick). Un `Objectif(geste,
quantité, cible)` ne fait que **biaiser la priorisation** (`BONUS_OBJECTIF`) et
**compter la progression** (`incrementer`). **Si la cible n'est même pas plantée,
il ne fabrique pas les conditions du but.**

D87 rend l'automate **dirigé par le but** : il comprend la **chaîne d'étapes** vers
un objectif et la **planifie à rebours** (moyens-fins), **déterministe, sans RNG ni
« IA »** (philo #3). Exemple canonique — `recolter tomate ×N` alors qu'aucune tomate
n'est plantée : obtenir la graine → semer → mener à l'adulte → favoriser
auxiliaires/pollinisation → récolter à maturité ; et si un chaînon manque sans
source → **impasse honnête**, sans tricher.

D87 **n'est PAS** le système de quêtes (D79, habillage narratif aval) ni un
changement du moteur : c'est le **moteur de planification** de l'automate, qui vit
**au-dessus du tick** comme le reste de l'instrument (invariant H2 → golden intact).

## 1. Recadrage : D87 est petit

Le cœur réactif **couvre déjà tout le « MAINTENIR »** (arroser, pailler + ravito,
désherber, grelinette, tailler, récolter) — pour les cultivées. Il ne joue **jamais**
que 3 gestes « créatifs » : `planter`, `acheter_au_magazine`, `favoriser_auxiliaire`.

Le planificateur ne comble que ce **« FAIRE ADVENIR »**. Pour l'exemple tomate la
chaîne est **quasi-linéaire, profondeur ≤ 3** :

```
recolter tomate ×N   ←   cultivée(s) fruitière(s) présente(s)   ←   planter(sp)   ←   graine en banque   ←   acheter_magazine(sp)
   (déjà RÉACTIF)          (Liebig MAINTIENT + pollinisation)      (créatif, 1×)     (sonde la banque)      (si palier 3 famille)
```

> **Partage du travail** — planificateur = faire ADVENIR les conditions initiales
> (gestes créatifs, ponctuels) · Liebig réactif = MAINTENIR (gestes correctifs,
> chaque tick). Une graine plantée devient cultivée **d'elle-même** à la levée
> (`planter` pose `cultive=True` → `marquer_replante`) → elle entre sous tutelle et
> Liebig prend le relais **sans mécanique neuve**.

**Archi B (régresser le modèle biologique) est REJETÉE** = sur-ingénierie : la
biologie est déjà servie par Liebig, il n'y a rien à régresser. On retient
l'**archi A/C** : un **petit catalogue d'opérateurs** dont les pré/post-conditions
sont **sondées sur l'état vivant du moteur** (patron `objectifs.est_atteignable` /
`proposition.proposer` étendu). Aucun geste nouveau, aucun seuil biologique recopié.

## 2. Le catalogue d'opérateurs (3)

Un **opérateur** = un geste créatif existant + ses pré/post-conditions symboliques,
vérifiées en sondant le moteur. `recolter` **reste réactif** (règle `organe_mur`).

| Opérateur | Pré-conditions (sondées) | Post-condition |
|---|---|---|
| `acheter_magazine(sp)` | `sp` offerte au magazine (palier 3 d'un membre de famille, `SEUIL_MAGAZINE`) ∧ Vigueur ≥ `COUT_MAGAZINE` | graine `sp` en `PlayerSeedBank` |
| `planter(sp)` | graine `sp` en banque ∧ un **plot libre** déterministe existe | grain en attente → (à terme) cultivée de `sp` |
| `favoriser_auxiliaire(zone)` | une cultivée **`fruitier`** de `sp` existe ∧ sa zone n'a pas encore de rondelle `auxiliaire` | habitat auxiliaire (pression pollinisation ↑), **one-shot** |

- **`planter` ≠ plante** (`gestes.py:100`) : il dépose un `GrainEnAttente` qui lève
  *plus tard* par succession (plot libre + niche favorable) — germination
  **conditionnelle, parfois jamais**. Le sous-but « adulte présent » cache donc deux
  portes que Liebig ne garantit pas (lever, survivre) → voir §5 (veille / re-semis).
- **Source de graine = banque UNIQUEMENT** pour `planter`. Le magazine est l'unique
  **ravitaillement** de la banque (voie n°2). La voie « récolter des semences d'une
  plante-mère » est **écartée** (circulaire, non implémentée, #2).

### 2.1 « Récoltable » typé organe (C2)

Le but `recolter sp` n'a pas le même sens selon l'organe. Signal = l'attribut de
classe **`fruitier`** (`plants/base/familles.py:79`) — **lu, jamais dupliqué** :

- **`fruitier=True`** (tomate, courgette, fraise, framboise…) → but satisfait par
  **fruit mûr** (`plant.fruits`) ; la **sous-chaîne pollinisation**
  (`favoriser_auxiliaire`) est AJOUTÉE au plan.
- **`fruitier=False`** (laitue, carotte…) → but satisfait à **maturité végétative**
  (`maturite ≥ MATURITE_MUR`, = `organe_mur` réactif) ; **pas** de sous-chaîne
  pollinisation.

C'est la différence de **longueur de chaîne** que le banc multi-espèces (§7) exhibe.

### 2.2 Suffisance N, pas simple présence (C1)

Une seule cultivée ne produit pas N récoltes. Le déclencheur « advenir » raisonne
en **culture permanente** : le planificateur maintient **`nb_plants_cible`** cultivées
vivantes de `sp` **tant que progression < N** (le comptage réel des récoltes reste
`incrementer`, rendement **non forcé** — on plante « assez pour espérer N »).

- Défaut `nb_plants_cible = min(N, 3)`, **surchargeable** au banc.
- Objectif actif jusqu'à N atteint **ou** graines épuisées sans source (→ veille §5).

### 2.3 Placement & déterminisme (T4/T5)

L'automate n'avait jamais « choisi où planter ». Politique déterministe : **premier
plot libre** en balayant `engine.tiles` (ordre de liste) puis `(r, c)` croissant,
où *libre* = `tile.plants_at(r,c)` sans vivant **et** aucun grain en attente. Les
objectifs sont déjà triés par `id` ; un objectif → une espèce → une chaîne ; la
cible florale de `favoriser_auxiliaire` = la cultivée de plus petit
`(tile_id, y_cm, x_cm)`. **Zéro RNG.**

### 2.4 Timing de `favoriser_auxiliaire` (C4)

L'habitat auxiliaire (rondelle persistante) doit être **établi AVANT la floraison**
pour que les pollinisateurs soient présents à temps. On le pose donc **au plus tôt** :
dès qu'une cultivée `fruitier` de `sp` existe (quel que soit son stade) et que sa
zone n'a pas de rondelle `auxiliaire` → **une seule fois**. Pas de calage sur le pic
de floraison (trop tard).

## 3. Articulation avec le cœur Liebig — préemption survie (Q3)

Le planificateur **ne remplace pas** la boucle réactive, il **s'y insère** : après
la collecte des plans réactifs, pour chaque objectif actif il produit les **plans de
gestes créatifs** (+ éventuelles impasses de veille), fusionnés dans le tri de
priorité de l'étape 4.

- **Préemption survie** : les gestes créatifs (advenir) reçoivent une priorité
  **MODÉRÉE, SOUS** les facteurs de survie du vivant existant. Advenir est *ralenti*,
  jamais joué au prix d'une plante qui meurt.
- **Vigueur** (D11) : en mode payé (`paie_vigueur=True`, preset BRIDE), le budget-cut
  existant (`_couper_au_budget`) fait naturellement gagner la survie. En mode
  coût-0 (`paie_vigueur=False`, preset LIBRE — le défaut), rien n'est coupé, mais
  **l'ordre de priorité reste requis** pour **ordonner** les gestes déterministement.

## 4. Persistance du plan & re-planification sur déclencheur (Q6)

Un sous-but « croître jusqu'à maturité » dure des semaines : **ne pas replanifier
chaque tick**. État planificateur persistant par objectif sous
`game_state["automate_plans"]` (opt-in, comme `automate_objectifs`) :
`{obj_id: {tentatives_semaille, essai_precedent:(saison, plot), en_veille, chainon}}`.

Le plan n'est ré-évalué que sur **déclencheur d'invalidation** :
- sous-but atteint (graine obtenue / cultivée levée / adulte atteint / fruit mûr) ;
- sous-but devenu infaisable (source disparue) ;
- prérequis apparu (offre magazine ouverte au palier 3, plot libéré) ;
- cible morte (re-évaluer `nb_plants_cible`).

Profondeur de récursion bornée (`PROFONDEUR_MAX ≈ 4`) ; **aucune** simulation
temporelle en avant — on émet le prochain geste créatif faisable, puis on **attend**
la biologie.

## 5. Veille, re-sonde, impasses honnêtes (Q7 + T1 + C3)

Sur chaînon sans source **ou** graine qui ne lève/survit pas : l'objectif **reste
ACTIF** (mise en veille), l'impasse est **tracée une fois** (chaînon nommé), et le
planificateur **re-sonde sur déclencheur** (§4). Types d'impasse :

- `chainon_manquant` — pas de graine, pas d'offre magazine. Réveil possible si la
  maîtrise ouvre le magazine, ou si un plot se libère.
- `niche_defavorable` — graine semée qui ne lève/survit pas.

**Re-semis armé sur changement de condition (C3)** : la simulation étant
déterministe, re-semer la **même** espèce au **même** plot dans les **mêmes**
conditions redonne exactement la même mort. Le re-semis n'est donc armé que si
`(saison, plot_choisi)` **diffère** de l'essai précédent (nouvelle fenêtre
favorable ou autre plot) ; sinon → `niche_defavorable` **directe**. Garde-fou dur
`tentatives ≤ 2`.

**Dépendance biologique dure (Q8)** : l'exemple tomate ne marche que si l'espèce
**survit et fructifie** (la tomate meurt tôt dans certains scénarios — froid de
démarrage + mildiou familial, cf. `tomate-mort-precoce`). D87 **suppose** D84/D86
corrects mais ne les **masque pas** : si la biologie ne suit pas, l'impasse honnête
la **révèle** (le banc §7 est fait pour ça).

## 6. Log exhaustif structuré (Q13)

Un comportement de planification déterministe est une **boîte noire** sans trace :
le log rend le raisonnement moyens-fins **inspectable** et sert d'**oracle de
déterminisme** (2 runs à entrées égales → log **identique**).

- **Canal = `automate_journal` existant** (`trace.py`), **ENRICHI** — pas un canal
  neuf. **Technique/debug, JAMAIS diégétique.** Frontière avec le **carnet D14**
  déjà nette dans le code : le carnet lit `sim/journal.py` (voix « je ») ; le flag
  `ecrit_carnet` gate les écritures diégétiques **séparément**. Les deux ne
  fusionnent jamais (sinon #5 HUD et #6 « pas de narrateur » violés).
- **Schéma de ligne** (dict champs-structurés ; le texte se **dérive** des champs) :
  - `categorie` ∈ {`perception`, `diagnostic`, `plan`, `geste`, `geste_coupe`,
    `veille`, `impasse`, `consequence`, `resultat`} (les 3 dernières existent déjà) ;
  - `semaine` (int), `niveau` (0 décision · 1 détail · 2 perception fine) ;
  - `objectif_id`|None, `espece`|None, `zone`=`(tile_id,r,c)`|None (plot choisi ;
    None pour `acheter_magazine`) ;
  - `detail` = dict spécifique (ex. `plan`→`{sous_but, raison}` ;
    `geste_coupe`→`{verbe, cause: budget|survie|veille}` ; `veille`→`{chainon, source}`).
- **Log toujours complet** (tous niveaux écrits → préserve l'oracle) ; verbosité et
  filtre = **vues LECTURE SEULE** (`filtre.py` : `filtrer(journal, categorie=…,
  espece=…, objectif_id=…, zone=…, niveau_max=…)` + `rendre(ligne)->str`). Un run
  filtré et un run brut partagent le **même** log sous-jacent.
- **Ordre total stable** : append déjà déterministe (boucle sur listes, départage
  `(tile_id, y_cm, x_cm)`) ; vue triée par `(semaine, _rang_categorie, objectif_id,
  zone)`. **Aucun horodatage horloge, aucun id non déterministe.** Golden intact
  (write-only hors tick).

## 7. Banc « X depuis rien » paramétré (exigence A) + vue Godot

Le banc du dernier tronçon n'est **pas « tomate » en dur** :

```
banc_culture_depuis_rien(espece, quantite=N, source_graine="auto", cout_vigueur=False)
    source_graine ∈ {auto, banque, magazine, aucune}   # force chaque branche de l'arbre
    cout_vigueur : mappe sur ProfilAutomate.paie_vigueur  # False = coût 0 (LIBRE)
```

→ **matrice de test** : chaîne complète / achat magazine / impasse × multi-espèces
(exhibe C2 fruit vs feuille/racine, révèle les bugs bio par espèce, Q8). Il consomme
le **log filtré** pour composer le récit d'une espèce.

**Vue Godot** (règle permanente = dernier tronçon) : l'onglet automate existant
(`WorldView.Automate.cs`) surface le **log filtrable** (l'utilisateur coche les
catégories). Le filtre est une **vue lecture seule** — un run filtré et non filtré
produisent le même log (déterminisme préservé).

### Exigence B — coût Vigueur réglable à 0

**Déjà présent** : `paie_vigueur=False` (preset LIBRE, défaut) → `assurer_solde_libre`
rehausse le solde chaque tick → rien n'est throttlé (= coût 0 effectif, golden
neutre, testé). On **réutilise** ce flag (param banc `cout_vigueur`), **pas** de
nouveau `cout_vigueur_actif`. Deux régimes documentés : **coût 0** = éprouver
chaîne + biologie isolément ; **coût normal** (BRIDE) = éprouver économie + arbitrage.

## 8. Philosophie (#1-#7)

- **#1/#2** — le plan **ne pose que des conditions** (gestes sur le milieu créant des
  contraintes de champ) ; il ne force **jamais** l'issue biologique. Aucun sous-but
  n'écrit directement sur l'état d'une plante. Une plante qui meurt/ne noue pas →
  **échec émergent honnête**, pas un bonus caché.
- **#3** — chaînage arrière déterministe borné (planification symbolique classique) ;
  **pas** l'« IA » proscrite (ni réseau, ni apprentissage, ni RNG). Ordre total
  stable partout ; le log est l'oracle.
- **#4/#7** — pas de game-over, pas de redémarrage ; lecture locale plot par plot.
- **#5/#6** — l'automate est un **instrument de test**, pas une surface joueur : son
  log est technique, jamais un HUD ni un contenu narratif. Le futur système de
  quêtes (D79, aval) devra rester diégétique et **ne jamais piloter le joueur**.

## 9. Découpage — 5 tronçons (golden intact partout)

1. **① Log structuré** — enrichit `trace.py` (catégories + `niveau` + `detail`) +
   `filtre.py` + verbosité harnais + **test oracle déterminisme**. *Fondation : le
   schéma précède ses écrivains.*
2. **② Opérateurs + moteur de régression** — `operateurs.py` (3 opérateurs,
   post-condition organe-typée `fruitier` **dès la définition**, sous-chaîne
   pollinisation conditionnelle, placement déterministe) + `planification.py`
   (chaînage arrière borné, état persistant `automate_plans`). Émet `plan`/`diagnostic`.
3. **③ Articulation boucle Liebig + préemption survie** — câblage
   `boucle.jouer_tick`, priorité créatif < survie (avec/sans coût), timing
   `favoriser_auxiliaire`. Émet `geste`/`geste_coupe`.
4. **④ Veille + re-sonde + impasses honnêtes** — déclencheurs (suffisance N,
   `(saison,plot)`), re-semis borné, `chainon_manquant`/`niche_defavorable`. Émet
   `veille`/`impasse`/`resultat`.
5. **⑤ Banc « X depuis rien » paramétré + vue Godot** — `banc_culture_depuis_rien`
   (matrice espèce × source_graine × cout_vigueur) + surfaçage log filtrable dans
   l'onglet automate Godot.

**Golden = `57c166d8…` INTACT sur les 5 tronçons, ZÉRO re-figeage** (planificateur
opt-in, hors tick, no-op strict quand le golden tourne sans joueur/objectif).

## 10. Rattachements

D78 (socle réactif) · D11 (Vigueur, budget) · D12 (Maîtrise, déblocage magazine) ·
D13 (Magazine, voie n°2) · D17 (`PlayerSeedBank`, voie n°1) · arc pollinisation &
cycle de vie (chaîne biologique dure : floraison → `pollen_recu` → nouaison →
`plant.fruits`) · D14 (carnet — **frontière** stricte avec le log technique) ·
D19/organes-fruits (`fruitier`, `plant.fruits`) · D79 (système de quêtes, aval,
hors périmètre) · D25 (banque-sol pionnière → impasses légitimes, pas des bugs).
