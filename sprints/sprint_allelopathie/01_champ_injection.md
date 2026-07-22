# ① Champ `allelopathie` + injection + décroissance

> Kickoff autosuffisant. Reprise à froid = lire `CLAUDE.md` + `00_etat.md` +
> ce fichier + `docs/vegetal/allelopathie/conception_allelopathie.md` §A. Aval :
> `/sprint-auto`. Golden **NEUTRE visé**.

## Objectif

Poser le **champ de sol `allelopathie`** (concentration d'allélochimiques par plot),
son **injection** par les émetteurs (empreinte racinaire) et sa **décroissance
labile modulée par le microbiome**. À ce tronçon, **rien ne LIT le champ** → aucune
lecture germination/croissance : golden strictement neutre.

## Fichiers à toucher

- `fields/ecofields/container.py` — déclarer le `GridField` `allelopathie`
  (`max_val` ≈ 3.0 comme n/p/k, `initial=0.0`). ⚠️ fichier déjà proche du seuil
  taille : ajout minimal, ne pas gonfler ; scinder seulement si vraiment requis.
- `fields/ecofields/sol.py` (ou le module de tick des champs de sol) — ajouter la
  **décroissance** au tick : `allelopathie[r,c] *= (1 − DECAY_BASE − DECAY_MICROBE ·
  microbiome[r,c])`, borné ≥ 0, snap à 0 sous un plancher (ex. 1e-4).
- `plants/base/familles.py` — **routeur d'effets** : permettre `inject_field
  variable="allelopathie"` (préférence : réutiliser le levier `inject_field`
  existant plutôt que créer une action neuve — l'ortie fait déjà
  `inject_field variable="n" cible="local"`). Vérifier que `variable="allelopathie"`
  route bien vers le nouveau champ.
- `plants/base/` (traits d'espèce, là où vivent les traits `PlantBase`) — nouveau
  trait **`allelopathie_emission: float = 0.0`** (défaut non-émetteur). **Ne pas
  encore le renseigner** sur les espèces (c'est le §E / tronçon ⑤).

## Modèle / formules

- Injection : un émetteur dépose `amount = allelopathie_emission` (placeholder
  calibrage) dans `allelopathie` sur son **empreinte racinaire** (`cible="local"`,
  rayon racinaire déjà dérivé → **scatter borné**, jamais O(N²)). Réutiliser le
  chemin d'injection local de l'ortie comme patron.
- Décroissance (labile) : cf. formule ci-dessus. `DECAY_BASE` (perte spontanée) +
  `DECAY_MICROBE` (détox par sol vivant). Placeholders — calibrage post-test.
- Champ **UNIQUE** (D4) : une concentration agrégée par plot, PAS un dict par
  molécule. Auto-tolérance/sensibilité se gèrent à la **lecture** (tronçons ②/③),
  pas ici.

## Golden attendu

**NEUTRE.** Personne ne lit le champ ; aucune espèce n'a encore `allelopathie_emission
> 0` (trait posé, valeur défaut 0 partout). Lancer `python3 -m tests.test_golden`
depuis `data/code/` → hash **inchangé**. Si dérive : c'est un bug (injection qui
part alors qu'aucun émetteur n'est doté, ou tick qui touche un autre champ).

## Ce qu'il NE faut PAS faire

- Ne PAS lire `allelopathie` à la germination ni à la croissance (tronçons ②/③).
- Ne PAS renseigner `allelopathie_emission` sur les espèces (tronçon ⑤).
- Ne PAS créer un dict multi-molécules (champ unique, D4).
- Ne PAS toucher `soil_memory` (il ne trace pas l'espèce — l'autotoxicité est le ④).
- Ne PAS relever le seuil de taille de `container.py` : scinder si dépassement.
- Ne JAMAIS lancer `test_epaisseur_500ans`.

## Vérif

`python3 -m tests.test_golden` (golden neutre) + un petit test ad hoc facultatif :
injecter manuellement dans un plot, avancer N ticks, vérifier la décroissance
monotone vers 0 et l'accélération quand `microbiome` est haut.
