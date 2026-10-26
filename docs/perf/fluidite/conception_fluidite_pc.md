# Conception — FLUIDITÉ AU PC (D116) + LISIÈRE EN DA SNES (D112 c/j)

> Figée le 2026-10-26 (`/conception D116`, accord Nico : méthode, lisière, découpage).
> Sprint : `sprints/perf/fluidite/sprint_fluidite_pc/`. **Golden jamais re-figé** :
> `fecccded8cd146368623372919f4bdc6c61fb8bb997c75fdc59806f08dc3898b`. Pont de départ 0.5.57.
> Sprint précédent : `docs/perf/fluidite/conception_fluidite_an2.md`.

## 1. Cible et point de départ

**Cible (Nico, 2026-10-26)** : PC de Nico (i5-4200H, 2 cœurs / 4 threads, HD 4600), an 2,
1 s/sem demandée → **≤ 2 s/sem effectives, aucune image > 100 ms**, automate compris.
Aujourd'hui (banc E au PC, sem. 98-99, graine 1521550718, `full`) : 3,33-3,75 s/sem, 105-108
images > 100 ms sur 271-310 [n=3 runs, PC]. Détail des postes : `DETTE.md` D116.

## 2. Ce que la phase de challenge a établi

1. **« Non attribué » est mal étiqueté.** `PerfPostes.TotalMs()` ne somme que les postes C# ;
   le rendu CPU (27-34 ms/image au PC) n'y entre pas (`world/WorldView.PerfMesure.cs`, bloc
   `EcrireDistribution`). Rapport PC de juillet, moteur AU REPOS : non attribué 30,6 ms ≈
   rendu CPU 28,7 ms [n=1 run, PC]. Le vrai inexpliqué D116 ≈ **40-50 ms/image**, présent
   seulement moteur en marche.
2. **Indice de contention CPU n°1** : « butineurs _Draw » 5-7 ms/image (pics 42-80 ms) avec
   0 butineur, alors qu'en hiver `ForagerLayer._Draw` et `PollenLot._Draw` sortent en tête
   (aucune entrée, pollen vidé à la saison). Une fonction quasi vide qui dure des ms = fil
   principal déchedulé pendant la mesure.
3. **Indice n°2** : moteur 1,7× PLUS LENT au PC que la VM headless, alors qu'en juillet le PC
   (headless) était ~1,3× plus RAPIDE. Le tick PC n'a jamais été mesuré sans Godot à côté.
   📖 Sur 2 cœurs hyperthreadés, deux fils sur les deux moitiés d'un même cœur partagent ses
   unités de calcul : chacun peut ralentir ~1,5×. Si c'est la cause, alléger la vue accélère
   le moteur et réciproquement — les leviers ne sont pas les mêmes que si le moteur est lent.
4. **Pont : le diff par plante est inutile** (s96-102, VM) : 0 % de plantes identiques d'une
   semaine à l'autre. Dans ~99 % des segments le seul champ qui bouge est `age_weeks` (+1/sem) ;
   `length_cm` bouge dans ~24 % des segments ; `genes` (9 % des octets plantes) ne bouge
   jamais. Piste gardée pour la 2ᵉ conception (âge → semaine de naissance + diff par segment),
   gain ≤ ~30 % de la réponse, complexité réelle.
5. Profil tick s98 (VM, cProfile 3 ticks, 637 pl.) : tick_light 21 % · tick_populations 14 % ·
   _apply_uptake 9 % · apply_disturbances 7 % · grow_plant 6 % · _update_physiology 5 %
   [n=1 run, cProfile gonfle le Python pur]. Matière pour la 2ᵉ conception.
6. **Lisière** (captures VM ×0,5 et ×2, graine 1521550718 : prairie N, prairie E, friche S,
   forêt O) : grands aplats unis (la forêt O = polygone sombre sans arbre en lisière),
   **coutures en fils fins** entre triangles, aucune texture ; friche = quelques points de
   fleurs. Le monde est déjà pixellisé (SubViewport 960×540) : c'est le DESSIN qui manque.
7. Bug F10 : au démarrage `Build(Seed)` (`WorldView.cs`, construction du monde) puis
   `ApplySnapshot` → `ApplyCeinture` → `SetCeinture` → `Build` : la ceinture arrive bien à la
   lecture du code. Cause non trouvée sans reproduction.

## 3. Décisions (Nico, 2026-10-26)

- **Diagnostic PC d'abord.** Ce sprint ne pose AUCUN levier moteur/vue de cadence : il
  instrumente pour qu'**un seul F5** produise un rapport en **3 phases** — A normal, B rendu
  suspendu pendant les steps (= moteur sans Godot qui dessine), C moteur en pause (= vue
  seule). A↔B mesure ce que Godot coûte au moteur ; A↔C ce que le moteur coûte aux images.
  Les leviers se conçoivent dans une **2ᵉ `/conception D116`** sur ces chiffres.
- **Arbitrage cadence ↔ images** (si les deux ne tiennent pas ensemble sur 2 cœurs) :
  **reporté** à la 2ᵉ conception, faute de chiffres.
- **F10 = bug d'affichage** : au démarrage le décor est faux, F10 ×2 le remet.
- **Lisière refaite en DA SNES**, pas seulement corrigée. Référence de niveau de détail
  (Nico) : **celui des zooms ×1 / ×0,5**, avec des **assets en patchwork qui rendent bien** —
  un kit de petites pièces pixel-art précuites (touffes d'herbe, bosquets, houppiers, rochers,
  strates, eau), assemblées et variées au hash, au lieu de polygones peints.
- L'ombre de la lisière sur le jardin (déjà calculée par le moteur) n'est PAS rendue ici.

## 4. Lisière — principes de rendu

- **Patchwork** : un atlas de pièces générées UNE fois (procédural déterministe, hash, zéro
  Random — philo #3), peintes en NIVEAUX de rampe puis teintées, même langage que le kit des
  plantes (`visuals/PlantRenderer.Kit.cs` : 0 vide · 1 contour · 2 ombre · 3 base ·
  4 lumière). Variantes par hash, teinte par motif et par saison si simple.
- **Densité** : aucune zone unie visible à ×0,5 / ×1 ; le bord du jardin reçoit des pièces
  (ourlet), le fond peut être plus calme mais tramé. Densité/hauteur pilotées par la ceinture
  du pont comme aujourd'hui (`DecorLayer.Pont.cs` : clairière, coupe, ligne d'eau, entaille).
- **Coût** : le décor reste INERTE (redessin seulement au build, au changement de LOD, à la
  réception de la ceinture, à la rotation). Draw calls du décor ≤ aujourd'hui (pièces d'un même
  atlas = lot). Mesuré au banc VM.
- **Animation** = signal seulement (DA) : scintillement de l'eau admis, rien d'autre.
- **Taille** : `DecorLayer.cs` est plein (298 LDC) → atlas et motifs dans des partials neufs.

## 5. Découpage

| # | Kickoff | Contenu | Golden |
|---|---|---|---|
| ① | `01_instruments_banc3.md` | rapport 3 phases + ménage des instruments + oracles périmés | intact |
| ② | `02_lisiere_bug_coutures.md` | bug F10 reproduit et corrigé, coutures | intact |
| ③ | `03_lisiere_kit_foret.md` | atlas patchwork + prairie/friche + forêt | intact |
| ④ | `04_lisiere_eau_roche_bilan.md` | rivière + falaise + bilan VM + protocole PC (1 run) | intact |

Après le sprint : Nico fait 1 run F5 (protocole du ④) → 2ᵉ `/conception D116` (leviers).
