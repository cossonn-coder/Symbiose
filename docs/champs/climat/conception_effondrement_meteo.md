# Conception — Effondrement du jardin par météo partagée (SYMBIOSE)

> **Document de conception. Aucun code écrit ici.** Spec de référence du sprint
> `sprints/champs/climat/sprint_effondrement_meteo/` (4 tronçons, `/sprint-auto`).
> Prolonge `conception_meteo.md` (signes §4, palier maîtrise §5, préparation §6).
>
> Origine : trouvaille du sprint MESURE `optim_vie_macro` (Dette C, 2026-08-02) —
> re-vérifiée au code. Décisions Nico du 2026-08-02 (Q1-Q3 + encart ciel).

---

## 0. Le constat, vérifié au code

La météo est **un tirage global fanné à l'identique aux 8 secteurs**.
`weather_state(seed, week)` est calculé **une seule fois par semaine**
(`sim/engine/boucle.py:95`), sans aucun paramètre de tuile, puis diffusé :
`eco.temperature.fill(temp_now)` (:117), gel (:130-146), grêle / `appliquer_alea`
/ orage (:148-167) dans la boucle `for tile in self.tiles`. `weather_at`
(`sim/weather.py:124`) produit un événement **global**, sans tuile.

Conséquence (mesurée sur 3 seeds, tuile isolée, sans jardinier) : une semaine à
malchance composée (gel tardif + double tempête + pluie prolongée) frappe les
8 secteurs *en même temps* → ce n'est pas « un coin qui flanche », c'est le
**jardin entier qui s'effondre le même hiver**, ~1-3 fois par partie, amplitude
jusqu'à 0,13 pl/plot depuis une médiane ~0,65. La fréquence par tuile isolée est
~1 chute ≥25 % / 7,9 ans ; la météo partagée les **corrèle** toutes.

---

## 1. Le pivot de conception : ce n'est pas « voulu ou subi »

« Voulu ou subi » est un **faux binaire**. On décompose :

