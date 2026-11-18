# ① Pâturin réaliste + un gène non exprimé ne coûte rien (D140 A+B)

Lire d'abord `docs/vegetal/genetique/conception_depart_jardin.md` §2 A-B.

## Objectif
1. **Pâturin** (`plants/species/adventices.py`, classe `PoaAnnua`) : mode de
   pollinisation « vent » (attribut `pollination_mode`, déjà présent sur les espèces —
   voir comment le dactyle/la fétuque de `plants/species/prairie.py` sont déclarés
   anémophiles et faire pareil) + neutre d'`autofecondation` ≈ 0,9 via le dict
   `genetique` de la classe (patron : `genetique = {"autofecondation": {"neutre": 0.95}}`
   déjà utilisé dans `adventices.py`). Vérifier ensuite que sa `fecondation` n'est
   plus bloquée à ≈ 0,085 (pollen du vent reçu, part autofécondée élevée).
2. **Gènes muets** : `PlantInstance.cout_genetique()` (`plants/base/instance.py`) somme
   l'excès de chaque caractère de `CARACTERES_COUTEUX` (champ `cout` du registre
   `plants/caracteres.py`). Ne compter un caractère que si l'espèce l'**exprime**.
   - Poser l'information **dans le registre**, à côté de `cout` (ex. un prédicat
     `exprime(plant_class) -> bool`, ou un nom d'attribut d'espèce), data-driven, une
     seule source.
   - « Exprimé » = au moins un LECTEUR du gène agit pour cette espèce. Établir la
     liste **lecteur par lecteur au code** (grep du nom de gène), pas de mémoire.
     Cas attendus à confirmer : `nectar`/`taille_fleur`/`guide_nectar` (fleurs à
     insectes seulement — `poids_floral`), `pollen` (toute plante qui fleurit),
     `parfum` (vérifier : il est aussi lu par l'herbivorie pour toutes ?),
     `limite_froid` (espèces à `t_froid_lesion` non None), `rusticite_froid` /
     `limite_chaud` (toutes), `coriacite_feuille` (toutes), `fixation_azote`
     (fixatrices), `allelopathie` (espèces à exsudat), `mycorhization` (espèces
     mycorhizées).
   - Le gène reste porté, hérité, muté : seul le COÛT disparaît.
3. Tests : un test ciblé (nouveau `tests/test_genes_muets.py` ou extension de
   `tests/test_caracteres.py`) — anémophile à nectar élevé = coût 1,0 ; entomophile
   au même nectar = coût < 1 ; non-fixatrice à `fixation_azote` élevée = 1,0.

## Golden
**RE-FIGÉ annoncé** (`tests/golden_hash.txt`, et `population_hash.txt` s'il bouge) :
le coût baisse chez les espèces qui portaient des gènes muets au-dessus du neutre, et
le pâturin peut lever dans le smoke. Noter la 1ʳᵉ divergence et vérifier qu'elle vient
bien de A ou B (neutraliser l'un puis l'autre).

## Ne PAS faire
- Toucher au trèfle (hors sujet, D140 D).
- Rendre un caractère gratuit pour une espèce qui l'exprime.
- Changer les valeurs de `cout`, `sigma_a`, `K_FLEUR`, `K_THERMO`.

## F5
Aucun (pure mécanique, lisible au survol G existant).
