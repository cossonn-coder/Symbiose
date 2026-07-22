# Amorce de conception — Jardinier automate (pilote de test)

**Date** : 2026-07-18
**Statut** : **AMORCE — non figée**, destinée au skill `/conception`
**Sujet** : un agent déterministe qui joue le jardin à notre place pendant les
phases de test accélérées (2,5 J/s), avec l'intention de faire pousser les
plantes et d'en récolter les fruits.

---

## 0. Origine & intention

Nico, après ses sessions F5 :

> « il faut faire un sprint de conception pour créer une IA qui joue au jeu et
> fait ce qu'il faut faire sur les plantes pendant la phase de test. Le jeu va à
> 2,5 J/S en phase de test et je n'ai pas le temps de faire les actions
> nécessaires. "L'IA" que l'on crée aura l'intention de faire pousser les plantes
> et d'en récolter les fruits en faisant de son mieux pour chaque plante. »

**Reformulation fidèle.** Le problème n'est pas écologique, il est
**instrumental** : à la vitesse de test, la simulation avance plus vite que la
main du testeur. Nico ne peut pas arroser, pailler, tuteurer, tailler et
récolter 50 à 600 plantes pendant qu'un an de jeu défile en ~2,5 minutes. Résultat :
**toutes ses observations sont faites sur un jardin de fait abandonné**. Il veut
une doublure qui tienne le jardin pendant qu'il regarde.

Trois choses sont explicites dans sa formulation et méritent d'être tenues :

