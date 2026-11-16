# ① Registre des caractères — refactor pur

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, puis
> `docs/vegetal/genetique/conception_genetique_infinitesimale.md` §3 (en entier).
> Golden attendu : **INTACT** (`b4a921f8…`).

## Objectif
Poser la table qui déclare chaque caractère génétique (unité, neutre, σ_A, bornes,
adaptogène), sans changer **aucune** valeur ni aucun comportement. C'est le socle des
tronçons ② et ③ et des sprints ② et ③.

## À faire
1. **Registre** dans la couche `plants` (`plants/genetics.py` aujourd'hui 28 LDC ; un module
   voisin `plants/caracteres.py` si c'est plus lisible). Une entrée par nom de `GENE_NAMES`,
   **dans le même ordre**. Valeurs de ce tronçon : unité `facteur`, neutre 1.0, σ_A 0.10,
   bornes [GENE_HARD_MIN, GENE_HARD_MAX] = celles d'aujourd'hui. `GENE_NAMES` reste
   exporté, dérivé du registre, pour que les appelants (`fields/seedbank.py`,
   `sim/reproduction.py`, `sim/actions/greffe.py`, `sim/seeds.py`, `sim/semiologie.py`,
   `bancs/climatique.py`) ne bougent pas.
2. **Surcharge par espèce** : attribut de classe optionnel `genetique = {nom: {champ: val}}`
   sur `PlantBase` (`plants/base/familles.py`), défaut `{}`. Un helper unique renvoie le
   neutre et le σ_A effectifs d'un caractère pour une classe.
3. **`PlantInstance.gene(name)`** (`plants/base/instance.py`) renvoie le **neutre** du
   caractère pour la classe de la plante quand le gène est absent (aujourd'hui 1.0 en dur ;
   identique tant que tous les neutres valent 1.0).
4. **Bornes par caractère** : `clamp_gene(x)` reste disponible ; ajouter une borne par
   caractère (`borne(nom, x)`) et l'utiliser là où le nom est connu. Valeurs identiques ici.
5. **`GeneStat`** (`fields/seedbank.py`) : la moyenne par défaut prend le neutre du caractère
   (identique ici).
6. Commentaires pédagogiques : expliquer la table (pourquoi une unité, pourquoi un σ_A par
   espèce) au cœur du fichier.

## Tests
- Test ciblé neuf : chaque nom de `GENE_NAMES` a une entrée ; l'ordre est stable ;
  `gene()` d'un gène absent = neutre ; une surcharge d'espèce est lue.
- `python3 -m tests.test_golden` → hash identique. Suites vertes : `tests.test_genetique`,
  `tests.test_plasticite`, `tests.test_diversite_fondatrice`, `tests.test_greffe`.

## Ne PAS faire
- Changer une valeur, un σ, une formule d'hérédité (c'est le ②).
- Renommer un gène. Réordonner `GENE_NAMES`.
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.
- Pas d'appel DeepSeek de routine (protocole `docs/meta/agent/deepseek_protocol.md`).

## Fin de tronçon
`00_etat.md` : ① FAIT, golden intact. Commit.
