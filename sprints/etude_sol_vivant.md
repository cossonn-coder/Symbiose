# Dossier d'étude — Le sol vivant dans Symbiose

> But de ce document : te donner les bases d'écologie du sol et l'état du
> moteur, pour que tu choisisses **en connaissance de cause** ce qu'on
> modélise. Pas de décision attendue avant que tu l'aies lu tranquillement.
> Tu es ingénieur sim/embarqué, pas biologiste — j'explique la bio, tu juges
> le modèle.

---

## Partie 1 — La biologie, expliquée pour un ingénieur

### Le sol n'est pas un substrat, c'est un système

Vu d'avion, un sol vivant est un **système à boucles de feedback** où l'énergie
(carbone) circule. La plante capte le carbone de l'air (photosynthèse) et en
**réinvestit une partie sous terre** pour « payer » des services. C'est une
économie souterraine.

### La rhizosphère

C'est la fine couche de sol (quelques mm) **autour des racines**. C'est le
quartier le plus actif du sol : densité microbienne ×10 à ×100 par rapport au
sol nu. Pourquoi ? Parce que la plante y déverse des **exsudats**.

### Les exsudats racinaires — la clé de tout

La plante envoie dans le sol, par ses racines, **10 à 40 % du carbone** qu'elle
photosynthétise, sous forme de sucres, acides, protéines. Ce n'est pas un
déchet : c'est un **investissement**. Elle nourrit les microbes pour qu'ils lui
rendent des services :

- **minéraliser** la matière organique → libérer azote/phosphore assimilables ;
- **protéger** ses racines (les bonnes bactéries occupent la place, certaines
  produisent des antibiotiques contre les pathogènes) ;
- **structurer** le sol (colles microbiennes → grumeaux → porosité → eau+air).

Analogie : la plante « loue » une main-d'œuvre microbienne en la payant en
sucre. Plus elle est vigoureuse (photosynthèse↑), plus elle peut payer, plus
le service rendu est grand, plus elle est vigoureuse… **boucle vertueuse**.

### Le microbiome

L'ensemble des micro-organismes : bactéries (rapides, opportunistes) et
champignons (lents, structurants). Dans Symbiose c'est déjà un champ. En vrai
il fait trois choses qui comptent pour le jeu : **minéralisation**,
**protection sanitaire**, **structuration**.

### Les mycorhizes — le réseau

