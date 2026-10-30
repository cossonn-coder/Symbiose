## 2026-10-30 — Sprint MARE VIVANTE (D121) — CLOS côté code (①→③)

Conçu en conversation au F5 de SOL NOURRICIER (Nico : « oui pour tes recommandations et
en hiver la mare est couverte de glace »), puis enchaîné en sous-agents. Golden
**`4c696821…` jamais re-figé**, pont 0.6.1 → **0.6.2**, `dotnet build` vert. État et
mesures : `sprints/champs/eau/sprint_mare_vivante/00_etat.md`.

- ① moteur + pont : `eco.glace` [0,1] (`fields/ecofields/glace.py`, sans effet en retour) ;
  bloc `marais` = `[r, c, marais, etat, lame, glace]` ; une bête ne nomme proie/prédateur
  que s'il est PEINT (même seuil que `perception`) ; coquille « La libellule ». Mare prise
  2-14 sem./an [seeds 1/2/42, n=3], centre jamais à sec ; bords découverts toute l'année.
  **Écarts** : seuils de gel recalés (climat doux, la mare ne gelait jamais) ; la glace
  tombe en semaines 3-11 que le calendrier appelle « printemps » (calendrier à trancher).
- ② `visuals/eau_mare.gdshader` + `PuddleLayer.Eau.cs` : eau tramée 3 tons, marnage
  continu eau → vase luisante → vase, scintillement lent visible dès ×1, glace tramée
  avec fêlures ; un draw call. Captures VM regardées (orchestrateur compris).
- ③ signaux dans le shader : rides au vent (perpendiculaires au vent MONDE projeté),
  ronds de pluie, ronds de gobage ; rien sous la glace. Nuée de moustiques dès ×4
  (`NueeMoustiques.cs`), libellule à taille plancher. 15 captures regardées.
- Taille : aucun fichier > 400 ; `serialize.py` 393 et `MacroLife.cs` 311 en vigilance.
- Attend le **F5 de Nico** (9 points, `00_etat.md` §Points F5).