1. **« pendant la phase de test »** — c'est un **instrument de développement**,
   pas une fonctionnalité de jeu, pas un PNJ. Voir §3 (friction philo #6) et §6-Q7.
2. **« l'intention de faire pousser les plantes et d'en récolter les fruits »** —
   l'objectif est **productif et par-plante**, pas écosystémique. L'automate n'a
   pas de doctrine permaculturelle ; il veut des plantes vivantes et des fruits.
3. **« en faisant de son mieux pour chaque plante »** — l'unité de décision est
   **la plante individuelle**, pas la parcelle. Ce qui pointe naturellement vers
   un solveur de **facteur limitant** (§1).

**Note de vocabulaire.** « IA » est trompeur ici : il n'y a ni apprentissage, ni
réseau, ni RNG (interdits par la philo #3). Proposition de nom de travail :
**jardinier automate** (ou *pilote de test*, *régisseur*). À trancher en aval —
mais le nom compte, il empêchera un futur contributeur de croire qu'on entraîne
un modèle.

**Réponses de Nico aux trois arbitrages d'amont (2026-07-18)** — intégrées
au doc et notées comme cadres, pas comme décisions figées :

- **Perception** : les **deux profils, commutables** (`omniscient` /
  `semiologique`).
- **Exécution** : **Python, headless + F5**.
- **Comptabilité** : **commutable par profil** (`bride` / `libre`).

---

## 1. Le phénomène

Ici, le « phénomène » visé n'est pas un fait biologique à modéliser mais un
**écart de régime** dans le banc d'essai. Il vaut quand même la peine d'être
posé, parce qu'il a une conséquence écologique réelle.

### 1.1 L'écart de vitesse

Rythme de design acté : **60 s / semaine simulée** ≈ **0,117 J/s**.
Rythme de test annoncé par Nico : **2,5 J/s**, soit environ **21×** le rythme de
design. À cette vitesse : 1 semaine ≈ 2,8 s, une saison ≈ 36 s, une année ≈ 2,4 min.

La fenêtre d'action humaine se referme : la maturité d'un fruit, la fenêtre de
palissage d'une vrille, le moment d'arroser avant flétrissure passent en une ou
deux secondes d'horloge. **Le geste juste devient physiquement inatteignable.**

### 1.2 La conséquence écologique : tous nos bancs mesurent un jardin abandonné

C'est le point le plus important de cette amorce, et il dépasse le confort de test.

Tous les calibrages récents ont été mesurés **sans aucun geste joueur** :

- **D69** (invasion d'adventices) : « dès la semaine 26 il ne reste que 8
  haricots, TOUT le reste = pionnières levées de la seedbank ». Constat exact —
  mais obtenu sur un jardin que **personne ne désherbe, ne paille et n'arrose**.
- **D71** (cap des colonies clonales), **D66/D67/D70** (perf, N plantes),
  **D74** (diversité fondatrice) : même régime.

Un jardin **tenu** est un objet écologique différent d'un jardin **délaissé** :
la couverture du sol, la banque de graines, la pression férale, la démographie
et donc **la charge CPU** n'y suivent pas les mêmes trajectoires. Nous n'avons
aujourd'hui **qu'un seul des deux régimes** dans nos mesures.

**Le jardinier automate est donc, au-delà du confort, le chaînon manquant du
banc d'essai** : il fournit le régime « jardin tenu » à comparer au régime
« jardin abandonné » existant.

### 1.3 L'ancrage biologique du comportement : la loi du minimum

« Faire de son mieux pour chaque plante » se traduit très proprement par la
**loi du minimum de Liebig** : la croissance d'une plante est bornée par la
ressource **la plus déficitaire**, pas par la somme des ressources. Arroser une
plante qui manque de lumière ne sert à rien ; l'ombre est son minimum.

Un bon jardinier fait exactement ça : il **identifie le facteur limitant** et
lève celui-là. C'est aussi ce qu'un automate sait bien faire, et c'est
philo-compatible (#2) : identifier un facteur limitant, c'est raisonner en
**flux et contraintes de champ**, pas en bonus.

*Nuance à ne pas perdre :* Liebig est une approximation. En réalité les
facteurs interagissent (une plante en déficit hydrique absorbe mal les
minéraux même si le sol en regorge). L'automate de première passe peut
ignorer ces interactions ; il n'a pas besoin d'être bon jardinier, il a besoin
d'être **reproductible** et **meilleur que rien**.

---

## 2. Traduction mécanique — 1re passe (hypothèses)

> Tout ce qui suit est **hypothèse**. Rien n'est arbitré.

### 2.1 Où ça vit — le point d'architecture critique

**Hypothèse H1.** L'automate est un **module Python au-dessus du moteur**, jamais
dedans. Règle de couches actuelle : `plants ← fields ← sim ← engine ← main`.
L'automate se place **au niveau `main` / `tools`**, il **importe** `sim.actions`
mais **rien ne l'importe**. Emplacement pressenti : `tools/jardinier_auto.py`,
ou un paquet `agent/` si le fichier dépasse la bande 🟢 ≤ 300 LDC (probable —
prévoir le découpage : perception / décision / exécution).

**Hypothèse H2 — l'invariant le plus important du sprint.** L'automate n'est
**jamais appelé depuis `tick_semaine`**. Il s'intercale **entre deux ticks**, du
côté appelant (boucle de `main.py`, boucle de `sim_server.py`, ou boucle de banc).

**Conséquence directe : le golden reste INTACT par construction.** Le moteur ne
change pas d'une ligne ; on ajoute un appelant. C'est le seul chemin qui évite
un re-figeage — à vérifier explicitement en aval, mais l'hypothèse est solide.

**Hypothèse H3.** Il tourne **headless** (bancs `diag_population`,
`profile_monde`, scénarios longue durée) **et** attaché à une session F5 (via la
boucle de `sim_server.py`). Corollaire élégant : **aucun changement du protocole
du pont**. Les gestes de l'automate passent par les mêmes fonctions
`sim/actions.py` que ceux du joueur ; la vue Godot voit simplement leurs effets
arriver dans le snapshot suivant. Un affichage « quels gestes viennent d'être
joués » serait un confort de vue, à traiter à part (§6-Q8).

### 2.2 La boucle de décision

**Hypothèse H4.** Cadence = **un passage par tick de semaine**, jamais par frame.
C'est la granularité du moteur et c'est ce qui rend l'automate reproductible
indépendamment du framerate. Cinq étapes :

1. **Percevoir** — construire une vue de l'état selon le profil de perception (§2.4).
2. **Diagnostiquer** — pour chaque plante *sous tutelle*, identifier son **facteur
   limitant** dominant.
3. **Proposer** — pour chaque facteur limitant, le **geste le moins cher** qui le
   relâche (table facteur → geste, §2.3).
4. **Prioriser** — trier les gestes candidats et couper au **budget de Vigueur**
   disponible (§2.5).
5. **Exécuter** — appeler `sim/actions.py` dans l'ordre trié.

**Hypothèse H5 — quelles plantes sont « sous tutelle ».** L'intention de Nico est
productive : par défaut, **les plantes cultivées** (semées par le joueur ou par
le scénario). Les férales/pionnières ne sont pas soignées — elles peuvent en
revanche être la **cible** d'un geste (désherbage, paillage anti-germination) si
elles sont le facteur limitant d'une cultivée. À confirmer : périmètre exact,
et sort des pérennes/arbres du décor.

### 2.3 Table facteur limitant → geste (esquisse, à durcir)

**Hypothèse H6.** Le cœur du système est une petite table, lisible et éditable,
qui est en réalité *la* pièce de conception à discuter. Esquisse indicative :

| Facteur limitant pressenti | Signal (source) | Geste candidat | Cible |
|---|---|---|---|
| Déficit hydrique | `humidite` du plot-foyer / flétrissure | `arroser`, puis **`pailler`** (durable) | milieu |
| Évaporation, sol nu | `couverture_sol` bas | `pailler` | milieu |
| Concurrence férale proche | densité de férales dans le rayon racinaire | `pailler` (préventif), désherbage (curatif, coûteux) | milieu / vivant |
| Lumière insuffisante | lumière reçue basse, voisin ombrageant | `tailler`/`couper` le voisin, palisser | milieu |
| Verse / absence de support (grimpante) | `mode_grimpe` sans support à portée | `poser_tuteur` / `poser_treillis`, `palisser` | milieu |
| Sol compacté / asphyxie | `structure_sol` bas | aération (grelinette) | milieu |
| Excès d'eau / engorgement | hydrologie de relief | `drainer` / `creuser` | milieu |
| Carence minérale | `fertilite`, `n/p/k` | apport organique / compost | milieu |
| Fruit mûr | stade de maturité de l'organe | **`recolter`** | vivant (prélèvement) |

⚠️ **Cette table est écrite de mémoire du contexte projet, pas depuis le code.**
Le premier travail de `/conception` doit être de **lire `sim/actions.py` et le
registre `GESTE_UNLOCK`** pour établir l'inventaire réel des gestes, leurs
signatures, leurs cibles et leurs coûts. Toute ligne ci-dessus qui ne
correspond pas à un geste existant est soit à retirer, soit à ouvrir comme
demande de geste neuf (probablement à retirer : ce sprint ne devrait pas
créer de gestes).

**Hypothèse H7 — biais permaculturel assumé.** À facteur limitant égal, préférer
le geste **durable sur le milieu** (paillage) au geste **répétitif** (arrosage).
Non par idéologie, mais parce que c'est ce qui économise la Vigueur sur la
durée — l'automate redécouvre le paillage par nécessité, ce qui est une jolie
validation de la boucle D69.

### 2.4 Les deux profils de perception

**Hypothèse H8.** Un commutateur, deux implémentations d'une même interface
« que sais-je de cette plante ? ».

- **`omniscient`** — lit directement `EcoFields`, `vitalite`, lumière reçue,
  densités de population. Fiable, sert de **référence haute** : ce que ferait un
  jardinier parfaitement informé.
- **`semiologique`** — ne lit que ce qu'un joueur voit à l'écran : signes
  diégétiques, notifications, `etat` discrétisé {sain/affaibli/malade/mort} de
  D75, marqueurs du carnet. Pas de valeur continue.

**L'intérêt de garder le second va au-delà du test.** L'écart de performance
entre les deux profils **mesure la qualité de la sémiologie du jeu** : si un
automate qui joue bien en `omniscient` échoue en `semiologique`, cela prouve que
**les indices visuels sont insuffisants pour qu'un joueur puisse agir** — un
défaut de design #5 rendu **chiffrable** pour la première fois. C'est un
sous-produit qui pourrait valoir plus que l'outil lui-même.

*Réserve honnête :* le profil `semiologique` est nettement plus coûteux à
écrire (il faut d'abord recenser les signes réellement émis) et il n'est pas
indispensable au besoin immédiat de Nico. Candidat naturel à un **tronçon
tardif et optionnel**, pas au tronçon ①.

### 2.5 Les deux profils de comptabilité

**Hypothèse H9.** Deuxième commutateur, orthogonal au premier.

- **`bride`** — l'automate paie la Vigueur (`cout_action`), est limité par
  `gestes_debloques[player]`, ses gestes alimentent carnet et maîtrise. Il joue
  **exactement dans les règles du joueur**.
- **`libre`** — Vigueur ignorée, tous gestes débloqués, écritures narratives
  désactivées. Isole le test écologique de l'économie.

Le mode `bride` produit une information de calibrage qu'on n'a jamais eue :
**l'économie de gestes tient-elle ?** Si un automate raisonnable est à sec de
Vigueur en semaine 12 sur 8 tuiles, c'est que le barème est trop dur (ou que le
monde est trop grand pour un joueur seul) — et il vaut mieux l'apprendre d'un
automate que d'un ami déçu.

Le mode `libre` sert quand on veut mesurer *l'écologie d'un jardin tenu*
sans que l'économie ne vienne brouiller le signal.

**Attention au couplage carnet/maîtrise en mode `bride`** — voir §6-Q4, c'est
le piège le plus sournois du lot.

### 2.6 Déterminisme — les pièges concrets

**Hypothèse H10.** L'automate doit être une **fonction pure de l'état du monde**
(+ seed). Trois pièges à verrouiller, chacun ayant déjà mordu des projets
comparables :

1. **Ordre d'itération.** Jamais itérer sur un `set`, ni se fier à l'ordre
   d'insertion d'un dict pour un tri. Tout tri final **doit** avoir une clé de
   départage stable et totale (identifiant de plante).
2. **Égalités de score.** Deux plantes au score identique doivent être départagées
   par une clé explicite, pas par l'ordre d'arrivée.
3. **Zéro RNG.** Aucun `random`. Si un tirage est un jour nécessaire, il passe
   par le hash de bruit déterministe existant — mais la première passe ne
   devrait avoir besoin d'aucun aléa.

Verrou de test proposé (à confirmer en aval) : rejouer deux fois la même
séquence automate → **même hash de fin** ; et un test qui prouve que
**l'automate désactivé laisse le golden bit-identique**.

### 2.7 Perf — chiffrage naïf

- Coût par tick ≈ **O(N plantes sous tutelle × k règles)**, k petit (~10).
  Lectures de champs **locales** (plot-foyer, rayon racinaire) — pas de balayage
  global, pas de O(N²) en vue.
- Ordre de grandeur pressenti : **négligeable devant le tick actuel**, qui est
  dominé par `LightField` (62 % avant D70, toujours le premier poste).
- **Le vrai risque perf est indirect** et mérite d'être signalé fort : un jardin
  bien tenu **porte plus de biomasse vivante** qu'un jardin délaissé. Plus de
  plantes hautes = plus d'émetteurs d'ombre au-dessus du seuil `SHADING_POWER_MIN`
  (D67) = **LightField plus cher**. L'automate risque donc de **rouvrir des
  postes de perf qu'on vient de fermer** (D66/D67/D70) — non par son propre coût,
  mais par le monde qu'il fabrique. À mesurer explicitement au banc, c'est
  peut-être le résultat le plus intéressant du sprint.

---

## 3. Respect de la philo (#1–#7)

| # | Principe | Lecture |
|---|---|---|
| **#1** | Agir sur le MILIEU | ✅ **et test du principe**. L'automate privilégie les gestes de milieu ; récolte et désherbage restent des actions sur le vivant, coûteuses. Si l'automate ne s'en sort qu'en tapant sur le vivant, c'est un **signal de calibrage** : les leviers de milieu sont trop faibles. |
| **#2** | Jamais bonus/malus direct | ✅ par construction — il ne peut **que** jouer des gestes existants. ⚠️ Vigilance : ne lui donner **aucune** API privilégiée « soigner cette plante ». S'il lui manque un moyen d'agir, la réponse est « le geste manque au joueur aussi », pas « ajoutons une porte de service ». |
| **#3** | Déterminisme | ⚠️ **point de vigilance n°1**. Voir §2.6. Verrous de test obligatoires. |
| **#4** | Run éternel | ✅ neutre. L'automate ne redémarre rien, il tient un jardin. Il devrait d'ailleurs bien servir aux tests de très longue durée. |
| **#5** | Pas de HUD chiffré | ⚠️ **friction réelle**. L'automate lit forcément des nombres. Défense : c'est un **instrument de dev**, du même statut que l'overlay debug F6 — hors du jeu perçu. Le profil `semiologique` est précisément ce qui **respecte** #5, et il en devient l'appareil de mesure (§2.4). |
| **#6** | Apprentissage diffus, pas de tutoriel | ⚠️ **friction sérieuse si l'outil devient diégétique**. Un automate visible qui joue à la place du joueur, c'est un tutoriel automatisé — exactement ce que la philo refuse. **Tant qu'il reste un outil de dev, aucun problème.** Voir §6-Q7. |
| **#7** | Hétérogénéité persistante | ✅ neutre, voire favorable : un automate identique lâché sur deux terrains différents (D74) produira deux jardins différents. Bon révélateur d'hétérogénéité. |

**Et « tout coexiste » ?** L'automate n'est pas un acteur de l'écosystème — c'est
un doigt, pas un être vivant. Il n'a ni Vigueur propre, ni présence, ni sprite,
ni entrée d'encyclopédie. **C'est délibéré** : lui donner une existence dans le
monde violerait « pas de PNJ ».

---

## 4. Interconnexions

- **`sim/actions.py`** — surface d'appel unique. Aucun geste neuf ne devrait être
  créé par ce sprint ; si le besoin apparaît, c'est un signal à remonter, pas à
  satisfaire sur place.
- **Vigueur (D11) / `cout_action`** — budget du mode `bride`.
- **Maîtrise (D12) / `gestes_debloques` / sprint palette de gestes (clos 2026-07-11)**
  — bridage des gestes disponibles ; question ouverte sur l'acquisition de maîtrise (§6-Q4).
- **Vitalité continue & constitution (D75, clos 2026-07-13)** — `vitalite ∈ [0,1]`
  et `etat` discrétisé sont **exactement** les entrées dont l'automate a besoin :
  `vitalite` pour le profil `omniscient`, `etat` pour le `semiologique`. Sprint
  très récent, arrivé au bon moment.
- **D69 (adventices & paillage)** — l'automate est le **contre-test** naturel de
  D69 : le levier paillage était censé rendre l'invasion « infléchissable par le
  joueur » ; personne ne l'a encore vérifié avec un joueur qui paille vraiment.
- **D66 / D67 / D70 / D71 (perf, démographie)** — rouverts en régime « jardin
  tenu » (§2.7). Recalibrages possibles à la clé.
- **D74 (diversité fondatrice)** — automate constant × terrains variés = mesure
  propre de l'hétérogénéité.
- **Bancs `tools/`** (`diag_population`, `profile_monde`, `diag_lod_ombre`,
  `compte_ldc`) — famille d'accueil de l'outil ; un banc « jardin tenu » viendrait
  s'y ranger.
- **Pont / `sim_server.py` (0.5.28)** — inchangé sous H3. À reconfirmer en aval.
- **Voix narratives** — aucune espèce ajoutée, donc **aucune voix à écrire**. En
  revanche le carnet est *touché* en mode `bride` (§6-Q4).

---

## 5. Voix narratives

**Sans objet pour ce sprint** — aucune espèce n'est ajoutée au catalogue, la
règle « toute plante ajoutée = toutes ses voix » ne s'applique pas.

Une seule remarque à ne pas perdre : en mode `bride`, l'automate **écrit dans le
carnet**. Le carnet est une voix à la **première personne** (« j'ai paillé le
pied de tomate ») — or ce n'est pas Nico qui a paillé. Soit on assume la fiction
(l'automate *est* la main du joueur, le « je » reste vrai), soit on désactive
l'écriture carnet même en mode `bride`. Voir §6-Q4.

---

## 6. Questions ouvertes pour `/conception`

**Q1 — Inventaire réel des gestes.** *Préalable à tout le reste.* Lire
`sim/actions.py` et `GESTE_UNLOCK` : quels gestes existent, quelles signatures,
quelles cibles, quels coûts, lesquels sont à deux temps (bouture, greffe) ?
La table §2.3 est une esquisse de mémoire et sera fausse par endroits.

**Q2 — La table facteur limitant → geste est *la* pièce de conception.**
Est-elle un dict Python en dur, un fichier de données éditable, une liste de
règles priorisées ? Un format éditable sans toucher au code aurait beaucoup de
valeur : Nico pourra tester des politiques de jardinage différentes sans sprint.

**Q3 — Périmètre de la tutelle.** Cultivées seulement ? Les pérennes du décor ?
Que fait l'automate face à une férale : rien, désherbage systématique, ou
seulement quand elle est le facteur limitant d'une cultivée ? Ce choix change
radicalement la trajectoire démographique mesurée — et donc la valeur de
comparaison avec D69.

**Q4 — Comptabilité narrative en mode `bride` (piège).** Si les gestes de
l'automate alimentent la **maîtrise**, un test long fait **monter les paliers
tout seul** : extension de terrain, magazine, carnet interprétatif se
déverrouillent sans que personne n'ait rien compris. On teste alors un état de
jeu qui n'a aucun sens. Trois pistes à arbitrer : (a) gestes comptés en Vigueur
mais **pas** en maîtrise ; (b) tout compté, assumé (on teste aussi la courbe de
progression) ; (c) troisième profil `bride_muet`. **Piste (a) semble la moins
mauvaise, mais c'est un arbitrage, pas une reco.**

**Q5 — Politique de récolte.** Récolter dès mûr (maximise le rendement,
maximise les gestes) ou laisser mûrir/tomber (nourrit la faune, alimente
`om_fresh`, ferme la boucle de décomposition) ? Ce n'est **pas neutre
écologiquement** : un jardinier qui récolte tout **exporte** de la matière
organique hors du système. Sur un run éternel, la différence pourrait être
mesurable — et c'est une leçon de permaculture que le jeu a peut-être envie
d'enseigner.

**Q6 — Découpage en tronçons.** Ampleur pressentie **moyenne**. Découpage
plausible, à confirmer : ① socle (boucle, tutelle, 2-3 gestes : arroser /
pailler / récolter, mode `omniscient` + `libre`, verrou de déterminisme) ;
② table de gestes complète + priorisation par budget ; ③ mode `bride`
(Vigueur, gestes débloqués, arbitrage Q4) ; ④ banc « jardin tenu » +
comparaison au régime abandonné (le livrable de mesure) ; ⑤ profil
`semiologique` — **optionnel, séparable, à faire seulement si ①–④ ont tenu**.
Le golden devrait être **INTACT partout** sous H2 : à vérifier au tronçon ①, et
si ce n'est pas le cas, c'est que l'architecture a dérapé dans le moteur.

**Q7 — L'outil peut-il devenir diégétique un jour ?** Tentation évidente :
recycler l'automate en « le jardin se tient tout seul » au palier
**transcendant** (la non-action existentielle). Ce serait cohérent
thématiquement — et frontalement en tension avec « pas de PNJ » et avec #6.
**À ne pas trancher maintenant, mais à ne pas fermer non plus** : il suffit de
garder l'automate **sans état narratif propre** pour que la porte reste
ouverte sans coût.

**Q8 — Retour visuel en F5.** Nico veut *voir* le jardin tenu. Faut-il un
retour visuel des gestes joués (surbrillance, ligne de log, marqueur au sol) ?
Confort de vue pur (golden neutre), potentiellement précieux pour le débogage —
mais c'est peut-être un tronçon à part plutôt qu'une ligne dans celui-ci.

**Q9 — Perf en régime tenu.** Mesurer explicitement : un jardin bien tenu
coûte-t-il plus cher qu'un jardin abandonné (§2.7) ? Si oui, D67
(`SHADING_POWER_MIN`) et D71 (cap clonal) méritent d'être **relus à cette
lumière** — ils ont été calibrés sur le mauvais régime.

**Q10 — Nommage.** « IA » est à éviter (ni apprentissage, ni RNG, ni modèle).
`jardinier_auto`, `regisseur`, `pilote_test` ? Le nom sera lu à froid par un
agent dans six mois.

---

## 7. Rattachement à l'existant

| Élément | Lien |
|---|---|
| **DETTE** | Aucune dette Dxx existante ne couvre ce sujet → **ouvrir une entrée neuve** (D76+ ?) : « jardinier automate / pilote de test ». Vérifier le dernier numéro libre dans `DETTE.md` avant d'écrire. |
| **D69** | Contre-test du levier paillage en présence d'un joueur actif. |
| **D66 / D67 / D70 / D71** | Perf & démographie à relire en régime « jardin tenu ». |
| **D74** | Automate constant × terrains hétérogènes. |
| **D75** | `vitalite` / `etat` = entrées de perception (les deux profils). |
| **D12 / D55 / palette de gestes (clos 2026-07-11)** | `gestes_debloques`, `GESTE_UNLOCK` = bridage du mode `bride`. |
| **D11** | Vigueur = budget du mode `bride`. |
| **BACKLOG** | Nouvelle ligne sprint. Ampleur **moyenne** (~5 tronçons, dont un optionnel). |
| **Sprint en cours** | Reste la tranche **⑦ packaging PyInstaller** du sprint Intégration Godot. À ordonnancer avec Nico — l'automate n'est pas bloquant, mais il éclairerait le packaging (un binaire figé se teste mieux avec un pilote). |
| **Garde-fou taille** | Prévoir le découpage dès le départ : perception / décision / exécution, ≤ 300 LDC par fichier. |
| **Préalable** | Git propre avant sprint (règle projet). |

---

*Fin de l'amorce. Non figée — à durcir, challenger et découper par `/conception`.*
