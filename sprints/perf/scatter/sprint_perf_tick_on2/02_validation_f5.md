# Tronçon 02 — Validation perf + checklist F5

> Kickoff AUTOSUFFISANT. Tronçon de clôture d'un sprint 100 % perf (zéro delta
> visuel/protocole). Pas de rendu neuf : on **mesure** le gain et on **prépare la
> validation F5** de Nico (la règle « vue Godot toujours » prend ici la forme
> d'une validation F5, cf. `00_etat.md`).

## Objectif

1. **Quantifier** le gain du tronçon 01 sur le régime lourd.
2. **Confirmer** l'absence de régression (golden + suites lumière).
3. **Confirmer** qu'aucun rebuild C# n'est requis (le diff est 100 % Python).
4. **Poser la checklist F5** pour Nico dans `00_etat.md`.

## Étapes

1. **Mesure post-② (obligatoire)** :
   `python3 -m tools.profile_monde --week 104 --top 40`
   - Relever le **ms/tick absolu** et la position de `light_index.py:covering`
     dans la table cProfile (avant : ~40 % du tick / 1ᵉʳ hors LightField.compute ;
     attendu : nettement en baisse, idéalement hors top).
   - Consigner le chiffre dans `00_etat.md` (section « mesure »), face au chiffre
     de référence de l'audit (bloc 4 ticks à 595 plantes ≈ 20,5 s cProfile avant ②).

2. **Non-régression** (re-jouer, tous doivent passer / hash inchangé) :
   - `python3 -m tests.test_golden` → `24ec11e7…`
   - `python3 -m tests.test_scatter_lumiere_recue`
   - `python3 -m tests.test_scatter_lumiere_sol`
   - suites lumière/ombre présentes (`test_lod_ombre`, `test_ombre_maison`…).

3. **Sanity build C#** (le diff ne touche que `data/code/` Python → aucun `.cs`
   modifié) : vérifier `git diff --name-only` ne liste QUE des fichiers Python +
   ce dossier sprint + doc. Donc **pas** de `dotnet build` nécessaire ; le noter.

4. **Checklist F5 pour Nico** (à écrire dans `00_etat.md`, section « F5 à faire ») :
   - Lancer le F5 sur un monde grandi (an ~2, forte population) et **confirmer que
     le rendu est visuellement INCHANGÉ** (ombres au sol, lumière reçue par les
     plantes → couleurs/stades identiques). Le scatter étant bit-identique, aucune
     différence n'est attendue ; toute différence visible = bug à remonter.
   - Relever **FPS + tick client + tick serveur** au HUD perf (F4/rapport terrain)
     à forte population, et comparer au rapport de référence (an 2 : tick serveur
     ~8 s AVANT). Consigner le nouveau chiffre.

## Golden attendu

**INCHANGÉ** (`24ec11e7…`). Ce tronçon ne modifie pas le moteur (mesure + doc).

## Ce qu'il NE faut PAS faire

- NE PAS « optimiser encore » au-delà du tronçon 01 (le cap démographique est la
  dette D71, hors périmètre).
- NE PAS lancer `test_epaisseur_500ans` (long, inutile — cf. garde-fou projet).
- NE PAS tenter de lancer Godot / F5 depuis la VM (F5 = Nico, sur Windows).
