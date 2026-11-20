# Conception — précuire les graphismes en gaussian splats (programme « tout en splats »)

> Figée le 2026-11-20 (`/conception`, Nico). Sprint (a) plantes :
> `sprints/rendu/splatting/sprint_precuisson_splats/`. Prototype fondateur :
> `docs/rendu/splatting/prototype/` (tomate mûre, validée par Nico : « c'est ça
> que je veux pour Symbiose »).

## 1. Intention

Amener le rendu en **gaussian splats** dans la vue Godot **actuelle** (iso 2D,
pixel-art SNES), sans attendre la vraie 3D temps réel ni un PC puissant. Les
images sont **précuites hors ligne sur la VM** avec
[ink-studio](https://github.com/siliconjungle/shapeshift-labs-ink-studio) (JS,
MIT, rendu CPU sous Node) ; Godot ne fait que les afficher. La vraie 3D reste
l'horizon (mémoire `project_refonte_splatting`) : les **recettes** écrites ici
(une feuille, une grappe, un port) resserviront telles quelles pour l'exporter en
splats temps réel.

**Golden : jamais touché.** Tout est vue + outillage ; le moteur Python ne bouge pas.

## 2. Décisions (Nico, 2026-11-20)

| # | Décision | Raison |
|---|---|---|
| D1 | **Fidélité maximale au moteur dans le jardin** : une plante reste construite sur ses vrais segments (taille au segment, phototropisme, vent, santé, rotation D35) | Philo #5 : l'indice visuel doit dire la vérité de la simulation |
| D2 | **Images versionnées dans git** avec leurs recettes ; poids du dépôt mesuré à chaque tronçon, alerte au-delà de ~200 Mo de pièces ; on ne régénère que ce dont la recette a changé | git = seul canal VM → Windows ; l'historique grossit à chaque régénération |
| D3 | **Option C** : kit d'organes précuits assemblé sur les segments dans le jardin + **portraits entiers** hors jeu | Les portraits n'ont pas de contrainte de fidélité, ils peuvent viser le rendu du prototype |
| D4 | **Tous les zooms en splats** (×0,5 → ×32) : même le kit des paliers bas (touffes 3-9 px, fleurons) vient des recettes | Une seule source graphique |
| D5 | **Symptômes ×16** : les TROUS (morsures, criblage de grêle) = variantes précuites, 2-3 degrés ; les COULEURS (nécrose, taches, givre) restent portées par la palette / peintes par-dessus | Un trou a un bord en volume ; une couleur est déjà dynamique |
| D6 | **Portraits : 3 par espèce** (jeune · mûre en pleine saison · fin de cycle / hiver), dévoilés avec les niveaux 1-2-3 de la fiche d'encyclopédie ; le magazine montre le portrait mûr | Le savoir se gagne en observant (philo #6) |
| D7 | **Programme par familles**, F5 entre chaque : (a) plantes → (b) décor de lisière → (c) faune + champignons → (d) structures + maison → (e) sol, litière, eau, neige, météo → (f) icônes | Un sprint par famille reste vérifiable |
| D8 | **Icônes de gestes = petits objets en splats** (trois quarts), après un F5 de lisibilité | Cohérence ; une icône doit rester lisible d'un coup d'œil |

Choix techniques (proposés à Nico sans objection) : ink-studio **copié dans le dépôt**
à un commit figé (`tools/splat/vendor/`, ~15 Mo) ; l'outil de cuisson est en
**JavaScript** (langue d'ink-studio), confiné à `tools/splat/`, VM seulement.

## 3. Le modèle : une pièce splat parle la langue de la palette indexée

La vue éclaire déjà ses plantes **au shader** (`visuals/PaletteIndexee.cs:14`) :
chaque pixel cuit porte R,G = n° de palette (posé à l'assemblage : espèce × saison
× santé × givre × maturité), B = `128 | ton << 4 | orientation` (ton 0-4 =
creux · ombre · base · clair · éclat ; orientation 0-7 = normale de face
quantifiée par 45° en repère écran, 8 = plat), A = posé / vide. Le shader monte
ou descend le ton selon le soleil réel.

Une **pièce splat** fournit exactement le canal B (et A) :
- **orientation** = la normale de surface du splat visible, projetée en repère
  écran et quantifiée à 45° (ink-studio sait sortir une passe de normales :
  commande `passes`, et `atlas --maps normal`) ;
- **ton** = le **volume** hors soleil : occlusion ambiante, creux, revers de
  feuille, base ; jamais l'ombre portée du soleil (c'est le shader qui la fait).

