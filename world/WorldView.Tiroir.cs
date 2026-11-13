// SYMBIOSE — WorldView.Tiroir.cs (partial de WorldView, sprint PALETTE & TIROIR ①)
// LE CÂBLAGE DU TIROIR DES GESTES. La barre de gauche n'a que dix cases ; le
// tiroir montre TOUS les gestes ouverts, rangés par familles (rangement donné par
// le pont : `player.familles`, source de vérité Python `sim/actions/familles.py`).
// Ce fichier relie trois choses qui s'ignorent :
//  - `TiroirPanel` (affichage pur) et `TiroirBouton` (le bouton en bas de barre) ;
//  - le modèle de cases de `WorldView.Palette.cs` (`_slots`, persistance) ;
//  - le geste actif (`_gesteIndex`, `SelectGeste`).
//
// Ce que le tiroir change au modèle : le GESTE ACTIF n'a plus besoin d'une CASE.
// `SelectGeste(idx)` acceptait déjà n'importe quel index de `Gestes[]` ; seule la
// vue supposait qu'il était dans la barre. Quand il n'y est pas, c'est le bouton
// du tiroir qui porte son pictogramme.
//
// 📖 Pédagogie Godot/C# :
//  - Le panneau vit dans le MÊME CanvasLayer que la barre (coordonnées écran).
//    `Visible = false` coupe son dessin ET sa réception de souris : fermé, il ne
//    coûte rien.
//  - On ne REMPLIT le tiroir que s'il est « sale » (l'ensemble des gestes ouverts
//    a changé) et seulement à l'ouverture — jamais par image ni par snapshot.
//  - Un clic DANS le panneau est avalé par lui (PanelContainer, MouseFilter Stop)
//    et n'arrive pas à `_UnhandledInput` : c'est pourquoi « clic ailleurs = fermer »
//    peut se tester là-bas sans connaître la géométrie du panneau.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		private TiroirBouton _tiroirBouton;
		private TiroirPanel _tiroirPanel;
		// Vrai = le contenu ne reflète plus les gestes ouverts → à refaire à la
		// prochaine ouverture (ou tout de suite si le tiroir est ouvert).
		private bool _tiroirSale = true;
		// Rangement reçu du pont (statique). null = pont antérieur à 0.6.12 →
		// repli : une seule rangée avec tous les gestes ouverts.
		private string[] _famillesOrdre;
		private Dictionary<string, string[]> _famillesGestes;
		private PopupMenu _caseMenu;          // menu clic droit « mettre en case » (lazy)
		private int _caseGeste = -1;          // geste que ce menu va ranger

		private bool TiroirOuvert => _tiroirPanel != null && _tiroirPanel.Visible;

		// -------------------------------------------------------------------
		// CONSTRUCTION — appelée par BuildPalette, avant RebuildPaletteIcons.
		// -------------------------------------------------------------------

		private void BuildTiroir()
		{
			_tiroirBouton = new TiroirBouton();
			_tiroirBouton.Pressed += BasculerTiroir;
			_paletteBox.AddChild(_tiroirBouton);

			// À droite de la barre (10 px de marge + une case + 8 px d'air).
			_tiroirPanel = new TiroirPanel
			{
				Position = new Vector2(10f + GesteIcon.Taille + 8f, 150f),
				Visible = false,
			};
			_tiroirPanel.OnChoisi = g => { SelectGeste(g); FermerTiroir(); };
			_tiroirPanel.OnClicDroit = OuvrirMenuCase;
			_paletteLayer.AddChild(_tiroirPanel);
		}

		// -------------------------------------------------------------------
		// RANGEMENT — `player.familles` du snapshot (lu une seule fois).
		// -------------------------------------------------------------------

		// Forme du pont : {ordre: [familles…], gestes: {famille: [verbes…]}}. Le bloc
		// est STATIQUE (ni le joueur ni le monde ne le changent) : on ne le relit pas.
		private void ApplyFamilles(GDict bloc)
		{
			if (_famillesOrdre != null || bloc == null) return;
			if (!bloc.ContainsKey("ordre") || !bloc.ContainsKey("gestes")) return;
			var gestes = bloc["gestes"].AsGodotDictionary();
			var ordre = new List<string>();
			_famillesGestes = new Dictionary<string, string[]>();
			foreach (var f in bloc["ordre"].AsGodotArray())
			{
				string famille = f.AsString();
				if (!gestes.ContainsKey(famille)) continue;
				ordre.Add(famille);
				_famillesGestes[famille] = gestes[famille].AsStringArray();
			}
			_famillesOrdre = ordre.ToArray();
			MarquerTiroirSale();
		}

		// L'ensemble des gestes ouverts (ou le rangement) a changé.
		private void MarquerTiroirSale()
		{
			_tiroirSale = true;
			if (TiroirOuvert) RemplirTiroir();
		}

		// Compose les rangées : familles dans l'ordre du pont, gestes OUVERTS
		// seulement ; une famille sans geste ouvert n'a pas de rangée. Un geste que
		// la vue connaît mais qu'aucune famille ne cite tombe dans « autres » — le
		// tiroir ne doit oublier aucun geste ouvert.
		private void RemplirTiroir()
		{
			var rangees = new List<(string Famille, List<TiroirPanel.Entree> Gestes)>();
			var ranges = new HashSet<int>();
			if (_famillesOrdre != null)
				foreach (string famille in _famillesOrdre)
				{
					var ligne = new List<TiroirPanel.Entree>();
					foreach (string verb in _famillesGestes[famille])
					{
						// Verbe sans entrée dans Gestes[] (ex. `grelinette`, qui est
						// Maj+ameublir côté vue) → ignoré.
						int g = IndexDuVerbe(verb);
						if (g < 0 || !EstDebloque(g) || !ranges.Add(g)) continue;
						ligne.Add(new TiroirPanel.Entree(g, Gestes[g].Verb, Gestes[g].Nom, Gestes[g].Kind));
					}
					if (ligne.Count > 0) rangees.Add((famille, ligne));
				}
			var autres = new List<TiroirPanel.Entree>();
			for (int g = 0; g < Gestes.Length; g++)
				if (EstDebloque(g) && !ranges.Contains(g))
					autres.Add(new TiroirPanel.Entree(g, Gestes[g].Verb, Gestes[g].Nom, Gestes[g].Kind));
			if (autres.Count > 0)
				rangees.Add((_famillesOrdre == null ? "gestes" : "autres", autres));
			_tiroirPanel.Remplir(rangees, _gesteIndex);
			_tiroirSale = false;
		}

		// -------------------------------------------------------------------
		// OUVERTURE / FERMETURE — bouton, touche Q, Échap, clic ailleurs.
		// -------------------------------------------------------------------

		private void BasculerTiroir()
		{
			if (TiroirOuvert) FermerTiroir();
			else OuvrirTiroir();
		}

		// Le tiroir ne met PAS le jeu en pause : la saison continue derrière.
		private void OuvrirTiroir()
		{
			if (_tiroirPanel == null) return;
			if (_tiroirSale) RemplirTiroir();
			else _tiroirPanel.MarquerActif(_gesteIndex);
			_tiroirPanel.Visible = true;
			_tiroirBouton.Ouvert = true;
			SynchroniserReglages();   // la rangée de réglages cède la place
		}

		private void FermerTiroir()
		{
			if (_tiroirPanel == null) return;
			_tiroirPanel.Visible = false;
			_tiroirBouton.Ouvert = false;
			SynchroniserReglages();   // … et revient
		}

		/// <summary>Ferme le tiroir s'il est ouvert. Vrai = il l'était (l'appelant
		/// s'arrête là : Échap ou le clic n'a servi qu'à fermer).</summary>
		private bool FermerTiroirSiOuvert()
		{
			if (!TiroirOuvert) return false;
			FermerTiroir();
			return true;
		}

		// -------------------------------------------------------------------
		// SYNCHRO AVEC LA BARRE — appelée quand les cases ou le geste actif bougent.
		// -------------------------------------------------------------------

		// La barre vient d'être reconstruite : le bouton du tiroir (qui a survécu au
		// vidage) retourne tout en bas.
		private void ReposerBoutonTiroir()
		{
			if (_tiroirBouton == null) return;
			_paletteBox.MoveChild(_tiroirBouton, -1);
			SynchroniserTiroir();
		}

		// Geste actif dans la barre → sa case porte le cadre, le bouton montre la
		// grille. Geste actif HORS barre → c'est le bouton qui porte son pictogramme.
		private void SynchroniserTiroir()
		{
			if (_tiroirBouton == null) return;
			if (_gesteIndex >= 0 && !DansUnSlot(_gesteIndex))
			{
				var (verb, nom, kind) = Gestes[_gesteIndex];
				_tiroirBouton.Porter(verb, nom, kind);
			}
			else _tiroirBouton.Vider();
			if (TiroirOuvert) _tiroirPanel.MarquerActif(_gesteIndex);
		}

		// -------------------------------------------------------------------
		// CLIC DROIT DANS LE TIROIR — « mettre en case 1…0 ».
		// -------------------------------------------------------------------

		private void OuvrirMenuCase(int geste, GesteIcon ancre)
		{
			_caseGeste = geste;
			if (_caseMenu == null)
			{
				_caseMenu = new PopupMenu();
				_paletteLayer.AddChild(_caseMenu);
				_caseMenu.IdPressed += OnCaseChoisie;
			}
			_caseMenu.Clear();
			// id = numéro de case (0..9). Le libellé dit la touche et ce qui s'y
			// trouve, pour savoir ce qu'on va déloger.
			for (int s = 0; s < SlotCount; s++)
			{
				int touche = (s + 1) % 10;             // cases 1..9 puis 0
				string occupant = _slots[s] < 0 ? "libre" : Gestes[_slots[s]].Nom;
				_caseMenu.AddItem($"case {touche} · {occupant}", s);
			}
			_caseMenu.Position = (Vector2I)(ancre.GetScreenPosition()
											+ new Vector2(GesteIcon.Taille, 0f));
			_caseMenu.Popup();
		}

		// Range le geste dans la case choisie. S'il occupait déjà une autre case, il
		// la QUITTE (un geste n'a jamais deux cases) ; l'ancien occupant de la case
		// sort de la barre mais reste dans le tiroir.
		private void OnCaseChoisie(long id)
		{
			if (_caseGeste < 0) return;
			for (int s = 0; s < SlotCount; s++)
				if (_slots[s] == _caseGeste) _slots[s] = -1;
			_slots[(int)id] = _caseGeste;
			_caseGeste = -1;
			PersisterSlots();
			RebuildPaletteIcons();
			UpdatePaletteSelection();
		}
	}
}
