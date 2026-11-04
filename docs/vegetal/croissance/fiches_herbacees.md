# Fiches morphologiques des 36 herbacées, arbustes et lianes

Sprint FORMES DES PLANTES ①. Référence de ce que chaque espèce **devrait être** à l'écran ; ce qu'elle
**est** aujourd'hui : `sprints/rendu/pixelart/sprint_formes_plantes/mesures/avant.md`.
Chaque fiche se traduit en une ligne de la table C# des ports (conception §4.1) ; aucune fonction par espèce.

## Lire ces fiches

- **Réel** : sujet ordinaire, sol correct, climat normand. Ces fourchettes sont des ordres de grandeur de
  mémoire de jardinier, sans source vérifiée ligne à ligne ; chacune le porte par `[odg]`.
- **Jeu** : `height_cm` et rayon de canopée du dernier stade au catalogue, à l'été. Ce sont les valeurs que le
  port dessiné doit suivre, à ±20 % (conception §6). Elles ne changent pas dans ce sprint ; un écart à la
  réalité est écrit, pas corrigé. Les proportions de dessin proposées sont des choix de jeu, `[choix]`.
- **Échelle** : le monde est à l'échelle réelle, 1 plot = 50 cm. À l'écran, 1 cm = 0,39 px internes par palier
  de zoom : un pied de 12 cm fait 5 px à ×1, 19 px à ×4, 37 px à ×8. Une feuille de 5 cm fait 2 px à ×1 : à
  ce palier on ne lit qu'un gabarit, une masse et une couleur, jamais une feuille.
- **Trois paliers** : à ×1 l'espèce se reconnaît à sa masse, à ×4 à son motif de feuilles et à sa fleur, à ×8 à
  ce qui reste du détail (nervure, nœud, dent). La grammaire est celle du brief, dialecte 3 : icône à 3 ou 4 tons.
- **Fruit** : seuls tomate, courgette, fraisier et framboisier sont `fruitier` au moteur. Ailleurs (poivron,
  haricot, myrtille…), le fruit de la fiche est décrit pour mémoire : tant que le moteur n'en produit pas, le
  port n'en dessine pas, sauf si le tronçon en fait une marque de stade sans état moteur, à signaler.
- **Ortie et lupuline** : les deux espèces renvoyées par D126 sont parmi les 36, sous `ortie` et `minette`
  (*Medicago lupulina*). Elles ne s'ajoutent pas au compte.

Ports (conception §4.2). Rosette : pissenlit, mâche, bourse-à-pasteur, molène, drosera, carotte, ail.
Tige : tournesol, ortie, basilic, poivron, phacélie, bourrache, moutarde, armoise, chanvre, achillée, consoude,
menthe. Chaume : blé, seigle, pâturin, bambou. Couvre-sol : fraisier, violette, minette, sphaigne. Buisson :
thym, lavande, myrtille, framboisier. Grande rampante : courgette. Volubile : haricot. Segments conservés :
tomate, lierre, jasmin.

## Espèces qui tiennent mal dans leur port ou leur gabarit

Signalées pour les tronçons ② à ⑥ ; aucune ne réclame de 8ᵉ port à ce stade.

- **Ail** : pas une étoile mais un éventail de rubans dressés. Il entre dans le port rosette par ses paramètres
  (feuilles dressées, 2 rangs). Sa hampe suit le stade moteur `hampe`, dès l'an 1 au catalogue, et non « l'an 2 ».
- **Pissenlit** : rayon moteur 55 cm pour une rosette réelle de 10-25 cm de rayon `[odg]`, et `height_cm` 30 qui
  ne vaut que pour la hampe. Dessiner au rayon réel, sinon il couvre plus de 2 plots. Écart de mesure à prévoir.
- **Molène** : à ce catalogue, stade `rosette` puis `hampe` ; la rosette reste au pied de la hampe.
- **Minette** : `height_cm` 30 pour un tapis réel presque couché. Le critère de hauteur à ±20 % se lit sur la
  tige redressée en fleur ; sinon l'exclure du critère, à consigner.
- **Consoude** : `height_cm` 50 contre 60-120 cm réels `[odg]`. Masse trapue assumée.
- **Bambou** : 250 cm pour 4-8 m réels `[odg]`, et une seule touffe là où l'espèce trace. Le port dessine une
  touffe ; la colonie reste faite de ramets moteur.
- **Lierre, jasmin** : segments conservés, hors port. Sans support, ils rampent au sol : c'est leur état normal
  sur `planche_especes`.

## Rosettes

### Pissenlit — `Taraxacum`

- **Port** : rosette plaquée au sol, feuilles en étoile, hampes nues au centre.
- **Réel** : rosette 10-25 cm de rayon, hampe 10-30 cm `[odg]`.
- **Tige** : aucune ; hampe creuse, lisse, un peu rougeâtre, sans feuille.
- **Feuille** : en étoile, oblongue, à dents profondes tournées vers le pied, 10-25 cm `[odg]`.
- **Limbe, nervation** : nervure médiane claire, souvent rose à la base ; le reste invisible.
- **Couleur** : vert franc, moyen.
- **Fleur** : capitule jaune d'or plein, 3-5 cm `[odg]`, à plat au sommet de la hampe.
- **Fruit** : boule d'aigrettes blanches, 4-5 cm `[odg]`, après la fleur.
- **Au pied** : le centre de la rosette, un peu sombre, d'où partent feuilles et hampes.
- **Jeu** : `height_cm` 30, rayon moteur 55 (voir écarts) ; rayon dessiné 20 cm `[choix]`, 3 à 5 hampes.
- **Distingue** : ×1, tache verte plate piquée d'un point jaune. ×4, feuilles en dents de scie, capitule plein.
  ×8, nervure rose, hampes nues.

