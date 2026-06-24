> ⚠️ **CADUC depuis le 2026-06-19.** Ce kickoff cadrait le modèle **A « parfum »**
> (animaux = variantes de sprite d'une guilde, triade mutualisée). Nico a tranché
> le **modèle B** (chaque animal a SA triade propre, guildes → catégories) — voir
> `docs/conception/CONCEPTION_FAUNE_DEDIEE.md` et les kickoffs `04a_*`→`04e_*`.
> Conservé en historique (règle « ne rien jeter »). **NE PAS implémenter ce doc.**

# Tronçon ④ — FAUNE nommée « parfums » (modèle A) — CADUC

> Sprint CATALOGUE ENRICHI. État partagé : `00_etat.md` (lire d'abord).
> Doc de référence FIGÉ : `docs/conception/CONCEPTION_CATALOGUE_ENRICHI.md`
> (§5.1 modèle A tranché, §5.2 catalogue nommé, §5.3 interconnexions, §7.1/§7.3).
> Kickoff **autosuffisant**. Lancement Python depuis `data/code/`.
> Filet C# : `dotnet build Symbiose.csproj` (**zéro C# attendu ici** — la vue
> Godot est le tronçon ⑥).

## Objectif

Donner un **visage nommé** aux trois guildes anonymes (ravageur, auxiliaire,
vers_de_terre) **sans toucher la dynamique** : 10 animaux nommés = des
**variantes de perception** (« parfums ») d'une guilde, pas de nouveaux champs.
Modèle **(A) tranché** (§5.1) : même champ de population, le nom est une
**lecture** du joueur choisie par **hash déterministe**. Coût moteur **NUL** →
**golden NEUTRE par construction** (le tick ne lit jamais ce registre).

| Nom FR | Guilde | Proie / ressource (doc) | Habitat / niche (doc) | Fenêtre |
|---|---|---|---|---|
| **Puceron** | ravageur | feuillage (sève) | monoculture, jeunes pousses | estival |
| **Limace** | ravageur | feuillage tendre | sol humide, sous litière | humide/frais |
| **Doryphore** | ravageur | feuillage (Solanaceae) | près des Solanaceae | estival |
| **Coccinelle** | auxiliaire | pucerons | nectar + stabilité | estival |
| **Carabe** | auxiliaire | limaces, larves (sol) | sol non perturbé, sous structures | nocturne |
| **Chrysope** | auxiliaire | pucerons | nectar | estival |
| **Merle** | auxiliaire | fruit frais (signal ④) | haies, structures hautes | toute saison |
| **Hérisson** | auxiliaire | limaces (nocturne) | piles/tas (structures ⑤) | nocturne |
| **Lombric** | vers_de_terre | MO + microbiome | sol non perturbé | quasi annuelle |
| **Cloporte** | vers_de_terre | litière en décompo | sous litière/structures | humide |

> ⚠️ Le **bourdon** et l'**osmie** (modèle B, pollinisateurs à champ dédié) sont
> **HORS de ce tronçon** → tronçon ⑤ (re-figé maîtrisé). Ici **uniquement** les
> 10 parfums (A), golden neutre.

## Périmètre EXACT (et frontière avec ⑥)

**DANS ④ (Python, source de vérité, golden NEUTRE)** :
- un **registre data-pur** des 10 parfums (métadonnées : guilde, proie, habitat,
  fenêtre, blurb d'encyclopédie, interconnexions §5.3) ;
- un **sélecteur de perception DÉTERMINISTE** : « quel animal nommé est perçu
  pour CETTE guilde, à CE plot, CETTE semaine ? » — par `_hash_noise` (zéro RNG) ;
- des **tests** (couverture, déterminisme, filtrage par guilde + fenêtre, golden
  NEUTRE).

**HORS ④ → tronçon ⑥ (vue Godot)** : choix du **sprite** correspondant, **rendu**
de l'entrée d'encyclopédie ingame, **export par le pont** (`tools/`). Le registre
④ est conçu pour être **lu plus tard** par Godot, mais **④ ne touche ni le pont
ni le C#**. Il n'existe **aucune infra d'encyclopédie en Python** aujourd'hui
(vérifié) — **ne pas en créer** : le blurb est une simple **donnée** portée par
le registre, son affichage est ⑥.

## Pourquoi le golden reste NEUTRE (à VÉRIFIER, pas à supposer)

Le mécanisme du tick (`PopulationField`, `_avancer_stades`, `_tick_*`) **n'importe
pas** le nouveau module et **ne l'appelle jamais**. Le registre/sélecteur est une
couche de **perception** parallèle. Donc le hash golden **doit** rester
`5fddfe54…`. Re-lancer `tests/test_golden` pour le **confirmer** : si le hash
bouge, c'est qu'un appel a fui dans une boucle de simulation (BUG) — pas un
re-figeage légitime.

## Conception technique (décisions FIGÉES pour ce tronçon)

### Fichier — `fields/faune_parfums.py` (NOUVEAU)

`population.py` est **déjà ≈ 369 LDC pur > garde-fou ~350** (signalé en ③) : **ne
rien y ajouter**. La perception est de toute façon un **concept distinct** de la
dynamique trophique → module dédié. Patron : data-driven comme `TrophicSpec` /
`PollinatorSpec` (registre + fabrique).

```python
@dataclass(frozen=True)
class ParfumSpec:
    nom: str                  # "Puceron" (FR, affiché)
    guilde: str               # "ravageur" | "auxiliaire" | "vers_de_terre"
    salt: int                 # canal _hash_noise DÉDIÉ (décorrélé du tick)
    proie: str                # doc/encyclopédie — la dynamique réelle est la guilde
    habitat: str              # doc/encyclopédie
    blurb: str                # texte d'encyclopédie (donnée ; rendu = ⑥)
    interconnexions: tuple[str, ...] = ()   # noms liés (§5.3), graphe relationnel
    daylen_min: float | None = None   # fenêtre phénologique optionnelle (heures de
    daylen_full: float | None = None  # jour) ; None = perçu toute l'année
```

- **Fenêtre saisonnière** : réutiliser la **longueur de jour** comme les guildes
  (cf. `TrophicSpec.daylen_min/full` + calendrier `saison_de`/photopériode). Mapper
  `estival` → fenêtre jours longs, `toute saison`/`quasi annuelle` → `None`.
  ⚠️ **`nocturne`/`humide` ne sont PAS des portes** (pas de cycle jour/nuit ni de
  porte humidité dans le tick hebdo) → **tags d'encyclopédie seulement** (champ
  `habitat`/`blurb`), pas de gate. L'expliciter dans la docstring (honnêteté du
  modèle, pas de fausse mécanique).

