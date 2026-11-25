# 2026-11-25 — Sprint PRÉCUISSON EN SPLATS (a, plantes) CLOS côté code

Sprint `sprints/rendu/splatting/sprint_precuisson_splats/` (conception
`docs/rendu/splatting/conception_precuisson_splats.md`), exécuté par `/sprint-auto`.
Golden `bce813af…` **intact à tous les tronçons** (vue + outillage, `data/code/` jamais
touché). Détail et mesures : `00_etat.md` du sprint.

**Tronçons.**
- ① atelier `tools/splat/` (ink-studio copié, JS sur la VM) : porte passée avec réserves,
  8 lacets × 3 inclinaisons, cuisson déterministe à l'octet (`6f36269`).
- ② 18 recettes de feuilles + touffes du kit + trous D5 (`adb5ea3`).
- ③ têtes, fleurs, fruits, épis, boutons ; **bois non livré** (couture visible) (`9ec00c0`).
- ④/④bis vue ×4 → ×32 : feuilles et organes en pièces splat (`aba3663`, `d6bf80f`).
- ⑤/⑤bis vue ×0,5 → ×2 : prémisse réfutée (le kit ne sert qu'aux plantes sans fiche),
  effet réel = ports des herbacées, prairie et lianes en pièces (`03e694d`, `ec958ca`).
- ⑥ 156 portraits (52 espèces × jeune/mûre/fin, 240×240, manifeste) ; correctif feuille
  de 0 cm qui faisait boucler ink (framboisier, myrtille) ; ~18 min en 10 processus
  [VM, charge 3→15] ; 1,1 Mo (`f18f5cb`).
- ⑦ portraits dans l'encyclopédie (niveau 1 = jeune, 2 = + mûre, 3 = les trois) et le
  magazine (mûr) ; `GD.Load` sur textures importées (compatible export) ; manifeste
  enrichi de la clé moteur (`tomate` ≠ `Tomato`) ; banc `capture_vm.sh -Z` (`b25fe41`).

**Incident.** La session du 2026-11-20 s'est coupée pendant le ⑥ : ①→⑤bis étaient
commités mais **jamais poussés** — Nico ne recevait rien au `git pull`. Poussés le
2026-11-25 au matin.

**Retour F5 partiel de Nico (2026-11-25).** « Les splats sont beaux, globalement
positif. » Mais à ×32 les splats disparaissent (piste : plante trop grande pour être
précuite → dessin direct sans pièces, cf. `backlog_splatting.md`) ; trèfle encore
dessiné (reliquat ④bis connu) ; écran de chargement devenu laid → point (g) du
programme (logo splat de la symbiose + barre de chargement). **F5 complet différé** à
l'homogénéité du style sur tout le jeu ; Claude fournira alors la checklist exhaustive.

**Suite.** Programme D7 : (b) décor de lisière à concevoir, + reliquats de (a) et (g).