### Mâche — `CornSalad`

- **Port** : très petite rosette serrée, en bouquet rond, feuilles redressées.
- **Réel** : 5-15 cm de haut, 5-10 cm de rayon `[odg]`.
- **Tige** : absente, puis tige fine à fourches successives à la montée en graine.
- **Feuille** : en spatule arrondie, entière, opposée, 3-8 cm `[odg]`, lisse.
- **Limbe, nervation** : tendre, à peine luisante ; médiane seule.
- **Couleur** : vert foncé, doux, le plus sombre des petites rosettes.
- **Fleur** : minuscules, bleu très pâle, en petits bouquets, au printemps.
- **Fruit** : akène invisible.
- **Au pied** : les feuilles se referment au centre, sans vide.
- **Jeu** : `height_cm` 18, rayon 30 au catalogue ; rayon dessiné 10 cm `[choix]`.
- **Distingue** : ×1, point vert sombre. ×4, cuillères rondes groupées, sans découpe. ×8, un bouquet de salade.

### Bourse-à-pasteur — `BursaPastoris`

- **Port** : petite rosette plate surmontée d'une tige grêle, presque nue, ramifiée en haut.
- **Réel** : rosette 5-10 cm de rayon, hampe 20-40 cm `[odg]`.
- **Tige** : fine, dressée, vert pâle, quelques petites feuilles embrassantes.
- **Feuille** : découpée en lobes irréguliers à la base, 5-10 cm `[odg]`.
- **Limbe, nervation** : mince, mat ; rien de lisible.
- **Couleur** : vert moyen, un peu terne.
- **Fleur** : très petite, blanche, à 4 pétales, en petit bouquet terminal.
- **Fruit** : silicule plate en cœur renversé, 5-8 mm `[odg]`, le long de la hampe, tenue par un fil. C'est la
  signature ; moteur non `fruitier`, la dessiner comme marque de stade, à signaler.
- **Au pied** : la rosette, nettement plus large que la tige.
- **Jeu** : `height_cm` 40, rayon 30 au catalogue ; rayon dessiné 8 cm `[choix]`.
- **Distingue** : ×1, trait vertical très fin sur un point. ×4, chapelet de petits triangles le long de la hampe.
  ×8, le cœur des silicules.

### Molène — `Molene` (*Verbascum thapsus*, choisi ici)

- **Port** : grande rosette de feuilles laineuses, puis cierge dressé unique l'année de floraison.
- **Réel** : rosette 20-40 cm de rayon, hampe 100-200 cm `[odg]`.
- **Tige** : droite, épaisse, laineuse, couverte de feuilles qui rapetissent en montant.
- **Feuille** : grande, ovale, entière, 15-40 cm `[odg]`, décurrente sur la tige.
- **Limbe, nervation** : feutré, épais ; aucune nervure lisible, un duvet gris en surface.
- **Couleur** : gris-vert argenté, le plus clair du jardin.
- **Fleur** : jaune, 2 cm `[odg]`, serrée en épi plein sur le tiers haut du cierge.
- **Fruit** : capsule brune sur le cierge sec, qui reste debout l'hiver.
- **Au pied** : la rosette garde sa place sous la hampe.
- **Jeu** : `height_cm` 160, rayon 55 au dernier stade [dérivé de la strate]. Lit le stade : `rosette`, puis `hampe`.
- **Distingue** : ×1, trait vertical pâle, épais, jaune en haut, sur une tache grise. ×4, feuilles feutrées sans
  découpe, épi jaune. ×8, duvet, feuilles collées à la tige.

### Rossolis — `Drosera`

- **Port** : minuscule rosette plaquée, feuilles rondes rouges, sur la mousse.
- **Réel** : 3-8 cm de rayon, hampe 5-15 cm `[odg]`.
- **Tige** : hampe fine, droite, sans feuille.
- **Feuille** : ronde en cuillère au bout d'un pétiole, 1 cm `[odg]`.
- **Limbe, nervation** : couverte de poils rouges terminés par une goutte brillante. C'est toute l'espèce.
- **Couleur** : rouge-vert, unique au jardin.
- **Fleur** : petite, blanche, en grappe penchée d'un côté.
- **Fruit** : capsule invisible.
- **Au pied** : pétioles en étoile, pas de centre lisible.
- **Jeu** : `height_cm` 10, rayon 12 `[choix du catalogue]`.
- **Distingue** : ×1, point rouge. ×4, disques rouges en étoile. ×8, gouttes claires sur les bords.

### Carotte — `Carrot`

- **Port** : touffe de feuilles très découpées, puis ombelle l'année de floraison (bisannuelle).
- **Réel** : touffe 20-40 cm, tige florale 60-120 cm `[odg]`.
- **Tige** : à la montée, dressée, côtelée, poilue, ramifiée.
- **Feuille** : plumeuse, plusieurs fois divisée, 15-30 cm `[odg]`, port léger.
- **Limbe, nervation** : pas de limbe lisible, un voile de fines lanières.
- **Couleur** : vert moyen vif.
- **Fleur** : ombelle plate, blanche, 5-10 cm `[odg]`, parfois un point pourpre au centre ; bractées en collerette.
- **Fruit** : ombelle refermée en nid, brune.
- **Au pied** : collet orangé à peine visible au ras du sol, à ×8 seulement.
- **Jeu** : `height_cm` 60, rayon 30 ; stades `rosette`, `ombelle`, `mature`. Lit le stade.
- **Distingue** : ×1, petit nuage vert, puis point blanc. ×4, plumeau de lanières, ombelle plate. ×8, collet orange,
  rayons de l'ombelle.

