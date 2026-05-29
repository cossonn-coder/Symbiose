# Sprint 4 — Intégration des mécaniques du Sprint conception

**Statut** : à faire (esquissé, à détailler quand Sprint 3 sera terminé)
**Prérequis** : Sprint 3 terminé (simulation C# en parité avec Python),
**et** Sprint conception bis terminé (sauvegarde, météo, etc. tranchés)
**Estimation** : 4 à 8 sessions (sprint le plus complet)
**Objectif** : implémenter en C# les 6 mécaniques centrales nouvelles
issues du Sprint conception du 2026-05-29 — Vigueur, paliers de maîtrise,
encyclopédie, carnet auto, magazine de botanique, foyer dans la maison.

---

## Avant de commencer

1. **`CLAUDE.md`** : section « Mécaniques centrales » est la spécification
   métier à respecter
2. **`journal.md`** — entrée « Sprint conception » du 2026-05-29 :
   les 12 décisions structurantes en détail
3. **Memory** — `project_game_vision.md` est la référence courte
4. **Code à étendre** :
   - `core/GameManager.cs` — étendre l'état global avec
     `PlayerVigueur`, `MasteryLevels`, `Encyclopedia`, `Notebook`
   - `core/EcologySystem.cs` — la Vigueur des plantes/auxiliaires/
     nuisibles doit s'inscrire dans le tick
   - `data/code/*.py` — propager toute nouvelle mécanique vers Python
     en parallèle (voir [[project-python-source]])

---

## Mission

Le Sprint conception a posé une vision riche que le moteur Python actuel
ne porte pas. Ce sprint instancie cette vision en code, **en propageant
chaque nouvelle mécanique vers Python ET C#** pour ne pas re-creuser
la dette D10.

C'est le sprint où **Symbiose v2 devient jouable** au sens où le joueur
peut interagir avec les nouvelles mécaniques.

---

## Lots de travail (à séquencer plus précisément quand on y arrive)

### Lot V — Vigueur universelle (dette D11)
- Modèle de données :
  - Joueur : `int CurrentVigueur, MaxVigueur` (max augmente avec
    maîtrise, voir lot M)
  - Plantes : déjà `vigueur_cost` par stade dans `models.py` ; ajouter
    une réserve courante `CurrentVigueur` à `PlantInstance`
  - Auxiliaires, nuisibles : `CurrentVigueur` aussi
- Sources de régénération joueur : +10/sem, full au passage de saison,
  récolte plante mûre, méditation au foyer
- Coûts : chaque action joueur consomme un montant à définir
- À propager vers `models.py` (Python) en parallèle

### Lot M — Paliers de maîtrise (dette D12)
- Granularité : par famille botanique (Solanaceae, Fabaceae, etc.) +
  par concept écologique (succession, polyculture, eau, compost, sol,
  lumière…)
- 5 paliers : découverte → investissement → maîtrise → expertise →
  transcendant
- Conditions de passage à définir précisément (XP-like ?
  événements-objectifs-like ? les deux ?)
- Effets : déblocage magazine, extension terrain, bascule carnet
  descriptif → interprétatif, augmentation Vigueur max joueur

### Lot E — Encyclopédie ingame (lié D13)
- Catalogue des espèces (déjà dans `PlantCatalogue.cs`) avec niveau de
  découverte par espèce :
  - 0 = inconnue
  - 1 = vue (entrée basique : nom, sprite)
  - 2 = cycle complet observé (description biologique)
  - 3 = plusieurs cycles avec succès (effets écosystémiques)
- UI : panneau accessible depuis la maison (T4)
- Pas un fichier Markdown statique — c'est généré depuis les données +
  un fichier de texte par espèce

### Lot C — Carnet auto (dette D14)
- Enregistrement automatique d'événements significatifs :
  actions joueur, événements écologiques notables (germination, mort,
  conflit, aléa météo, atteinte d'un palier)
- Format de stockage : JSON ou format binaire compact (selon décision
  sauvegarde Sprint conception bis)
- UI : panneau consultable, indexé par saison/année, recherche par
  espèce/lieu/type d'événement
- Bascule descriptif → interprétatif au seuil de maîtrise correspondant
  (le carnet ajoute des hypothèses de causalité quand le concept est
  maîtrisé)

### Lot G — Magazine de botanique (dette D13)
- UI : panneau de la maison, liste d'éléments déblocables
- Pour chaque entrée : coût Vigueur, palier de maîtrise requis,
  description, image
- Achat : consomme Vigueur joueur, ajoute l'espèce dans l'inventaire de
  semis disponible (lot V de Sprint conception bis sur les semis ?)
- L'encyclopédie pré-remplit l'entrée à l'achat (la connaissance précède
  la possession)

### Lot F — Foyer dans la maison
- Sprite intérieur de la maison (placeholder en attendant l'art)
- Action « méditer » : consomme une fraction de tour, restaure une
  partie de la Vigueur
- Visuel chaleureux — feu de cheminée, ambiance contemplative
- Premier dispositif narratif (lien avec décisions Sprint conception bis
  sur le lore)

### Lot X — Extension terrain par maîtrise (dette D15)
- À l'atteinte du palier maîtrise sur une famille botanique, une tuile
  thématique apparaît :
  - Solanaceae → serre / coin chaud
  - Fabaceae → légumière
  - Asteraceae → prairie mellifère
  - Lamiaceae → coin aromatique
  - Poaceae → friche basse / prairie
  - etc.
- Position : périphérie du jardin 3×3 initial
- La tuile s'inaugure visuellement avec un effet (ne pas spammer)

---

## Pièges connus

- **Le moteur Python doit suivre** (canon — voir [[project-python-source]]).
  Concevoir chaque mécanique côté Python d'abord, ou simultanément.
- **L'UI est lourde** — ce sprint touche à beaucoup de panneaux. Ne pas
  négliger l'UX : pause libre, notifications, zoom contextuel sont déjà
  des contraintes (cf `CLAUDE.md` Mécaniques centrales > UX).
- **La Vigueur joueur** est centrale — sans elle, tous les autres lots
  perdent leur sens économique. Commencer par le lot V.
- **Tests à chaque lot** : éviter le big bang. Chaque lot doit pouvoir
  être validé indépendamment.

---

## À produire à la fin

- [ ] Code C# pour chaque lot + propagation Python
- [ ] **`journal.md`** : entrée datée, dettes D11/D12/D13/D14/D15 ✅ levées
- [ ] Tests de comportement écologique (la nouvelle Vigueur ne casse pas
      la simulation existante)
- [ ] Sauvegarde fonctionnelle (selon décision Sprint conception bis)
- [ ] **Commit** dédié ex :
      `Sprint 4 : intégration des mécaniques du Sprint conception`
- [ ] Proposer le sprint suivant à Nico (jeu jouable de bout en bout,
      polish, équilibrage, intégration version physique…)

---

## Critère de fin

Le joueur peut, dans Godot 4.6 :
1. Démarrer un nouveau jardin (choix entre 3 écoles)
2. Naviguer à la maison, consulter encyclopédie, carnet, magazine, foyer
3. Posséder une réserve de Vigueur qui se régénère
4. Acheter une espèce dans le magazine si Vigueur + maîtrise suffisantes
5. Atteindre le palier maîtrise sur au moins une famille → voir une
   tuile thématique apparaître
6. Voir le carnet basculer en mode interprétatif quand un seuil est
   franchi
7. Sauvegarder et reprendre son jardin sans perte
