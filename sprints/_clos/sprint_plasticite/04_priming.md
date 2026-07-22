# Tronçon ④ — Priming transgénérationnel

> Sprint « plasticité ». Conception : `docs/vegetal/genetique/conception_plasticite_expression.md`
> (§2.5, §3-P2). **Lire la conception + relire le journal `00_etat.md` des ①②③.**
> **Re-figeage golden MAÎTRISÉ et annoncé** (les enfants naissent pré-armés).

## Objectif
La mère transmet son ÉTAT D'EXPRESSION (pas son génotype) à ses graines : une
lignée éprouvée naît pré-alertée. **Oubli émergent** (aucun compteur) : si le
stress cesse, l'expression retombe seule sur 2-3 générations.

## Périmètre
- `sim/reproduction.py:108` — `child_genes(mother, father, …)`. Le génotype est
  déjà géré ici (moyenne parents + mutation, ne PAS y toucher).
- Transmettre l'expression initiale de l'enfant **depuis la mère seule** :
  ```
  child.expression[g] = 1.0 + PRIMING_FRAC × (mother.expression[g] − 1.0)
  ```
  pour chaque `g` ∈ `ADAPTOGENIC_GENES`. `PRIMING_FRAC` = knob (~0.3–0.5, P2).
- Repérer le SITE exact où l'enfant `PlantInstance` est construit (suite à
  `child_genes`) pour y injecter `expression` initiale — soit dans `reproduction.py`,
  soit là où la graine devient plante (vérifier la chaîne graine→germination,
  `sim/seeds.py` / `fields/seedbank.py`). L'expression doit voyager avec la GRAINE
  si la germination est différée (sinon le priming est perdu). **Décision à acter
  dans le journal** : porté par la graine (banque) ou recalculé à la germination.
- **Aucun mécanisme d'oubli explicite** (P2 acté) : ne RIEN ajouter pour la
  décroissance générationnelle. L'oubli émerge de la désacclimatation (③/①) + de
  `PRIMING_FRAC < 1`.

## Vérifs
- `python3 -m tests.test_golden` → hash possiblement changé SI le smoke produit
  des graines de mères acclimatées. Si le scénario 2 tuiles × 4 ans ne déclenche
  pas de reproduction sous stress, le hash **peut** rester neutre → vérifier et
  annoncer le cas réel.
- Test d'unité : mère à expression 1.25 + `PRIMING_FRAC=0.4` → enfant à 1.10 ;
  mère neutre → enfant neutre ; sans stress sur l'enfant, son expression retombe
  vers 1.0 (oubli émergent) sur quelques ticks/générations.
- `dotnet build` vert.

## Sortie
MAJ `00_etat.md` (statut ④ clos, hash + justification, décision graine/germination,
journal). Commit. `/clear` avant `05_signe.md`.