### Ail — `Garlic`

- **Port** : éventail de rubans dressés à 2 rangs, puis hampe droite à tête ronde. Voir écarts.
- **Réel** : feuilles 30-50 cm, hampe 50-100 cm `[odg]`.
- **Tige** : fausse tige blanche, formée par les gaines ; hampe lisse, ronde.
- **Feuille** : ruban plat, pointu, plié en long, 1-2 cm de large `[odg]`, arquée au bout.
- **Limbe, nervation** : lisse, cireux ; un pli central.
- **Couleur** : vert bleuté, glauque.
- **Fleur** : tête ronde, blanc rosé, sortant d'une spathe en bec.
- **Fruit** : bulbilles dans la tête ; moteur non `fruitier`.
- **Au pied** : base blanche de la fausse tige, au ras du sol.
- **Jeu** : `height_cm` 50, rayon 30 au catalogue ; rayon dessiné 12 cm `[choix]`. Stades `feuilles`, `hampe`.
- **Distingue** : ×1, petit V bleuté. ×4, rubans en éventail, boule pâle. ×8, base blanche, pli des feuilles.

## Tiges à feuilles étagées

### Tournesol — `Sunflower`

- **Port** : tige unique, droite, grosse, couronnée d'un seul capitule penché vers l'est.
- **Réel** : 150-300 cm `[odg]`.
- **Tige** : épaisse, poilue, vert clair, sans ramification.
- **Feuille** : alterne, en cœur large, 15-30 cm `[odg]`, rétrécie vers le haut, pendante.
- **Limbe, nervation** : rêche ; 3 nervures partant de la base.
- **Couleur** : vert franc moyen, mat.
- **Fleur** : capitule 15-30 cm `[odg]`, centre brun sombre, couronne de rayons jaunes. C'est l'icône à ×1.
- **Fruit** : disque sombre chargé de graines, penché, à la fin de l'été.
- **Au pied** : tige nue en bas, feuilles basses souvent sèches.
- **Jeu** : `height_cm` 250, rayon 55. Capitule dessiné 25 cm `[choix]`, soit 10 px à ×1.
- **Distingue** : ×1, trait haut et disque jaune à centre brun. ×4, grandes feuilles en cœur, étagées. ×8, rayons un
  à un, nervures.

### Ortie — `Nettle` (renvoyée par D126)

- **Port** : tiges dressées raides, en colonie serrée, non ramifiées, feuilles en croix sur toute la hauteur.
- **Réel** : 60-150 cm `[odg]`.
- **Tige** : carrée, verte à rougeâtre, velue de poils urticants, 3 à 6 axes dessinés `[choix]`.
- **Feuille** : opposée, ovale pointue, fortement dentée, 5-12 cm `[odg]`, à pétiole.
- **Limbe, nervation** : gaufré, nervures creusées, dents en scie.
- **Couleur** : vert sombre et mat, le plus sombre des tiges.
- **Fleur** : petites grappes pendantes, verdâtres, à l'aisselle des feuilles du haut. Pas de couleur vive.
- **Fruit** : grappes brunes, mêmes places.
- **Au pied** : stolons jaunes rarement visibles ; base des tiges dense.
- **Jeu** : `height_cm` 90, rayon 30.
- **Distingue** : ×1, petit fagot vertical sombre, sans aucune fleur. ×4, feuilles dentées par paires, grappes
  pendantes. ×8, dents et gaufrage.

### Basilic — `Basil`

- **Port** : petit buisson rond, très ramifié, feuilles denses jusqu'au sol.
- **Réel** : 25-50 cm, 15-25 cm de rayon `[odg]`.
- **Tige** : carrée, tendre, vert clair, ramifiée dès le bas. Le pincement accentue la ramification.
- **Feuille** : opposée, ovale, entière, bombée en cuillère, 3-7 cm `[odg]`.
- **Limbe, nervation** : lisse et luisant, un éclat franc par feuille ; nervures creusées, dentelure quasi nulle.
- **Couleur** : vert vif, clair, le plus vif des aromatiques.
- **Fleur** : petits épis dressés, blancs, à étages, en bout de tige.
- **Fruit** : aucun visible.
- **Au pied** : tige à peine visible, feuillage presque au sol.
- **Jeu** : `height_cm` 40, rayon 30.
- **Distingue** : ×1, boule vert vif. ×4, feuilles rondes brillantes par paires. ×8, surface bombée, éclat.

### Poivron — `Pepper`

- **Port** : plant ramifié en fourches régulières, cime étalée, un peu en parasol.
- **Réel** : 50-80 cm, 25-40 cm de rayon `[odg]`.
- **Tige** : vert franc, lisse, cassante, fourchue par deux à chaque nœud.
- **Feuille** : alterne, ovale pointue, entière, 5-12 cm `[odg]`, pétiole net.
- **Limbe, nervation** : lisse, brillant ; médiane claire.
- **Couleur** : vert foncé luisant.
- **Fleur** : petite étoile blanche, à 5-6 pétales, solitaire, tournée vers le bas, dans les fourches.
- **Fruit** : gros, en cloche, pendant, vert puis rouge ; moteur non `fruitier` à ce jour. Écart à signaler au ③.
- **Au pied** : courte tige nue.
- **Jeu** : `height_cm` 80, rayon 50 au dernier stade ; rayon dessiné 35 cm `[choix]`.
- **Distingue** : ×1, masse verte sombre et ronde, tige visible. ×4, fourches, feuilles lisses, étoiles blanches. ×8,
  pétiole et éclat de la feuille.

