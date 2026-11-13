// SYMBIOSE — WorldView.Palette.cs (partial de WorldView, palette de gestes ④)
// LA PALETTE DE GESTES en COLONNE VERTICALE au bord GAUCHE (D11) — une icône
// muette par geste (GesteIcon, philo #5). Modèle de SLOTS gérable (T1, retours
// UI post-fenêtrage) : au plus 10 slots (touches 1..9 puis 0), chaque slot porte
// l'index d'un geste dans Gestes[] (ou vide). La palette ne dessine QU'UN icône
// par slot occupé — les gestes non débloqués n'occupent aucun slot (on MASQUE,
// on ne grise plus : D2).
//
// Auto-remplissage : les gestes DÉBLOQUÉS remplissent les slots libres dans
// l'ordre de Gestes[] ; un geste débloqué au-delà du 10ᵉ reste hors palette tant
// qu'on ne l'assigne pas à la main (clic droit → menu). Édition clic droit sur un
// slot : assigner un débloqué absent, ou vider. Le layout est persisté GLOBALEMENT
// (PaletteLayout, `user://palette.json`) et survit au retour à l'accueil.
//
// 📖 Pédagogie Godot/C# :
//  - CanvasLayer (coordonnées ÉCRAN, ignore la Camera2D, comme le HUD).
//  - Un VBoxContainer empile les GesteIcon des slots occupés (ordre = slots).
//  - On ne RECONSTRUIT les icônes qu'aux VRAIS changements (déblocage, édition) —
//    event-driven, jamais par tick (un snapshot par 60 s).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		private const int SlotCount = 10;              // cap 10 (touches 1..9 + 0)
		private CanvasLayer _paletteLayer;
		private VBoxContainer _paletteBox;
		// _slots[i] = index d'un geste dans Gestes[] (ou -1 = slot vide). L'icône du
		// slot vit dans _slotIcons[i] (null si vide) — parallèle, pour la sélection.
		private readonly int[] _slots = new int[SlotCount];
		private GesteIcon[] _slotIcons = new GesteIcon[SlotCount];
		// Ensemble des verbes ouverts (null = pas encore reçu = tout ouvert). Sert
		// aussi d'empreinte pour ne recomposer les slots qu'au changement.
		private HashSet<string> _gestesOuverts;
		private string _paletteEmpreinte = "";         // signature du dernier layout
		private PopupMenu _editMenu;                   // menu clic droit (lazy)
		private int _editSlot = -1;                    // slot en cours d'édition

		// -------------------------------------------------------------------
		// CONSTRUCTION — appelée une fois dans _Ready (après BuildHud).
		// -------------------------------------------------------------------

		private void BuildPalette()
		{
			_paletteLayer = new CanvasLayer { Name = "Palette", Layer = 6 };
			AddChild(_paletteLayer);

			// Colonne ancrée en haut-gauche, sous l'horloge du HUD (y≈150).
			_paletteBox = new VBoxContainer { Position = new Vector2(10f, 150f) };
			_paletteBox.AddThemeConstantOverride("separation", 4);
			_paletteLayer.AddChild(_paletteBox);

			for (int s = 0; s < SlotCount; s++) _slots[s] = -1;
			ChargerSlotsPersistes();   // layout sauvegardé (par verbe) → indices
			AutoRemplirSlots();        // complète les slots restés libres
			BuildTiroir();             // bouton en bas de barre + panneau (WorldView.Tiroir.cs)
			RebuildPaletteIcons();
		}

		// -------------------------------------------------------------------
		// FILTRE PAR DÉBLOCAGE — lit `gestes_debloques` du snapshot (①).
		// -------------------------------------------------------------------

		// Reçoit la liste des verbes ouverts (ou null si la clé est absente) + les
		// verbes fraîchement débloqués au dernier tick (notification diégétique).
		// Recompose les slots SEULEMENT si l'ensemble ouvert a changé.
		private void ApplyGestesDebloques(Godot.Collections.Array ouverts,
										  Godot.Collections.Array recents)
		{
			// null = binaire pré-0.5.23 → tout dispo (repli sûr, kickoff §Existant).
			_gestesOuverts = ouverts == null ? null : new HashSet<string>();
			if (ouverts != null)
				foreach (var v in ouverts) _gestesOuverts.Add(v.AsString());

			// Empreinte triée : ne recompose qu'au VRAI changement (event-driven).
			string empreinte = _gestesOuverts == null ? "*"
				: string.Join(",", Sorted(_gestesOuverts));
			if (empreinte != _paletteEmpreinte && _paletteBox != null)
			{
				_paletteEmpreinte = empreinte;
				PurgerSlotsVerrouilles();   // un slot devenu non débloqué se vide
				AutoRemplirSlots();         // complète les slots libres
				RebuildPaletteIcons();
				MarquerTiroirSale();        // le tiroir liste les gestes ouverts : à refaire
			}

			// Flash discret d'un déblocage récent (voie savoir), si le geste occupe
			// un slot visible. Non bloquant (philo #6 : pas de pop-up).
			if (recents != null && _paletteBox != null)
				foreach (var v in recents) FlashGesteDebloque(v.AsString());
		}

		private static List<string> Sorted(HashSet<string> set)
		{
			var l = new List<string>(set);
			l.Sort(System.StringComparer.Ordinal);
			return l;
		}

		// -------------------------------------------------------------------
		// MODÈLE DE SLOTS — masquage, auto-remplissage, purge (D2).
		// -------------------------------------------------------------------

		private bool EstDebloque(int g) =>
			_gestesOuverts == null || _gestesOuverts.Contains(Gestes[g].Verb);

		private bool DansUnSlot(int g)
		{
			for (int s = 0; s < SlotCount; s++) if (_slots[s] == g) return true;
			return false;
		}

		private int PremierSlotLibre()
		{
			for (int s = 0; s < SlotCount; s++) if (_slots[s] < 0) return s;
			return -1;
		}

		// Vide tout slot dont le geste n'est plus débloqué (changement de maîtrise).
		private void PurgerSlotsVerrouilles()
		{
			for (int s = 0; s < SlotCount; s++)
				if (_slots[s] >= 0 && !EstDebloque(_slots[s])) _slots[s] = -1;
		}

		// Parcourt Gestes[] dans l'ordre ; chaque geste DÉBLOQUÉ pas déjà présent va
		// au premier slot libre, jusqu'à épuisement. Les gestes au-delà du 10ᵉ
		// restent hors palette tant qu'on ne les assigne pas à la main (D2).
		private void AutoRemplirSlots()
		{
			for (int g = 0; g < Gestes.Length; g++)
			{
				if (!EstDebloque(g) || DansUnSlot(g)) continue;
				int libre = PremierSlotLibre();
				if (libre < 0) break;
				_slots[libre] = g;
			}
		}

		// -------------------------------------------------------------------
		// (RE)CONSTRUCTION DES ICÔNES — une par slot occupé.
		// -------------------------------------------------------------------

		private void RebuildPaletteIcons()
		{
			if (_paletteBox == null) return;
			foreach (var c in _paletteBox.GetChildren())
			{
				if (c == _tiroirBouton) continue;   // le bouton du tiroir survit au vidage
				_paletteBox.RemoveChild(c);
				c.QueueFree();
			}
			_slotIcons = new GesteIcon[SlotCount];
			for (int s = 0; s < SlotCount; s++)
			{
				int g = _slots[s];
				if (g < 0) continue;
				var (verb, nom, kind) = Gestes[g];
				var icon = new GesteIcon();
				icon.Init(verb, nom, kind);
				int gi = g, si = s;                // capture par valeur pour lambdas
				icon.Pressed += () => SelectGeste(gi);
				icon.OnRightClick = () => OuvrirEditSlot(si, icon);
				icon.Actif = (g == _gesteIndex);
				_slotIcons[s] = icon;
				_paletteBox.AddChild(icon);
			}
			ReposerBoutonTiroir();   // tout en bas, après les cases (WorldView.Tiroir.cs)
			SynchroniserReglages();  // la rangée suit la case du geste actif (WorldView.Reglages.cs)
		}

		// -------------------------------------------------------------------
		// SÉLECTION — par SLOT (touches 1..9+0) et cycle Tab sur slots occupés.
		// -------------------------------------------------------------------

		// Touche d'un slot (0..9) : sélectionne le geste du slot, ou no-op si vide.
		private void SelectSlot(int slot)
		{
			if (slot < 0 || slot >= SlotCount) return;
			if (_slots[slot] >= 0) SelectGeste(_slots[slot]);
		}

		// Tab : cycle sur les SLOTS OCCUPÉS uniquement (remplace l'ancien cycle sur
		// Gestes[] brut). Premier appel sans geste → bord selon le sens.
		private void CycleSlots(int dir)
		{
			var occ = new List<int>();
			for (int s = 0; s < SlotCount; s++) if (_slots[s] >= 0) occ.Add(s);
			if (occ.Count == 0) return;
			int cur = -1;
			for (int i = 0; i < occ.Count; i++)
				if (_slots[occ[i]] == _gesteIndex) { cur = i; break; }
			int next = cur < 0 ? (dir > 0 ? 0 : occ.Count - 1)
							   : ((cur + dir) % occ.Count + occ.Count) % occ.Count;
			SelectGeste(_slots[occ[next]]);
		}

		// SelectGeste (clic OU touche) rappelle ceci pour aligner l'entrée active de
		// la palette (source de vérité = _gesteIndex).
		private void UpdatePaletteSelection()
		{
			if (_slotIcons == null) return;
			for (int s = 0; s < SlotCount; s++)
				if (_slotIcons[s] != null)
					_slotIcons[s].Actif = (_slots[s] == _gesteIndex);
			// Geste actif sans case → le bouton du tiroir le porte (WorldView.Tiroir.cs).
			SynchroniserTiroir();
			SynchroniserReglages();  // rangée de réglages du geste actif (WorldView.Reglages.cs)
		}

		// -------------------------------------------------------------------
		// ÉDITION CLIC DROIT — assigner un débloqué absent, ou vider le slot.
		// -------------------------------------------------------------------

		private void OuvrirEditSlot(int slot, GesteIcon anchor)
		{
			_editSlot = slot;
			if (_editMenu == null)
			{
				_editMenu = new PopupMenu();
				_paletteLayer.AddChild(_editMenu);
				_editMenu.IdPressed += OnEditMenuChoisi;
			}
			_editMenu.Clear();
			// id = -1 → vider ; id = index de geste → assigner. (Les indices ≥ 0.)
			_editMenu.AddItem("vider ce slot", -1);
			_editMenu.AddSeparator();
			for (int g = 0; g < Gestes.Length; g++)
			{
				if (!EstDebloque(g) || DansUnSlot(g)) continue;
				_editMenu.AddItem(Gestes[g].Nom, g);
			}
			var pos = anchor.GetScreenPosition() + new Vector2(GesteIcon.Taille, 0f);
			_editMenu.Position = (Vector2I)pos;
			_editMenu.Popup();
		}

		private void OnEditMenuChoisi(long id)
		{
			if (_editSlot < 0) return;
			// -1 = vider ; sinon assigner le geste id (le menu ne liste que des
			// gestes ABSENTS de tout slot → pas de doublon possible).
			_slots[_editSlot] = id == -1 ? -1 : (int)id;
			_editSlot = -1;
			PersisterSlots();
			RebuildPaletteIcons();
			UpdatePaletteSelection();
		}

		// -------------------------------------------------------------------
		// PERSISTANCE — par VERBE (PaletteLayout, `user://palette.json`).
		// -------------------------------------------------------------------

		// (IndexDuVerbe vit dans WorldView.Macros.cs — partagé, même classe partial.)

		// Recharge le layout sauvegardé. Un verbe inconnu (renommé) est ignoré ; un
		// verbe non débloqué sera purgé au 1er snapshot (PurgerSlotsVerrouilles).
		private void ChargerSlotsPersistes()
		{
			string[] verbs = PaletteLayout.Charger();
			if (verbs == null) return;
			for (int s = 0; s < SlotCount && s < verbs.Length; s++)
			{
				if (string.IsNullOrEmpty(verbs[s])) continue;
				int g = IndexDuVerbe(verbs[s]);
				if (g >= 0) _slots[s] = g;
			}
		}

		private void PersisterSlots()
		{
			var verbs = new string[SlotCount];
			for (int s = 0; s < SlotCount; s++)
				verbs[s] = _slots[s] >= 0 ? Gestes[_slots[s]].Verb : "";
			PaletteLayout.Sauver(verbs);
		}

		// Flash vert bref de l'icône d'un geste fraîchement débloqué (voie savoir) —
		// « un nouvel outil s'ajoute à ta palette ». Ne fait rien si le geste
		// n'occupe aucun slot visible (débordé au-delà du 10ᵉ, à assigner à la main).
		private void FlashGesteDebloque(string verb)
		{
			if (_slotIcons == null) return;
			for (int s = 0; s < SlotCount; s++)
			{
				var icon = _slotIcons[s];
				if (icon == null || icon.Verb != verb) continue;
				icon.Modulate = new Color(0.4f, 1f, 0.4f);
				icon.CreateTween().TweenProperty(icon, "modulate", Colors.White, 1.2f);
				GD.Print($"[WorldView] palette : geste débloqué → {verb}.");
				return;
			}
		}
	}
}
