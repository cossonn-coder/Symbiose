# ② SimBridge C# + nœud VoicePanel + hub-maison cliquable

> Lire d'abord `00_etat.md` + `docs/narration/voix/conception_voix_narratives_ui.md` (§1 invariant, §5
> archi C#). Tronçon **C# pur** (couche vue). Dépend du ① (commandes de pont
> présentes). Filet de compil = `dotnet build Symbiose.csproj` sur la VM (F5 visuel
> = Nico). **INVARIANT** : le C# ne fait que de la mise en page, jamais de texte.

## Objectif
Poser l'**ossature de présentation** sans encore remplir les panneaux : (A) une
méthode `SimBridge` par commande voix ; (B) un nœud `VoicePanel` réutilisable ; (C)
le hub-maison cliquable (menu 5 fonctions, non-voix grisées). `dotnet build` vert.
Golden intact (aucun Python touché).

## À faire

### A. `core/SimBridge.cs` — une méthode par commande
Sur le modèle des méthodes existantes (`Init`/`StepWeek`/`GetSnapshot`/`Action`/
`Fields`/`ListBancs`, pipe stdin/stdout synchrone, `Request(GDict)`), ajouter :
- `Carnet(string filtreConcept = null)` → tableau d'entrées ;
- `Encyclopedie(string espece = null)` → index (liste) ou fiche (dict) ;
- `Pages()` → liste de pages trouvées (id + texte + voix) ;
- `MagazineOffres()` / `MagazineFiche(string espece)` ;
- `AcheterMagazine(string espece)` → passe par `Action("acheter_magazine", …)`
  (verbe `cmd_action`, cohérent Q3) et renvoie le `snapshot`/`bilan`.
Chaque méthode construit le `GDict` de requête, envoie, renvoie la réponse
désérialisée telle quelle (pas de reformulation).

### B. Nœud `VoicePanel` réutilisable (`world/` ou `ui/`)
- `CanvasLayer` plein écran, **pause-aware** : à l'ouverture, mettre la simulation
  en pause (temps figé — on consulte le carnet la partie arrêtée, cohérent boucle
  hybride) ; à la fermeture, restaurer l'état précédent.
- Squelette de contenu générique (titre + zone défilante + bouton fermer) que ③④
  spécialisent. Aucun appel voix encore (panneaux vides / « à venir »).
- Un seul `VoicePanel` actif à la fois (le menu hub route vers le bon contenu).

### C. Hub-maison cliquable (`world/WorldView.*`)
- Rendre la maison (placeholder `Polygon2D`, D4) **cliquable** : un clic ouvre un
  petit menu **5 fonctions** (Atelier · Semis intérieur · Magazine · Carnet ·
  Foyer — cf. CLAUDE.md « Maison normande hub »).
- Entrées **actives** : Carnet, Encyclopédie, Magazine, Pages (ouvrent un
  `VoicePanel`). ⚠️ La maison a 5 fonctions design mais 4 VOIX + Pages : afficher
  Carnet / Encyclopédie / Magazine / **Pages** (coffret grenier) comme entrées
  voix ; **Atelier / Semis intérieur / Foyer** = entrées **grisées « à venir »**
  (micro-déc. A → dette D54). Ne pas inventer leur comportement.

## Definition of done
- `dotnet build Symbiose.csproj` **vert** (0 err ; warnings idéalement 0).
- Clic maison → menu ; les 4 entrées voix ouvrent un `VoicePanel` (vide, titré) ;
  les 3 entrées non-voix sont visibles mais grisées/inertes.
- Aucun fichier Python touché → golden `ae445d3f…` trivialement intact.
- LDC C# : un fichier = une classe/responsabilité (`compte_ldc.py`), `partial`
  `WorldView` si besoin. MAJ `00_etat.md` (②) + commit.
