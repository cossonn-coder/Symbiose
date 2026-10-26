# Sprint FLUIDITÉ PC (D116 + lisière D112 c/j) — carnet de conception

> Phase : **A — challenge en cours** (`/conception D116`, ouverte le 2026-10-26).
> Rien n'est figé. Sprint précédent : `sprints/perf/fluidite/sprint_fluidite_an2/00_etat.md`
> (golden `fecccded…`, pont 0.5.57). Mesures PC de référence : `DETTE.md` D116.

## Cible (Nico, 2026-10-26)
PC (i5-4200H, 2 cœurs / 4 threads, HD 4600), an 2, 1 s/sem demandée → **≤ 2 s/sem effectives**,
**aucune image > 100 ms**, automate compris. Aujourd'hui : 3,33-3,75 s/sem, 105-108 images
> 100 ms sur 271-310 [n=3 runs, PC].

## Constats de la phase A (vérifiés au code / mesurés sur VM le 2026-10-26)
1. **« Non attribué » contient le rendu CPU** : `PerfPostes.TotalMs()` ne compte que les postes
   C# ; le rendu CPU (27-34 ms/image) n'y est pas (`WorldView.PerfMesure.cs:157-159`). Ancien
   rapport PC moteur AU REPOS (perf_vue, 2026-07) : non attribué 30,6 ≈ rendu CPU 28,7 ms
   [n=1 run, PC]. Le vrai inexpliqué D116 ≈ 70-81 − 27-34 ≈ **40-50 ms/image**, et il
   n'apparaît qu'avec le moteur en marche → contention présumée (toujours NON mesurée).
2. **« butineurs _Draw » 5-7 ms/image avec 0 butineur** : en hiver `ForagerLayer` et
   `PollenLot` sortent en tête de fonction (aucune entrée, pollen vidé à la saison) → une
   fonction quasi vide chronométrée à plusieurs ms = fil principal **déchedulé pendant la
   mesure** (2ᵉ indice de contention). L'invalidation par image (8-10 appels/s) reste à
   trouver mais coûte ~0 en soi.
3. **Moteur PC 1,7× plus lent que la VM headless**, alors qu'en juillet le PC était ~1,3×
   plus RAPIDE (headless) → le tick au PC est mesuré SOUS la charge de Godot ; vitesse PC
   moteur seul **inconnue**.
4. Profil tick s98 (VM, cProfile ×3 ticks, 637 pl.) : tick_light 21 % · tick_populations 14 %
   · _apply_uptake 9 % · apply_disturbances 7 % · grow_plant 6 % · _update_physiology 5 %
   · succession 4 % · décomposition 4 % [n=1 run, cProfile gonfle le Python pur].
5. **Pont, mesure delta (s96-102, VM)** : 0 % de plantes identiques d'une semaine à l'autre ;
   segments = 70 % des octets plantes (plantes = 56 % de la réponse 2,3 Mo). Dans ~99 % des
   segments le SEUL champ qui bouge est `age_weeks` (+1/sem) ; `length_cm` bouge dans ~24 %
   des segments, `genes` (9 % des octets plantes) ne bouge jamais. Un « diff par plante » est
   donc inutile ; un diff par segment exigerait `age_weeks` → semaine de naissance.
6. **Lisière** (capture VM ×0,5, graine 1521550718 = prairie N / prairie E / friche S /
   forêt O) : masse sombre de forêt sur une partie du bord O seulement, aplats verts rayés
   ailleurs, aucune rivière ni falaise (falaise 2,7 % des terrains). Au démarrage :
   `Build(Seed)` (`WorldView.cs:311`) puis `ApplySnapshot` → `SetCeinture` (`Snapshot.cs:137`)
   → la ceinture DOIT arriver ; le besoin de F10 n'est pas expliqué à la lecture.
7. HUD : « pont 0.5.30 — 2026-07-18 » affiché alors que le pont est 0.5.57 (étiquette figée).

8. Captures ×2 (bords O et S) : grands aplats unis (la « forêt » O = polygone sombre sans
   arbre en lisière), **coutures en fils fins** entre triangles, aucune texture ; friche =
   quelques points de fleurs + bouleaux. Le monde est déjà rendu dans un SubViewport 960×540
   (pixellisé ×2) : le défaut est le DESSIN (aplats, coutures), pas l'absence de pixellisation.
9. LDC : `DecorLayer.cs` 298 code (512 total) → plein ; tout motif neuf va dans un partial neuf.

## Décisions arrêtées (Nico, 2026-10-26)
- **Méthode : diagnostic PC d'abord.** Ce sprint instrumente (un seul F5 = rapport en 3 phases :
  normal / rendu suspendu pendant les steps / moteur en pause) et corrige les instruments ; les
  LEVIERS (moteur, vue) se conçoivent dans une 2ᵉ `/conception` sur les chiffres PC.
- **F10 = bug d'affichage** (au démarrage le décor est faux, F10 ×2 le remet) — à reproduire.
- **Lisière refaite en DA SNES** (pas seulement corrigée) dans ce sprint.
- Q3 (cadence vs images si les deux ne tiennent pas) : REPORTÉE à la 2ᵉ conception (chiffres).

- **DA lisière (Nico)** : niveau de détail des zooms ×1 / ×0,5, **assets en patchwork** (kit de
  pièces pixel-art précuites, assemblées au hash) ; pas d'ombre de lisière sur le jardin.

## Carte des tronçons (FIGÉE 2026-10-26)
| # | Kickoff | Contenu | Golden | État |
|---|---|---|---|---|
| ① | `01_instruments_banc3.md` | banc E 3 phases (normal / rendu suspendu / moteur en pause) + ménage instruments + PollenLot + oracles périmés | intact | à faire |
| ② | `02_lisiere_bug_coutures.md` | bug « il faut F10 » reproduit/corrigé + coutures | intact | à faire |
| ③ | `03_lisiere_kit_foret.md` | atlas patchwork + prairie/friche + forêt | intact | à faire |
| ④ | `04_lisiere_eau_roche_bilan.md` | rivière + falaise + bilan VM + protocole PC (1 run) + clôture | intact | à faire |

## §REPRISE
Conception FIGÉE → doc `docs/perf/fluidite/conception_fluidite_pc.md`. Exécution :
`/sprint-auto sprint_fluidite_pc` (tronçon suivant = le premier « à faire »). Après le sprint :
Nico fait 1 run PC → 2ᵉ `/conception D116` (leviers moteur/vue + arbitrage cadence ↔ images).