### Phacélie — `Phacelia`

- **Port** : touffe dressée de tiges ramifiées, légère, à feuillage plumeux, très fleurie.
- **Réel** : 30-80 cm `[odg]`.
- **Tige** : velue, verte, ramifiée dès la base.
- **Feuille** : alterne, profondément découpée, en plume, 5-10 cm `[odg]`.
- **Limbe, nervation** : découpe seule lisible.
- **Couleur** : vert moyen, un peu grisé.
- **Fleur** : bleu-mauve, en cymes enroulées en crosse, étamines qui dépassent. Masse mauve au sommet.
- **Fruit** : petites capsules, sans intérêt.
- **Au pied** : tiges qui divergent peu.
- **Jeu** : `height_cm` 80, rayon 30.
- **Distingue** : ×1, touffe verte nimbée de mauve. ×4, crosses mauves. ×8, plumes et étamines.

### Bourrache — `Borage`

- **Port** : touffe lâche et charnue, tiges épaisses, large en bas, fleurs penchées.
- **Réel** : 40-80 cm, 25-40 cm de rayon `[odg]`.
- **Tige** : creuse, épaisse, couverte de poils raides blancs.
- **Feuille** : alterne, ovale large, entière, 10-20 cm `[odg]` en bas, plus petites en haut.
- **Limbe, nervation** : rugueux, gaufré, poils raides qui blanchissent le contour.
- **Couleur** : vert grisé, moyen.
- **Fleur** : étoile bleu pur à 5 pointes, cône noir au centre, penchée. Le bleu le plus vif du jardin.
- **Fruit** : akènes dans le calice, invisibles.
- **Au pied** : grandes feuilles basses, tombantes.
- **Jeu** : `height_cm` 70, rayon 30.
- **Distingue** : ×1, tache gris-vert piquée de bleu. ×4, larges feuilles rêches, étoiles bleues. ×8, poils, cône noir.

### Moutarde — `Mustard`

- **Port** : tige dressée, très ramifiée en haut, feuilles larges en bas, nue et fleurie en haut.
- **Réel** : 60-120 cm `[odg]`.
- **Tige** : verte, un peu glauque, fine pour sa hauteur.
- **Feuille** : alterne, large et lobée à la base, 10-20 cm `[odg]`, étroite et entière en haut.
- **Limbe, nervation** : tendre, lisse ; médiane claire.
- **Couleur** : vert clair, frais.
- **Fleur** : jaune vif, à 4 pétales, en grappes denses au sommet de chaque ramification.
- **Fruit** : siliques fines dressées le long de la tige ; moteur non `fruitier`.
- **Au pied** : les grandes feuilles forment une base large.
- **Jeu** : `height_cm` 60, rayon 30.
- **Distingue** : ×1, nuage jaune sur tige fine. ×4, grappes jaunes, feuilles larges en bas. ×8, siliques. Voir
  « Couples proches ».

### Armoise — `Mugwort`

- **Port** : grandes tiges dressées, en colonie, sombres, feuillage dense jusqu'à la panicule.
- **Réel** : 80-150 cm `[odg]`.
- **Tige** : rougeâtre, striée, ramifiée surtout en haut.
- **Feuille** : alterne, profondément découpée en lobes pointus, 5-10 cm `[odg]`.
- **Limbe, nervation** : deux faces qui comptent : dessus vert sombre, dessous blanc feutré. Au vent, l'argent se voit.
- **Couleur** : vert foncé argenté ; tige pourpre.
- **Fleur** : tardive, minuscule, en longue panicule jaunâtre à roussâtre.
- **Fruit** : même panicule, brune, l'hiver.
- **Au pied** : souche ligneuse, base des tiges nue et rouge.
- **Jeu** : `height_cm` 110, rayon 35.
- **Distingue** : ×1, colonne sombre pointue. ×4, feuilles découpées bicolores, tige rouge. ×8, dessous argenté.

### Chanvre — `Hemp`

- **Port** : grande tige élancée, fuselée, cime pointue, le plus haut du jardin.
- **Réel** : 150-400 cm `[odg]`.
- **Tige** : droite, fine, verte, cannelée, peu ramifiée quand les pieds sont serrés.
- **Feuille** : palmée, 5 à 9 folioles étroites et dentées, 10-20 cm `[odg]`, opposée en bas, alterne en haut.
- **Limbe, nervation** : foliole lancéolée en éventail : forme neuve, la seule du jardin.
- **Couleur** : vert sombre, assez uni.
- **Fleur** : verdâtre, discrète, en épis au sommet. Pas de couleur.
- **Fruit** : petits akènes, invisibles.
- **Au pied** : tige nue sur le quart bas.
- **Jeu** : `height_cm` 300, rayon 25.
- **Distingue** : ×1, longue flèche sombre et fine. ×4, mains à 7 doigts en étages. ×8, dents des folioles.

### Achillée — `Yarrow`

- **Port** : tiges raides en touffe peu dense, feuilles plumeuses, tête plate blanche.
- **Réel** : 30-60 cm `[odg]`.
- **Tige** : dressée, striée, peu ramifiée, un peu laineuse.
- **Feuille** : alterne, très finement divisée, en plume étroite, 5-10 cm `[odg]`.
- **Limbe, nervation** : aucun limbe lisible : un duvet de lanières.
- **Couleur** : vert grisé, doux.
- **Fleur** : corymbe plat, blanc cassé, 5-10 cm `[odg]`, serré, sans rayons distincts.
- **Fruit** : tête sèche brune, qui persiste.
- **Au pied** : tapis bas de feuilles plumeuses.
- **Jeu** : `height_cm` 40, rayon 30.
- **Distingue** : ×1, petite touffe grise surmontée de blanc. ×4, plateau blanc, plumes. ×8, grains du plateau.

