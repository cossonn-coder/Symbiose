# ② Constitution d'espèce + niche grêle

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + ce fichier. Prérequis :
> tronçon ① fait (`vitalite`, `etat`, `erode()` no-op via `getattr(...,1.0)`).
> Doc : `docs/vegetal/sante/conception_sante_resilience.md` §2. **AUCUN gène** —
> `GENE_NAMES` reste intact. Tout est data-driven par attribut de classe.

## Objectif

1. **Activer la constitution d'espèce** : poser un attribut de classe
   **`resilience_base: float`** COMPLET (une valeur explicite pour CHAQUE espèce
   du catalogue) → `erode()` (posé au ①) divise enfin par une vraie valeur ≠ 1.0.
2. **Compléter la couche niche** : brancher **`hail_resistance_base`** sur le
   dégât de grêle (aujourd'hui médié par RIEN, `gene_name=None`).

## Partie A — `resilience_base` (constitution, couche 2)

Modèle : « quand un coup PASSE, à quel point je plie vs je casse ? ». Tampon de
magnitude générique EN AVAL, à `erode()`. **Orthogonal à la niche** (susceptibilité
à la source). CSR fast-fragile / slow-tough.

### Où le poser (patron `fungal_susceptibility`)

- **Défaut PlantBase** : `plants/base/familles.py` (~ligne 81, à côté de
  `fungal_susceptibility: float = 0.5`) → `resilience_base: float = 1.0`.
- **Bases de FAMILLE** : les classes de famille de `familles.py` (~302-477) et/ou
  les espèces de `plants/species/*.py` + `plants/perennials.py` overrident.
- **Table COMPLÈTE exigée (Nico)** : passe le catalogue en revue (les ~27 espèces)
  et donne à CHACUNE une valeur explicite selon la bande §2 du doc :

  | profil CSR | base | qui (indicatif — ajuste selon le catalogue réel) |
  |---|---|---|
  | coriaces (S) | **1.25** | sedum/orpin, ligneuses établies, pionnières rustiques (ortie, consoude, pissenlit), sauvages robustes |
  | intermédiaires | **1.0** | vivaces herbacées, aromatiques, compagnes, grimpantes établies |
  | fragiles (R) | **0.8** | tomate & Solanaceae, annuelles tendres, potagères exigeantes, semis délicats |

  Ne laisse AUCUNE espèce au défaut silencieux : soit elle hérite d'une base de
  famille explicite, soit tu poses sa valeur. Documente le choix CSR en commentaire
  pédagogique (Nico apprend l'écologie — cf. garde-fous).

### Vérifie le point de consommation

`erode()` (instance.py, ①) lit `getattr(self.plant_class, "resilience_base", 1.0)`.
Une fois l'attribut posé, plus de `getattr` défaut atteint pour les espèces du
catalogue → différenciation active. (Laisse le `getattr` : robustesse pour un
éventuel test qui fabrique une classe nue.)

## Partie B — `hail_resistance_base` (niche grêle, couche 1)

**Aujourd'hui** : `boucle.py:153` appelle `_mediated_damage(tile, eco, hail_sev,
"grêle (feuillage)", cause="grele")` SANS `gene_name` → dans `_mediated_damage`
(`mortalite.py:373`) `suscept = 1.0` (rien ne médie la grêle). On ajoute une
susceptibilité D'ESPÈCE (feuilles petites/coriaces résistent, grandes feuilles
tendres se déchirent).

1. **Attribut de classe** `hail_resistance_base: float = 1.0` (défaut PlantBase,
   à côté de `resilience_base`). Overrides : >1 = coriace (petites feuilles,
   graminées, aromatiques ligneuses), <1 = feuillage tendre exposé (courges,
   potagères à grandes feuilles). Quelques espèces suffisent — pas besoin d'une
   table exhaustive ici (contrairement à `resilience_base`), le défaut 1.0 est
   un comportement neutre acceptable pour la niche grêle.
2. **Brancher dans `_mediated_damage`** (`mortalite.py`) : ajoute un paramètre
   optionnel `species_base: str | None = None`. Quand `gene_name is None` ET
   `species_base` fourni : `suscept = 1.0 / getattr(p.plant_class, species_base,
   1.0)`. Le gel (`gene_name="rusticite_froid"`) est INCHANGÉ (garde sa branche
   `expressed_gene`). La grêle passe `species_base="hail_resistance_base"` depuis
   `boucle.py:153`.

⚠️ La constitution `resilience_base` s'applique DÉJÀ en aval (via `erode()` dans la
résolution du `ReduceHealth` produit par `_mediated_damage`). La niche grêle
(`hail_resistance_base`) agit EN AMONT sur la sévérité. Les deux se composent
proprement (source × aval), c'est voulu — pas un double-compte.

## Golden — RE-FIGÉ #2 (annoncé)

Dérive attendue : les espèces du smoke (dont la constitution ≠ 1.0) encaissent
désormais différemment ; si la grêle frappe des semis au smoke, la niche grêle
module aussi. **Prouve la localisation** : la dérive doit se cantonner aux plantes
qui SUBISSENT un dégât ; neutraliser (forcer `resilience_base=1.0` +
`hail_resistance_base=1.0` partout) doit **retomber sur le hash du ①**. Si une
plante jamais blessée dévie → BUG, corrige.

Re-fige le hash, mets à jour `00_etat.md` (§REPRISE + hash) et le message de commit.

## Ce qu'il NE faut PAS faire

- **Aucun gène** (ne touche pas `GENE_NAMES`/`ADAPTOGENIC_GENES`). resilience et
  hail sont des BASES D'ESPÈCE, pas des gènes.
- Ne pas toucher au canal campagnol (`root_herbivory`, tronçon ③) ni à la vue (④).
- Ne pas modifier la formule de convalescence (récupération = `vigueur`, inchangé).
- Ne pas lancer `test_epaisseur_500ans` (interdit — long/inutile).

## Vérif de sortie

`python3 main.py` sans crash ; `python3 -m tests.test_golden` vert (hash re-figé,
localisation prouvée) ; suites `tests/` vertes. `tools/compte_ldc.py` sur les
fichiers touchés (familles.py peut approcher la bande — signale si dépassement).
