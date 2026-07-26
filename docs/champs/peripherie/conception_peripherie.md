# CONCEPTION — La PÉRIPHÉRIE : le jardin n'est pas une île (D73)

> **FIGÉE le 2026-07-26** (`/conception`, à partir de l'amorce de Nico du même jour).
> Dette source : **D73** (terraforming). Absorbe **D92** (motifs de décor uniformes)
> et **périme partiellement D93** (inventaire d'outils).
> Lignée : D58 (décor d'ambiance) → D83 (lisibilité) → D92 → **D73**.
>
> Re-tag assumé : D73 était étiquetée `rendu/ambiance` par héritage de D58. Le sujet
> est **moteur** (champs écologiques + gestes joueur) → rangée en **`champs/peripherie`**.

---

## 1. Intention

*Le jardin n'est pas une île, et le joueur doit pouvoir en négocier les bords — au
prix fort.*

Deux mouvements, dans cet ordre :

1. **La périphérie agit sur le jardin.** Aujourd'hui le décor (D58) est cosmétique :
   il ne fait rien. Tant qu'il ne fait rien, « couper la forêt » ne produit aucune
   conséquence observable — et la tentation serait d'écrire « moins de forêt →
   −10 % de croissance », ce qui violerait frontalement la philo #2.
2. **Le joueur agit sur la périphérie.** Abattre, recéper, étêter, endiguer, entailler,
   creuser. Chaque geste est lourd, coûteux, et laisse une trace *dans le milieu*.

L'ordre est structurant, mais **ce n'est pas une frontière de sprint** (décision D-2) :
tous les points de greffe existent déjà dans le moteur, donc le premier mouvement fait
2-3 tronçons, pas une fondation.

---

## 2. Ce que le moteur contient DÉJÀ

Cette conception **n'invente presque rien**. Elle branche un état neuf sur six systèmes
existants. Vérifié par lecture du code le 2026-07-26 :

| Système existant | Ce qu'il fournit à la périphérie |
|---|---|
| `fields/light.py` — `LightField.compute(plants, saison, house=, tile_origin=)` | Le patron **« obstacle global en coordonnées MONDE »** : la maison y est un rectangle balayé + albédo de mur. Une lisière est un second obstacle du même type. **Aucun « masque d'horizon » à inventer.** |
| `fields/abri.py` — `compute_abri(...)`, `_obstacles()` | Un **champ d'abri spatial complet** : capsule de sillage, portée ∝ hauteur (`ABRI_PORTEE_HAUTEUR = 10×`), réduction (`ABRI_REDUCTION_MAX = 0.6`), venturi, cache angulaire. `_obstacles()` liste maison + plantes hautes → **la lisière y entre comme une ligne de plus**. |
| `fields/ecofields/{hydrologie,ruissellement,marais}.py` + gestes `creuser`/`drainer` | L'hydrologie est **implémentée**, pas seulement conçue : `altitude`, `eau_surface`, double-buffer, `marais_memory`, `est_marais()`, coûts et outil `("terrassement", "bêche")` déjà déclarés. |
| `fields/seedbank.py` — `tick_late_succession_enrichment(om_index)` | Le patron d'**apport exogène de propagules** par archétype. La pluie de graines de la friche s'y calque. |
| `sim/outils.py` (D82) + `sim/actions/deblocage.py` (`GESTE_UNLOCK`) | Un **registre d'outils data-driven** + une grammaire de déblocage `("action", marqueur)`. Gater `abattre` sur une hache = deux entrées de registre. |
| `fields/ecofields/matiere_organique.py` — `deposer_litiere` · `sim/actions/compost.py` — `empiler_bois` · `sim/actions/paillage.py` — `broyer` | Le **circuit du bois** : parcelle de litière typée `bois` au sol → pile à bois (`STRUCTURE_ACCEPTE["pile"] = {"bois"}`, le bac le refuse) ou broyage → BRF. Le bois coupé y rentre. |

Deux caches rendent l'ensemble gratuit en régime permanent : `geom_key` dans
`light.compute` (géométrie inchangée → `return []` immédiat) et `_signature` dans
`abri.compute_abri` (obstacles + direction discrétisée).

---

## 3. Le phénomène — ce qu'on modélise et pourquoi

### 3.1 L'exposition : ce que la géométrie donne gratuitement

À 49°N (Normandie), une lisière de 15 m de haut à 9 m du bord du jardin :

| Saison | Élévation solaire à midi | Longueur d'ombre | Pénétration dans le jardin |
|---|---|---|---|
| Hiver (décl. −23,4°) | 17,6° | 47,3 m | **tout le jardin** |
| Équinoxes (décl. 0°) | 41,0° | 17,3 m | 8,3 m |
| Été (décl. +23,4°) | 64,4° | 7,2 m | **aucune** (la bande fait 9 m) |

Une forêt **au sud** vole donc toute la lumière d'hiver et rien de l'été ; une forêt
**au nord** n'ombre jamais à midi mais abrite du vent de nord. Ce comportement sort
**intégralement de `solar_slice` + `_point_in_swept_rect` déjà en place** : il n'y a
rien à écrire pour l'obtenir. C'est la leçon d'exposition la plus classique du
jardinage, et elle devient jouable pour le prix d'un obstacle de plus.

### 3.2 L'abri : la porosité, et pourquoi la règle des manuels ne s'applique pas ici

L'agronomie enseigne qu'un brise-vent **poreux** (40-50 % d'ouverture) protège plus
loin qu'un mur plein : zone abritée jusqu'à 20-30 H contre 10-15 H. **À l'échelle de
ce jeu, cette règle ne se manifeste pas** : derrière une lisière de 15 m, un jardin de
20 m tient entre 0 et 1,3 H. À cette distance le mur plein est *le plus* protecteur,
et la parabole de portée ne discrimine rien. Il faut le dire, sinon on écrit une
formule qui a l'air savante et ne produit aucun effet observable.

Ce qui, en revanche, se manifeste parfaitement à 0-3 H, c'est la **turbulence de
décollement** : derrière un obstacle imperméable, le flux décroche et retombe en
rafales descendantes. C'est le fait de terrain que tout jardinier connaît — *le vent
tombe par-dessus le mur*. Une haie filtrante, elle, lisse le flux.

Le modèle retenu module donc **deux** grandeurs par la porosité φ, et le moteur porte
déjà les deux (`eco.vent` pour le vent moyen, `gust_peak`/`_wind_damage` pour la rafale) :

```
φ = 1 − densite_ligneuse            porosité du secteur ∈ [0,1]

reduction_lisiere = REDUCTION_LISIERE_MAX × (1 − φ)      REDUCTION_LISIERE_MAX = 0.75
turbulence_lisiere = TURBULENCE_MUR × (1 − φ)²           TURBULENCE_MUR = 0.45
```

La turbulence est **quadratique** : elle ne pénalise que le très dense. Conséquence de
design, et c'est le cœur pédagogique du sprint :

> Une lisière trop dense abrite du vent constant **mais fait tomber des rafales**.
> L'éclaircir un peu — un recépage — réduit la casse sans perdre l'abri.

C'est contre-intuitif, entièrement émergent, et personne ne le dit au joueur (#6). Ce
n'est pas « couper c'est mal » : c'est « couper *bien* est un savoir-faire ».

**Garde-fou golden.** La porosité ne s'applique **qu'aux obstacles de lisière**.
`_obstacles()` passe à des 5-uplets `(cx, cy, h, rayon, poro)` avec `poro=None` pour
la maison et les plantes → branche historique **bit-identique**. Donner leur vraie
porosité aux haies du jardin est un calibrage ultérieur → **dette D94**.

### 3.3 La sylviculture : trois gestes, trois cinétiques

Le vrai matériau pédagogique est l'**asymétrie de réversibilité**. Trois gestes que le
paysan distingue et que le jeu doit distinguer :

- **Abattre** — l'arbre meurt. Trouée franche, lumière au sol, structure perdue.
- **Recéper** — coupe au ras de la souche des essences qui *rejettent*. La souche,
  libérée de sa dominance apicale, émet des rejets vigoureux : **l'arbre ne meurt pas,
  il rajeunit**. C'est un flux de bois renouvelable, l'inverse d'une ressource qu'on
  épuise.
- **Étêter** (trogne) — on coupe la tête, le tronc reste. Le saule têtard normand.
  Le tronc vieillit, se creuse, et **devient un habitat**.

**Le fait discriminant**, et il tombe bien : toutes les essences ne rejettent pas.

| Essence (catalogue existant) | Rejette de souche ? | Rotation |
|---|---|---|
| **charme** | oui, vigoureusement | 10-12 ans |
| **aulne** | oui | 8-12 ans |
| **saule** *(ajouté, cf. §7)* | oui, très vite | 3-5 ans en trogne |
| **hêtre** | **non** (rejette très mal) | — |
| **bouleau** | **non** | — |

Le catalogue porte donc déjà les deux camps. Recéper une hêtraie, c'est l'abattre — et
le joueur ne l'apprend qu'en le faisant, ou en lisant l'encyclopédie une fois la
maîtrise acquise.

### 3.4 L'eau : le barrage est une condition aux limites, pas une rivière

**Correction d'une prémisse de l'amorce.** Il n'existe pas de grille hydraulique hors
jardin : `altitude` et `eau_surface` s'arrêtent au bord. « La même physique appliquée
hors terrain de jeu » n'a donc pas de support. Simuler un cours d'eau serait un second
système, pour un bénéfice nul.

Le barrage se traduit en **condition aux limites de la grille existante** : le secteur
`riviere` porte une `ligne_eau` qui, selon sa hauteur relative au bord du jardin,
**pousse** de l'eau dans les plots de la première rangée (nappe de berge) ou **en
retire**. Le ruissellement et `marais_memory` déjà en place font le reste — la zone
gorgée puis le marécage émergent, ils ne sont pas scriptés.

Endiguer relève la ligne d'eau (amont gorgé). Dériver l'abaisse (aval asséché). Le
joueur découvre qu'il a **déplacé** l'eau, pas créé.

---

## 4. Le modèle — la ceinture

### 4.1 État (décision D-1 : 4 secteurs cardinaux, vérité Python)

La ceinture vit dans `game_state["ceinture"]` — **4 secteurs**, un par bord cardinal,
bande de 900 cm (aligné sur `DecorLayer.DepthCm`). Ce n'est **pas** une liste de
`PlantInstance` : simuler une forêt comme N arbres réels ferait exploser `LightField`
(D32) pour rien.

```python
Secteur = {
    "cote":              0..3,          # 0=N, 1=E, 2=S, 3=O
    "type":              "foret" | "riviere" | "falaise" | "prairie" | "friche",
    "essence":           "hetre" | "charme" | "bouleau" | "aulne" | "saule" | None,
    "hauteur_canopee":   float,         # cm — pilote ombre ET portée d'abri
    "densite_ligneuse":  float,         # ∈ [0,1] — ce que la coupe abaisse
    "souche_memory":     "vivante" | "morte" | None,
    "annees_depuis_coupe": float,       # cinétique de repousse (déterministe)
    "ligne_eau":         float,         # cm relatif au bord — riviere seulement
    "altitude_relative": float,         # cm — falaise seulement
}
```

**Génération déterministe** (`fields/_hash_noise`, philo #3/#7), et c'est ici que
**D92 se referme par construction** : le tirage repart d'un hash correctement brassé
par côté, au lieu du `decor|{seed}|{cote}` du C# dont seuls les bits bas différaient.
Mesure du bug actuel, sur 300 000 seeds répliqués : **287 929 terrains (96,0 %) ont
les 4 côtés identiques, et 0 falaise n'a jamais été produite**. La nouvelle génération
doit garantir, sur le même échantillon, une distribution où la falaise existe
réellement (cible : ≥ 5 % des terrains en portent une) — c'est un test, pas un vœu.

**Essence dominante** (décision D-4) : un secteur `foret` tire une essence du catalogue
ligneux existant. Elle fixe le comportement au recépage (§3.3) et la densité d'ombre.
Un secteur `foret` adjacent à un secteur `riviere` devient **ripisylve** → essence
aulne ou saule. C'est exact écologiquement et ça donne de l'hétérogénéité (#7) gratuite.

### 4.2 Flux entrants — la périphérie agit

Quatre flux, tous greffés sur un système existant, **aucune règle nouvelle** :

| Flux | Greffe | Modèle |
|---|---|---|
| **Ombre de lisière** | `light.compute` — un obstacle de plus, à côté de la maison | Rectangle balayé en coordonnées monde, hauteur = `hauteur_canopee`, opacité ∝ `densite_ligneuse`. Le comportement saisonnier du §3.1 en découle. |
| **Abri & turbulence** | `abri._obstacles()` — une entrée de plus | §3.2. `reduction_lisiere` sur `eco.vent`, `turbulence_lisiere` sur la rafale locale. |
| **Pluie de graines** | `seedbank` — patron `tick_late_succession_enrichment` | Un secteur `foret`/`friche` sème dans les plots de bord, avec **décroissance de la distance au bord** ; archétype selon le type (friche → `pioneer`, forêt → `competitor`). Donne enfin un support mécanique au **canal d'acquisition #3**. |
| **Nappe de berge** | `hydrologie` — condition aux limites | §3.4. |

**Le corridor faune** mérite une note, parce que l'amorce y voit un piège #2 et qu'elle
a à moitié raison. Le champ de population **colonise déjà depuis zéro** partout où
ressource + habitat existent (`fields/population/field.py`) : il n'y a pas de barrière
de dispersion à lever. Ajouter « la périphérie augmente l'habitat » serait bien un
bonus déguisé.

La formulation juste : la lisière **est** un habitat — c'est de l'écologie, pas une
faveur. On l'exprime donc comme un **champ du milieu**, `eco.lisiere ∈ [0,1]` (gradient
décroissant depuis le bord, porté par le type de secteur), que les guildes lisent
**chacune à sa manière** via un poids `lisiere_w` déclaré par spec — **défaut 0.0**.
Le carabe et le hérisson y répondent, le puceron non. Le milieu porte l'information,
la réponse est biologique et différenciée (#2), et le défaut à 0 garde le golden intact.

### 4.3 Gestes sortants — le joueur agit

Event-driven, hors tick, patron `sim/actions/` + `cout_action` → **golden neutre**.
Nouveau module `sim/actions/paysage.py` (`gestes.py` est à 233 LDC, on ne le gonfle pas).

| Geste | Effet sur le secteur | Outil requis | Coût |
|---|---|---|---|
| `abattre` | `densite_ligneuse` ↓ franc, `souche_memory = "morte"` | hache | TRÈS ÉLEVÉ |
| `receper` | `densite_ligneuse` ↓, `souche_memory = "vivante"` **si l'essence rejette**, `"morte"` sinon | serpe | ÉLEVÉ |
| `eteter` | `hauteur_canopee` ↓, densité conservée, souche vivante, **habitat ↑** | serpe | ÉLEVÉ |
| `endiguer` / `deriver` | `ligne_eau` ↑ / ↓ | bêche | ÉLEVÉ |
| `entailler` | `altitude_relative` ↓, **irréversible**, érosion | pioche | TRÈS ÉLEVÉ |
| `creuser` (mare) | **geste EXISTANT** appliqué à un secteur | bêche *(déjà)* | ÉLEVÉ *(déjà)* |

Le gating par outil réutilise `sim/outils.py` + `GESTE_UNLOCK` (grammaire
`("action", "posseder_hache")`). Trois outils s'ajoutent au registre `OUTILS` :
**hache**, **serpe**, **pioche**. Aucun système à concevoir — **D93 tombe** pour ce
périmètre.

**Ne jamais bloquer le geste destructeur** (#6) : abattre toute la lisière sud doit
être possible. C'est le jardin qui répond, pas un avertissement.

### 4.4 Cinétiques — l'asymétrie de réversibilité

Repousse **déterministe** (cinétique + `annees_depuis_coupe`, jamais de tirage, #3) :

| Intervention | Retour à densité pleine | Leçon implicite |
|---|---|---|
| Étêtage (trogne) | **5 ans** | le prélèvement peut être un flux |
| Recépage (essence qui rejette) | **10 ans** | la souche a de la mémoire |
| Recépage (hêtre, bouleau) | *jamais* — devient un abattage | toutes les essences ne pardonnent pas |
| Abattage → pionnières | 4 ans | le vide se remplit vite… |
| Abattage → canopée fermée | **30 ans** | …mais la structure est lente |
| Entaille de falaise | **jamais** | certaines échelles ne nous appartiennent pas |
| Barrage non entretenu | se rompt vers **8 ans** | l'artefact demande un entretien perpétuel |

Calé sur le réel (noisetier 7-9 ans, charme 10-12, saule têtard 3-5, canopée tempérée
refermée en 25-40 ans) et sur le rythme du jeu (1 semaine = 60 s ⇒ 10 ans ≈ 8,7 h de
jeu en temps réel, mais le run est éternel : la trogne revient dans une partie, la
hêtraie non).

### 4.5 Érosion (Q11 — retenue, minimale)

C'est le retour le plus lisible d'une coupe excessive, et le seul qui rende
l'irréversible *visible*. Modèle minimal, greffé sur `structure_sol` (D30) : un secteur
à `densite_ligneuse` effondrée **ou** une falaise entaillée dépose des colluvions sur
les plots de bord — `structure_sol` dégradée, humus dilué. Pas de nouveau champ, pas de
nouvelle boucle. Émet un signe diégétique (#5).

---

## 5. « Comptabilisé » (décision D-3)

Quatre formes, dont trois retenues :

1. **Coût en Vigueur ÉLEVÉ** — justifié par l'**effort physique**, pas par « action
   directe sur le vivant ». L'arbre périphérique est un agrégat, pas une
   `PlantInstance` ; fonder un barème sur cette fiction se paierait plus tard.
2. **Trace au ledger** (`sim/journal.py`) → carnet, encyclopédie du geste (découverte
   à la 1ʳᵉ utilisation, D60), détection de maîtrise. Le geste est *enregistré*, jamais
   *scoré*.
3. **Trace dans le milieu** — `souche_memory`, clairière, cicatrice de falaise,
   éboulis. C'est un **état écologique persistant**, pas un compteur : la lecture la
   plus conforme à #4 et #5.
4. **Retour de matière** — le bois abattu **tombe en parcelles de litière `bois`** sur
   les plots du bord (`eco.deposer_litiere(r, c, "bois", masse)`). Le joueur va ensuite
   le chercher : `empiler_bois` vers une pile (qui devient habitat), ou `broyer` en BRF
   avec sa faim d'azote (D40). Gain écologique et différé.

   ⚠️ **Il n'existe pas de nature `"bois"` dans `mulch_stock`** (`NATURES_MULCH` =
   paille · brf · aiguilles · feuilles) — et il ne faut pas en créer une. Dans ce
   projet le bois est une **matière posée qu'on voit et qu'on déplace**, pas une jauge :
   créditer un stock directement court-circuiterait tout le circuit décompo/structures
   et remplacerait une matière visible par un compteur (#5).

**Aucun indicateur d'impact cumulé.** Pas de jauge « bois coupé », pas de compteur à
l'écran. La comptabilité vit au carnet (#5).

Note d'honnêteté : le garde-fou « surtout pas de stock » de l'amorce est déjà nuancé par
le projet — `mulch_stock` existe et est assumé (paille, BRF, aiguilles, feuilles). Mais
le **bois**, lui, n'y a jamais été une jauge : il vit en parcelles posées. Le sprint
suit cette distinction plutôt que de l'aplatir. Le vrai garde-fou n'est donc pas
« pas de stock », c'est **pas de chiffre en HUD** (#5) et **rien d'épuisable** (#4).
La friche se reconstitue ; le bois est un flux, pas un gisement.

---

## 6. Philosophie — passe #1 → #7

| # | Lecture | Verdict |
|---|---|---|
| #1 milieu > vivant | Barrage, mare, entaille = milieu pur. Abattre/recéper touche un **agrégat**, pas un être simulé — et reste coûteux. | ✅ |
| #2 flux, jamais de bonus | Tout passe en flux : lumière, vent, rafale, eau, graines. Le corridor faune passe par un **champ du milieu** (`eco.lisiere`) lu différemment par chaque guilde, jamais par un bonus d'habitat. | ✅ |
| #3 déterminisme | Gestes event-driven ; repousse par cinétique + `annees_depuis_coupe` ; génération par `_hash_noise`. Zéro RNG. | ✅ |
| #4 run éternel | La friche se reconstitue, rien de terminal, aucun stock épuisable. | ✅ |
| #5 indices visuels | On **voit** la clairière, l'ombre qui recule, la ligne d'eau qui monte, l'éboulis. Aucun compteur. | ✅ |
| #6 pas de tutoriel | La coupe excessive s'apprend par les rafales qui cassent et le sol qui part. Le geste destructeur n'est jamais bloqué. | ✅ |
| #7 hétérogénéité | 4 secteurs décorrélés + essence dominante + ripisylve ⇒ **D92 refermée**, chaque terrain a sa périphérie. | ✅ |

---

## 7. Voix narratives

**Une seule espèce ajoutée : le SAULE** (décision D-5, règle « le catalogue grandit
avec les idées » — signalée). Archétype de la **trogne** : le sprint invente `eteter`,
il lui faut son incarnation. Essence normande du bocage, et il **se bouture
spontanément** → croise l'événement rare « bouture » et le canal d'acquisition #2 déjà
en place. Il reçoit ses **5 voix** (règle « toute plante ajoutée = toutes ses voix »).
Noisetier et prunellier/ronce sont **écartés** — le charme et le bouleau les portent
côté agrégat → notés au BACKLOG.

À écrire :

- **Encyclopédie — technique `taillis`** : « couper pour que ça repousse plus fort. La
  souche a de la mémoire ; l'arbre étêté vit plus vieux que l'arbre libre. »
- **Encyclopédie — gestes** `abattre` · `receper` · `eteter` · `endiguer` · `entailler` :
  niveau 1 descriptif ; niveau 3, une fois la maîtrise acquise, la conséquence énoncée
  (vent, lumière, érosion). Registre `sim/geste_corpus.py`.
- **Encyclopédie — outils** hache · serpe · pioche (`sim/outil_corpus.py`).
- **Carnet** — concepts via `CONCEPT_DE` : `lisiere`, `brise_vent`, `erosion`,
  `rejet_de_souche`.
- **Pages secrètes** — gisement exceptionnellement riche : le bocage normand et le
  remembrement, l'essartage, la trogne (« l'arbre que l'on coupe pour qu'il dure »),
  le meunier et le droit d'eau, la chouette dans le saule creux.
- **Événements** — marqueurs au ledger : 1ʳᵉ clairière ouverte, 1ᵉʳ rejet de souche,
  rupture de barrage, 1ᵉʳ éboulis.
- **Quêtes (D79)** — « ouvrir une clairière », « rendre la mare aux libellules » sont
  des objectifs à condition d'état tout trouvés, sans code neuf.

---

## 8. Perf

| Poste | Coût | Justification |
|---|---|---|
| État ceinture | O(1) — 4 secteurs | négligeable |
| Gestes | 0 | event-driven, hors tick |
| Ombre de lisière | **≈ 0 en régime permanent** | entre dans `geom_key` de `light.compute` comme quelques scalaires ; la ceinture est statique → cache HIT → `return []` |
| Abri de lisière | **≈ 0 en régime permanent** | entre dans `_signature` d'`abri` ; recalcul seulement au franchissement d'un pas angulaire (déjà le cas aujourd'hui) |
| Pluie de graines | O(bord) ≈ 4 × 40 plots | une passe sur la première rangée, pas la grille |
| Champ `eco.lisiere` | O(bord), calculé **une fois** | statique tant que la ceinture ne change pas |

**Budget visé : < +2 % de tick**, très en-deçà du plafond projet (+10 %/tronçon). Le
point chaud redouté par l'amorce (masque d'horizon recalculé par plot et par bord à
chaque tick) **n'a pas lieu d'être** : les deux caches existants l'absorbent.

---

## 9. Golden

**INCHANGÉ sur tout le sprint.** `tests/test_golden.py build_world()` ne pose **aucune
maison** et ne posera aucune ceinture : le patron `house=None` → comportement
historique strictement inchangé s'applique tel quel (`ceinture=None` → aucun obstacle
de lisière, `eco.lisiere` nul, `lisiere_w=0.0` par défaut, porosité `None` → branche
historique bit-identique).

L'amorce annonçait un « re-figeage LARGE ». Il est **évitable**, donc évité : une
dérive dont on n'a pas besoin est une dérive qu'on ne saura pas expliquer dans six mois.
**Aucun tronçon de ce sprint n'est autorisé à re-figer le golden.** Si un tronçon fait
bouger le digest, c'est un bug — on annule, on ne fige pas.

---

## 10. Découpage — 7 tronçons

| # | Tronçon | Golden |
|---|---|---|
| ① | **Ceinture moteur + génération déterministe** (`fields/peripherie.py`) — état, `_hash_noise` par côté, essence dominante, ripisylve, **D92 refermée** (test de distribution sur 300 000 seeds) | INCHANGÉ |
| ② | **Exposition & abri** — lisière comme obstacle dans `light.compute` et `abri._obstacles()`, porosité (réduction + turbulence quadratique) | INCHANGÉ |
| ③ | **Pluie de graines, nappe de berge, corridor** — seedbank de bord, condition aux limites hydraulique, champ `eco.lisiere` + `lisiere_w` par spec | INCHANGÉ |
| ④ | **Gestes forestiers** (`sim/actions/paysage.py`) — `abattre`/`receper`/`eteter`, outils hache/serpe/pioche, cinétiques de repousse, retour de matière | INCHANGÉ |
| ⑤ | **Eau & roche** — `endiguer`/`deriver`/`entailler`, `creuser` étendu au secteur, érosion et colluvions | INCHANGÉ |
| ⑥ | **Voix narratives** — saule + ses 5 voix, gestes/techniques/outils à l'encyclopédie, concepts carnet, pages secrètes, événements au ledger | INCHANGÉ |
| ⑦ | **Vue Godot** — `DecorLayer` consomme le snapshot (cesse de générer), pont, gestes cliquables sur secteur, banc F5 | INCHANGÉ |

---

## 11. Dettes touchées

| Dette | Effet |
|---|---|
| **D73** | **levée** par ce sprint (c'en est la conception) |
| **D92** | **absorbée** au tronçon ① — la génération passe en Python, le hash mal brassé disparaît |
| **D93** | **périmée pour ce périmètre** — `sim/outils.py` (D82) existe ; hache/serpe/pioche s'ajoutent au registre. La récompense de quête « outil » redevient implémentable. |
| **D94** *(ouverte)* | Donner leur **vraie porosité** aux haies et plantes hautes du jardin (§3.2). Aujourd'hui `poro=None` → branche historique, pour garder le golden. Dérive assumée à faire un jour, avec re-figeage annoncé. |
| D15 · D29 · D30 · D32 · D37 · D40 · D42 · D58 · D60 · D79 | touchées en lecture, aucune n'est modifiée |
