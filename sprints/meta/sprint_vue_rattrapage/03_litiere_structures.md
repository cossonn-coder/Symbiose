# 03 — Sol vivant & compost : litière + structures bac/pile + gestes

> Lire `00_etat.md`. **Snapshot enrichi en LECTURE seule** (litière) + rendu C#
> + câblage des 6 gestes compost (déjà routés 0.3.5). Rend visible le canal
> vertueux de la décompo·compost ①⑤. Ampleur : **moyen/gros** (le plus chargé).

## Partie A — Python : exposer la litière (read-only, golden NEUTRE)
`tools/simserver/serialize.py`, `_snapshot` : ajouter la litière par tuile, de
façon **compacte** (comme `sprites`/`structures`). Par plot non vide :
- proposition : `litiere[tile_id] = [[r, c, tissu_dominant, masse_totale], …]`
  (tissu dominant = parcelle de plus grande masse hors `diffus` ; `diffus` est
  l'exsudat permanent du sol, **non rendu**). Arrondir `masse` (déterministe).
  S'appuyer sur l'API existante (`EcoFields.litiere`, `TISSU_ORDER`) — **lecture
  seule**, aucun calcul nouveau dans le tick.
- Vérifier `908f591bee…` inchangé. Bump `ENGINE_VERSION` 0.3.6 → 0.3.7 + historique.
- `tests/test_sim_server.py` : +checks (litière d'un plot avec nécromasse, vide
  ailleurs, déterminisme).

## Partie B — C# : rendu de la litière
- Couche au sol **sous** les plantes (ZIndex entre le sol et les sprites macro) :
  petit décor / teinte par plot ∝ `tissu_dominant` (couleur par tissu : `feuille`
  ocre, `bois` brun, `fruit` rouille, `herbace` paille…) et **densité ∝ masse**.
  Volontairement **discret** (indice écologique, philo #5 — pas une heatmap ;
  la heatmap des champs reste F6). Réutiliser la projection du sol (losanges).
- *(Look exact à régler au F5 : décalques ronds jitterés vs teinte de plot. Défaut
  sobre : petits amas semi-transparents jitterés au plot, stables inter-frames
  via hash — pas de Random, philo #3.)*

## Partie C — C# : structures bac/pile + jauge
- `structures{}` est déjà au snapshot (`{kind, plot, compost_mur}`). Dessiner au
  plot un **placeholder procédural** : bac à compost (caisse) / pile à bois
  (tas), distincts. Afficher la **jauge `compost_mur`** (épandable) — barre/anneau
  discret au-dessus de la structure, OU réservé au survol (cohérent « pas de
  chiffres en HUD primaire » ; un remplissage visuel suffit).
- Les structures vivent au snapshot → les (re)créer/retirer dans `ApplySnapshot`
  comme les plantes (diff par `(tile, plot, kind)`).

## Partie D — C# : câbler les 6 gestes compost (routés 0.3.5)
Ajouter à la palette (cf. 01, palette étendue) :
- `poser_bac` / `poser_pile` (kind `q`, **phase Planification** — poser = geste
  de planification) : `target {tile, r, c}`.
- `composter` / `empiler_bois` (kind `q` + structure) : clic sur un plot où une
  structure existe → ramasse la litière acceptée vers la structure. Le serveur
  exige cohérence kind/geste (composter↔bac, empiler↔pile) → refus relayé.
  Désignation de la structure : par `target.structure` (index) — la vue résout
  la structure au plot cliqué.
- `retourner` (structure) : clic sur un bac → accélère la maturation.
- `epandre` (structure → plot, `params.q` optionnel) : clic sur un bac/pile mûr
  → trio humus borné par `compost_mur` au plot. Refus en amont si jauge vide
  (relayé). `q=None` ⇒ tout le dispo.
- **Garde-fou phase** : poser/composter/empiler/epandre = planification (temps
  figé) ; cohérent avec le modèle préparation/réaction. À confirmer au F5.

## Vérification
- `dotnet build` vert ; golden `908f591bee…` inchangé (Partie A = lecture seule).
- `tests/test_sim_server` : 123 + checks litière verts, protocole 0.3.7.
- **F5 Nico** : poser un bac, composter une parcelle de feuilles voisine (la
  litière au sol diminue, le bac se remplit), retourner, épandre → le sol
  s'enrichit (microbiome/fertilité, observable via F6 si besoin) ; poser une
  pile à bois (empiler du `bois` de taille/mort) → des auxiliaires apparaissent
  autour (habitat ⑤, via `MacroLife` — gratuit).

## Définition de fait
- [ ] Snapshot expose la litière (Partie A), golden inchangé, protocole 0.3.7.
- [ ] Litière + structures (bac/pile + jauge) rendues, discrètes.
- [ ] 6 gestes compost câblés, cohérence kind/phase, messages relayés.
- [ ] Build vert, témoin incrémenté, `00_etat.md` MAJ. Commit.

## Commit suggéré
`feat(vue·rattrapage) : 03 — litière au sol + structures bac/pile + 6 gestes compost (snapshot 0.3.7 RO, golden intact)`