### Consoude — `Comfrey`

- **Port** : grosse touffe large et feuillue, feuilles très grandes, tiges trapues. Voir écarts.
- **Réel** : 60-120 cm `[odg]`.
- **Tige** : épaisse, ailée, rêche, ramifiée en haut.
- **Feuille** : alterne, lancéolée, large et entière, 20-30 cm `[odg]` en bas, décurrente sur la tige.
- **Limbe, nervation** : rugueux, poilu, réseau de nervures creusées.
- **Couleur** : vert foncé, mat.
- **Fleur** : clochettes pendantes en crosse, crème à violet.
- **Fruit** : akènes noirs, invisibles.
- **Au pied** : grandes feuilles qui couvrent le sol ; aucune adventice sous elles.
- **Jeu** : `height_cm` 50, rayon 40.
- **Distingue** : ×1, large masse sombre, plus large que haute. ×4, grandes feuilles pointues, clochettes. ×8, gaufrage.

### Menthe — `Mint`

- **Port** : tiges dressées courtes, en colonie, densité égale, sans forme propre, sommets fleuris.
- **Réel** : 30-60 cm `[odg]`, en plaque qui s'étend par rhizomes.
- **Tige** : carrée, souvent violacée, 3 à 5 axes serrés `[choix]`.
- **Feuille** : opposée, ovale pointue, dentée, 3-8 cm `[odg]`, presque sans pétiole.
- **Limbe, nervation** : mat, un peu gaufré, nervures creusées, dents visibles.
- **Couleur** : vert moyen, mat, un peu bleuté.
- **Fleur** : petits épis mauve pâle, en bout de tige.
- **Fruit** : invisible.
- **Au pied** : pousses au sol autour des axes, pas de tige centrale.
- **Jeu** : `height_cm` 30, rayon 22.
- **Distingue** : ×1, petite plaque verte terne. ×4, paires dentées, épis mauves. ×8, tige violacée. Voir « Couples proches ».

## Chaumes

### Blé — `Wheat`

- **Port** : faisceau de chaumes droits partant de la base, tous à la même hauteur, épi dressé.
- **Réel** : 70-120 cm `[odg]`.
- **Tige** : chaume creux, à nœuds, vert puis doré, 5 à 8 brins `[choix]`.
- **Feuille** : ruban alterne, large de 1-2 cm `[odg]`, arqué, rare en haut.
- **Limbe, nervation** : nervures parallèles, trop fines pour se dessiner avant ×16.
- **Couleur** : vert franc, à peine glauque, qui vire au blond à maturité.
- **Fleur** : discrète, étamines pâles sur l'épi.
- **Fruit** : épi dense, compact, droit ou à peine penché, court ; sans barbes `[choix]`.
- **Au pied** : touffe tallée, feuilles sèches en bas à maturité.
- **Jeu** : `height_cm` 100, rayon 15. Stades `tallage`, `épiaison`, `mature`.
- **Distingue** : ×1, petit fagot droit vert ou doré. ×4, épis épais et droits. ×8, grains en deux rangs. Voir « Couples proches ».

### Seigle — `Rye`

- **Port** : faisceau plus haut, plus fin et plus souple que le blé, épi qui penche.
- **Réel** : 120-180 cm `[odg]`.
- **Tige** : chaume long et fin, un peu duveteux sous l'épi, qui plie.
- **Feuille** : ruban étroit, glauque.
- **Limbe, nervation** : idem blé.
- **Couleur** : vert glauque, bleuté, puis paille grisée à maturité.
- **Fleur** : anthères pendantes jaune pâle, visibles sur l'épi.
- **Fruit** : épi long, mince, penché, avec de longues barbes.
- **Au pied** : touffe tallée, plus lâche que le blé.
- **Jeu** : `height_cm` 160, rayon 15.
- **Distingue** : ×1, fagot haut, fin, bleuté, à pointe courbée. ×4, épis barbus penchés. ×8, barbes. Voir « Couples proches ».

### Pâturin annuel — `PoaAnnua`

- **Port** : très petite touffe souple, plus basse que tout autre chaume.
- **Réel** : 5-30 cm `[odg]`.
- **Tige** : fins chaumes couchés à la base, puis redressés.
- **Feuille** : ruban tendre, court, à bout en carène, 2-8 cm `[odg]`.
- **Limbe, nervation** : lisse, ligne médiane double, invisible.
- **Couleur** : vert clair, tendre, jaunissant.
- **Fleur** : panicule pyramidale, lâche, à petits épillets vert pâle, presque toute l'année.
- **Fruit** : épillets secs, paille.
- **Au pied** : touffe sans vide, au ras du sol.
- **Jeu** : `height_cm` 30, rayon 30 au catalogue ; dessiné à rayon 10 cm `[choix]`. Se distingue du dactyle et de la
  fétuque de prairie par son vert clair et sa panicule en triangle.
- **Distingue** : ×1, point vert clair. ×4, triangle ajouré au-dessus de la touffe. ×8, épillets.

### Bambou traçant — `RunningBamboo`

