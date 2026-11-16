# ③ Vraies unités et compromis

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, puis
> `docs/vegetal/genetique/conception_genetique_infinitesimale.md` §3 (table des valeurs),
> §6 et §7.
> Golden attendu : **RE-FIGÉ annoncé** — la germination et la phénologie lisent des
> décalages plus larges, et la hauteur dépend de la précocité.

## Objectif
Exprimer `germination_thermique` en °C et `phenologie_florale` en semaines d'avance, avec
des σ_A réalistes, et poser le compromis précocité ↔ taille. Mesurer que la sélection
répond.

## À faire
1. **`germination_thermique`** : unité °C (abaissement de l'optimum), neutre 0, σ_A 1.5.
   Lecteurs : `sim/succession.py` (≈ l. 96-108 `_germ_gene_mean`, ≈ l. 250). Aujourd'hui
   `GERM_GENE_SHIFT·(g−1)` (`fields/ecofields/constants.py:147`) : le lecteur prend
   directement la valeur en °C. Garder `GERM_GENE_SHIFT` défini (commentaire « obsolète
   depuis D139 »).
2. **`phenologie_florale`** : unité « semaines d'avance du tempo de vie », neutre 0. Elle
   pilote **trois horloges** (floraison `sim/engine/floraison.py` ≈ l. 60-83
   `FLORA_GENE_SHIFT` ; sénescence `sim/engine/mortalite.py` ≈ l. 81 `SEN_ONSET_JITTER` ;
   abscission/automne `sim/engine/decompo.py` ≈ l. 63), plus `sim/semiologie.py` ≈ l. 170
   (miroir exact de la sénescence) et `bancs/biotique.py` ≈ l. 203. Écrire **une** fonction
   de conversion partagée qui rend, pour chaque horloge, le décalage équivalent, et
   l'utiliser partout (le miroir sémiologie doit rester EXACT). Calibrer σ_A pour qu'un
   écart-type décale la floraison d'environ **une semaine** (mesure par un petit script).
3. **Compromis précocité ↔ taille** (§6) : `hauteur × (1 − K_PREC·avance)`, `K_PREC = 0.03`,
   borné, au point de calcul de la hauteur effective (`plants/base/familles.py` ≈ l. 435-442
   et l'équivalent ligneux `plants/perennials/base.py` ≈ l. 103 — vérifier).
4. **Greffe** : `sim/actions/greffe.py` liste des gènes aériens/racinaires ; vérifier que la
   greffe recopie correctement des valeurs en °C (pas de produit ni de moyenne qui suppose un
   neutre à 1).
5. **Banc headless « réponse à la sélection »** : script sous `mesures/` de ce sprint, seed 42.
   (a) Une parcelle froide, 10 ans : la moyenne de `germination_thermique` du pool dérive
   (attendu ≥ +1 °C [cible]). (b) Tomate (autogame) vs courgette (allogame), 6 générations :
   F moyen et variance entre frères. Consigner les chiffres dans `00_etat.md`. Si la réponse
   est nulle, **enquêter avant de clore** : un tronçon inerte n'est pas un succès.
6. **Re-figeage** : lire le diff du digest, puis `--capture`, et consigner les hashes.

## Tests
- Test ciblé : conversion phénologie cohérente entre les trois horloges et la sémiologie ;
  une avance de floraison réduit la hauteur ; la germination lit des °C.
- Suites : `test_genetique`, `test_greffe`, tests de floraison/sénescence/germination
  existants (adapter seulement ce qui figeait l'ancienne unité, en le disant).

## Ne PAS faire
- Changer les autres gènes (facteurs : ils restent des facteurs).
- Créer un nouveau gène de tempo (décision du sprint DÉSYNC PHÉNOLOGIE).
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`00_etat.md` : ③ FAIT, hashes, chiffres du banc. Commit.
