# CONCEPTION — Jardinier automate (pilote de test)

> **Statut** : FIGÉE le 2026-07-18 (`/conception`), prête pour `/sprint-auto`.
> **Amorce source** : `docs/meta/amorce/amorce_conception_automate.md`.
> **Dette** : D78 (ce sprint) ; D79 (système de quêtes complet, hors scope).

Un **agent déterministe** qui joue le jardin à la place du testeur pendant les
phases de test accélérées (2,5 J/s), avec l'intention de **faire pousser les
plantes et d'en récolter les fruits**, « de son mieux pour chaque plante ». Ce
n'est **pas une IA** (ni apprentissage, ni réseau, ni RNG — philo #3) et **pas
une fonctionnalité de jeu** (ni PNJ, ni tutoriel — philo #6) : c'est un
**instrument de développement**, du même statut que l'overlay debug F6.

---

## 0. Intention & vocabulaire

Le problème est **instrumental**, pas écologique : à 2,5 J/s (≈ 21× le rythme de
design de 60 s/semaine), une année de jeu défile en ~2,4 min. Le testeur ne peut
pas arroser, pailler, tailler et récolter 50 à 600 plantes à cette vitesse →
**toutes nos observations récentes (D69, D66/67/70/71, D74) mesurent un jardin de
fait ABANDONNÉ**. Le jardinier automate fournit le régime manquant : **le jardin
TENU**, à comparer au jardin délaissé.

**Nom** : `jardinier_automate` (« IA » proscrit — trompeur). Modules sous
`tools/jardinier_auto/`.

---

## 1. Ancrage comportemental — la loi du minimum de Liebig

« Faire de son mieux pour chaque plante » = **identifier le facteur limitant
dominant et lever CELUI-LÀ**. La croissance est bornée par la ressource la plus
déficitaire, pas par la somme : arroser une plante qui manque de lumière ne sert
à rien. C'est philo-compatible (#2) — raisonner en **flux et contraintes de
champ**, jamais en bonus. L'automate n'a pas besoin d'être un bon jardinier ; il
a besoin d'être **reproductible** et **meilleur que rien**. Il ignore les
interactions fines entre facteurs (approximation de Liebig assumée).

---

## 2. Architecture — les trois invariants

- **H1 — au-dessus du moteur.** Règle de couches : `plants ← fields ← sim ←
  engine ← main`. L'automate se place au niveau `main`/`tools` : il **importe**
  `sim.actions` mais **rien ne l'importe**. Paquet `tools/jardinier_auto/`
  (découpé perception / diagnostic / regles / execution / boucle / trace, ≤ 300
  LDC par fichier).
- **H2 — jamais dans `tick_semaine`. L'invariant central.** L'automate s'intercale
  **entre deux ticks**, côté APPELANT (boucle de `main.py`, de `sim_server`, ou
  d'un banc). **Conséquence : le golden reste INTACT par construction.** Le moteur
  ne change pas d'une ligne ; on ajoute un appelant. `tests/test_golden.py` (2
  tuiles × 4 ans, succession spontanée SANS joueur) ne l'invoque jamais → son hash
  ne peut pas bouger. Vérifié explicitement au tronçon ① (verrou « automate OFF →
  golden bit-identique »).
- **H3 — headless ET F5.** Il tourne dans les bancs (`tools/bancs/`) **et** attaché
  à une session F5 via la boucle de `sim_server`. Ses gestes passent par les mêmes
  fonctions `sim/actions.py` que ceux du joueur → la vue Godot voit simplement
  leurs effets arriver dans le snapshot suivant. **Aucun changement du protocole du
  pont** n'est requis pour le cœur (le tronçon ⑥ ajoute une commande de contrôle
  opt-in + une expo de la trace au snapshot).

### 2.1 Point d'ancrage dans le moteur (faits code, 2026-07-18)
- Boucle : `Engine.tick_semaine()` (`sim/engine/boucle.py:76`).
- Monde : `engine.tiles` = `game_state["tiles"]` (liste de `Tile`) ;
  `engine._eco(tile)` = `game_state["eco"][tile.tile_id]` (EcoFields par tuile) ;
  `tile.plants` = liste de `PlantInstance`. Joueur = `game_state["current_player"]`
  (`"joueur_1"`).

---

## 3. La boucle de décision — cinq étapes, un passage par tick de semaine