- **Port** : chaumes raides, verticaux, peu nombreux, arqués en tête, feuillage en panaches légers. Voir écarts.
- **Réel** : 4-8 m en sol fertile `[odg]`.
- **Tige** : cylindre lisse, vert puis jaunâtre, **nœuds marqués** à intervalles réguliers. 3 à 5 chaumes `[choix]`.
- **Feuille** : lancéolée, 8-15 cm `[odg]`, en éventails de 3-5 au bout de rameaux courts.
- **Limbe, nervation** : fin, retombant ; rien de lisible.
- **Couleur** : vert franc et frais ; chaume plus jaune.
- **Fleur** : absente en pratique. Le port ne dessine pas de fleur, même à `floraison` 1.
- **Fruit** : aucun.
- **Au pied** : gaines brunes aux nœuds du bas, jeunes pousses en cône.
- **Jeu** : `height_cm` 250, rayon 30. Moteur en stade `chaume`.
- **Distingue** : ×1, colonnes hautes et claires, panaches en haut. ×4, nœuds, éventails de feuilles. ×8, gaines.

## Couvre-sols

### Fraisier — `Strawberry`

- **Port** : petites touffes basses reliées par des stolons rouges qui courent au sol.
- **Réel** : 10-25 cm, stolons 30-100 cm `[odg]`.
- **Tige** : aucune lisible ; pétioles poilus, stolons rougeâtres.
- **Feuille** : trifoliolée, folioles ovales à grosses dents, 3-6 cm `[odg]`.
- **Limbe, nervation** : gaufré, nervures parallèles creusées, dents régulières.
- **Couleur** : vert moyen luisant.
- **Fleur** : blanche, 5 pétales ronds, cœur jaune, 2 cm `[odg]`.
- **Fruit** : fraise rouge, pendante, au ras des feuilles. Récolte par clic à vérifier au ④.
- **Au pied** : stolons qui sortent de la touffe et plantules à leur bout.
- **Jeu** : `height_cm` 15, rayon 18.
- **Distingue** : ×1, tache verte piquée de rouge. ×4, trois folioles dentées, stolons. ×8, gaufrage. Voir « Couples proches ».

### Violette odorante — `SweetViolet`

- **Port** : petite touffe plus dense et plus basse, feuilles en cœur, fleurs juste au-dessus.
- **Réel** : 5-15 cm `[odg]`.
- **Tige** : aucune ; stolons courts, verts.
- **Feuille** : simple, en cœur arrondi, à bord finement crénelé, 3-6 cm `[odg]`.
- **Limbe, nervation** : lisse, sombre, légèrement bombé ; la base du cœur est lisible à ×8.
- **Couleur** : vert foncé.
- **Fleur** : violet franc, 5 pétales inégaux, le bas en éperon, penchée, 1-2 cm `[odg]`, tôt au printemps.
- **Fruit** : petite capsule ronde, invisible.
- **Au pied** : pétioles serrés, pas de vide.
- **Jeu** : `height_cm` 12, rayon 14.
- **Distingue** : ×1, point sombre, violet au printemps. ×4, cœurs plats, fleurs violettes. ×8, éperon. Voir « Couples proches ».

### Minette, lupuline — `MedicagoLupulina` (renvoyée par D126)

- **Port** : tapis lâche et couché, tiges fines rampantes, sans centre lisible. Voir écarts.
- **Réel** : tiges 10-50 cm couchées, 5-20 cm de haut `[odg]`.
- **Tige** : fine, un peu velue, verte à rougeâtre.
- **Feuille** : trifoliolée, folioles ovales à petite pointe, 1-2 cm `[odg]`. Proche du trèfle, plus petite, foliole
  du milieu portée par un petit pétiole.
- **Limbe, nervation** : mat, sans marque blanche (ce qui la sépare du trèfle).
- **Couleur** : vert moyen, un peu jaune.
- **Fleur** : petite tête ronde jaune vif, 5 mm `[odg]`.
- **Fruit** : petite gousse enroulée, noire à maturité, en grappe.
- **Au pied** : tiges qui rayonnent, sol visible entre elles.
- **Jeu** : `height_cm` 30, rayon 25 au dernier stade [dérivé de la strate].
- **Distingue** : ×1, tache verte lâche à points jaunes. ×4, trèfles menus sans marque, têtes jaunes. ×8, gousses noires.

### Sphaigne — `Sphagnum`

- **Port** : coussin continu et bombé, sans tige ni feuille distinctes, comme une éponge.
- **Réel** : quelques cm au-dessus de l'eau, tapis sans limite `[odg]`.
- **Tige** : invisible ; capitules serrés.
- **Feuille** : aucune lisible.
- **Limbe, nervation** : surface grumeleuse de petites étoiles.
- **Couleur** : vert pâle jaunâtre à rouge cuivré, clair au sec, plus vif au mouillé.
- **Fleur** : aucune. Le port n'en dessine pas, même à `floraison` 1.
- **Fruit** : aucun.
- **Au pied** : rien ; le coussin touche le sol de partout.
- **Jeu** : `height_cm` 6, rayon 25.
- **Distingue** : ×1, tache plate pâle. ×4, grain d'étoiles. ×8, capitules. Nul autre tapis n'est sans feuille.

## Buissons et coussins

### Thym — `Thyme`

