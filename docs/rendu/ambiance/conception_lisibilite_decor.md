# CONCEPTION — Lisibilité du décor d'ambiance (reprise D58 · falaise / forêt / rivière)

> Cap : rendre **lisibles** la forêt, la rivière et la falaise du backdrop, qui
> apparaissent aujourd'hui « éclatées au sol » (plates, fondues dans le sol,
> indifférenciées). **Reprise** du rendu existant (`DecorLayer`), PAS une refonte,
> PAS un ajout de décor. Conçu le 2026-07-23 (`/conception`, reprise D58 / sprint
> RENDU AMBIANCE T4-T5, clos 2026-07-10).

## 0. Constat — vérifié dans le code, pas un bug d'affichage

Le décor est implémenté (`DecorLayer.cs` = T4 ossature, `DecorLayer.Arbres.cs` =
T5 arbres) et **il s'affiche réellement** : le projet compile (0 erreur — le
`DrawEllipse` utilisé est le **natif Godot 4.6** de `CanvasItem`, pas le privé de
`PlantRenderer`), les 4 dispatchs `DrawForet/Riviere/Falaise/Prairie` sont
appelés, ZIndex −5 hors picking, LOD visible à `CurrentZoom ≤ 4`. Le screenshot
(printemps an 1) ne montre donc pas « T5 absent » mais **T5 dessiné, aplati et
fondu dans le sol**. → **reprise ciblée du rendu (volume/contraste)**.

## 1. Diagnostic (5 causes, par impact)

1. **Contraste forêt quasi nul (principal).** Feuillages ≈ assise du sol
   forestier : hêtre `#2c5730` vs fond forêt `#2f5738` = même vert ; le houppier
   est encore assombri de −16 % → il colle au sol. Seul le bouleau (`#6f9a4c`,
   clair) tranche, mais réservé à la lisière peu dense. → forêt = tache verte plate.
2. **Aucun volume.** Pas d'ombre portée au pied ; amplitude de valeur timide
   (±15 %) ; pas de lumière directionnelle commune → rien ne se décolle du plan-sol.
   La densité, elle, est **bonne** (canopées 340 cm >> cellule 130 cm → masse
   continue) ; le manque n'est pas la densité mais le relief.
3. **Falaise rare et plate.** Dérive d'un couplage rivière+prairie voisine → souvent
   0 secteur ; quand elle apparaît, redans à plat sans face verticale ni ombre.
4. **Rivière = bande bleue morte.** La plus lisible (bleu vs vert) mais surface
   plate ; reflets 2 px sous-pixel au dézoom ; berges = simple assise.
5. **Échelle détail/distance.** Fleurs 1.5 px, reflets 2 px, chevrons 1.5 px :
   calibrés vue proche, invisibles à la distance réelle d'observation (zoom large).

**Repères mesurés :** `PxPerCmX = PxPerCmZ = 0.39`, `PxPerCmY = 0.195` (px internes
avant zoom). Monde 2000 cm → ~1560 px final à zoom 0.5. Chêne : canopée ~133 px,
fût ~86 px (~8 % de la largeur du monde). LOD décor visible zoom ≤ 4 ; `DepthCm=900`.

## 2. Décisions (arbitrages Nico 2026-07-23)

