# Sous-sprint t6·C3 — finitions heatmap (retours F5 du 2026-06-12)

> **Kickoff autosuffisant** (démarrage à froid : lire `00_etat.md` d'abord).
> Contexte : le volet C (heatmaps F6, protocole 0.3.0) est **fonctionnel et
> confirmé** au F5 du 2026-06-12 (« c'est bien de pouvoir enfin voir les
> heatmaps ») — ce sous-sprint traite les 4 retours de ce F5. Ampleur :
> **petit/moyen**, majoritairement C# (vue) + un diagnostic Python en lecture.
> Golden intact par construction (rien ne touche le tick).

## État de départ
- `visuals/FieldOverlay.cs` : palettes PAR CHAMP (`Palettes`/`PaletteOf`),
  dessin = `Lerp(low, high, t)` avec **normalisation AUTO min/max par grille**.
- `WorldView.cs` : F6/Maj+F6, machine `fields` dans la file du pipe
  (`PipeFree`), légende `RichTextLabel` BBCode (2 pavés ██ + libellés +
  min/max), build témoin « t6·C2 légendes heatmap ».
- `MacroLife.cs` : points ancrés + errance visuelle (ravageur/auxiliaire
  ±6 cm, **pollinisateur ±120 cm**, ver ±1,5 cm), fondu de mort 0,9 s.

## Retour 1 — « les couleurs devraient être des gradients, pas un binaire ;
## l'échelle devrait le refléter au lieu de montrer deux couleurs »
1. **Légende en barre dégradée** : remplacer les 2 pavés par une rampe
   continue — N pavés `██` interpolés en BBCode (10-16 suffisent, zéro
   nouveau nœud) entre `low` et `high`, bornes min/max aux extrémités.
2. **Le vrai sujet dessous : la normalisation**. Min/max AUTO sur un champ
   quasi uniforme étale les couleurs sur du bruit (rendu « binaire » ou
   psychédélique) ; sur un champ bimodal, tout est aux extrêmes. Options à
   trancher AU SPRINT :
   - (a) **échelle FIXE par champ** quand le sens physique existe (la table
     `Palettes` gagne `min`/`max` optionnels : température en °C réels
     p. ex. −5..35, humidité 0..1, populations 0..1) — la couleur devient
     COMPARABLE d'une semaine/saison à l'autre (une carte météo, pas un
     contraste auto) ; repli auto min/max pour les champs sans bornes
     naturelles (om_*, soil_memory*) ;
   - (b) percentiles 5-95 (robuste aux outliers, mais l'échelle « respire »
     encore) ;
   - Recommandation kickoff : **(a)** — c'est aussi ce qui répond au
     retour 2 (cf. ci-dessous). La légende affiche alors les bornes de
     l'ÉCHELLE (fixes) et plus le min/max de la grille (les deux si utile).

## Retour 2 — « la température est la même partout alors qu'il y a des
## zones d'ombre »
3. **Diagnostic Python d'abord** (lecture seule) : imprimer la grille
   `temperature` d'une tuile à plusieurs semaines — vérifier si le champ est
   réellement uniforme par construction (l'air hebdo de `weather_at` diffusé
   par plot) ou s'il a une variance que la normalisation auto écrase/étale.
   Probable : champ ~uniforme → span minuscule → l'écran montre du bruit ou
   un aplat (le « même partout »). L'échelle fixe (1.a) rend ça honnête :
   une tuile uniforme à 18 °C s'affiche uniforme, c'est la vérité du modèle.
4. **L'ombre qui rafraîchit le sol = MOTEUR** : c'est le sprint
   « physico-chimie du sol » déjà gravé au BACKLOG (température du sol
   tamponnée, modulée par couverture/ombre + pH). PAS dans ce sous-sprint —
   le jour venu, l'introspection 0.3.0 exposera `temperature_sol` à F6 tout
   seul. Ici on n'ajoute que la pédagogie (HUD ou réponse) : temperature
   actuelle = AIR hebdo, pas le microclimat du sol.

## Retour 3 — « les zones d'OM / microbiome semblent aléatoires »
5. **Pédagogie + vérification, pas un correctif a priori** : l'hétérogénéité
   de fondation est VOULUE (règle de design #7 — bruit spatial déterministe
   `_hash_noise` : deux joueurs n'ont jamais le même terrain) et l'OM se
   dépose là où la vie meurt. Vérifier visuellement (avec l'échelle fixe de
   1.a) que les motifs CORRÈLENT avec le vivant : humidité vs plantes,
   om_fresh vs zones de mortalité, microbiome vs couverture. Si après ça un
   champ reste illisible → consigner le constat (calibrage moteur éventuel =
   backlog, pas ici).

## Retour 4 — « des ravageurs/auxiliaires/pollinisateurs bougent dans des
## cases où la heatmap dit qu'ils sont absents »
6. Causes IDENTIFIÉES (vue, pas moteur) : l'**errance visuelle** sort du
   plot d'ancrage (le pollinisateur déambule à ±120 cm = ±2,4 plots —
   demande du F5 t6·B !) + le **fondu de mort** (0,9 s d'agonie visible).
   Options à trancher AU SPRINT :
   - (a) **assumer + pédagogie** : le point se DÉPLACE, le champ dit où il
     VIT (son habitat) — un butineur traverse des plots où il ne niche pas ;
   - (b) quand la heatmap de SA guilde est affichée, réduire l'errance (les
     points se rassemblent sur leur ancre → la corrélation saute aux yeux) ;
   - (c) dessiner un fil/point d'ancre discret en mode heatmap.
   - Recommandation kickoff : **(b)** — un instrument doit montrer la
     corrélation ; l'errance libre reste le mode normal hors heatmap de
     guilde. (a) en complément dans la réponse.

## Critères de succès (F5 Nico)
- [ ] La légende est une **rampe continue** (≥ 10 nuances), bornes lisibles.
- [ ] Champs à échelle fixe : les couleurs sont COMPARABLES entre semaines
      (l'humidité qui sèche se VOIT glisser vers l'ocre, pas re-normalisée).
- [ ] Température : rendu honnête (uniforme si le modèle l'est) + une ligne
      de pédagogie donnée à Nico (air ≠ sol, backlog physico-chimie).
- [ ] Heatmap d'une guilde affichée → les points de CETTE guilde collent
      visiblement aux zones chaudes de la carte.
- [ ] OFF = coût nul inchangé ; golden intact (`16a1b937…`) ; aucun fichier
      moteur touché.

## Contraintes & rappels
- C# seul attendu (+ script de diagnostic Python en LECTURE si besoin,
  conservé dans tools/ ou tests/ — on ne jette pas de code).
- Témoin de build à incrémenter (« t6·C3 … ») — piège sync Nextcloud.
- `DebugSecondsPerWeek=3` encore actif ; la FIN DE TRANCHE 6 (remise à 0,
  CLAUDE.md, journal.md) vient APRÈS validation de ce sous-sprint.
- Ensuite : t7 = packaging PyInstaller (kickoff à écrire).