Cadence = **un passage par tick**, jamais par frame (granularité du moteur →
reproductible indépendamment du framerate).

1. **Percevoir** — construire une vue de l'état selon le profil de perception (§9).
2. **Diagnostiquer** — pour chaque plante *sous tutelle*, identifier son **facteur
   limitant** dominant (§5).
3. **Proposer** — pour chaque facteur limitant, le **geste le moins cher** qui le
   relâche (table §5). Si aucun geste applicable → **impasse** (§7).
4. **Prioriser** — trier les gestes candidats (biaisés par les objectifs actifs
   §8) et couper au **budget de Vigueur** disponible (mode `paie_vigueur`).
5. **Exécuter** — appeler `sim/actions.py` dans l'ordre trié ; consigner chaque
   geste et ses conséquences dans la **trace** (§6).

**Tutelle** (Q3, tranché) : par défaut **les plantes cultivées** (`cultive=True`,
semées joueur/scénario). Les pérennes/arbres du décor ne sont pas soignés. Les
férales ne sont **jamais soignées** mais peuvent être la **cible** d'un geste
(désherbage) selon le profil `desherbage` (§4).

---

## 4. Profil d'automate — dataclass configurable (remplace bride/libre figés)

Nico (2026-07-18) : **tout est commutable par profil**. Les anciens modes
`bride`/`libre` de l'amorce deviennent des **presets** de flags orthogonaux.

```python
@dataclass(frozen=True)
class ProfilAutomate:
    perception: str       = "omniscient"   # "omniscient" | "semiologique"
    paie_vigueur: bool    = False          # dépense cout_action / borne au solde
    credite_maitrise: bool = False         # les gestes alimentent la maîtrise
    desherbage: str       = "curatif"      # "curatif" | "aucun" | "systematique"
    part_recoltee: float  = 1.0            # ∈ [0,1] — slider (Q5)
    ecrit_carnet: bool    = False          # écritures narratives (carnet)
```

- **`desherbage`** (Q3) : `curatif` (défaut) = déraciner une férale UNIQUEMENT
  quand elle est le facteur limitant d'une cultivée ; `aucun` = jamais ;
  `systematique` = toute férale à portée d'une cultivée.
- **`part_recoltee`** (Q5) : récolte **dès mûr**, mais seule cette **fraction** des
  organes mûrs est prélevée (le reste tombe → nourrit la faune, alimente `om_fresh`,
  ferme la boucle décompo). Défaut 1.0 (récolte tout) ; slider pour tester
  l'appauvrissement du sol par export de MO sur run éternel.
- **Presets** : `LIBRE = ProfilAutomate(paie_vigueur=False, credite_maitrise=False,
  ecrit_carnet=False)` ; `BRIDE = ProfilAutomate(paie_vigueur=True,
  credite_maitrise=<Q4>, ecrit_carnet=True)`. Chaque axe reste réglable à la main.

**Q4 (maîtrise en mode payé)** — tranché : `credite_maitrise` est un **flag de
profil**, PAS un choix figé. La **trace** (§6) consigne quoi qu'il arrive les
conséquences (déverrouillages, paliers) : Nico veut « une trace des actions ET de
leurs conséquences ». Le flag décide seulement si ces conséquences **arrivent
vraiment** ou sont neutralisées.

---

## 5. Table facteur limitant → geste (RÉELLE, vérifiée au code)

Corrigée depuis l'esquisse de l'amorce §2.3 après lecture de `sim/actions/`. **Ce
sprint ne crée AUCUN geste.** Signatures et coûts réels :

| Facteur limitant | Signal (source) | Geste candidat | Cible | Coût |
|---|---|---|---|---|
| Déficit hydrique | `eco.humidite.at_plot(r,c)` bas / `etat`↓ | `arroser`, puis `pailler` (durable) | milieu | MODÉRÉ |
| Évaporation, sol nu | couverture/`paillage` bas | `pailler` ⚠ | milieu | MODÉRÉ |
| Concurrence férale proche | densité férale rayon racinaire | `deraciner` (curatif) selon `desherbage` | vivant | ÉLEVÉ |
| Lumière insuffisante | `eco.light_received(plant)` bas | `tailler` le voisin ombrageant | vivant | MODÉRÉ |
| Sol compacté | `eco.structure_sol` bas | `grelinette` (aère sans retourner) | milieu | MODÉRÉ |
| Organe mûr | `maturite(plant)` / fruits mûrs | `recolter` (× `part_recoltee`) | vivant | FAIBLE |

