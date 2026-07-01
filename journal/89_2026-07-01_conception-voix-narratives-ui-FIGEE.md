# 2026-07-01 — Conception UI des VOIX NARRATIVES (D24 · brique voix) — FIGÉE

> Skill `/conception` phase B. Conception SEULE (aucun code moteur/vue touché).
> Source figée : `docs/conception/CONCEPTION_VOIX_NARRATIVES_UI.md`. Sprint prêt :
> `sprints/sprint_voix_narratives_ui/` (00_etat + 01→04). S'appuie sur le doc
> MOTEUR `CONCEPTION_VOIX_NARRATIVES.md` (voix implémentées ①→⑥ le 2026-06-29,
> golden `db5e7c66…`).

## Objet
Rendre **jouables** les 4 voix (carnet, encyclopédie, magazine, pages) dont le
moteur Python est 100 % fait : brancher les commandes sur le **pont** + poser la
**couche de présentation Godot** (hub-maison cliquable + panneaux de consultation).

## Décisions arbitrées avec Nico (toutes validées)
- **Cadrage** : le sprint = brancher les 4 voix sur le pont + UI de consultation.
  HORS sprint (= D54) : HUD primaire philo #5, page d'accueil pictogrammes, notifs
  temps réel saison.
- **Q1 maîtrise = chaîne complète 3 hooks** (`observer` découverte + `detecter`
  crédit palier + `noter_geste` imputation). Câbler `detecter` SEUL est insuffisant
  (il ne crédite que le déjà-découvert → sans `observer`, encyclopédie/carnet/
  magazine restent vides).
- **Q2 = hub-maison cliquable d'emblée** (clic maison → menu 5 fonctions).
- **Q3 = achat magazine via `cmd_action`** (verbe `acheter_magazine`, chemin
  Vigueur unique) ; lecture = commandes pont read-only.
- **Micro-A** : menu hub Carnet/Encyclopédie/Magazine/Pages actifs ; Atelier/Semis/
  Foyer grisés « à venir » (→ D54).
- **Micro-B** : pages révélées par robinet « récompense » au palier 3
  (`reveler_page(robinet="récompense", {concept})`). Hasard/fouille → D54.

## INVARIANT gravé (téléonomie / « Godot bête »)
L'UI restitue le texte des voix **verbatim** depuis Python. AUCUNE synthèse/conseil/
phrase générée côté C#. Le registre (naturaliste téléonomique pour encyclopédie+
carnet ; téléologique assumé pour les pages) est porté par le **corpus Python**. Le
C# ne fait que de la mise en page. Rappelé dans chaque kickoff.

## Faits code VÉRIFIÉS (base des kickoffs)
- 8 signatures de voix confirmées (`carnet.py`/`encyclopedie.py`/`magazine.py`/
  `pages.py`), 3 hooks (`sim/actions.observer`, `maitrise_detection.detecter/
  noter_geste`), dispatch pont (`server.py:25`), `cmd_action`+`bilan` (`actions.py`),
  `consigner`+`J.` (`commands.py:143`), `SimBridge.cs`, `WorldView.Hud.cs`.

## Découpage FIGÉ — 4 tronçons + F5
- **①** Pont (Python `tools/`) : 3 hooks maîtrise + révélation page palier +
  commandes read-only `carnet`/`encyclopedie`/`pages`/`magazine` + verbe
  `acheter_magazine` ; bump `ENGINE_VERSION` ; golden intact.
- **②** `SimBridge` C# (1 méthode/commande) + nœud `VoicePanel` pause-aware +
  hub-maison cliquable (non-voix grisées) ; `dotnet build` vert.
- **③** Panneau Carnet (filtrable par concept) + panneau Encyclopédie (index →
  fiche N1/N2/N3).
- **④** Panneau Pages (coffret grenier) + panneau Magazine (offres → fiche → achat
  bout-en-bout via `cmd_action`).
- **F5 = Nico** (Godot pas sur la VM ; tronçons C# validés au `dotnet build`).

## Golden
Intact partout — le pont est opt-in joueur (hors golden hors-serveur), le C# est
une couche vue, le tick moteur n'est pas touché. Réf du sprint = `ae445d3f…`.

## Dette
Nouvelle entrée **D54** (reliquats UI : HUD primaire, page accueil, notifs temps
réel, robinets pages hasard/fouille + marqueurs bouture/oiseau/vent, entrées hub
non-voix, corpus encyclo paliers 4-5, filtre saison magazine). Annotées « UI
conçue → sprint prêt » : **D24** (brique voix), **D13/D14/D18/D43** (parts UI),
**D12(.5)** (chaîne maîtrise branchée au pont = 1re consommation UI de D12).

## Suite
CONCEPTION SEULE, aucun dev. Prêt pour `/sprint-auto sprint_voix_narratives_ui`.