- **L'effondrement en soi est VOULU.** La philo #4 (run éternel, le sol porte la
  mémoire, seedbank + succession repeuplent) et la philo du transcendant
  (« les perturbations entretiennent l'engagement à très long terme ») réclament
  des revers **récupérables**. Un jardin qui ne subit jamais de coup dur contredit
  l'intention de design. Ce qui est ouvert, c'est la **dose** et l'**exécution**.

- **Ce qui le rend SUBI = trois défauts séparables :**
  1. **Global / synchronisé** (8 secteurs, zéro survivant) → viole la philo #7
     (hétérogénéité persistante) et **tue la leçon centrale de permaculture** : le
     microclimat et l'abri. Dans un vrai jardin, le gel tue le fond de cuvette
     exposé et épargne le coin adossé au mur sud.
  2. **Invisible** — le préavis n'est pas ressenti pour le *composé* (les signes
     annoncent chaque événement isolément, jamais « l'hiver de tous les dangers »).
  3. **Non-atténuable** — l'appareil de préparation §6 n'est construit qu'à moitié
     (brise-vent, tuteur, paillage oui ; **voile / cloche / ombrière non**), et la
     mesure a été faite **sans jardinier** = plancher non préparé, pas le cas joué.

### 1.1 Le levier tentant qui est un piège
« Décorréler la météo par secteur (micro-climats d'ÉVÉNEMENT) » est **écarté** :
à l'échelle 20 m, la météo est une **masse d'air unique** (un gel dans le lit nord
et une canicule dans le lit sud la même semaine est absurde), et surtout cela
**casse le système de signes** (§4 de `conception_meteo.md` suppose UN ciel que le
joueur apprend à lire) et **dilue le palier de maîtrise climat**. On paierait cher
pour dégrader une mécanique déjà conçue et implémentée.

### 1.2 Le levier retenu (décision Nico Q1)
**Événement GLOBAL** (signes / forecast / palier maîtrise intacts), **IMPACT
spatialement hétérogène**. Un même hiver catastrophe produit « l'exposé flanche,
l'abrité tient et re-sème » — les tampons locaux qui *existent déjà* modulent
l'impact au plot : abri (ceinture D73, maison, brise-vent), paillage / litière,
neige (effet igloo), inertie, drainage / altitude (hydrologie), ombre (LightField).

### 1.3 Le plancher de survie ÉMERGE (décision Nico Q2)
Pas de constante gravée. Le plancher `f(abri, paillage, diversité)` émerge du
milieu : jardin bien conçu → survivants garantis (~0,45) ; jardin nu → chute
profonde (~0,13, récupérée par seedbank sur plusieurs saisons). La **diversité**
agit via la médiation gène × milieu × protection : dans un polyculture, les espèces
résistantes (rusticité au froid, susceptibilité fongique, hauteur) survivent au
composé qui tue les vulnérables → un noyau reste toujours. Les chiffres ci-dessus
sont des repères, pas des seuils codés.

---

## 2. Audit — l'impact est déjà majoritairement spatialisé

Le sprint **finit une spatialisation à moitié faite**, il n'ajoute pas de système.

| Canal catastrophe | Lecture actuelle | Statut |
|---|---|---|
| **Gel** | `t_min_nuit_at(eco,r,c,t_air,nébul)` — couvert litière/neige + nébulosité + wind chill local | ✅ déjà local |
| **Tempête / verse** | `_wind_damage` lit `eco.vent.at_plot` (sillage d'abri / venturi D73) | ✅ déjà local |
| **Fongique / pluie** | humidité locale + vent local + dispersion des spores sous le vent | ✅ déjà local |
| **Grêle / orage** | `event.scope="local"` **déclaré mais jamais lu** → fan-out aux 8 secteurs, uniforme intra-tuile | ❌ dormant |
| **Sécheresse / Pluie** | `eco.apply_weather(var, delta)` = **fill uniforme** de la tuile | ❌ uniforme |
| **Canicule (chaleur)** | `temperature.fill` uniforme ; impact via évaporation | ⚠️ à brancher sur l'ombre locale |

**Ce qu'il reste à faire** (tronçon ①) :
- Sécheresse / Pluie : moduler le delta `apply_weather` par le **drainage / altitude
  local** (`eco.altitude`, `eco.eau_surface`, `eco.drainage_last` existent, container
  hydrologie) — l'eau s'accumule dans les creux, s'écoule des hauteurs.
- Canicule : brancher l'impact hydrique sur l'**ombre / évaporation locale** (le
  LightField est déjà spatial) plutôt que sur une chaleur uniforme.
- **Honorer `event.scope="local"`** : grêle / orage frappent un **patch** (masque
  spatial déterministe via `_hash_noise`, canal sentinelle), plus les 8 secteurs.
- **Élargir la dispersion** des tampons (abri / paillage / inertie / neige) pour
  qu'un plot bien abrité franchisse le seuil de survie tandis qu'un plot nu chute.
- **Médiation complète** : résorber les voies `health` plates résiduelles
  (`appliquer_alea` mode `health`) → tout impact passe par milieu × gène × protection
  (philo #1/#2), condition pour que la diversité fasse plancher.

> **Note perf** : quasi-neutre. Les points de lecture locaux existent déjà ;
> honorer le scope *réduit* le travail (grêle sur patch au lieu de 8 tuiles) ;
> aucun nouveau balayage O(N²). Budget très en deçà de +10 %/tronçon.

---

## 3. Lisibilité — préavis dramatique du composé (tronçon ②)

Aujourd'hui `weather_signs(seed, week, horizon)` annonce chaque événement à venir
isolément (le `forecast` est déjà **pur et déterministe** — « le cadeau de la
fonction pure », §3 de `conception_meteo.md`). Un effondrement est un **composé** :
plusieurs événements haute intensité rapprochés. On ajoute :

- **Détection de convergence** : évaluer `forecast` sur un horizon court, détecter
  une grappe d'événements à forte intensité dans une fenêtre resserrée → un **niveau
  de convergence** (donnée dérivée, read-only, zéro RNG, déterministe). Ce n'est
  **pas un nouvel événement**, c'est une *lecture* de la fonction météo existante.
- **Signe diégétique intensifié** — « l'hiver de tous les dangers » : oiseaux
  affolés, ciel plombé, un poids dans l'air. Donnée (voix naturaliste), pas de HUD
  ni de chiffre (philo #5). Rattaché au palier maîtrise climat : l'expertise / le
  transcendant révèlent la convergence (l'événement ne change pas, seule sa lecture).
- **Helper `ciel_semaine`** (équivalent Python de l'encart Godot du tronçon ④,
  CLAUDE.md « toute mécanique Godot a son équivalent Python ») : agrège les signes
  lisibles 1-2 semaines en avant + le niveau de convergence en une structure prête
  à sérialiser. Read-only, ne touche aucun champ.

---

## 4. Couvertures — finir l'appareil de préparation §6 (tronçon ③)

Trois gestes posables manquants, **modelés sur `poser_bac` / `poser_pile` /
`poser_pot`** (`sim/actions/`), chacun un **modificateur de milieu local** (philo
#1 : pose en planification = Vigueur modérée, vs réaction dans l'urgence = chère) :

| Geste | Agit sur le milieu | Atténue |
|---|---|---|
| **Voile d'hivernage** | relève le `couvert` local lu par `t_min_nuit_at` + écran physique | gel + grêle sur une zone |
| **Cloche** | protection par-plante (petite empreinte) : couvert + écran | gel + grêle d'un individu |
| **Ombrière** | réduit la lumière / chaleur locale (couplage LightField) | canicule / sécheresse sur une zone |

Déblocage par maîtrise (`sim/actions/deblocage.py`, comme `poser_tuteur`). **Voix
des gestes** : entrées carnet + encyclopédie du geste (`sim/geste_corpus.py`,
`sim/outil_corpus.py`), voix naturaliste. (Règle « toute plante = 5 voix » ne
s'applique pas : ce sont des gestes/structures, pas des espèces.)

---

## 5. Vue Godot — encart « état du ciel » (tronçon ④, demande Nico)

> **Exigence Nico (2026-08-02)** : un petit encart qui affiche l'état du ciel et
> permet d'anticiper la météo de la semaine suivante.

**Contrainte philo #5 / §4 — l'encart est DIÉGÉTIQUE, pas un widget de prévision
chiffrée.** Ce n'est pas « Semaine +1 : 🌧 70 % ». C'est une **fenêtre rapprochée
sur le ciel** : sa couleur, ses nuages, le halo lunaire, la brume, la lumière. Le
joueur **lit le ciel** comme un vrai jardinier, au lieu de scruter tout le jardin
pour repérer les signes épars. L'encart **condense** les signes de `ciel_semaine`
et **s'assombrit visiblement à l'approche du composé catastrophe** (convergence de
②) — c'est le préavis dramatique rendu perceptible *avant* que le jardin soit frappé.

- **Masque de maîtrise intact** (§4.2) : l'encart montre **toujours** le ciel
  (signal parfait) ; ce qui dépend du palier, c'est si le carnet **nomme** ce qu'il
  annonce (« ciel blanc laiteux → canicule probable » à la maîtrise ; brut avant).
- **Pont** : `tools/simserver/serialize.py` exporte `ciel_semaine` ; Godot affiche,
  ne calcule rien.
- **Rendu des couvertures** (placeholders voile / cloche / ombrière).
- **Banc d'observation F5** : scénario du collapse connu (seed 12345, an 26) — on
  voit l'encart **virer au plomb**, puis la zone abritée **survivre** pendant que
  l'exposée meurt. Preuve visuelle de l'hétérogénéité + du préavis.

---

## 6. Découpage en tronçons (perf-first, finit par la vue)

| # | Tronçon | Golden |
|---|---|---|
| **①** | Impact hétérogène (spatialiser canaux uniformes + honorer scope local + élargir dispersion + médiation complète → plancher ∝ abri) | **RE-FIGÉ** une fois, localisé + annoncé (impacts météo spatialisés) |
| **②** | Préavis dramatique du composé + helper `ciel_semaine` (convergence read-only sur forecast pur) | **INTACT** |
| **③** | Couvertures posables (voile / cloche / ombrière + déblocage + voix) | **NEUTRE** (rien posé dans le golden) |
| **④** | Vue Godot : encart « état du ciel » + pont `ciel_semaine` + rendu couvertures + banc F5 | **INTACT** |

**Re-figeage golden** : une seule fois, au tronçon ①. Le kickoff de ① séquence les
canaux un par un et ne re-fige qu'en fin, pour qu'un golden qui casse reste
localisable. Les tronçons ②③④ préservent le golden.

---

## 7. Garde-fous transversaux

- **Déterminisme (philo #3)** : aucune spatialisation ne doit introduire de RNG
  vivant. Le patch de grêle et toute variation spatiale passent par `_hash_noise`
  (canal sentinelle réservé, comme la météo). La convergence est une lecture pure
  du `forecast`.
- **Flux → contrainte → réponse (philo #1/#2)** : aucun bonus/malus direct sur la
  plante ; tout impact reste médié par le milieu, le gène et la protection. Les
  couvertures agissent par le milieu, jamais en multiplicateur sur la plante.
- **Signes, pas HUD (philo #5)** : le préavis et l'encart sont diégétiques ; aucun
  chiffre ni barre en HUD primaire.
- **Récupérable (philo #4)** : l'effondrement ne termine rien ; seedbank + succession
  repeuplent. Aucun game over, aucun bouton recommencer.
- **Hétérogénéité (philo #7)** : c'est l'objectif même du sprint — deux zones du
  même jardin ne réagissent plus identiquement au même hiver.
