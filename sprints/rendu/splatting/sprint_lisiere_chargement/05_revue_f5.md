# ⑤ Revue des paliers, liste F5 exhaustive S1+S2+S3, clôture — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md` (①→④), `docs/rendu/splatting/conception_lisiere_chargement.md`,
les sections « F5 consolidé » de `sprints/rendu/splatting/sprint_reliquats_plantes/00_etat.md` (S1)
et `sprints/rendu/splatting/sprint_bois_arbres/00_etat.md` (S2).
Golden attendu : **`bce813af…` INTACT**. Build vert, 0 avertissement.

## Objectif
Tronçon vue Godot final de la séquence « style homogène » : revue « beau à chaque palier » de la
lisière, finitions, puis la **liste exhaustive** que Nico jouera à son F5 complet (mémoire
`feedback_f5_splats_differe` : le F5 n'a lieu qu'une fois le style homogène partout).

## À faire
1. Planches ×0,5 → ×32 avant (`SYMBIOSE_SPLATS=0`) / après : les 4 motifs de lisière (prairie,
   forêt, rivière, falaise, friche), 4 saisons + neige, vent (`-v`), orientations D35 (`-r`),
   monde `full`. Finitions sans recette neuve (seuils, tri, fondus).
2. Mémoire de précuisson, draw calls, ms par image par palier [VM, n=1, non transposable].
3. **Liste F5 exhaustive** dans `00_etat.md` : reprend et fusionne S1 + S2 + S3 en une seule
   checklist ordonnée (chargement → jardin par palier → plantes → arbres → graminées → lisière →
   portraits/encyclopédie/magazine → interrupteur Maj+F11 → perf rapport C), chaque point
   observable en une phrase (« à ×32, … doit … »).
4. Clôture : entrée `journal/` + `journal.md` ; `docs/rendu/splatting/backlog_splatting.md` (S3 CLOS,
   séquence close, prochain = F5 complet de Nico puis proof of concept ×64) ; `BACKLOG.md` ;
   `DETTE.md` si un reste doit y aller (règle : pas de dette ouverte sans en fermer une) ;
   `/refactor` auto-léger.

## Ne PAS faire
- Recettes neuves (les signaler). `data/code/`, `test_epaisseur_500ans`, DeepSeek.

## Fin
`00_etat.md` §REPRISE → « séquence style homogène CLOSE côté code ; attend le F5 complet de Nico
(liste dans ce fichier) ». Commit.
