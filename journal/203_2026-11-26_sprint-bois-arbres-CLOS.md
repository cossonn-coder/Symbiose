## 2026-11-26 — Sprint BOIS ET ARBRES (S2 du style homogène) CLOS côté code

`/sprint-auto sprint_bois_arbres`, six tronçons enchaînés, golden `bce813af…` **intact
à chaque tronçon** (vue + outillage, `data/code/` jamais touché). Build C# vert, 0
avertissement partout. Sprint : `sprints/rendu/splatting/sprint_bois_arbres/` ; conception :
`docs/rendu/splatting/conception_bois_arbres.md`.

| # | Commit | Fait |
|---|---|---|
| ① | `a4eb11f9` | `parent` lu côté C# ; axes et courbe passant par tous les nœuds (`BoisAxes.cs`), primitive ruban (`RubanTexture.cs`), tube du bois (`PlantRenderer.Tube.cs`) : pied évasé, cols de branche, tri par profondeur ; rameaux/fruits/feuilles/clic/surbrillance suivent la courbe ; rapport C dit les espèces en repli et la cuisson la plus lente ; Maj+F11 = ancien bois. |
| ② | `fe7e8815` | Écorces cuites 13 essences (12 + générique) × 3 âges × 4 paliers ; C3 tranché : la bande ne porte que les marques, l'orientation vient de la géométrie du tube (shader écarté : il s'attache au nœud entier ; variantes par rotation écartées : ~100 Mo GPU [calcul]). |
| ③ | `ba3f5561` | Limbes cuits des graminées en ruban (nervures peintes, médiane, bords) dès 7 px ; petit bois des arbres en tubes effilés à écorce « rameau » ; chargeur commun `BandesCuites.cs`. |
| ④ | `79a2dde0` | Bouquets de fleurs d'arbre cuits au palier ×4 (`bouquet_corolles`, `bouquet_boutons`) ; ~420 → ~106 tracés par arbre [n=3 pieds] ; masses d'été constatées, rien à corriger. |
| ⑤ | `b679ad9f` | Cône du sapin en jeu par la vue (étages tous les 30 cm, longueur suivant la hauteur) ; 36 portraits d'arbres recuits (cône, tube lissé, écorce par essence ; cerisier fleuri au jeune, cerises au mûr). |
| ⑥ | `1ac1097a` | Revue ×0,5→×32 (12 essences hiver, 5 été, verger, graminées, arbre mort, `full`) ; départ d'une branche posée devant le tronc arrondi ; F5 consolidé. |

**Mesures :** `assets/splats/` 65 Mo (inchangé à 0,3 Mo près) ; précuisson ×32 926/1024 Mo
en `full` [VM, n=1], 2 plantes en repli (menthe, noyer) ; frame 53-58 ms ×4-×32 [VM charge 4,
non transposable au PC].

**Écarts aux kickoffs (tranchés en tronçon) :**
- ④ prémisse fausse : le vide ×4 venait de la taille d'une fleur (5-6 px), pas du plafond.
- ③ nervures peintes en pigment (les sillons ne donnaient presque pas d'ombre).
- ⑤ longueur des rameaux du sapin par la hauteur, pas l'âge (sinon cylindre tronqué à 25 ans).
- ⑥ « branches pâles en arcs » de `full` = géométrie moteur (la branche plonge puis remonte), non corrigé.

**Restes (non ouverts en dette, règle « pas de dette neuve sans en fermer une » — à trancher
par Nico au F5) :** recette « rameau aplati » du sapin ×8-×32 (aujourd'hui bâtons bruns) ;
marche de couleur du bois à certains nœuds (aulne ×16, tramage) ; écorces grises (hêtre,
noyer, charme, sapin) presque blanches, confondues avec le bouleau de loin (préexistant) ;
figuier en cépée = moteur.

**F5 :** différé après S3 ; liste consolidée dans le `00_etat.md` du sprint.
**Prochain : `/conception` S3 (lisière sur `RubanTexture` + écran de chargement mycélium).**
