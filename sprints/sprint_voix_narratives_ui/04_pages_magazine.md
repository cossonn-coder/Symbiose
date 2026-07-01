# ④ Panneau Pages + panneau Magazine (achat bout-en-bout)

> Lire d'abord `00_etat.md` + `CONCEPTION_VOIX_NARRATIVES_UI.md` (§1, §3, §5).
> Tronçon **C# pur**, dernier avant F5. Dépend de ①②③. Filet = `dotnet build`.
> **INVARIANT** : texte des pages/fiches affiché **verbatim** ; seul l'achat MUTE
> l'état (via `cmd_action`, chemin Vigueur unique).

## Objectif
Remplir les deux derniers `VoicePanel` : les **Pages secrètes** (coffret du
grenier, voix multiples) en lecture, et le **Magazine** (offres → fiche → **achat
complet** : Vigueur débitée, graine en banque). Golden intact.

## À faire

### A. Panneau Pages (`SimBridge.Pages`)
- Appeler `Pages()` → pages TROUVÉES (id + texte + voix, dans `ORDRE`). Afficher
  chaque page **verbatim** ; le champ `voix` (poème / savoir paysan / herbier /
  citation…) peut styler l'en-tête, sans toucher le texte.
- Registre **téléologique assumé** = responsabilité du corpus Python — le panneau
  ne « corrige » rien.
- Aucune révélation déclenchée ici : les pages arrivent par le robinet
  « récompense » au palier (câblé au ①, côté pont). Le panneau est un **lecteur**.
  (Robinets hasard/fouille + marqueurs bouture/oiseau/vent = D54.)
- Habillage « coffret au grenier de la maison » cohérent avec le hub (entrée Pages).

### B. Panneau Magazine (`SimBridge.MagazineOffres/Fiche/Acheter`)
- **Offres** : `MagazineOffres()` → `list[str]` (sœurs palier ≥ 3 hors banque).
  Liste cliquable.
- **Fiche** : au clic, `MagazineFiche(espece)` → `{espece, niveau_max, niveaux}`
  (n'exige PAS gs/player). Afficher verbatim.
- **Achat bout-en-bout** : bouton « Acheter » → `AcheterMagazine(espece)` (passe par
  `cmd_action` verbe `acheter_magazine`). Au retour :
  - succès → rafraîchir la Vigueur affichée (le `bilan` porte `vigueur`/
    `vigueur_max`), retirer l'espèce des offres, feedback « ajoutée à la banque » ;
  - refus (offre fermée / Vigueur insuffisante → `ok=False`) → message sobre, aucune
    mutation. Ne PAS ré-implémenter le gate en C# (le pont décide).

## Definition of done
- `dotnet build` **vert**.
- Depuis le hub : Pages affiche les pages trouvées ; Magazine affiche offres →
  fiche → **achat qui débite la Vigueur et ajoute la graine** (vérifiable au
  `bilan`/à la banque au snapshot suivant).
- Golden `ae445d3f…` intact (aucun Python touché).
- LDC C# maîtrisé. MAJ `00_etat.md` (④ = sprint moteur/vue FAIT, reste F5 Nico) +
  commit. **Rappeler à Nico le F5** : hub 5 entrées (3 grisées), 4 panneaux, achat
  bout-en-bout.
