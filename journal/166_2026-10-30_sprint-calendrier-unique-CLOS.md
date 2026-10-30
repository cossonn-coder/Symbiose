## 2026-10-30 — Sprint CALENDRIER UNIQUE (D122) — CLOS côté code (①→④)

Ouvert au F5 de MARE VIVANTE (Nico : « les saisons sont pas bonnes » — glace au
printemps). Deux calendriers coexistaient : climat depuis le 1ᵉʳ janvier, étiquettes de
saison depuis l'équinoxe (~11 sem. d'écart). État et mesures :
`sprints/champs/climat/sprint_calendrier_unique/00_etat.md`.

- ① banc `bancs/mesure_calendrier.py` + photo « avant » (`mesures/avant.md`), golden intact.
- ② `data/code/calendrier.py` (racine, zéro import) = source unique, ré-exportée par
  `sim/engine/calendrier.py` ; climat décalé (`W_T_MIN = 45`, `W_SOLSTICE_ETE = 14`).
  Golden re-figé annoncé `4c696821…` → `a3dfbec3…` (plomberie vérifiée bit-identique).
- ③ recalibrage au mois réel (aléas, champignons, abscission 30-36, pivot 38 → 34) ;
  décision C5/C5bis : réveil THERMIQUE des ravageurs + sol nu sans habitat (la population
  suit l'hôte). Golden re-figé annoncé → `bfe6f889…`.
- ④ vue : audit C# — aucune phase « 1ᵉʳ janvier » en dur, tout lit le pont ; seul un
  commentaire recâblé. Code mort signalé (non supprimé) : `core/LightField.cs` +
  `core/EcoFields.cs`. Pont inchangé, `dotnet build` vert.
- Résultat [n=3 ans, VM] : T min en hiver, pommier fleurit fin avril, 1ʳᵉ abscission fin
  octobre, glace de mare en hiver. Points ouverts : butineurs absents l'an 1, gelée d'avril.
- Attend le **F5 de Nico** (protocole « une année », 6 points, `00_etat.md` §F5).
