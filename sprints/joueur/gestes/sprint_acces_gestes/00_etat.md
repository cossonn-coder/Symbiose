# Sprint ACCÈS AUX GESTES — état

> Sprint ① de la refonte de l'accès aux gestes (3 sprints). Conception figée le
> 2026-11-12 : `docs/joueur/gestes/conception_refonte_palette.md` (à lire en entier).
> Suite : `sprint_palette_tiroir` puis `sprint_icones_curseur`.

## But
Rendre **tous** les gestes du moteur atteignables en jeu normal et jouables dans la
vue. Aujourd'hui 20 gestes gatés sur 32 ne s'ouvrent jamais (poule-œuf : la
technique n'est découverte qu'en utilisant le geste qu'elle verrouille) et 10 gestes
n'existent pas dans la vue. Ferme D133.

## Décisions clés (Nico, 2026-11-12)
- On **garde** `GESTE_UNLOCK` ; on **ajoute** `PORTES_TECHNIQUE` : franchir une porte
  DÉCOUVRE la technique (palier 1), ce qui rend vraies les conditions existantes.
- Quatre portes : Atelier, geste de base voisin, observation, courrier.
- Posséder une structure offerte vaut l'avoir posée.
- Trois états : inconnu / pressenti (calculé) / ouvert. Pressenti = silhouette +
  phrase d'ambiance, jamais la piste.
- `FAMILLE_GESTE` (8 familles) vit en Python, exposée au pont.
- Test d'atteignabilité permanent.

## Golden
`b4a921f8…` (`tests/golden_hash.txt`). **INTACT sur les 4 tronçons** : état joueur
opt-in, hooks au-dessus du tick. S'il bouge : fuite dans le tick → annuler, ne
jamais re-figer.

## Tronçons
| # | Kickoff | Golden | État |
|---|---|---|---|
| ① | `01_portes_atteignabilite.md` — table des portes, conditions `stock`/`compte`, test du point fixe | intact | **FAIT** 2026-11-12 |
| ② | `02_atelier_courrier_observations.md` — outils neufs, récompense `technique`, lettres, marqueurs d'observation | intact | à faire |
| ③ | `03_pressentis_familles_pont.md` — pressentis + phrases, familles, routes supports/couvertures, snapshot, bump pont | intact | à faire |
| ④ | `04_vue_minimale_banc.md` — gestes manquants dans `Gestes[]`, banc F5 | intact | à faire |

## Interdits communs à tous les tronçons
- Ne JAMAIS lancer `tests/test_epaisseur_500ans`.
- Pas de `ps aux` / `pgrep -f` ; `uptime` pour la charge.
- Ne supprimer aucun code existant (macros, anciens tests).
- Aucun appel DeepSeek de routine ; un besoin de fouille = kickoff incomplet → le
  consigner ici.

## Constats d'exécution
### ① (2026-11-12) — golden intact `b4a921f8…`
- `deblocage.py` : formes `stock`/`compte`, `PORTES_TECHNIQUE`, `compter_geste`,
  `VERBES_COMPTES` ; `evaluer_deblocages` découvre d'abord les techniques. 150 LDC →
  pas de module frère `deblocage_tables.py`.
- `DECLENCHEURS` est désormais dérivé des DEUX tables et descend dans les `et`
  (sinon `posseder_greffoir`, cité sous un `et`, n'y était pas). Il contient donc les
  `posseder_*` neufs — sans effet tant que le ② ne les pose pas.
- Pont : `compter_geste` appelé dans `cmd_action` à côté de `marquer_action`. Un
  achat de botte de paille passe aussi par `cmd_action` → la porte `paillage` est
  réévaluée sans toucher `sim/outils.py`.
- **`broyer` est fermé jusqu'au ②** (plus de `maitrise paillage`, broyeur pas encore
  vendu). L'aide de `tools/bancs/automate_demo.py --amorce-maitrise` dit encore
  « paillage ouvre pailler/broyer » : seul `pailler` s'ouvre. Texte non retouché.
- `gestes_comptes` : aucun sérialiseur de save ne liste `actions_faites` ni
  `marqueurs_ecolo` aujourd'hui ; rien à brancher. À revoir quand la save existera.
- `planter_conteneur` est dans `GESTE_UNLOCK` mais pas dans `COUTS` (antérieur au
  sprint) : le test vérifie les deux ensembles.
- Test : `MARQUEURS_PROMIS_PAR_2` (5 marqueurs) à **vider au ②** — le cas `[0]` du
  test échoue dès qu'un de ces marqueurs est vendu, pour forcer le resserrage.
  Événements tenus pour atteignables : `merle_seme`, `grimpante_sans_appui`,
  `lettre_greffe`, `lettre_essaim` — au ② de les poser réellement.
- Suites : atteignabilite 34/34, deblocage 24/24, palette 22/22,
  acquisition_outils 16/16 ; voisines (paillage, automate ②, périphérie ×3,
  progression_geste, vision, bouture) vertes.

## §REPRISE
Lire `CLAUDE.md`, ce fichier, le doc de conception, puis le premier kickoff « à faire ».
Prochain : **②** `02_atelier_courrier_observations.md` (① fait, non commité par le sous-agent).
