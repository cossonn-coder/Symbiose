# CONCEPTION — gestes `planter` & `arroser` (+ modèle « eau » : drainage du sol & asphyxie)

> **Statut : conception FIGÉE (2026-06-13, Q1–Q12 tranchées par Nico).** Prête
> pour l'implémentation. Fait suite au kickoff
> `sprints/sprint_planter_arroser_conception.md` (cadrage §0 du 2026-06-12,
> Q12 tranchée le 2026-06-13). Les `planter`/`arroser` sont les **derniers
> gestes de base** absents du moteur (page d'accueil CLAUDE.md : cliquer ·
> **planter** · observer · méditer · manger). Tous deux relèvent du **canal
> vertueux** (philo #1 : le joueur agit principalement sur le MILIEU).
>
> **Re-figeage golden ANNONCÉ** : le modèle « eau » (drainage par `soil_type`
> + asphyxie) vit DANS le tick → re-figeage **maîtrisé et localisé** du golden
> (cf. §5). Les deux gestes, eux, restent event-driven (golden intact).

## 1. L'intention (source de vérité du « quoi »)

`docs/joueur/vigueur/conception_vigueur.md` §3.2 (« Actions sur le milieu — le canal vertueux ») :

| Action | Phase | Champ / effet | Coût | Réponse émergente |
|---|---|---|---|---|
| **Semer / planter** | planif. | introduit une graine (banque-joueur) à `x_cm,y_cm` | `FAIBLE` | germination → succession ordinaire |
| **Arroser** | saison | `humidite` locale ↑ | `MODÉRÉ × URGENCE` | sort de la stagnation sécheresse (`ok_hum`) |

§3.1 ajoute : « arroser en **prévention** ≠ arroser en **catastrophe** » — une
même action vit dans les **deux phases** à des coûts différents. **Principe non
négociable (philo #2)** : l'action ne touche **jamais** la plante directement,
elle modifie un **champ** ; la plante répond par **émergence** au tick suivant.

Le cadrage §0 du kickoff a **élargi le scope** : `planter` devient une
**germination différée** (dépôt d'une graine, pas un semis garanti), et le
sur-arrosage devient une **vraie fausse bonne idée** (asphyxie), le drainage
étant une **propriété du sol** et non un geste.

## 2. Modèle proposé (mappé sur le code vérifié, 2026-06-12/13)

### 2.1 `planter` — dépôt d'une **graine en attente**, germination différée (Q1, A, B)

Planter **ne spawn pas** un semis. Il **dépose une graine** qui germera via la
**succession ordinaire** quand la niche le permettra (`niche_index` :
lumière / densité racinaire / perturbation / sol). On enseigne ainsi le **bon
moment** (méthode scientifique : planter hors saison → ça ne lève pas → hypothèse).

**Pourquoi PAS la banque-sol agrégée** (`fields/seedbank.py:SeedBank`, génétique
moyenne/variance par espèce×plot) : elle **diluerait** les gènes de la graine
sélectionnée. Or semer une **belle graine récoltée** doit avoir un sens
(sélection D17/D22). On introduit donc une **structure neuve, distincte** :

```python
# fields/seedbank.py — à côté de SeedBank (banque-sol agrégée)
@dataclass
class GrainEnAttente:
    species: str
    genes:   dict          # gènes PROPRES (non moyennés) — viennent de la Seed jouée
    cultive: bool = True   # tag « replanté » (B) → transmis à la plante à la germination
    semaine_depot: int = 0
```

Stockée **par plot** (liste `grains_en_attente[(r, c)]`), elle germe **telle
quelle** : à chaque tick de succession, si le plot est **libre** (`occupied_roots`)
**et** la niche favorable, la graine en attente lève en `PlantInstance` semis
avec **ses** gènes (pas un échantillon de la banque-sol) + son tag `cultive`.

- **Source = banque-joueur uniquement** (Q2). `sim/seeds.py:PlayerSeedBank.take(species)`
  (FIFO) rend une `Seed{species, genes}` ; **refus si lot vide**. Le pont
  `planter` ↔ récolte est déjà câblé (une plante mûre récoltée dépose une `Seed`).
- **Cible = plot cliqué** (Q3) → plot-foyer, `x_cm/y_cm` déduits (comme les autres gestes).
- **Empilement autorisé** (Q4) : on ne refuse jamais un plot occupé. La
  succession ne germant que sur plot **libre**, une graine déposée sur un plot
  occupé **patiente** (germe quand le plot se libère). La **compétition
  intra-plot** (sprint suivant) gérera la cohabitation/éclaircissage.
- **Tag « replanté » différé** (Q5, B) : posé **à la création du dépôt**, **se
  transmet à la plante** quand elle germe → `maitrise_detection.py:163`
  (`marquer_replante`, hook déjà présent) distingue **cultivé** vs **féral** (§9.4).
- **Plein air uniquement v1** (Q6). Semis intérieur (maison) + bouture/division
  (Q7) = sprints futurs, hors scope.
- **Coût `FAIBLE`, phase planification** (Q7).

> Réutilise `succession.py` (zéro chemin de germination neuf) et n'appelle pas
> `world/tile.py:add_plant` directement : le geste **dépose**, la succession **lève**.

### 2.2 `arroser` — écriture sur le champ `humidite` (Q8, Q9, Q10, Q12)

Canon philo #2 : `arroser` **écrit le champ `eco.humidite`** au plot cliqué,
**rien d'autre**. La plante **répond au tick** (sa stagnation « sec » se lève si
l'eau remonte ; l'excès → asphyxie, §2.3). C'est **Q12 → option (a)** : effet
**visible sur la plante mais médié par le champ** — la plante « se débrouille »
avec l'humidité du sol, on n'écrit **jamais** un attribut de la plante.

- **Cible = plot cliqué** + **diffusion naturelle** (`HUMIDITY_INERTIA = 0.55`,
  déjà au tick) = l'arrosoir mouille un peu autour (Q8).
- **Dose cumulative, plafonnée à [0, 3]** (Q9) : chaque geste fait
  `hum += DOSE_ARROSAGE` (cap 3.0). **Transitoire par construction** :
  `tick_hydrology` (évaporation × drainage) **fait redescendre** l'apport →
  ré-arroser **coûte** = l'usure de la solution facile (philo #1).
- **Deux phases** (Q10) : **planification** (prévention, coût simple) **ET**
  **saison** (réaction, `× URGENCE_MULT = 1.5` déjà codé). Coût **MODÉRÉ**.
- **Cumul → asphyxie** : empiler les doses peut faire franchir le seuil d'excès
  (§2.3). Arroser n'est donc bénéfique **que dosé** — fausse bonne idée si abusé.

### 2.3 Modèle « eau » au TICK — drainage par `soil_type` + asphyxie par paliers (Q11)

Deux mécaniques de **tick** (≠ gestes), à isoler du reste car elles **re-figent
le golden** (§5).

**(a) Drainage = propriété du SOL** (Q8, Q11). Aujourd'hui
`fields/ecofields.py:tick_hydrology` applique `h *= DRAINAGE` avec
**`DRAINAGE = 0.993` constant**. On le rend **fonction de `soil_type`**
(`world/tile.py:65` : `"terre" / "argile" / "sable" / "roche"`) :

```python
DRAINAGE_PAR_SOL = {
    "terre":  0.993,   # référence — VALEUR ACTUELLE inchangée (cf. §5)
    "argile": 0.997,   # retient → s'engorge, asphyxie facile
    "sable":  0.985,   # draine vite → sèche vite, asphyxie rare
    "roche":  0.975,   # ruisselle → très drainant
}
```

`DRAINAGE` plus proche de 1 = **moins** d'eau évacuée par tick = sol qui
**retient**. Le **remède du joueur au sur-arrosage = connaître son sol**
(argile → arroser peu ; sable → arroser plus souvent), **pas un bouton**
`drainer` (Q8 : `drainer` n'est PAS un geste).

**(b) Asphyxie par paliers** (Q11, C.iii) — symétrique de la gradation
sécheresse existante. Aujourd'hui seul le **manque** d'eau pénalise
(`engine.py:195` `ok_hum = hum >= 0.15/tolerance_secheresse` → stagnation
« sec » ; `engine.py:302` `drought_stress` → `drought_memory` → santé). On
ajoute le **versant haut**, en **deux paliers** :

1. **Palier 1 — uptake (doux, réversible).** Au-dessus de `HUM_EXCES`, les
   racines **boivent mal** (sol gorgé, anoxie) → l'uptake baisse ∝ l'excès →
   **croissance ralentie**. Nouvelle stagnation **« noyé »** quand
   `hum > HUM_NOYE` (miroir du « sec ») : `ok_hum` devient faux aussi **par le
   haut**.
2. **Palier 2 — santé (si ça dure).** Une **mémoire d'asphyxie**
   (`asphyxie_memory`, intégration lente comme `drought_memory`, lerp 0.05)
   monte tant que `hum > HUM_EXCES`. Au-delà d'une durée, elle **fait chuter la
   santé** (`health ↓`) — exactement symétrique du stress sécheresse.

> **Émergent, pas écrit à la main** (philo #2) : on ne touche que le **champ**
> (l'arrosage) et la **lecture du champ au tick** (uptake/santé). La plante
> « se noie » comme elle « a soif » — même médiation. Cohérent avec Q12 (a).

## 3. Décisions FIGÉES (Nico, 2026-06-12 / Q12 le 2026-06-13)

- **Q1 → GERMINATION DIFFÉRÉE.** `planter` dépose une graine ; la **succession
  ordinaire** la lève au bon moment. Réutilise `succession.py`.
- **Q2 → SOURCE = banque-joueur uniquement.** `PlayerSeedBank.take(species)`,
  gènes inclus, **refus si lot vide**. Pas de « graine générique du catalogue ».
- **Q3 → CIBLE = plot cliqué.** `x_cm/y_cm` déduits du plot-foyer.
- **Q4 → EMPILEMENT AUTORISÉ.** Jamais de refus sur plot occupé ; la graine
  **patiente** (germe sur plot libre). Compétition intra-plot = sprint suivant.
- **Q5 → TAG « replanté » à la création du dépôt**, transmis à la plante à la
  germination (`marquer_replante`, détection §9.4).
- **Q6 → PLEIN AIR uniquement v1.** Semis intérieur = sprint futur.
- **Q7 → COÛT `FAIBLE`, phase planification.** Bouture/division = sprint dédié.
- **A → GRAINE EN ATTENTE (ii).** Dépôt **distinct identifié**, gènes **propres**
  (non moyennés) — préserve la sélection D17/D22. Nouvelle `GrainEnAttente`.
- **B → TAG « replanté » EN DIFFÉRÉ → OUI.** Posé sur le dépôt, transmis à la plante.
- **Q8 → CIBLE arroser = plot cliqué + diffusion.** `drainer` **n'est PAS un
  geste** : le drainage dépend du `soil_type` (modèle eau, tick).
- **Q9 → DOSE cumulative, plafonnée [0, 3].** Apport fixe calé sur la pluie d'aléa.
- **Q10 → DEUX phases.** Planification (prévention) **et** saison (`× URGENCE`).
  Coût **MODÉRÉ**.
- **Q11 → ON PUNIT L'EXCÈS, PAR PALIERS.** Sur-arrosage → **asphyxie** : uptake
  d'abord (doux, réversible), santé si ça dure (C.iii). Stagnation **« noyé »**.
  Drainage = **propriété du sol** (`soil_type`), pas un geste.
- **C (asphyxie) → PAR PALIERS (iii).** Uptake puis santé. Calibrage en §4.
- **Q12 → option (a) : l'eau écrit le CHAMP, la plante répond au tick.**
  « On arrose le champ et la plante se débrouille avec » (Nico, 2026-06-13).
  Effet **visible sur la plante mais médié par le champ** → **philo #2 préservée**
  (pas d'écriture directe sur la plante, geste hors-tick). L'asphyxie agit déjà
  « sur la plante » via le champ lu au tick → (a) donne « c'est sur la plante »
  SANS casser philo #2.

## 4. Calibrage chiffré PROPOSÉ (à valider — valeurs de départ)

Comme les `K`/`BASE` de la maîtrise : **valeurs de départ**, affinées post-test.

| Constante | Valeur proposée | Justification (ancrage) |
|---|---|---|
| `DOSE_ARROSAGE` | **+0.5** / geste | calé sur l'aléa « Pluies » (`+0.5`), cap 3.0 |
| `HUM_EXCES` (seuil palier 1, uptake↓) | **2.3** sur [0,3] | au-dessus du régime sain ; demande un vrai sur-arrosage (≥ 2 doses cumulées) ou une argile gorgée |
| `HUM_NOYE` (seuil stagnation « noyé ») | **2.6** sur [0,3] | miroir haut du seuil « sec » (`0.15/tol`) |
| `asphyxie_memory` lerp | **0.05** | identique à `drought_memory` (`engine.py:303`) — symétrie |
| Durée avant bascule uptake→santé | **~3–4 semaines** au-dessus de `HUM_EXCES` | « si ça dure » (C.iii) ; émerge de la mémoire qui monte |
| `DRAINAGE_PAR_SOL` | terre 0.993 / argile 0.997 / sable 0.985 / roche 0.975 | **terre = valeur actuelle** (cf. §5) ; ordre rétention argile>terre>sable>roche |

**Modulation par espèce (proposée, à trancher au calibrage).** La sécheresse est
déjà modulée par le gène `tolerance_secheresse` (`engine.py:195`). Symétrie
naturelle : un gène/trait **`tolerance_exces_eau`** (défaut 1.0) relèverait
`HUM_EXCES` pour les plantes de milieu humide (vs basse pour les plantes de sol
sec). **Reco : commencer SANS** (un seuil global), ajouter le trait seulement si
le test montre que toutes les espèces « se noient » pareil — *simplicité d'abord*.

## 5. Garanties (par construction)

- **Les 2 GESTES sont event-driven → golden INTACT.** `planter` (dépôt) et
  `arroser` (écriture champ) ne sont **jamais** appelés par le tick déterministe ;
  le golden ne les invoque pas. Les nouveaux coûts (`COUTS`/`OBJETS_TOUCHES`)
  sont **neutres sans maîtrise** (`cout_action` → base ; golden Vigueur intact).
- **Le MODÈLE EAU re-fige le golden — maîtrisé et LOCALISÉ.** Le golden a deux
  tuiles : **T0 `terre` (hum init 1.5)** et **T1 `argile` (hum init 2.0)**
  (`tests/test_golden.py:62-69`). Conséquences ciblées :
  - **Drainage** : terre conserve **0.993** (valeur actuelle) → **T0 inchangée**.
    Seule **T1 (argile 0.997)** draine différemment → dérive **localisée sur T1**.
  - **Asphyxie** : T1 démarre à **2.0**, sous `HUM_EXCES = 2.3` → pas de
    déclenchement immédiat ; mais l'argile retient → la dérive éventuelle reste
    **sur T1**. T0 (terre, hum ≤ 1.5) ne franchit jamais le seuil → **inerte**.
  - → **Re-figeage attendu : T1 uniquement**, expliqué (drainage argile + bord
    d'asphyxie). T0 doit rester **bit-identique** — c'est le **garde-fou de
    revue** (si T0 bouge, un couplage involontaire a fui). Dérive annoncée,
    conforme à la règle CLAUDE.md (re-figeage maîtrisé).
- **Déterminisme** : aucun RNG dans les gestes ; la germination différée
  réutilise le **hash de succession** existant (déterministe).
- **Philo** : aucun bonus/malus direct (#2 — on n'écrit que des **champs**, la
  réponse émerge au tick, Q12 a) ; action sur le milieu = canal vertueux (#1) ;
  l'usure (évaporation/drainage) rend la solution facile coûteuse (#1) ; le
  « bon moment » de germination et le sur-arrosage se **découvrent** par
  l'observation (#6) ; deux joueurs sur des sols différents (argile/sable)
  vivront l'eau différemment (#7).

## 6. Découpage d'implémentation (conception figée → kickoff d'impl séparé)

Ampleur **moyen→gros**. Tronçons autosuffisants, chacun préserve/re-fige
explicitement le golden :

1. **`planter`** — `GrainEnAttente` (gènes propres + tag `cultive`) par plot dans
   `fields/seedbank.py` ; dépôt depuis `PlayerSeedBank.take` ; germination via
   `succession.py` (plot libre + niche) qui lève le dépôt **tel quel** et
   **transmet le tag** ; coût `FAIBLE`. **Golden INTACT** (event-driven).
2. **`arroser`** — `arroser(gs, player, eco, r, c, phase)` écrit `humidite`
   (`+DOSE`, cap 3.0, cumulatif) ; deux phases ; coût `MODÉRÉ × URGENCE` en
   saison. **Golden INTACT** (event-driven).
3. **Modèle « eau » au tick** — *tronçon ISOLÉ, le plus risqué* :
   (a) `DRAINAGE_PAR_SOL` dans `tick_hydrology` (terre inchangé) ;
   (b) asphyxie : seuil haut sur `ok_hum` (stagnation « noyé »), pénalité uptake,
   `asphyxie_memory` → santé. **Golden RE-FIGÉ maîtrisé (T1 uniquement, T0
   bit-identique)** — diff expliqué dans le commit.
4. **Pont** `tools/sim_server.py` : router `planter`/`arroser` ; **exposer la
   banque-joueur** au snapshot (pour que la vue propose les graines plantables) ;
   bump de protocole.
5. **Tests** : germination différée (lève au bon moment, gènes propres, tag
   transmis) ; arrosage (champ monte, redescend au tick) ; asphyxie (uptake↓ puis
   santé↓, stagnation « noyé ») ; drainage par sol contrasté ; **golden re-figé
   T1, T0 inchangée**.

Le **rendu Godot** des gestes (choisir une graine, viser, voir le sol
s'humidifier, indices d'asphyxie) = **volet vue ultérieur**.
**NB** : la **compétition intra-plot** est le sprint qui suit (réalise pleinement
Q4 / l'empilement).

---
*Réfs : `docs/joueur/vigueur/conception_vigueur.md` §3.1-3.2 (intention, philo #2, urgence),
`docs/joueur/gestes/conception_ecrasement.md` (gabarit de structure), `sim/seeds.py`
(`PlayerSeedBank`), `fields/seedbank.py` (`SeedBank` agrégée vs `GrainEnAttente`),
`sim/succession.py` (germination niche), `fields/ecofields.py:tick_hydrology`
(`DRAINAGE`, `BASE_RAIN`, [0,3]), `sim/engine.py:195/302` (`ok_hum`,
`drought_stress`), `sim/actions.py` (`COUTS`/`OBJETS_TOUCHES`, `URGENCE_MULT`),
`maitrise_detection.py:163` (`marquer_replante`), `tests/test_golden.py:62-69`
(T0 terre / T1 argile).*
