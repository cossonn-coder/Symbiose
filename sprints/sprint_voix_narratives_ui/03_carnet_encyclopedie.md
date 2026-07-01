# ③ Panneau Carnet + panneau Encyclopédie

> Lire d'abord `00_etat.md` + `CONCEPTION_VOIX_NARRATIVES_UI.md` (§1, §3, §5).
> Tronçon **C# pur**. Dépend du ① (commandes pont) et du ② (`SimBridge` + nœud
> `VoicePanel` + hub). Filet = `dotnet build`. **INVARIANT** : affichage
> **verbatim** du texte renvoyé par Python ; le C# ne concatène/ne reformule rien.

## Objectif
Remplir deux `VoicePanel` avec le contenu réel des voix : le **Carnet** (liste
filtrable par concept) et l'**Encyclopédie** (index → fiche 3 niveaux). Golden
intact.

## À faire

### A. Panneau Carnet (`SimBridge.Carnet`)
- Appeler `Carnet()` → liste d'entrées `{semaine, zone, concept, registre, texte}`.
  Afficher chaque entrée **verbatim** (le `texte` porte déjà le bon registre :
  descriptif, ou interprétatif au palier 3 du concept — décidé côté Python, NE PAS
  re-décider en C#).
- **Filtre par concept** : un sélecteur listant les `concept` présents ; re-appeler
  `Carnet(filtreConcept)` (le pont passe `filtre={"concept": …}`). Filtres `zone`/
  `saison` = optionnels/backlog visuel, non requis ici.
- Affichage minimal lisible : semaine + concept en tête de ligne, texte en dessous ;
  zone défilante. Deux registres visuellement distincts si trivial (ex. italique
  pour l'interprétatif) — sans changer le texte.

### B. Panneau Encyclopédie (`SimBridge.Encyclopedie`)
- **Index** : `Encyclopedie()` → `list[str]` d'espèces (palier ≥ 1, ordre corpus).
  Liste cliquable.
- **Fiche** : au clic, `Encyclopedie(espece)` → `{espece, niveau_max, niveaux:{n:
  texte}}`. Afficher les niveaux **1..niveau_max** verbatim (N1 basique / N2 bio /
  N3 écosystémique) ; les niveaux au-dessus de `niveau_max` restent masqués (le
  joueur ne les a pas débloqués — ne PAS inventer de placeholder textuel).
- Retour à l'index (bouton). Gérer le cas `None` (espèce non découverte) sans
  crash.

## Definition of done
- `dotnet build` **vert**.
- Depuis le hub : Carnet ouvre la liste filtrable ; Encyclopédie ouvre l'index →
  fiche N1/N2/N3. Tout le texte vient de Python, aucun littéral narratif en C#.
- Golden `ae445d3f…` intact (aucun Python touché).
- LDC C# maîtrisé (un panneau = un fichier/responsabilité). MAJ `00_etat.md` (③) +
  commit.
