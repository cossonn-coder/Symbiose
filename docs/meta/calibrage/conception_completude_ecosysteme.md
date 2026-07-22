# CONCEPTION — Complétude de l'écosystème téléonomique (D61)

> **Statut : FIGÉ 2026-07-11** (`/conception`, arbitrages Nico Q1-Q3).
> **Nature : MÉTA — ce n'est PAS un sprint `/sprint-auto`.** Aucun moteur, aucun
> champ, aucun golden, aucune vue Godot. Deux livrables : (1) **ce référentiel**
> fonctionnel ; (2) un **volet « complétude écosystème »** ajouté au skill
> `/audit-projet` (§5). L'ajout effectif d'espèces se fait dans des `/conception`
> DÉDIÉES, nourries par ce référentiel — jamais en vrac.

---

## §0. Principe : la complétude se mesure aux BOUCLES, pas aux espèces

Un écosystème en **run éternel** (philo #4) + la règle « le catalogue grandit
avec les idées » interdisent la notion de liste finie « à cocher puis c'est
complet ». Le critère durable est **téléonomique** : **chaque flux écologique a
une SOURCE et un PUITS**. Une fonction dont le puits (ou la source) manque = une
**boucle ouverte** = un déséquilibre latent (accumulation ou disparition non
régulée). C'est ça qu'on traque, pas un décompte.

Corollaire pour l'audit : on ne demande pas « combien d'espèces ? » mais « quelle
**fonction écologique** est orpheline (flux sans puits/source) ? ». Le taxon
découle de la fonction, jamais l'inverse.

Rappel des garde-fous de design que toute future espèce devra respecter :
- **#1/#2** — l'espèce agit par un FLUX/contrainte, jamais par bonus/malus direct
  sur les plantes. Un prédateur est un **puits** sur un champ de population, pas
  un `-2 santé` scripté.
- **#3** — déterministe, zéro RNG vivant (positions par `_hash_noise`, salt dédié).
- **#7** — hétérogénéité (l'espèce ne se distribue pas uniformément).
- **Règle projet** — toute espèce ajoutée reçoit ses **5 voix** (encyclopédie /
  carnet / pages secrètes / magazine / événements) : cf.
  `docs/narration/voix/conception_voix_narratives.md`. Une fonction bouchée par une fiche muette n'est
  pas bouchée.

---

## §1. Inventaire réel (source de vérité = le code, 2026-07-11)

| Règne | Décompte | Où |
|---|---|---|
| Végétal | ~41 espèces (32 non-arbres + 9 arbres), 13+ familles | `plants/catalogue.py` |
| Faune | 15 espèces nommées data-driven | `fields/population/registry.py` |
| Fongique | 1 acteur mycélium GÉNÉRIQUE (3 rôles), 0 espèce nommée | `sim/champignon_encyclo.py` |

Faune par catégorie : **ravageur** (puceron, limace, doryphore) · **détritivore**
(lombric, cloporte) · **auxiliaire/prédateur** (coccinelle, chrysope, carabe,
merle, hérisson) · **pollinisateur** (abeille, syrphe, papillon, bourdon, osmie).
Ponts de cycle de vie : chenille→papillon, syrphe(larve→adulte).

L'inventaire chiffré n'est PAS la source de complétude — la matrice §2 l'est.
Le décompte ci-dessus n'existe que pour dater l'écart mesuré par l'audit §5.

---

## §2. Matrice fonctionnelle téléonomique

Légende statut : **✅** incarné · **🔵** conçu, non implémenté (pipeline §4, ne
PAS recompter comme trou) · **⚠️** TROU (boucle ouverte, §3) · **∅** volontairement
hors périmètre (justifié).

Colonne « bouclage » = ce qui prouve que le flux a source ET puits.

### A. Production primaire (autotrophes)
| Fonction | Bouclage (source→puits) | Statut | Incarné par |
|---|---|---|---|
| A1 Production par strate (sol→arborée) | lumière→biomasse→herbivores/litière | ✅ | 41 esp., 5 strates + arbres |
| A2 Fixation symbiotique N | N₂ air→sol via nodosités→uptake | ✅ / 🔵 | Fabaceae (trèfle, haricot, minette) ; **aulne** 🔵 |
| A3 Accumulateur dynamique (pompe minérale) | horizon profond→litière riche→surface | ✅ | consoude, pissenlit (pivots) |
| A4 Ressource mellifère (nectar/pollen) | fleur→pollinisateur | ✅ | bourrache, phacélie, lavande, achillée… |
| A5 Floraison de SOUDURE (fin hiver) | nectar précoce→pollinisateur au réveil | ⚠️ **T6** | — (aucun bulbe précoce) |
| A6 Floraison NOCTURNE parfumée | nectar nuit→pollinisateur nocturne | ⚠️ **T5** | — |
| A7 Grimpante ligneuse mellifère tardive | manne automnale→pollinisateur | ✅ | lierre, jasmin |
| A8 Acidophile / tourbière | niche pH bas | ✅ / 🔵 | myrtille ; **sphaigne**, **carnivore** 🔵 |
| A9 Plante parasite / hémiparasite | ponction hôte→régulation densité | ⚠️ **T8** | — (gui, rhinanthe) |
| A10 Rudérale pionnière (cicatrise sol nu) | sol nu→couverture→succession | ✅ | bourse-à-pasteur, pâturin, moutarde |

### B. Consommateurs primaires (herbivores)
| Fonction | Bouclage | Statut | Incarné par |
|---|---|---|---|
| B1 Suceur de phloème | plante→puceron→prédateur | ✅ | puceron |
| B2 Folivore broyeur (insecte) | feuille→larve→prédateur/métamorphose | ✅ | doryphore, chenille |
| B3 Mollusque herbivore | plante→limace→prédateur | ✅ | limace |
| B4 Herbivore VERTÉBRÉ | racine/écorce→rongeur→super-prédateur | ✅ (T7, 2026-07-11) | campagnol (cat. `herbivore_vertebre`, dégât racinaire dédié) |
| B5 Larve aquatique (mare) | détritus mare→larve→prédateur aérien | 🔵 | **moustique** 🔵 (hydrologie) |

### C. Consommateurs secondaires (prédateurs / auxiliaires)
| Fonction | Bouclage | Statut | Incarné par |
|---|---|---|---|
| C1 Prédateur de pucerons | puceron→coccinelle/chrysope/syrphe | ✅ | coccinelle, chrysope, syrphe(larve) |
| C2 Prédateur de sol (limaces) | limace→carabe/hérisson | ✅ | carabe, hérisson |
| C3 Insectivore aérien (oiseau) | insectes→oiseau | ✅ | merle |
| C4 **Parasitoïde** | pond DANS puceron/chenille→régule de l'intérieur | ⚠️ **T2** | — (guêpe aphidius/ichneumon) |
| C5 Prédateur aérien de mare | moustique/larve→libellule | 🔵 | **libellule** 🔵 (hydrologie) |
| C6 Prédateur VÉGÉTAL (puits N carné) | faune de mare→plante carnivore | 🔵 | **Drosera** 🔵 (hydrologie) |

### D. Consommateurs tertiaires (super-prédateurs, niveau 3)
| Fonction | Bouclage | Statut | Incarné par |
|---|---|---|---|
| D1 **Super-prédateur** (ferme le sommet) | auxiliaires/rongeurs→couleuvre/belette/rapace | ✅ (T1, 2026-07-11) | rapace (aérien : campagnol+merle), couleuvre (terrestre : campagnol+limace) |

> **Boucle ouverte la plus grave** : aujourd'hui hérisson, merle, carabe,
> coccinelle n'ont **aucun puits** → leur population n'est régulée que par la
> ressource (bottom-up), jamais par le haut (top-down). Un écosystème téléonomique
> ferme le sommet.

### E. Pollinisateurs
| Fonction | Bouclage | Statut | Incarné par |
|---|---|---|---|
| E1 Généraliste diurne | fleur→pollen transporté→nouaison | ✅ | abeille, bourdon |
| E2 Langue longue (fleur tubulaire) | fleur profonde→pollinisation | ✅ | papillon, bourdon |
| E3 Solitaire | fleur→osmie/syrphe | ✅ | osmie, syrphe |
| E4 **Pollinisateur NOCTURNE** | fleur nocturne (A6)→sphinx/noctuelle | ⚠️ **T5** | — |

### F. Décomposeurs / recycleurs
| Fonction | Bouclage | Statut | Incarné par |
|---|---|---|---|
| F1 Détritivore de litière | litière→cloporte/lombric→humus | ✅ | cloporte, lombric |
| F2 Saprophyte fongique (lignine/bois) | bois mort→mycélium→humus | ✅ | mycélium (rôle saprophyte) |
| F3 Liant d'humus (fongique) | om_stable→agrégats stables | ✅ | mycélium (rôle liant) |
| F4 Mycorhize (mobilise P) | racine↔réseau→uptake P | ✅ | mycélium (rôle mycorhize) |
| F5 Faune fongivore | carpophores→fongivore | ✅ | (conçu mycélium ④) |
| F6 Coprophage (déjections) | fèces→bousier→sol | ∅ | hors périmètre (pas de gros herbivore) |

### G. Pathogènes / régulation par la maladie
| Fonction | Bouclage | Statut | Incarné par |
|---|---|---|---|
| G1 **Pathogène fongique ACTEUR relié** | spores(humidité)→infection→puits (résistance/fongivore/météo sèche) | ⚠️ **T3** | mildiou/oïdium = **scalaire** familial, NON relié |

> Le mildiou existe comme pénalité familiale scalaire (Solanaceae…), mais ce n'est
> pas un **acteur** : pas de source spatialisée (foyer de spores), pas de puits
> (aucun fongivore ne le mange, aucune météo sèche ne l'éteint explicitement), pas
> d'interconnexion. Flux « maladie » à moitié modélisé.

### H. Services de dispersion des graines
| Fonction | Bouclage | Statut | Incarné par |
|---|---|---|---|
| H1 Anémochorie (vent) | graine ailée→vent→plot lointain | ✅ | pissenlit (+ sprint vent) |
| H2 Barochorie/autochorie | chute/éjection→plot voisin | ✅ | implicite (seedbank locale) |
| H3 **Endozoochorie** (fruit→oiseau→graine) | fruit mûr→merle→graine déposée AILLEURS | ⚠️ **T4** | merle mange, mais pas de transport de graine bouclé |
| H4 **Myrmécochorie** (élaïosome→fourmi) | graine à élaïosome→fourmi→dispersion | ⚠️ **T9** | violette (a l'élaïosome !) mais **fourmi absente** |

### I. Ingénieurs d'écosystème
| Fonction | Bouclage | Statut | Incarné par |
|---|---|---|---|
| I1 Bioturbation du sol | galeries→structure/infiltration | ✅ | lombric |
| I2 Ingénieur hydraulique | rétention d'eau/tourbe | 🔵 | **sphaigne** 🔵 (hydrologie) |
| I3 Ingénieur végétal (nourrice/brise-vent/ombrage) | modifie microclimat voisin | ✅ | arbres, haies (ombre maison, abri vent) |

### J. Base microbienne (abstraite — champs, pas acteurs)
| Fonction | Statut | Incarné par |
|---|---|---|
| J1 Microbiome du sol | ✅ | champ `microbiome` |
| J2 Rhizobium (fixation symbiotique) | ✅ | implicite (gène fixation Fabaceae) |
| J3 Nitrification / minéralisation | ✅ | cascade OM + NPK (Liebig) |

> Le niveau microbien est **volontairement abstrait** en champs continus (pas
> d'espèces bactériennes nommées) — cohérent avec l'échelle du jeu. Ne PAS
> traiter comme trou.

---

## §3. Trous priorisés (le diagnostic actionnable)

Chaque trou = une future `/conception` dédiée (espèce(s) + 5 voix + moteur + vue).
Priorité = gravité de la boucle ouverte × cohérence permaculturelle.

| # | Trou | Fonction | Priorité | Espèce(s) candidate(s) | Boucle fermée par l'ajout |
|---|---|---|---|---|---|
| ~~T1~~ ✅ | Super-prédateur (sommet trophique) | D1 | 🔴 **haute** | **rapace + couleuvre** (implémentés 2026-07-11) | régule merle/limace/campagnol (top-down) |
| **T2** | Parasitoïde | C4 | 🔴 **haute** | guêpe aphidius / ichneumon | régule puceron/chenille de l'intérieur (clé permaculture) |
| **T3** | Pathogène fongique en ACTEUR | G1 | 🟡 moyenne-haute | acteur « rouille/mildiou » spatialisé + fongivore | ferme le flux maladie (source spores ↔ puits) |
| **T4** | Endozoochorie | H3 | 🟡 moyenne | (merle existant, ajouter le transport de graine) | fruit→oiseau→colonisation d'un plot lointain |
| **T5** | Pollinisateur nocturne + fleur nocturne | E4 + A6 | 🟡 moyenne | sphinx/noctuelle **+** onagre/chèvrefeuille | niche pollinisation nuit (paire indissociable) |
| **T6** | Nectar de soudure (fin hiver) | A5 | 🟡 moyenne (facile) | perce-neige, crocus, noisetier (chatons) | nourrit les pollinisateurs au réveil (`daylength` déjà là) |
| ~~T7~~ ✅ | Herbivore vertébré | B4 | 🟢 basse-moyenne | **campagnol** (implémenté 2026-07-11) | proie du super-prédateur T1 (couple à T1) |
| **T8** | Plante parasite/hémiparasite | A9 | 🟢 basse | gui (arbre), rhinanthe (gramin.) | régulation de densité par ponction |
| **T9** | Myrmécochorie / fourmi | H4 | 🟡 moyenne | fourmi (la violette a DÉJÀ l'élaïosome) | dispersion des graines à élaïosome |

**Couplages notables** : T1↔T7 (le super-prédateur a besoin d'une proie vertébrée
crédible) ; T5 = paire fleur+insecte à concevoir ENSEMBLE ; T9 exploite une amorce
déjà au catalogue (violette). Recommandation de séquence : **T1+T7** (ferme le
sommet trophique, le plus structurant), puis **T2** (parasitoïde), puis les
services (T4/T5/T6/T9), enfin T3/T8.

---

## §4. Pipeline conçu-non-implémenté (NE PAS recompter comme trou)

Ces acteurs sont **déjà arbitrés** dans des conceptions figées ; ils bouchent des
fonctions marquées 🔵 ci-dessus. L'audit les compte comme « en attente », pas comme
trous.

| Acteur | Fonction bouchée | Doc source |
|---|---|---|
| aulne | A2 (fixation N arborée) | `docs/champs/eau/conception_hydrologie_marecage.md` |
| sphaigne | A8, I2 (acidophile, ingénieur hydraulique) | idem |
| plante carnivore (Drosera) | A8, C6 (prédateur végétal, puits N) | idem |
| moustique | B5 (larve aquatique = proie) | idem |
| libellule | C5 (prédateur aérien de mare) | idem |

Quand l'hydrologie sera implémentée, repasser leur statut 🔵→✅ dans ce doc.

---

## §5. Volet d'audit « complétude écosystème » (extension de `/audit-projet`)

Le skill `/audit-projet` gagne un contrôle **complétude écosystème** (semi-auto :
l'agent lit le code + ce référentiel et raisonne, pas de parseur rigide). Il
produit, en fin de sprint ou à la demande :

1. **Fonctions orphelines** — parcourt la matrice §2, liste les lignes **⚠️** encore
   ouvertes, priorisées (§3). Chaque trou → reco « ouvrir `/conception <sujet>` ».
2. **Espèces conçues-non-implémentées** — confronte le pipeline §4 aux catalogues
   réels (`PLANT_CATALOGUE`, `registry.py`, mycélium) : signale un 🔵 dont le doc
   source est marqué implémenté (statut à passer ✅) OU un 🔵 qui traîne.
3. **Espèces « hors-sol téléonomique »** — toute espèce présente au catalogue mais
   rattachée à AUCUNE fonction de la matrice §2 → signal que **le référentiel doit
   être mis à jour** (une espèce a été ajoutée sans que sa fonction soit inscrite).
   C'est le garde-fou anti-dérive du référentiel lui-même.
4. **Croisement 5 voix** — réutilise le contrôle existant (« toute plante = ses 5
   voix ») : une fonction « bouchée » par une espèce à la fiche muette est signalée
   🟡 (bouchée sur le papier, pas dans l'expérience).

Rapport priorisé 🔴/🟡/🟢, chaque constat relié à une fonction de la matrice + à
D61. **Lecture seule** (le skill audit ne corrige rien, cf. sa règle).

**Convention de lecture** : la matrice §2 est la source ; la colonne « Incarné
par » cite les **clés de catalogue** (ex. `trefle`, `coccinelle`) pour que le
diff catalogue↔référentiel soit mécanique. Garder ces clés à jour est la seule
maintenance de données du référentiel.

---

## §6. Maintenance (la 2ᵉ moitié de D61)

- **À chaque fin de sprint** qui touche au catalogue (plante/faune/champignon) :
  lancer `/audit-projet ecosysteme`. Mettre à jour la matrice §2 (statut +
  « Incarné par ») et le pipeline §4 en conséquence.
- **Quand une `/conception` d'ajout d'espèce est figée** : passer la fonction
  correspondante en 🔵 (avec pointeur doc) dans §4/§2.
- **Quand elle est implémentée** : 🔵→✅, retirer du pipeline §4.
- Ce doc est **vivant** : il grandit avec les idées (une nouvelle niche pensée =
  une nouvelle ligne, d'abord en ⚠️). Il n'est jamais « terminé » — c'est le
  point, philo #4.

---

## §7. Ce que D61 ne fait PAS

- N'ajoute **aucune espèce** (les ajouts = `/conception` dédiées, nourries d'ici).
- Ne touche **aucun code moteur** (pas de golden, pas de champ, pas de pont).
- N'écrit **pas de kickoff `0N`** — ce n'est pas un `/sprint-auto`.
- Ne remplace pas les conceptions du pipeline §4 (il les recense).
