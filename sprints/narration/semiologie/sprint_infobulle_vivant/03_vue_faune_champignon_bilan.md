# Tronçon ③ — Vue faune & champignon : nom, rôle, état + bilan F5

> Lire d'abord `CLAUDE.md`, `00_etat.md` (formes snapshot / légende livrées par ①) et
> `docs/narration/semiologie/conception_infobulle_vivant.md` (§2, §3, §4.2).
> Golden **INTACT**. Filet : `dotnet build Symbiose.csproj` ; capture `tools/capture_vm.sh`.
> Jamais `test_epaisseur_500ans`. Dernier tronçon = tronçon vue (règle permanente).

## Objectif
Survoler une bête ou un carpophore donne, en peu de mots, ce qu'on voit, combien il y en a,
puis — une fois appris au fil des saisons — son nom, son rôle et s'il a de quoi manger.

## À faire
1. **Picking enrichi** : `MacroLife.SpeciesNear` / `ForagerLayer.SpeciesNear` /
   `CarpophoreLayer.HasNear` ne rendent qu'une clé ou un booléen. Il faut l'entrée la plus
   proche : clé, plot, `activite` (bête), rôle + densité (carpophore). Étendre sans
   dupliquer le parcours (un seul balayage, comme aujourd'hui) ; `BeteSousSouris` reste le
   point unique partagé par l'observation et l'info-bulle (`world/WorldView.Observation.cs`).
2. **Abondance** = nombre d'entrées vivantes de la même espèce dans le **même plot** que
   l'entrée survolée (ce que la vue affiche). Libellés de la légende ① (1 / 2-3 / ≥ 4).
3. **Lignes** (tableau §3 de la conception), textes tous issus de la légende ① :
   - bête non apprise : `vu · abondance` ;
   - bête apprise : `Nom — rôle · abondance, nourriture` (nourriture = bande de
     `activite` selon les bornes ①) ;
   - carpophore non appris : `vu champignon · réseau` (densité → clairsemé / dense) ;
   - carpophore appris : `Champignon — rôle local · réseau`.
   - Butineurs : si ① n'a pas pu leur donner de ressource, pas de nourriture (ligne sans).
4. **Technique** (Maj+F3) : nom dès le 1er survol + chiffres (`abondance n · activite x.xx`,
   `rôle · densité x.xx`).
5. **Observation saisonnière** : `_especesMacroObservees` (une fois par session) bloque le
   crédit des saisons suivantes → dédup par **(clé, saison)**, saison calculée comme
   `ObserverSigne` (même formule, la factoriser si elle sert deux fois). Après une réponse
   pont qui franchit un palier, relire `appris` (comme `RelireAppris`) pour que le nom
   apparaisse sans attendre la semaine suivante — vérifie d'abord ce que renvoie `observer`
   après ①.
6. **Bilan + F5** : captures ×4 (bête non apprise, apprise via debug `palier3`, carpophore
   bois / humus, technique) dans `mesures/` ; `00_etat.md` §F5 = procédure courte pour Nico
   (quoi survoler, quoi doit apparaître, comment forcer l'automne / les paliers en debug).
   Clôture : `journal.md` (+ entrée `journal/`), `DETTE.md` (D110 a·b·g → fermés, D110
   archivée si plus rien d'ouvert, sinon reste c·d·e·f), `BACKLOG.md`.

## NE PAS
- Inventer un état non fourni par le snapshot (pas de santé animale).
- Texte en dur côté C#.
- Changer le dessin de la vie macro ou des carpophores.

## Fin de tronçon
`dotnet build` vert, golden intact, `00_etat.md` à jour. Commit.
