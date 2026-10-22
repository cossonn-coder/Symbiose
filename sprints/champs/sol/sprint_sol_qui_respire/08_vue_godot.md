# ⑧ Vue Godot — bois mort, carpophores par espèce, manger, vision + re-mesure finale

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §6, `DETTE.md` D112 (a).
**Golden** : INTACT (C# + éventuels champs de pont déjà ajoutés). Build : `dotnet build
Symbiose.csproj` (le F5 est à Nico). Captures VM possibles via le banc Xvfb du sprint
JARDIN VIVANT (`world/WorldView.Capture.cs`, scripts `mesures/` des sprints rendu).

## Objectif
1. **Bois mort au sol** visible (masse + âge de bois exposés au ②) : sprite de branche à
   stades de décomposition (fraîche → grise → moussue → fragments), orientation par hash
   du plot. Patron `visuals/LitterLayer.cs` / `LeafLitterLayer.cs`.
2. **Carpophores par espèce** (`visuals/CarpophoreLayer.cs`) : silhouette/couleur propre
   à chaque espèce (DA SNES mignon, palette du projet). D112 (a) dit qu'ils ne sont
   « jamais dessinés » : diagnostiquer d'abord (absence de données en jeu normal avant ③,
   ou bug de rendu ?) et consigner. Absorbe la part carpophores de D112 (a) ; la part
   faune reste à D112.
3. **Info-bulle** : nom d'espèce / comestibilité selon le palier (⑤).
4. **Manger** un carpophore depuis la palette (verbe `manger` ciblé carpophore, ⑥).
5. **Vision** : couleurs plus vives (saturation/lumière, sans casser la palette F11),
   info-bulle qui parle (commande ⑥ au survol), overdose (phrases sur tous les êtres
   visibles, sans s'effondrer en FPS — mesurer), compteur de survol pour « ce qui reste »
   si le pont l'attend côté vue.
6. **Re-mesure finale D110 (g)(h)(i)** sur `full`, 3 graines : part de plantes en
   `acclimatation` et vitalité médiane (`mesure_sante.py` du sprint info-bulle), carpophores
   par an, nourriture des butineurs. Consigner dans `00_etat.md` + `DETTE.md` (fermer ou
   reformuler g/h/i).
- Points F5 pour Nico (liste courte, ressenti seulement) : bois mort lisible, carpophores
  reconnaissables, vision « trip » agréable. Rappeler : Vigueur infinie OFF pour sentir
  les champignons vénéneux.

## Ne PAS faire
Pas de logique écologique en C# (Python = vérité). Pas de faune dessinée (reste D112).