- **Port** : coussin bas, serré, ligneux, plus large que haut.
- **Réel** : 10-30 cm, 15-30 cm de rayon `[odg]`.
- **Tige** : rameaux grêles, bruns, tortueux, visibles à la base.
- **Feuille** : minuscule, 5-10 mm `[odg]`, opposée, en masse de grain fin.
- **Limbe, nervation** : aucun, grain seul.
- **Couleur** : gris-vert sombre.
- **Fleur** : petites têtes mauve pâle, à ras du coussin, sans hampe.
- **Fruit** : invisible.
- **Au pied** : bois brun nu, tortueux, sur les vieux pieds.
- **Jeu** : `height_cm` 25, rayon 25.
- **Distingue** : ×1, petit dôme gris sombre. ×4, grain fin, mauve collé au coussin. ×8, bois tortueux. Voir « Couples proches ».

### Lavande — `Lavender`

- **Port** : boule de feuilles linéaires, hérissée de longues hampes nues.
- **Réel** : 40-70 cm, 30-50 cm de rayon `[odg]`.
- **Tige** : bois gris à la base, hampes vertes fines et droites, en gerbe.
- **Feuille** : linéaire, étroite, 3-5 cm `[odg]`, dressée.
- **Limbe, nervation** : aucun ; duvet gris.
- **Couleur** : gris bleuté, clair.
- **Fleur** : épi violet serré, au bout d'une hampe nue, qui dépasse le coussin de 15-25 cm `[odg]`.
- **Fruit** : épi sec gris-brun, sur hampe, à l'automne.
- **Au pied** : souche ligneuse grise, tordue.
- **Jeu** : `height_cm` 50, rayon 40. Masse sur 60 % de la hauteur `[choix]`, hampes au-dessus.
- **Distingue** : ×1, dôme gris bleu frangé de violet. ×4, gerbe de hampes rayonnantes. ×8, épis. Voir « Couples proches ».

### Myrtille — `Vaccinium`

- **Port** : petit buisson bas, ouvert, en balai, à rameaux verts anguleux.
- **Réel** : 20-60 cm `[odg]`.
- **Tige** : rameaux dressés, verts, à arêtes, ramifiés en balai.
- **Feuille** : alterne, ovale fine, 1-3 cm `[odg]`, à bord finement crénelé.
- **Limbe, nervation** : mince, vert clair ; réseau invisible.
- **Couleur** : vert frais ; rouge vif à l'automne (caduc).
- **Fleur** : petit grelot rose pâle, penché, à l'aisselle.
- **Fruit** : baie bleu-noir pruineuse, 6-10 mm `[odg]` ; moteur non `fruitier`.
- **Au pied** : souche courte, tapis possible.
- **Jeu** : `height_cm` 40, rayon 30.
- **Distingue** : ×1, petit buisson vert clair, rouge en automne. ×4, rameaux verts en balai. ×8, grelots.

### Framboisier — `Raspberry`

- **Port** : cannes dressées, arquées en haut, en fourré, chacune à peine ramifiée.
- **Réel** : 100-200 cm `[odg]`.
- **Tige** : canne ronde, brune au fil de l'âge, finement épineuse, 4 à 7 `[choix]`.
- **Feuille** : alterne, à 3-5 folioles dentées, 5-10 cm `[odg]`, dessous blanc.
- **Limbe, nervation** : gaufré, dessus vert, dessous blanc qui se voit au vent.
- **Couleur** : vert moyen, avec pointes blanches.
- **Fleur** : petite, blanche, à pétales étroits, pendante.
- **Fruit** : framboise rouge, sur le côté des cannes. Récolte par clic à vérifier au ④.
- **Au pied** : nouvelles cannes vertes qui sortent de terre autour des anciennes.
- **Jeu** : `height_cm` 150, rayon 30.
- **Distingue** : ×1, gerbe haute en arc. ×4, cannes arquées, folioles. ×8, épines, dessous blanc.

## Grande rampante

### Courgette — `Zucchini`

- **Port** : grosse touffe sans tige lisible, immenses feuilles palmées, large et basse.
- **Réel** : 40-70 cm de haut, 50-100 cm de rayon `[odg]`.
- **Tige** : courte, grosse, côtelée, rampante ; longs pétioles creux et piquants.
- **Feuille** : palmée à 5 lobes, 25-40 cm `[odg]`, portée par son pétiole, nettement la plus grande du jardin.
- **Limbe, nervation** : rêche, marbré de taches argentées le long des nervures.
- **Couleur** : vert foncé, marbré d'argent.
- **Fleur** : grosse trompette jaune orangé, 10-15 cm `[odg]`, au centre.
- **Fruit** : allongé, vert sombre, 15-25 cm `[odg]`, posé au sol au centre de la touffe. Récolte par clic à vérifier au ④.
- **Au pied** : ombre dense, sol à peine visible.
- **Jeu** : `height_cm` 45, rayon 60. Un seul port, qui ne court pas.
- **Distingue** : ×1, large tache sombre. ×4, 5 à 8 grandes mains et une trompette. ×8, marbrure argent.

## Volubile

### Haricot — `Bean`

- **Port** : sur support, tige en spirale autour du tuteur, feuilles qui s'écartent. Sans support, tas emmêlé bas.
- **Réel** : variété à rames, 150-300 cm `[odg]`.
- **Tige** : fine, verte, s'enroulant toujours dans le même sens, à pas régulier.
- **Feuille** : alterne, trifoliolée, folioles en cœur pointu, 6-12 cm `[odg]`.
- **Limbe, nervation** : mat, un peu rêche, médiane claire.
- **Couleur** : vert franc, moyen.
- **Fleur** : papilionacée, blanche ou mauve `[choix : blanc]`, en petites grappes à l'aisselle.
- **Fruit** : gousse pendante, fine, 10-20 cm `[odg]`, verte ; moteur non `fruitier`.
- **Vrilles** : aucune, c'est la tige qui s'enroule (le moteur le nomme pourtant `vrille_volubile`).
- **Au pied** : tige seule, support visible.
- **Jeu** : `height_cm` 200, rayon 25. Lit `support` au snapshot. Sur `planche_especes`, aucun support : c'est le tas.
- **Distingue** : ×1, trait penché en zigzag, ou petit tas. ×4, spires, triades de feuilles. ×8, grappes.

