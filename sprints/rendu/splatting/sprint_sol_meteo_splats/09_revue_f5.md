# ⑨ Revue des paliers, liste F5 de la famille (e), clôture — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md` (①→⑧), conception, la section « F5 EXHAUSTIF » de
`sprints/rendu/splatting/sprint_lisiere_chargement/00_etat.md` (format à suivre).
Golden attendu : **`bce813af…` INTACT**. Build vert, 0 avertissement.

## Objectif
Tronçon vue final : revue « beau à chaque palier » du sol et de la météo, finitions sans recette neuve,
puis la **liste F5 de la famille (e)** à ajouter à la liste exhaustive S1-S3 (le F5 complet de Nico reste
différé jusqu'à l'homogénéité des familles c-f, mémoire `feedback_f5_splats_differe`).

## À faire
1. Planches ×0,5 → ×32 avant (`SYMBIOSE_SPLATS=0`) / après, monde `full` : 4 saisons, neige, pluie,
   orage, sécheresse, automne, paillis, mare, rotation D35 ; + la capture ×64 du ⑧.
2. Mémoire, draw calls, ms par image par palier [VM, non transposable] ; **consignes du rapport C au PC**
   (seuils : pas sous 21 FPS à ×4, pas au-dessus de 143 draw calls, référence du 2026-11-26).
3. Liste F5 (e) dans `00_etat.md`, chaque point observable en une phrase (« à ×16, … doit … »).
4. Clôture : entrée `journal/` + `journal.md` ; `docs/rendu/splatting/backlog_splatting.md` (famille (e)
   CLOSE côté code, POC ×64 fait, prochain = familles c, d, f) ; `BACKLOG.md` ; `DETTE.md` seulement si
   on en ferme une ; `/refactor` auto-léger.

## Ne PAS faire
Recettes neuves (les signaler). `data/code/`, `test_epaisseur_500ans`, DeepSeek.

## Fin
`00_etat.md` §REPRISE → « famille (e) CLOSE côté code ; prochain = conception (c), (d) ou (f) ». Commit.
