# ⑥ `epandre` 2 clics + vue Godot (carpophores, tas colonisé, overlay)

> Lire d'abord `00_etat.md` + `docs/conception/CONCEPTION_MYCELIUM_INTERCONNEXIONS.md`
> (§3.2, §4). Prérequis : ①→⑤ FAITS (moteur clos). Tronçon **vue + protocole pont**
> — **Godot DIFFÉRÉ** (intégration en pause). La vue ne touche AUCUN champ
> écologique → **golden trivialement NEUTRE**. Filet = `dotnet build Symbiose.csproj`,
> F5 visuel = Nico.

## Objectif
Rendre VISIBLE l'acteur mycélium : `epandre` en **2 clics** (bac → plot),
**carpophores** après la pluie, **tas colonisé** (avancement de maturation + voile
fongique), **palette overlay `mycelium`** (F6). Le réseau souterrain reste invisible
hors debug.

## À faire

### A. `epandre` 2 clics — protocole pont (`tools/simserver`, `WorldView`)
- Le MOTEUR gère déjà `q=None ⇒ tout` + bornage `compost_mur` (`compost.py:epandre`).
  Le neuf = **UX à 2 cibles** : clic sur le bac (source) → clic sur le plot (cible).
- Côté C# : geste **à 2 temps** (patron `deplacer_pot` du sprint pots/bacs ⑥b :
  1er clic saisit la source, 2e clic = destination). Câbler dans
  `world/WorldView.Actions.cs`. Le verbe `epandre` existe déjà au pont — vérifier/
  étendre le routage pour accepter source + cible (incrément de protocole si besoin).

### B. Carpophores (sprites échantillonnés, exposés en ④)
- Lire la liste `carpophores` du snapshot (④) et dessiner des sprites champignons
  là où c'est dense+humide+automne. Patron de rendu = vie macro (`MacroLife.cs`) /
  structures compost. Perception pure, aucun retour moteur.

### C. Tas colonisé
- Bac/pile montrent leur **avancement de maturation** (frais → en cours → mûr, ⑤) et
  un **voile fongique** quand le mycélium les habite. Étendre le rendu des structures
  compost existant (`visuals/CompostStructure.cs` + `WorldView.Compost.cs`).

### D. Palette overlay `mycelium` (F6)
- Le champ `mycelium` est exposé AUTO au registre `fields` par introspection (①) →
  ajouter une **palette/teinte** côté `visuals/FieldOverlay.cs` pour le visualiser en
  heatmap debug (souterrain visible uniquement en mode technique).

## Couches
100 % VUE (C#) + éventuel incrément de protocole pont (`tools/simserver`, lecture/
routage). AUCUN fichier de simulation `fields/`/`sim/` touché côté écologie.

## Définition de done
- `epandre` 2 clics opérationnel (geste 2 temps), carpophores rendus, tas colonisé
  (maturation + voile), overlay `mycelium` F6.
- `dotnet build Symbiose.csproj` **vert** (0 erreur). Golden **trivialement NEUTRE**
  (aucun fichier Python écolo touché ; si incrément protocole, re-mesurer = inchangé).
- Sections « Points à VALIDER au F5 (Nico) » ajoutées à `00_etat.md` (lisibilité
  carpophores, voile fongique, ergonomie `epandre` 2 temps, palette overlay).
- MAJ `00_etat.md` (⑥ → FAIT + **SPRINT mycélium CLOS, vue comprise**) puis commit.

## Pièges
- **Godot en pause** : ce tronçon peut rester en attente après ⑤ (moteur clos,
  jouable au pont). Ne pas bloquer la clôture du moteur dessus.
- La vue ne RECALCULE rien : carpophores et voile sont DÉRIVÉS du snapshot. Si un
  rendu a besoin d'une donnée absente, l'EXPOSER au pont (lecture), pas la recalculer
  en C#.
- `epandre` : ne pas réimplémenter le bornage `compost_mur` côté C# (le moteur le
  fait) — la vue n'envoie que source + cible.
- Vérifier l'incrément de version de protocole (`ENGINE_VERSION`) si le snapshot
  change (carpophores, colonisation du tas).