## Segments conservés

Ces trois espèces gardent leurs segments et leur taille au segment. La fiche guide feuilles et fleurs au ⑥.

### Tomate — `Tomato`

- **Port** : tige longue et velue, faible, qui s'affaisse sans tuteur, grands bouquets de feuilles.
- **Réel** : 100-200 cm sur tuteur `[odg]`.
- **Tige** : verte, velue, assez épaisse, odorante.
- **Feuille** : alterne, composée, 15-30 cm `[odg]`, à folioles inégales et profondément dentées.
- **Limbe, nervation** : gaufré, mat, un peu velu.
- **Couleur** : vert moyen à sombre, un peu gris.
- **Fleur** : petite étoile jaune, à pétales rabattus, en grappes.
- **Fruit** : rouge, rond, en grappes, de 3 à 8 cm `[odg]` selon la variété.
- **Au pied** : feuilles basses souvent jaunies.
- **Jeu** : `height_cm` suit la structure (84,5 après un an, sans lumière ni gènes, seed du banc), rayon 18.
- **Distingue** : ×1, trait vert et points rouges. ×4, feuilles découpées, grappes. ×8, poils.

### Lierre — `Ivy`

- **Port** : tiges collées au mur ou au tronc, feuilles plaquées en tapis ; au sol, nappe rampante.
- **Réel** : plusieurs mètres `[odg]`.
- **Tige** : brun-vert, garnie de crampons ; forte et ligneuse sur le vieux pied.
- **Feuille** : alterne, coriace, 3 à 5 lobes en triangle, 4-10 cm `[odg]` ; entière et ovale sur le bois fleuri.
- **Limbe, nervation** : sombre, luisant, nervures nettement plus pâles : le motif de l'espèce.
- **Couleur** : vert très sombre, persistant.
- **Fleur** : ombelles rondes vert-jaune, à l'automne, sur le vieux bois.
- **Fruit** : baie noire, en boule, en hiver ; moteur non `fruitier`.
- **Vrilles** : aucune ; crampons le long de la tige, à ×8 seulement.
- **Au pied** : nappe de feuilles autour du départ.
- **Jeu** : stade `mature` 300 cm d'empreinte, 84,5 cm de structure à 1 an, plus à 3 ans. Sans support : au sol.
- **Distingue** : ×1, plaque sombre au sol ou au mur. ×4, feuilles lobées luisantes, serrées. ×8, nervures pâles.

### Jasmin — `Jasmine`

- **Port** : sarments longs, souples et fins, retombants sans palissage, feuillage léger.
- **Réel** : 3-6 m palissé `[odg]`.
- **Tige** : verte, fine, anguleuse, arquée.
- **Feuille** : opposée, composée, 5 à 9 folioles pointues, 4-8 cm `[odg]`.
- **Limbe, nervation** : lisse, rien de lisible.
- **Couleur** : vert franc, léger ; caduc.
- **Fleur** : blanc pur, en étoile à 5 pétales, en petits bouquets, 2 cm `[odg]`, très nombreux.
- **Fruit** : baie noire rare, absente au moteur.
- **Vrilles** : aucune ; il faut le palisser (`sarmenteux`).
- **Au pied** : quelques tiges fines, sol visible.
- **Jeu** : stade `mature` 250 cm d'empreinte, rayon moteur 45 ; 84,5 cm de structure à 1 an, plus à 3 ans.
- **Distingue** : ×1, trait léger et points blancs. ×4, folioles, étoiles blanches. ×8, pétales.

## Couples proches

- **Blé / seigle** : le seigle est 60 % plus haut (160 cm contre 100), plus fin et plus souple ; bleuté contre vert
  franc, paille grise contre blond. Épi du blé épais, droit, sans barbes `[choix]` ; épi du seigle long, mince,
  penché, barbu. À ×1 : hauteur et pointe courbée.
- **Thym / lavande** : deux coussins gris, mais le thym est deux fois plus bas (25 cm contre 50), plus sombre, à grain
  fin, mauve pâle collé au coussin. La lavande est plus claire et bleutée, à feuilles lisibles et longues hampes nues
  qui dépassent, violet franc en bout. À ×1 : la frange de hampes.
- **Moutarde / bourse-à-pasteur** : même famille, mais la moutarde est un nuage ramifié jaune vif sur une tige
  feuillue en bas, sans rosette. La bourse est un fil presque nu au-dessus d'une rosette plate, fleurs blanches
  infimes, chapelet de cœurs. À ×1 : tache jaune contre trait presque invisible.
- **Menthe / basilic** : deux tiges carrées à feuilles opposées. Le basilic est une boule vert vif, à feuilles
  bombées et luisantes, sans dents, épis blancs. La menthe est une plaque mate, plus sombre, à feuilles dentées et
  gaufrées, tiges violacées, épis mauves. À ×1 : vif et rond contre terne et plat.
- **Fraisier / violette** : le fraisier a trois folioles dentées vert moyen, des stolons rouges, une fleur blanche, un
  fruit rouge. La violette a une feuille simple en cœur vert foncé, plus petite et plus basse, une fleur violette.
  À ×1 : point rouge contre point violet ; hors fleur et fruit, vert moyen contre vert foncé.
