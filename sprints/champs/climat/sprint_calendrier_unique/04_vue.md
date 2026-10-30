# ④ Vue Godot — cohérence saisonnière + protocole F5 — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (tableau final de ③),
`docs/champs/climat/conception_calendrier_unique.md`.

## Objectif

S'assurer que la vue ne porte aucune hypothèse de l'ancien calendrier, et donner à Nico
un protocole F5 court pour **ressentir** qu'une année tombe juste.

## À faire

1. **Audit C#** de tout ce qui dérive une saison ou une phase d'une semaine :
   `world/WorldView.Snapshot.cs` (`week_in_year` → `_weekInSeason`, `CurrentSeason`),
   `world/WorldView.Soleil.cs` (déclinaison par saison — doit rester identique à
   `fields/light.SOLAR_DECLINATION`, décision C4), `core/LightField.cs` (tables par
   saison : vérifier s'il est encore utilisé ; s'il est mort, le signaler sans le supprimer),
   et toute teinte/ambiance indexée sur la saison ou la semaine (`grep -rn "week\|saison\|Season"`
   dans `world/ visuals/ core/`). Corriger uniquement une hypothèse de phase
   « 1ᵉʳ janvier » écrite en dur ; le reste lit le pont et suit seul.
2. **Pont** : vérifier que `tools/simserver/serialize.py` exporte toujours `week_in_year`
   + la saison issue de `calendrier` (ré-export). Pas de bump de protocole sauf champ
   ajouté (aucun prévu).
3. `dotnet build Symbiose.csproj` vert.
4. **Protocole F5** (≤ 6 points, écrit dans `00_etat.md` §F5) : une partie neuve en
   rythme accéléré sur une année (`DebugSecondsPerWeek` ou l'option vitesse, remis au
   rythme design après) ; ce que Nico doit voir, par saison :
   - printemps : pas de glace sur la mare ; gelées tardives seulement en début de saison ;
     le pommier fleurit et des butineurs sont là en même temps ;
   - été : jours longs, sécheresse/orages possibles, pas de gel ;
   - automne : feuilles qui tombent, champignons qui sortent après la pluie ;
   - hiver : glace, neige, croissance ralentie.
   Ressenti seulement (mémoire F5 : le calibrage se valide par mesure, déjà fait en ③).
5. Mettre à jour `DETTE.md` (D122 → « code clos, en attente F5 »), `BACKLOG.md`,
   `journal.md` (entrée de clôture de sprint).

## Golden

**INTACT** (vue seule).

## NE PAS

- Changer une mécanique Python.
- Supprimer du code C# jugé mort (le signaler).