### Sélecteur déterministe

```python
def parfum_percu(guilde, week, r, c) -> ParfumSpec | None:
    """Quel animal nommé est PERÇU pour `guilde` au plot (r,c), semaine `week`.
    Filtre les variantes de la guilde dont la fenêtre est ouverte à `week`
    (photopériode), puis en choisit UNE par _hash_noise(salt_guilde, week, r, c).
    PURE perception : zéro RNG, jamais lu par le tick → golden NEUTRE."""
```

- Source unique du hash : `fields/noise.py` (`_hash_noise(seed, week, r, c)` ∈
  [0,1)). Indexer `int(h * n) % n` parmi les `n` variantes ouvertes (déterministe,
  stable). Choisir un **salt par guilde** (constantes neuves `_SALT_PARFUM_*`,
  canaux inédits → n'altèrent rien).
- Si aucune variante ouverte (fenêtre fermée) → `None` (perception « guilde
  générique » conservée, comme avant ④).

### Interconnexions (§5.3) = MÉTADONNÉE, pas dynamique neuve

Les boucles proie↔prédateur existent **déjà** (`TrophicSpec.predators`,
`signal_fn` fruit ④ décompo, ponts larvaires). Ici on les **rend lisibles** en
remplissant `interconnexions` (ex. puceron → `("coccinelle","chrysope","syrphe")`).
**Aucune** nouvelle prédation, **aucun** abaissement de pression : le doryphore
« contré par l'ail » et l'hérisson « habitant les piles » sont des **liens
d'encyclopédie** (le répulsif réel est l'`adjacency_bonus` Amaryllidaceae de ③,
déjà en place). Si Nico veut un effet littéral plus tard → **dette**, pas ④.

### Câblage API publique

Exporter `ParfumSpec`, `build_parfum_registry`, `parfum_percu` via
`fields/__init__.py` (suivre la convention de ré-export du paquet ; imports
appelants par `from fields import …`). **Ne rien importer** depuis `sim`/`engine`
(respect de la règle de couches `plants ← fields ← sim`).

## Validation

1. `python3 -m tests.test_golden` → **PASS, hash `5fddfe54…` INCHANGÉ** (preuve de
   neutralité — le cœur de ce tronçon).
2. **Nouveau `tests/test_faune_parfums.py`** :
   - **Couverture** : chacune des 3 guildes a ≥1 parfum ; les 10 noms attendus
     présents ; toute `guilde` ∈ {ravageur, auxiliaire, vers_de_terre}.
   - **Filtrage guilde** : `parfum_percu("ravageur", …)` ne rend JAMAIS un
     auxiliaire/vers (et réciproquement) — sur un balayage de plots/semaines.
   - **Déterminisme** : deux appels identiques → même parfum ; deux « runs »
     (re-construction du registre) → identiques ; salts distincts par guilde
     (deux guildes au même (week,r,c) ne sont pas corrélées triviallement).
   - **Fenêtre saisonnière** : un parfum estival n'est jamais perçu en plein hiver
     (fenêtre fermée) ; un parfum `daylen=None` est candidat toute l'année.
   - **Neutralité** : `grep`/import — le module n'est PAS importé par les boucles
     de tick (assert d'architecture léger : aucun `import` de `faune_parfums` dans
     `sim/engine/*`). À défaut, le test golden #1 le prouve déjà.
3. `python3 -m tests.test_population` et `test_attraction` → toujours PASS
   (non-régression : la dynamique macro n'a pas bougé).
4. Garde-fou taille : `fields/faune_parfums.py` < ~350 LDC pur (large marge
   attendue) ; **ne pas** gonfler `population.py`.

## À faire en fin de tronçon

- Mettre à jour `00_etat.md` (④ ✅ : registre + sélecteur, golden NEUTRE confirmé,
  frontière ⑥ rappelée, tags non-gatés `nocturne`/`humide` signalés).
- **Entrée `journal/` + index `journal.md`** (catalogue enrichi ④ : 10 parfums A,
  perception déterministe, golden NEUTRE, interconnexions = métadonnée).
- Commit : `feat(catalogue) : faune nommée lot ④ — 10 parfums (A) ravageur/auxiliaire/vers, golden NEUTRE`.
- Proposer ⑤ (pollinisateurs B : bourdon/osmie, re-figé maîtrisé) ou ⑥ (vue Godot
  sprites/encyclopédie) — **pas** d'enchaînement auto.