Des champignons **symbiotiques** qui s'associent aux racines : la plante leur
donne du sucre, ils lui donnent en échange un **prolongement racinaire** (leurs
filaments explorent 100× plus de sol qu'une racine) → accès à l'eau et au
phosphore lointains. Et ils **connectent plusieurs plantes entre elles** (le
fameux « wood wide web ») : transfert d'eau, de nutriments, de signaux d'alerte
entre voisines. C'est de la coopération inter-plantes, pas de la compétition.

### La matière organique (MO) — trois vitesses

Quand quelque chose meurt (feuille, racine, plante entière), ça devient de la
MO qui se décompose **en cascade**, comme des caches de vitesses différentes :

| Compartiment | Quoi | Vitesse | Rôle |
|---|---|---|---|
| **Fraîche** | débris récents, sucres | rapide (semaines) | nourriture microbienne immédiate |
| **Active** | partiellement digérée | moyenne (mois) | réserve de fertilité |
| **Stable (humus)** | très transformée | lente (décennies) | structure, rétention d'eau, mémoire |

C'est **exactement** le modèle `om_fresh / om_active / om_stable` déjà codé en
C# (et qu'on va porter en Python — voir Partie 2). La minéralisation
(active → fertilité) est **d'autant plus rapide que le microbiome est actif**.

### La fertilité

Le stock de **nutriments minéraux immédiatement assimilables** (azote, etc.).
Elle vient de la minéralisation de la MO, et se perd par lessivage (pluie) et
par consommation racinaire.

### Récapitulatif : la grande boucle du sol vivant

```
  photosynthèse → exsudats racinaires → microbiome nourri
        ↑                                      │
   plante vigoureuse                           ▼
        ↑                          minéralisation + protection + structure
        └──────────── uptake (eau, nutriments, santé) ←─┘

  morts/résidus → MO fraîche → active → stable (humus)
                                  │
                                  └→ fertilité (minéralisation, ∝ microbiome)
```

Tout le « sol vivant » de la permaculture tient dans cette boucle : **ne pas
perturber, nourrir les microbes, laisser les racines et la MO faire le
travail**. C'est la philosophie du jeu (philosophie #1 et #4 du CLAUDE.md).

---

## Partie 2 — Ce que le moteur simule déjà

### Les champs en place (`fields.py`)

| Champ | Représente | Évolue comment | Alimenté par | Effets |
|---|---|---|---|---|
| `microbiome` | vie microbienne | diffuse (aura) | Fabaceae (N₂), aromatiques, basilic | protège maladie, accélère minéralisation, réduit herbivorie |
| `fertilite` | nutriments dispo | minéralisation − lessivage | MO, fixation N₂ | seuil de croissance |
| `organic_matter` | MO **(mono-compartiment v3)** | décroît (minéralise + respire) | nécromasse, résidus récolte | → fertilité |
| `humidite` | eau du sol | évapo/pluie/drainage | météo, rétention sol | seuil de croissance |
| `soil_memory` fast/deep | « état » intégré du sol | lerp lent (0.15 / 0.02) | microbiome+fert+MO | rétention d'eau, niche succession |
| `disturbance` | perturbation | bruit déterministe | aléas | ouvre les niches, fragilise |

### Les trois simplifications qui sautent aux yeux

1. **L'uptake n'est pas spatial.** Une plante puise (et enrichit) uniquement
   sur **son plot central**, jamais sur son empreinte racinaire `root_plots`.
   Le pivot du pissenlit et les fibres du pâturin ne servent qu'aux conflits.
   → Les racines, dans le moteur, ne « travaillent » pas vraiment le sol.

2. **L'enrichissement du sol est scripté par famille**, pas émergent. Les
   Fabaceae « injectent » du microbiome/fertilité par une règle fixe ; les
   autres plantes ne nourrissent pas le sol du tout. **Il n'y a pas
   d'exsudats** : la grande boucle de la Partie 1 n'existe qu'en pointillés.

3. **L'OM est mono-compartiment en Python (v3)** alors que le C# a déjà les
   trois vitesses (v4). C'est la dette D10. On répare ça en premier (ta
   décision) : c'est le socle dont les exsudats ont besoin (un exsudat nourrit
   l'OM *fraîche* et le microbiome).

### Ce qui manque, en une phrase

Le sol est aujourd'hui un décor qui réagit ; on veut qu'il devienne un
**organisme** : les racines le nourrissent, il leur rend des services, et une
vitalité émerge de cette boucle.

---

## Partie 3 — Les chantiers possibles

Pour chacun : le concept, comment le coder, l'effet sur le jeu, le coût.

### Chantier A — La boucle rhizosphère (exsudats ↔ microbiome) ⭐ cœur

**Concept** : chaque plante vivante dépose des exsudats sur sa zone racinaire,
proportionnels à sa biomasse et à sa photosynthèse (donc à la lumière reçue et
au stade). Ces exsudats nourrissent le microbiome local. Microbiome élevé →
minéralisation + protection + un bonus d'uptake → plante plus vigoureuse →
plus d'exsudats.

**Modélisation** : à chaque tick, `exsudat = f(stade, lumière, santé)` ajouté
au `microbiome` (et un peu à l'`om_fresh`) sur les plots racinaires. Le
microbiome existant gagne une **rétroaction sur la croissance** (aujourd'hui
il ne protège que). C'est ~30-50 lignes, déterministe, testable sur `main.py`.

**Effet jeu** : le sol vivant devient **émergent** — une polyculture dense et
photosynthétiquement active enrichit son propre sol ; un sol nu reste pauvre.
Récompense la couverture végétale permanente (principe permaculture).
Supprime le scripting « Fabaceae = +microbiome » au profit d'une règle
universelle (les Fabaceae garderaient juste un bonus N₂ spécifique).

**Coût/risque** : moyen. Touche le tick et l'équilibrage (risque d'emballement
de la boucle → à borner). **Dépend du socle OM v4.**

### Chantier B — Racines réellement spatiales 🔧 socle

