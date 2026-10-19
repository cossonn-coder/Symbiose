# ⑦ Vue : info-bulle à deux niveaux + affichage technique + bilan + procédure PC — kickoff autosuffisant

## Lire d'abord
`CLAUDE.md` · `00_etat.md` · `docs/rendu/pixelart/conception_plante_assemblee.md` §3-§4.4 ·
résultats consignés par ①-⑥ dans `00_etat.md`.

## Objectif
1. **Info-bulle au survol** (plantes ET bêtes), par défaut, diégétique et sans chiffre :
   - plante : nom (comportement d'étiquette actuel) + le **signe dominant visible au palier courant**
     décrit par son `vu` ; si le signe est **appris** (`appris.signes` du snapshot, ⑥) : + sa cause
     en mots ;
   - bête (vie macro / butineurs / carpophores) : `vu` descriptif ; son nom si **appris**.
   Réutiliser le picking existant (`FindPlant(_sourisMonde, HoverRadiusCm)` — `WorldView.Genes.cs`,
   `Etiquettes.cs`, `Observation.cs`, et le picking vie macro de `Observation.cs`), la clé de survol
   (`_survolSale`), le CanvasLayer `Hud`. Pas un 4ᵉ système de survol parallèle.
   « Visible au palier » : signes foliaires fins dès ×16 (`PlantRenderer.PaliersHauts.cs`), teinte de
   santé dès ×2 ; vie macro dès son palier d'apparition (taille réelle).
2. **Observation** : au survol d'une plante portant un signe visible, envoyer l'observation du signe
   au pont (⑥), dédup côté vue comme `_especesObservees`.
3. **Affichage technique** : une touche (libre, vérifiée au code ; ajoutée à la légende F1) qui
   bascule l'info-bulle en mode technique : cause brute + intensité (`leaf_symptoms`), espèce animale
   (clé) — étiqueté « affichage technique — déconseillé en première découverte », comme F6.
4. **Bilan perf** final VM (×4 nominal, ×2, ×1, ×0,5, accéléré ×8) contre le départ (2 013 draw
   calls ×4) dans `00_etat.md`.
5. **Procédure PC pour Nico** (seul point F5 de mesure) dans `00_etat.md` : `git pull`, F5, full →
   touche **E** (banc ×4) puis la touche du **banc accéléré** (③), coller les deux rapports.
   Critères : 60 FPS à ×4 ; aucune image > 100 ms en accéléré. Raté → dette chiffrée (pas de boucle).
6. **F5 ressenti** (3 questions max) : paliers bas encore horribles ? l'info-bulle aide-t-elle à
   savoir ce qu'on regarde ? accéléré agréable ?

## Vérifications
Captures VM avec souris (`tools/capture_vm.sh -s X,Y`) sur : une plante à signe à ×16 (descriptif),
la même après `cmd_debug palier3` (cause nommée), une bête à ×4, mode technique. `dotnet build` vert ;
golden `22768f33…` ; LDC (`Hud.cs`, `Observation.cs`, `Genes.cs` ≤ 300).

## Clôture du sprint (après ce tronçon)
`DETTE.md` (D109 d/e/f → fermées ou reliquats chiffrés ; nouvelle dette seulement si une autre se
ferme), `BACKLOG.md`, `journal/` + `journal.md`, mémoire projet ; `/refactor` auto-léger.

## NE PAS
Afficher des chiffres hors mode technique (philo #5) · nommer une cause non apprise en mode défaut ·
toucher au moteur · lancer `test_epaisseur_500ans`.

## Golden
Intact.