Conséquence : **une géométrie sert toutes les teintes**. La même feuille composée
habille la tomate, le frêne et le rosier ; un fruit précuit une fois sert du vert
au mûr au pourri (la palette change, pas l'image).

## 4. La bibliothèque : le vocabulaire de la vue, pas 54 espèces

La vue décrit les espèces par une grammaire fermée (`PlantRenderer.PortsFiches.cs`) :
7 ports (`FormePort`), les arbres (`PlantRenderer.Houppier.cs`, `.Arbres.cs`),
15 formes de feuille (`FormeFeuille`), 14 formes de tête (`FormeTete`), 8 marques
(`MarqueFeuille`) ; plus les formes du kit et des feuilles des paliers hauts
(`PlantRenderer.Leaf.cs`, `LeafShape`). On écrit **une recette par mot** de ce
vocabulaire. Chaque recette est cuite :
- sous plusieurs **vues** (lacet × inclinaison, nombre fixé au ① par la mesure),
  la vue choisie à l'assemblage étant la plus proche de l'orientation 3D de
  l'organe vue par la caméra — la rotation D35 et les poses de vent restent ainsi
  servies sans recuire ;
- à **chaque palier** (×0,5, ×1, ×2, ×4, ×8, ×16, ×32) en pixels natifs, jamais
  mise à l'échelle (règle des zooms entiers) ;
- en **variantes** au hash (zéro aléa vivant, philo #3), plus les degrés de trous
  (D5).

Les pièces sont rangées en **planches** (atlas PNG, peu de fichiers) + un
**manifeste JSON** (recette, palier, vue, variante, rectangle, point d'attache),
pas des milliers de PNG isolés (imports Godot, poids git).

## 5. Les portraits

Une recette de **plante entière par port** (+ arbres), paramétrée par la ligne de
l'espèce dans la table de la vue (rayon, axes, forme de feuille et de tête…). La
table n'est **pas recopiée à la main** : elle doit avoir une seule source (le ⑥
choisit comment la lire ou l'exporter). Trois états par espèce (D6) → 162
portraits pour 54 espèces [classes distinctes de `plants/catalogue.py`, compté le
2026-11-20]. Rendu à la manière du prototype (palette pleine, lumière cuite) :
ce sont des illustrations, pas des pièces de jeu.

## 6. Tronçons du sprint (a)

| # | Tronçon | Golden |
|---|---|---|
| ① | Atelier de cuisson + preuve de faisabilité (une recette, format palette indexée, tous paliers, mesures) — **porte de décision** | intact |
| ② | Bibliothèque des feuilles (formes, variantes, vues, trous) | intact |
| ③ | Têtes, fleurs, fruits, bourgeons, bois | intact |
| ④ | Vue : assemblage ×4 → ×32 | intact |
| ⑤ | Vue : assemblage ×0,5 → ×2 (le kit vient des splats) | intact |
| ⑥ | Portraits (162) | intact |
| ⑦ | Vue : encyclopédie et magazine | intact |

## 7. Risques et coût

- **Lisibilité à 3 px** (D4) : le plus incertain, testé en premier (①). Si une
  pièce splat réduite n'est pas lisible, on garde le kit pixel aux paliers bas et
  on revient en conception — pas de contournement silencieux.
- **Couture du bois** : des tronçons d'écorce posés bout à bout peuvent laisser
  des joints ; ③ le mesure, sinon le bois reste dessiné par la vue (signalé).
- **Coût en jeu** : poser une texture coûte moins que tracer des polygones ; la
  cuisson en jeu (`PlantBaker`, file à budget) ne doit pas ralentir. Mémoire
  vidéo des planches ×16/×32 à mesurer au ④ (chargement par palier si besoin).
- **Cuisson hors ligne** : 17 s pour une plante entière de 106 000 splats sur la
  VM [n=1] ; une pièce est bien plus petite, ① donne le vrai chiffre.
- **ink-studio jeune** (créé 2026-11-16) : copie figée, jamais de mise à jour
  sans raison.
- Le port de beaucoup d'espèces est **inventé par la vue** (le moteur ne décrit
  qu'une tige pour la tomate) : de belles feuilles sur une silhouette pauvre
  resteront pauvres. Hors périmètre ; à signaler au F5.
