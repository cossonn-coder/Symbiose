// SYMBIOSE — WorldView.Palette.cs (partial de WorldView, palette de gestes ④)
// LA PALETTE DE GESTES en COLONNE VERTICALE au bord GAUCHE (D11) — une icône
// muette par geste (GesteIcon, philo #5). Remplace l'accès historique « touches
// 1..9 + Tab » et le HUD debug qui listait les gestes (qui « débordait »). Le
// clic sur une icône devient LA SOURCE DE VÉRITÉ de la sélection ; Tab/1..9
// restent des accélérateurs (WorldView.Controls.cs), synchronisés via
// UpdatePaletteSelection appelée par SelectGeste.
//
// Filtre par DÉBLOCAGE (①) : la palette lit `gestes_debloques` du snapshot. Un
// geste OUVERT est cliquable ; un geste VERROUILLÉ reste visible mais grisé et
// inerte (calibrage F5 : masquer ou griser — on grise, plus pédagogique). Un
// binaire pré-0.5.23 n'émet pas la clé → tout est considéré ouvert (repli sûr).
//
// 📖 Pédagogie Godot/C# :
//  - CanvasLayer (coordonnées ÉCRAN, ignore la Camera2D, comme le HUD).
//  - Un VBoxContainer ancré à gauche empile les GesteIcon ; l'ordre suit Gestes[]
//    (identique aux touches 1..9/Tab historiques → cohérence).
//  - On ne RECONSTRUIT la colonne que si l'ensemble ouvert CHANGE (comparaison de
//    l'empreinte triée) : un snapshot par 60 s, coût trivial, mais inutile de
//    recréer des nœuds à chaque tick.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		private VBoxContainer _paletteBox;
		// Une icône par ENTRÉE de Gestes[] (index aligné sur Gestes[] et _gesteIndex).
		private readonly GesteIcon[] _paletteIcons = new GesteIcon[Gestes.Length];
		// Ensemble des verbes ouverts (null = pas encore reçu = tout ouvert). Sert
		// aussi d'empreinte pour ne reconstruire qu'au changement.
		private HashSet<string> _gestesOuverts;
		private string _paletteEmpreinte = "";   // signature du dernier layout construit

		// -------------------------------------------------------------------
		// CONSTRUCTION — appelée une fois dans _Ready (après BuildHud).
		// -------------------------------------------------------------------

		private void BuildPalette()
		{
			var layer = new CanvasLayer { Name = "Palette", Layer = 6 };
			AddChild(layer);

			// Colonne ancrée en haut-gauche, sous l'horloge du HUD (y≈150) pour ne
			// pas la recouvrir. La largeur suit celle d'une icône + un peu d'air.
			_paletteBox = new VBoxContainer
			{
				Position = new Vector2(10f, 150f),
			};
			_paletteBox.AddThemeConstantOverride("separation", 4);
			layer.AddChild(_paletteBox);

			// On crée TOUTES les icônes une fois (l'ordre = Gestes[]) ; la visibilité
			// et l'état verrouillé se règlent ensuite selon `gestes_debloques`.
			for (int i = 0; i < Gestes.Length; i++)
			{
				var (verb, nom, kind) = Gestes[i];
				var icon = new GesteIcon();
				icon.Init(verb, nom, kind);
				int idx = i;                       // capture par valeur pour le lambda
				icon.Pressed += () => SelectGeste(idx);
				_paletteIcons[i] = icon;
				_paletteBox.AddChild(icon);
			}
			RebuildPaletteVisibility();
		}

		// -------------------------------------------------------------------
		// FILTRE PAR DÉBLOCAGE — lit `gestes_debloques` du snapshot (①).
		// -------------------------------------------------------------------

		// Reçoit la liste des verbes ouverts (ou null si la clé est absente) + les
		// verbes fraîchement débloqués au dernier tick (notification diégétique).
		// Reconstruit la visibilité SEULEMENT si l'ensemble ouvert a changé.
		private void ApplyGestesDebloques(Godot.Collections.Array ouverts,
										  Godot.Collections.Array recents)
		{
			// null = binaire pré-0.5.23 → tout dispo (repli sûr, kickoff §Existant).
			_gestesOuverts = ouverts == null ? null : new HashSet<string>();
			if (ouverts != null)
				foreach (var v in ouverts) _gestesOuverts.Add(v.AsString());

			// Empreinte triée : ne reconstruit qu'au VRAI changement (event-driven).
			string empreinte = _gestesOuverts == null ? "*"
				: string.Join(",", Sorted(_gestesOuverts));
			if (empreinte != _paletteEmpreinte)
			{
				_paletteEmpreinte = empreinte;
				if (_paletteBox != null) RebuildPaletteVisibility();
			}

			// Notification diégétique d'un déblocage récent (voie savoir) : flash de
			// l'icône concernée. Discret, non bloquant (philo #6 : pas de pop-up).
			if (recents != null && _paletteBox != null)
				foreach (var v in recents) FlashGesteDebloque(v.AsString());
		}

		private static List<string> Sorted(HashSet<string> set)
		{
			var l = new List<string>(set);
			l.Sort(System.StringComparer.Ordinal);
			return l;
		}

		// Applique l'ouvert/verrouillé à chaque icône. `gestes_debloques` == null →
		// tout ouvert. Une icône verrouillée reste VISIBLE mais grisée/inerte
		// (calibrage F5 : passer à Visible=false pour masquer complètement).
		private void RebuildPaletteVisibility()
		{
			for (int i = 0; i < _paletteIcons.Length; i++)
			{
				var icon = _paletteIcons[i];
				if (icon == null) continue;
				bool ouvert = _gestesOuverts == null
							  || _gestesOuverts.Contains(Gestes[i].Verb);
				icon.Verrouille = !ouvert;
				icon.Actif = (i == _gesteIndex);
			}
		}

		// -------------------------------------------------------------------
		// SÉLECTION — SelectGeste (clic OU touche) rappelle ceci pour aligner
		// l'entrée active de la palette (source de vérité = _gesteIndex).
		// -------------------------------------------------------------------

		private void UpdatePaletteSelection()
		{
			if (_paletteBox == null) return;
			for (int i = 0; i < _paletteIcons.Length; i++)
				if (_paletteIcons[i] != null)
					_paletteIcons[i].Actif = (i == _gesteIndex);
		}

		// Flash vert bref de l'icône d'un geste fraîchement débloqué (voie savoir) —
		// « un nouvel outil s'ajoute à ta palette ». Ne fait rien si le verbe est
		// inconnu de la palette (sécurité).
		private void FlashGesteDebloque(string verb)
		{
			for (int i = 0; i < Gestes.Length; i++)
			{
				if (Gestes[i].Verb != verb) continue;
				var icon = _paletteIcons[i];
				if (icon == null) return;
				icon.Modulate = new Color(0.4f, 1f, 0.4f);
				icon.CreateTween().TweenProperty(icon, "modulate", Colors.White, 1.2f);
				GD.Print($"[WorldView] palette : geste débloqué → {verb}.");
				return;
			}
		}
	}
}
