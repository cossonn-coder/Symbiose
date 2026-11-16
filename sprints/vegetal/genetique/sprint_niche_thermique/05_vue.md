# ⑤ Vue Godot — postures, teintes, banc `niche_thermique`

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, puis
> `docs/vegetal/genetique/conception_niche_thermique.md` §6 et §7 (effets attendus).
> Golden attendu : **INTACT** (vue seulement).

## Objectif
Que Nico voie la gamme thermique au F5 et vérifie le basilic.

## À faire
1. **Rendu** (`visuals/PlantRenderer*.cs` ; lire d'abord `PlantRenderer.Froid.cs` et
   `PlantRenderer.Meteo.cs`, rendus froid et météo existants à étendre plutôt que dupliquer ;
   palette maître de la DA pixel-art) : `posture_thermique` pilote l'angle des feuilles (pendantes ↔ étalées ↔
   repliées de profil) et la teinte (violacé, translucide, noirci ; jaune aux bords, brûlé).
   Marques `froid` et `brulure` comme les marques existantes. Respecter la précuisson par
   plante (une posture = une variante précuite, pas un calcul par frame).
2. **Survol de debug G** : afficher la plage vivable de la plante en °C (gel, froid, chaud).
3. **Banc `niche_thermique`** (`data/code/bancs/`, patron existant) : deux scènes forcées.
   (a) Automne-hiver : basilics sur sol nu, paillé, voilé + mâche + seigle. (b) Canicule
   forcée : même espèce à l'ombre, en plein soleil arrosée, en plein soleil assoiffée.
   Défilement des semaines pour voir les paliers.
4. **`dotnet build Symbiose.csproj`** vert. **Capture VM** (`tools/capture_vm.sh`), regarder
   les PNG, planche dans `planche/` du sprint.
5. **Recette F5** dans `00_etat.md` : le basilic pend, noircit puis meurt avant l'hiver sur sol
   nu, plus tard sous paillage ou voile ; la mâche reste verte ; la plante assoiffée se
   replie, jaunit puis brûle.
6. **Clôture** : `DETTE.md` D139 (sprint ② clos côté code, F5 attendu ; D131, D107 restent
   ouvertes), `BACKLOG.md`, entrée `journal/` + pointeur `journal.md`.

## Ne PAS faire
- Toucher au moteur. Afficher des chiffres hors du survol de debug.
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
Sprint CLOS côté code, F5 attendu. Commit, puis enchaîner sur `sprint_caracteres_vivants`.
