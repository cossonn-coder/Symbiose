## 2026-06-07 — Kickoff Sprint Intégration Godot ↔ Python : Option B actée

**Décision structurante : Option B — Python reste le moteur, Godot devient la
vue.** Pas de portage C# intégral du moteur (l'Option A). Validée par Nico
(« tes recommandations sont bonnes, on suivra ce chemin »). Pourquoi :
- Le moteur fait **~7 500 lignes 100 % stdlib** (vérifié) → il se **gèle en
  exécutable autonome** (PyInstaller/Nuitka), zéro Python à installer chez les
  joueurs — le seul vrai reproche fait à B tombe.
- **Source de vérité unique** (règle projet) : A dédoublerait le moteur →
  divergence permanente à re-porter à chaque évolution.
- **Budget temps réel énorme** : 1 sem = 60 s réel, tick ≈ 177 ms → la
  sérialisation JSON + IPC est négligeable (marge ×339).
- Déterminisme + debug : flux JSON inspectable, même seed → même run.

**Protocole** (direction actée, détails en tranche 1) : sous-process +
stdin/stdout, **JSON ligne-délimité**, Godot pilote la boucle ; **snapshot complet**
du monde (diffs = optimisation ultérieure) ; schéma versionné (`engine_version`) ;
**Python possède les règles**, Godot est « bête » (rend + transmet l'intention).

**Découpage en 6 tranches verticales** : 1 pont vivant minimal (`sim_server.py` ↔
`SimBridge.cs`) → 2 monde statique rendu (corrige D2/D3/D8) → 3 saison animée →
4 actions joueur → 5 organes/overlays/vie macro → 6 packaging PyInstaller.

**Conséquence dette** : **D24 change de nature** (« portage intégral » → « pont » ;
seul le rendu se porte) ; D2/D3/D4/D8 seront levées par les tranches 2. Kickoff
autosuffisant : `sprints/sprint_integration_godot/00_etat.md` (commit `ae2d958`).

**Statut.** Kickoff prêt. **PROCHAIN sprint actif.**

---
