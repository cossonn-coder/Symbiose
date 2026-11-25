## 2026-11-25 — Sprint RELIQUATS DES PLANTES (S1 du style homogène) CLOS côté code

`/sprint-auto sprint_reliquats_plantes`, six tronçons enchaînés, golden `bce813af…` **intact
à chaque tronçon** (vue + outillage, `data/code/` jamais touché). Build C# vert partout.
Sprint : `sprints/rendu/splatting/sprint_reliquats_plantes/` ; conception :
`docs/rendu/splatting/conception_reliquats_plantes.md`.

| # | Commit | Fait |
|---|---|---|
| ① | `b5509b1d` | Budget de précuisson 1 Go (`visuals/BudgetCuisson.cs`) remplace les plafonds de `PlantBaker` ; tournesol et pommiers enfin cuits à ×32 ; éviction hors champ puis par distance ; mémoire lue au rapport C / F4. |
| ② | `60d40f99` | 1 à 3 classes de taille par recette sur l'échelle ×√2 (`tools/splat/lib/classes.js`), cuites en rapprochant la caméra (k = 1 inchangée à l'octet) ; correction √2 des organes ronds au manifeste ; la vue pose la classe la plus proche. 34 recettes recuites (~3 h VM chargée). |
| ③ | `c90e304c` | Inventaire des détails ; 9 détails cuits en **sur-couches** (nervures, duvet, poils, éclat, revers, pruine, glandes, gouttes, étamines) pour 17 recettes, posés par seuil de palier (`PlantRenderer.SplatsDetails.cs`) ; sonde ×64 (94-144 s/pièce). |
| ④ | `fca98c1a` | Recettes trèfle 3/4 folioles, thym, lavande, fétuque ; anthères du blé ; cœur jaune des fleurons. |
| ⑤ | `1175e338` | 156 portraits recuits : tournesol de face, molène, drosera, thym/lavande, bois des buissons, tuteurs. |
| ⑥ | `03e792db` | Revue ×0,5→×32 de 16 espèces ; tête du tournesol de face en jeu, poils/pruine fondus à ×32 (plus d'aspect oïdium), épi de la molène sur le tiers haut ; F5 consolidé. |

**Mesures :** `assets/splats/` 26 → 65 Mo ; précuisson 927/1024 Mo en monde `full` ×32
[VM, n=1] — le budget est presque plein ; premier passage à ×32 ≈ 1,5-2,4 s de gel par
grand plant [VM chargée, n=1-3].

**Écarts aux kickoffs (tranchés en tronçon) :**
- ① les planches ne sont pas évincées pour faire place à une cuisson (rechargement
  immédiat → gel) : le budget peut être dépassé de la taille des planches en usage.
- ② `feuille_paume` (courgette) garde une seule classe : sa planche ×32 touche la limite GPU.
- ③ détails en sur-couches séparées et non en couches dans la recette (sinon trous chez
  les espèces sans le détail).
- ④ le 4-feuilles suit le marqueur moteur `quatre_feuilles` (cueillable), pas de tirage côté vue.
- ⑤ prémisse fausse : la myrtille n'est pas fruitière au moteur → baies au portrait
  seulement, constat versé dans D134.

**Restes :** recette dédiée plantain ; framboisier persistant au moteur (vrai = caduc) —
non ouvert en dette (règle « pas de dette neuve sans en fermer une »), à trancher par
Nico ; dôme du thym trop visible ; drosera non revu au ⑥ (banc vise le plantain).

**F5 :** différé après S3 (décision E1) ; la liste consolidée par espèce et par palier
est dans le `00_etat.md` du sprint. **Prochain : `/conception` S2 arbres.**