⚠ **`pailler` consomme un STOCK de mulch** (`mulch_stock`) et **refuse si le stock
est insuffisant — même en mode `libre`** (le stock n'est pas de la Vigueur). Il
faut donc **chaîner le ravitaillement** : `broyer` (bois → BRF) / `recolter_paille`
(plantes à paille) **avant** de pouvoir pailler. Ce chaînage vit au tronçon ②.

**Retirés de l'esquisse amorce** (n'existent pas / hors scope) : `drainer`/`creuser`
(excès d'eau — hydrologie conçue mais non implémentée) ; apport minéral via
`epandre` (exige une chaîne compost mûre poser_bac→composter→retourner→epandre,
tardif).

**Gating (mode payé)** : `pailler`/`broyer`/`tailler` sont GATED par la maîtrise
(`gestes_debloques`). En mode `paie_vigueur`/`bride`, l'automate ne peut pas les
jouer tant que le palier n'est pas acquis → soit maîtrise pré-accordée au scénario,
soit **impasse** consignée (§7). Le set BASE (toujours ouvert) = {planter, arroser,
recolter, manger, ecraser, becher, favoriser_auxiliaire, deraciner, grelinette}.

**Format de la table (Q2)** : liste **ORDONNÉE de règles priorisées** dans un
module Python dédié (`regles.py`), lisible et éditable à la main — PAS de fichier de
données externe (simplicité #2 : pas de config spéculative pour un outil de dev).
Une règle = `(prédicat de facteur limitant, geste, sélecteur de cible, priorité)`.

**Biais permaculturel (H7)** : à facteur limitant égal, préférer le geste
**durable sur le milieu** (paillage) au geste **répétitif** (arrosage) — non par
idéologie mais parce que ça économise la Vigueur sur la durée. L'automate
redécouvre le paillage par nécessité (jolie validation de la boucle D69).

---

## 6. Trace structurée — livrable central (exigence Nico)

Un **journal déterministe** par tick, réutilisé partout (banc, onglet objectifs,
vue F5). Chaque entrée :

```
{ semaine, tile_id, cible (id plante ou plot), facteur_limitant,
  geste, cout, resultat (ok/échec/tronqué), objectif_id? }
```

Plus les **conséquences** consignées au même journal : déverrouillages de gestes
(`evaluer_deblocages` renvoie les nouveaux verbes), franchissements de palier de
maîtrise, morts de plantes. Progressif : **minimal** en ① (geste/facteur/résultat),
**conséquences** en ③, **rapport agrégé** en ⑤, **visuel** en ⑥.

Vit dans `game_state` (opt-in, sous une clé dédiée `automate_journal`) ou dans
l'objet automate — **jamais lu par le tick** (golden intact). Sérialisable JSON.

---

## 7. Détecteur d'impasses — objectif important (exigence Nico)

Quand l'étape **Proposer** (§3.3) diagnostique un facteur limitant mais qu'**aucun
geste-réponse n'est APPLICABLE**, consigner une **impasse typée** = « trou de
gameplay » :

- **geste inexistant** — le facteur n'a aucune ligne dans la table (ex. excès
  d'eau : pas de `drainer`) ;
- **geste verrouillé** — la ligne existe mais le geste est GATED et non débloqué
  (mode payé) ;
- **ravitaillement manquant** — `pailler` sans stock de mulch et sans moyen de le
  produire ;
- **objectif inatteignable** — cible d'un objectif absente du monde et sans moyen
  de l'obtenir (§8).

L'automate devient ainsi un **instrument de découverte des problèmes insolubles
dans l'état actuel du jeu**. Les impasses sont agrégées en **rapport** au banc ⑤.

---

## 8. Objectifs donnés à l'automate — germe du système de quêtes

**Scope de ce sprint = cœur mécanique seulement** (le système de quêtes complet
part en D79).

- **Structure** : `Objectif(geste, quantite, cible)` où `cible` = clé d'espèce ou
  type de structure. Ex. `Objectif("recolter", 1, "tomate")`,
  `Objectif("recolter", 10, "pomme_de_terre")`.
- **Injection** : au **début** de la sim OU **à tout moment en phase de
  planification** (temps figé). Liste d'objectifs actifs dans `game_state`
  (opt-in).
- **Effet sur la boucle** : **biaise la priorisation** (§3.4) — les plantes/gestes
  qui servent un objectif actif passent devant ; **compte la progression**
  (incrément sur chaque geste-cible réussi). Objectif accompli quand `quantite`
  atteinte → consigné.
- **Onglet** : vue de la **trace (§6) filtrée sur l'objectif** + les **événements
  du monde** (lus dans le `log` du tick) pendant sa poursuite. Aucune machinerie
  neuve — c'est une projection du journal.
- **Couplage émergent** : un objectif dont la cible est absente et inatteignable →
  **impasse** (§7). Objectifs et détecteur d'impasses composent.

**Hors scope → D79** : sources diégétiques (courrier du voisin/oncle/enfant),
objectifs à **condition d'état** au-delà de geste+quantité (« kiwi de 5 m » =
hauteur, « parterre de trèfles fleuris » = floraison), panneau de quêtes Godot,
voix narratives. C'est l'habillage ludique du cœur mécanique.

---

## 9. Perception — deux profils commutables

Une interface « que sais-je de cette plante ? », deux implémentations :

- **`omniscient`** — lit directement `EcoFields`, `plant.vitalite` (continu, D75),
  `eco.light_received`, `qi_local`, densités de population. **Référence haute** :
  ce que ferait un jardinier parfaitement informé. Câblé dès ①.
- **`semiologique`** (tronçon ⑦, optionnel) — ne lit que ce qu'un joueur VOIT :
  signes diégétiques, `plant.etat` discrétisé {sain/affaibli/malade/mort},
  notifications, marqueurs du carnet. Pas de valeur continue. **L'écart de
  performance omniscient↔sémiologique MESURE la qualité de la sémiologie du jeu**
  (défaut de design #5 rendu chiffrable). Coûteux (recenser les signes émis) →
  tardif et séparable.

---

## 10. Déterminisme — verrous obligatoires (philo #3)

L'automate est une **fonction pure de l'état du monde** (+ seed global). Trois
pièges verrouillés :

1. **Ordre d'itération** — jamais itérer sur un `set` ni se fier à l'ordre
   d'insertion d'un dict pour un tri. Itération sur `engine.tiles` (liste) puis
   `tile.plants` (liste) = déterministe.
2. **Départage des scores** — tout tri final a une **clé de départage stable et
   totale**. Pas d'uid sur `PlantInstance` → clé = `(tile_id, plant.y_cm,
   plant.x_cm)` (positions continues, uniques).
3. **Zéro RNG** — aucun `random`. Si un tirage devenait nécessaire, il passerait
   par le hash de bruit déterministe existant (pas nécessaire en 1re passe).

**Verrous de test** (tronçon ①) : (a) rejeu de deux fois la même séquence automate
→ **même hash de fin** ; (b) **automate désactivé → golden bit-identique**.

---

## 11. Perf — chiffrage & le vrai risque

- Coût par tick ≈ **O(N plantes sous tutelle × k règles)**, k ~ 10. Lectures de
  champs **locales** (plot-foyer, rayon racinaire) — pas de balayage global, pas de
  O(N²). **Négligeable devant le tick** (dominé par `LightField`, 62 %).
- **Le vrai risque est INDIRECT** (Q9) : un jardin bien tenu **porte plus de
  biomasse** → plus d'émetteurs d'ombre au-dessus de `SHADING_POWER_MIN` (D67) →
  **`LightField` plus cher**. L'automate risque de **rouvrir des postes de perf
  qu'on vient de fermer** (D66/D67/D70) — non par son coût propre, mais par le
  monde qu'il fabrique. **À mesurer explicitement au banc ⑤** : peut-être le
  résultat le plus intéressant du sprint. Si avéré, D67 (`SHADING_POWER_MIN`) et
  D71 (cap clonal) sont à relire — ils ont été calibrés sur le mauvais régime.

---

## 12. Respect de la philo (#1–#7)

| # | Lecture |
|---|---|
| #1 | ✅ **et test du principe** : l'automate privilégie les gestes de milieu. S'il ne s'en sort qu'en tapant sur le vivant → signal de calibrage (leviers de milieu trop faibles). |
| #2 | ✅ par construction : il ne peut **que** jouer des gestes existants. **Vigilance** : aucune API privilégiée « soigner cette plante ». Geste manquant = « il manque au joueur aussi » (→ impasse §7), pas une porte de service. |
| #3 | ⚠ **point de vigilance n°1** — §10, verrous de test obligatoires. |
| #4 | ✅ neutre : il tient un jardin, ne redémarre rien. Utile aux tests longue durée. |
| #5 | ⚠ friction : il lit des nombres. Défense : instrument de dev (statut overlay F6, hors jeu perçu). Le profil `semiologique` **respecte** #5 et en devient l'appareil de mesure. |
| #6 | ⚠ friction sérieuse **si l'outil devient diégétique**. **Tant qu'il reste outil de dev, aucun problème.** Automate SANS état narratif propre → porte « transcendant » (non-action) ouverte à coût nul, sans la trancher (Q7). |
| #7 | ✅ favorable : automate identique × terrains hétérogènes (D74) = deux jardins différents, bon révélateur. |

**« Tout coexiste » ?** L'automate n'est pas un acteur de l'écosystème — c'est un
**doigt**, pas un être vivant. Ni Vigueur propre, ni présence, ni sprite, ni entrée
d'encyclopédie. Délibéré (respect de « pas de PNJ »).

---

## 13. Interconnexions

- **`sim/actions.py`** — surface d'appel unique. Aucun geste neuf.
- **Vigueur (D11) / `cout_action`** — budget du flag `paie_vigueur`.
- **Maîtrise (D12) / `gestes_debloques`** — bridage du mode payé + flag
  `credite_maitrise`.
- **Vitalité & constitution (D75)** — `vitalite` (omniscient) / `etat`
  (semiologique) = entrées de perception.
- **D69 (adventices & paillage)** — l'automate est le **contre-test** : personne
  n'a encore vérifié l'infléchissement de l'invasion avec un joueur qui paille.
- **D66/D67/D70/D71** — rouverts en régime « jardin tenu » (§11).
- **D74** — automate constant × terrains variés = mesure de l'hétérogénéité.
- **Bancs `tools/`** — famille d'accueil ; le banc « jardin tenu » (⑤) s'y range.
- **Voix narratives** — aucune espèce ajoutée → aucune voix à écrire. Le carnet
  est *touché* seulement si `ecrit_carnet=True`.

---

## 14. Découpage en tronçons (golden intact partout sous H2)

- **①** Socle : paquet `tools/jardinier_auto/`, boucle 5 étapes, `ProfilAutomate`
  (dataclass, tous les axes ; seuls `arroser`/`recolter` câblés), perception
  `omniscient`, tutelle = cultivées, journal minimal, **verrous déterminisme**.
- **②** Table `regles.py` complète + priorisation par budget + chaînage
  `broyer→pailler` + `tailler`/`deraciner` (désherbage) + slider `part_recoltee` +
  **détecteur d'impasses**.
- **③** Comptabilité commutable : flags `paie_vigueur`/`credite_maitrise`, respect
  de `gestes_debloques`, **trace des conséquences**.
- **④** Objectifs (cœur mécanique) : `Objectif(geste, quantite, cible)`, injection
  début/planification, biais de priorisation + comptage, **onglet** (trace scopée +
  événements monde) ; objectif inatteignable → impasse.
- **⑤** Banc « jardin tenu » : tenu vs abandonné (démographie, couverture,
  **perf LightField**) + **rapport d'impasses agrégé**. Livrable de mesure.
- **⑥** Vue Godot (RÈGLE PERMANENTE) : automate branché dans `sim_server` (option
  F5) + retour visuel des gestes + journal/impasses + onglet objectifs. Golden
  neutre.
- **⑦** *(optionnel, hors chaîne)* profil `semiologique` : mesure l'écart
  omniscient↔sémiologique. Seulement si ①-⑤ tiennent.

Ampleur **gros** (6 tronçons + 1 optionnel) — chaque tronçon est une unité
testable qui préserve le golden.

---

## 15. Ce que ce sprint ne fait PAS

- Ne crée **aucun geste** (si un besoin apparaît → impasse consignée, pas satisfaite).
- Ne modifie **aucune ligne du tick** (golden intact par construction, H2).
- Ne livre **pas** le système de quêtes complet (→ D79).
- N'entraîne **aucun modèle**, n'introduit **aucun RNG** (philo #3).