- **Hiérarchiser, forêt d'abord** (gain visuel maximal) : forêt > rivière > falaise.
- **Rester procédural peint** (pas de sprites) : déterminisme par seed (#3), léger
  (perf), cohérent avec tous les placeholders procéduraux (maison comprise).
- **Falaise laissée au seed** : on ne force pas sa présence (#7 hétérogénéité) ; on
  la rend lisible seulement quand elle apparaît.
- **Cap qualité = maison normande** : volume par **ombre portée + marches de valeur
  franches + face verticale contrastée**. Cap pixel-art SS² respecté : 2-3 valeurs
  par masse, pas de dégradé continu, `Palette16`, invariant `DrawVolumeEllipse`
  (masse froide + calotte éclairée décalée vers le **SO**, comme plantes/maison).

## 3. Design de reprise

### 3.1 Forêt (T1 — le gros gain)
- **Marches de valeur franches** (remplace ±15 %) : masse du houppier ≈ −25 %,
  calotte éclairée ≈ +30 %, décalée **SO** (soleil commun). Chaque blob acquiert un
  relief 2 valeurs qui tranche sur le sol.
- **Ombre portée** : une ellipse sombre aplatie au pied de chaque arbre, peinte
  AVANT le houppier → la masse se décolle du plan-sol.
- **Silhouette de cime** : liseré éclairé sur le haut des houppiers de lisière → un
  bord supérieur « bosselé » lisible contre le jardin.
- **Palette** : sol forêt (`DecorForetFond`) poussé un cran plus froid/sombre pour
  que les cimes éclairées ressortent ; feuillages re-répartis en valeurs pour créer
  du contraste inter-essences (pas tous le même vert).

### 3.2 Rivière (T2)
- **Berges franches** de part et d'autre du lit (galets/terre clairs, pas juste
  l'assise), avec bord d'eau assombri (ombre de berge) qui creuse le lit.
- **Surface d'eau à 2-3 valeurs** (pas un aplat) ; **reflets agrandis et allongés**
  dans le sens du courant (traits, pas points 2 px), calibrés pour la distance.
- Le tracé sinueux du lit donne déjà le **sens du courant** (axe) → orienter les reflets dessus.

### 3.3 Falaise (T3 — lisible quand le seed la produit)
- **Vraie face verticale** : un pan qui monte en −Y écran au front de la falaise,
  contrasté (ombre) → elle surplombe au lieu de bandes plates.
- **Ombre portée** au pied côté jardin (surplomb) + **éboulis** clairs au pied.
- 3 valeurs de roche plus dures ; sommet végétalisé conservé.

### 3.4 Transitions, échelle & banc (T4 — vue Godot finale)
- **Lisière nette** côté jardin (démarque décor/jardin) sur les 4 motifs.
- **LOD 2 niveaux** : la masse/silhouette reste à toute distance ; les détails fins
  (reflets, fleurs prairie, chevrons bouleau) ne se dessinent qu'à zoom ≥ 2 →
  recalibre l'échelle détail/distance et allège le dessin au dézoom.
- **Banc d'observation** : un seed (ou toggle debug) qui expose les 4 motifs côte à
  côte, pour valider la lisibilité d'un regard au F5.

## 4. Perf & invariants

- **Golden inchangé partout** — pure vue C#, zéro moteur, aucun re-figeage.
- Coût : `_Draw` **statique** (re-dessin au build seulement, hors tick moteur).
  +1 ellipse d'ombre par arbre = négligeable ; le LOD 2 niveaux **réduit** le dessin
  au dézoom. Budget largement sous +10 %.
- **Déterminisme (#3)** : tout dérive du hash djb2 + 3-sinus par seed, **zéro
  `Random`**. Aucune nouvelle source d'aléa.
- **#5** (pas de HUD chiffré), **#7** (hétérogénéité par seed) préservés.

## 5. Découpage (4 tronçons, chacun testable F5, golden INCHANGÉ)

| T  | Objet | Fichiers |
|----|-------|----------|
| T1 | Forêt : contraste + volume + ombre + cime | `DecorLayer.Arbres.cs`, `Palette16.cs` |
| T2 | Rivière : berges + surface + reflets courant | `DecorLayer.cs` (DrawRiviere), `Palette16.cs` |
| T3 | Falaise : face verticale + ombre (surplomb) | `DecorLayer.cs` (DrawFalaise), `Palette16.cs` |
| T4 | Transitions + LOD détail + banc F5 + MAJ doc | `DecorLayer.cs`, `DecorLayer.Arbres.cs` |

Tout le sprint est de la **vue Godot** → la règle « dernier tronçon = vue » est
satisfaite d'office ; T4 porte le banc d'observation F5.

## 6. Interconnexions

- **D58 / RENDU AMBIANCE** T4-T5 — code repris.
- **D73 terraforming** — la lisibilité (ici) précède l'actionnable (plus tard).
- **Maison normande** (`WorldView.Maison.cs`) — cap de qualité.
- **Cap pixel-art SS²** (`Palette16`, invariant `DrawVolumeEllipse`) — style à tenir.
- **D66/D67 perf** — garde-fou : LOD 2 niveaux au lieu de densifier.

*Aucune voix narrative concernée (décor pur ; essences forestières déjà voisées en T1 D58).*