**Concept** : l'uptake **et** les exsudats/enrichissements opèrent sur **toute
l'empreinte racinaire**, pas le plot central. Une grosse racine explore et
travaille plus de sol.

**Modélisation** : dans `_apply_uptake` et les `inject_field`, boucler sur
`plant.root_plots` au lieu de `plant.position` (en répartissant la quantité).
~20-40 lignes. La compétition racinaire entre voisines devient **spatiale et
émergente** (deux pivots qui se chevauchent s'épuisent mutuellement).

**Effet jeu** : la place souterraine devient une vraie ressource ; le choix
des espèces (racines complémentaires vs concurrentes) prend du sens — c'est
le **design en strates** de la permaculture.

**Coût/risque** : faible. C'est surtout une **correction de cohérence**. C'est
le socle naturel de A (les exsudats se déposent sur l'empreinte). Bon premier
pas.

### Chantier C — Réseau mycorhizien 🌐 extension

**Concept** : un champ `mycorhize` (ou un graphe de connexions) qui étend la
zone d'uptake effective d'une plante et **partage** eau/nutriments entre
plantes connectées. Coopération souterraine.

**Modélisation** : plus lourd. Soit un champ ambiant qui « lisse » les
ressources entre plots connectés, soit un vrai graphe plante↔plante. Demande
de décider qui se connecte (même famille ? distance ? compatibilité ?).

**Effet jeu** : le « wood wide web », très évocateur ; les plantes-mères qui
soutiennent les jeunes ; un levier de résilience avancé. Mais c'est une
**couche en plus**, pas un fondement.

**Coût/risque** : élevé. Recommandé **après** A et B, comme palier de
maîtrise avancé.

### Question transverse — La « vigueur du sol »

Trois façons de la traiter (rappel : la décision #2 dit que le Qi territorial
= les champs existants, pas un nouveau champ stocké) :

1. **Grandeur dérivée** (recommandé) — une fonction
   `vitalite(r,c) = g(microbiome, om_active, fertilite, structure, −disturbance)`
   calculée à la demande. Zéro champ en plus, cohérent avec le design, et c'est
   l'indicateur que le joueur apprendra à « lire » (et la préfiguration de la
   Vigueur D11 dans laquelle plantes et joueur puiseront).
2. **Nouveau champ stocké** — un `GridField` vitalité avec sa propre inertie.
   Plus simple à manipuler, mais **contredit la décision #2** : à rouvrir
   explicitement si tu y tiens.
3. **Aucune grandeur** — on approfondit juste les couplages existants.

---

## Partie 4 — Ordre que je recommande

```
0. Socle    : réaligner l'OM Python → v4 (fresh/active/stable)   ← ta décision
1. Chantier B : rendre racines/uptake/exsudats spatiaux           (faible coût)
2. Chantier A : boucle rhizosphère (exsudats ↔ microbiome)        (le cœur)
3. Vitalité : grandeur dérivée lisible                            (la lecture)
4. Chantier C : mycorhizes                                        (extension future)
```

Logique : chaque étape pose le socle de la suivante. 0 et 1 sont peu risqués
et « nettoient » le moteur ; 2 apporte l'émergence ; 3 rend le tout lisible ;
4 est un bonus de profondeur qu'on peut différer.

**Critère de validation à chaque étape** : `main.py` tourne plusieurs centaines
d'années sans crash, et on **observe** une dynamique plausible (un sol nu se
peuple et s'enrichit ; une polyculture dense bâtit un sol riche ; un sol
saccagé se régénère par la succession). C'est ton terrain — de la sim
déterministe qu'on lit dans le terminal.

---

## Partie 5 — Ce que tu auras à décider (après lecture, à tête reposée)

1. **Le cœur** : on part bien sur B → A (racines spatiales puis rhizosphère) ?
   Ou tu veux prioriser autrement ?
2. **La vigueur du sol** : grandeur dérivée (reco), nouveau champ, ou rien ?
3. **L'ampleur** : on s'arrête à l'étape 2 (boucle qui tourne) pour ce sprint,
   ou on pousse jusqu'à 3 (vitalité lisible) ? Les mycorhizes (4), je les vois
   différées.

Pas de réponse attendue maintenant. Lis, laisse infuser, et on en reparle.
Quand tu veux, on transformera ça en kickoff de sprint exécutable.
