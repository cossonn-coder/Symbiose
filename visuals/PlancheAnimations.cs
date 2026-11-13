// SYMBIOSE — PlancheAnimations.cs (sprint ICÔNES & CURSEUR ④, GESTES LISIBLES ②)
// BANC D'OBSERVATION « planche des animations du curseur » : pour CHAQUE geste
// (ordre des familles du tiroir), une bande qui montre l'icône immobile suivie
// de toutes les images de sa suite ; puis deux bandes témoins, refus et tap.
// GESTES LISIBLES ② : 46 gestes ne tiennent pas sur un écran aux deux échelles,
// la planche ALTERNE donc deux pages d'une image à l'autre :
//   - page A : ×4, chaque image sur un carreau de gazon, 4
//     colonnes × 12 bandes ; un petit trait rouge au-dessus de chaque image (et à
//     gauche de l'icône immobile) marque le POINT CHAUD — il ne bouge jamais ;
//   - page B : ×2 (taille réelle du curseur) sur terre, 7 colonnes.
// Constaté au banc (`tools/capture_vm.sh -W -n 4`, = --capture-icones=2) :
// frame00000001/3.png = page A, frame00000000/2.png = page B. L'ordre des bandes
// est imprimé au journal. Pas un livrable joueur.

using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	public partial class PlancheAnimations : Node2D
	{
		private const int Grand = 4, Petit = 2;
		private const float Bord = 8f;

		// Bandes : (verbe, sorte), une par geste, puis refus et tap sur deux témoins.
		private readonly List<(string Verbe, AnimationGeste.Sorte Sorte)> _bandes = new();
		private int _image;   // compteur d'images : pair = page A (×4), impair = page B (×2)

		public override void _Ready()
		{
			foreach (var (_, grilles) in IconeGeste.Familles)
				foreach (string verbe in grilles.Keys)
					_bandes.Add((verbe, AnimationGeste.Sorte.Execution));
			_bandes.Add(("deraciner", AnimationGeste.Sorte.Refus));
			_bandes.Add(("couper", AnimationGeste.Sorte.Tap));
			var noms = new List<string>();
			foreach (var (v, sorte) in _bandes)
				noms.Add(sorte == AnimationGeste.Sorte.Execution ? v : $"{sorte}({v})");
			GD.Print($"[PlancheAnimations] {_bandes.Count} bandes, colonne par colonne, de haut "
				+ $"en bas : {string.Join(", ", noms)}. Pages alternées : A ×4, B ×2.");
		}

		public override void _Process(double delta)
		{
			_image++;
			QueueRedraw();
		}

		public override void _Draw()
		{
			bool pageA = _image % 2 == 0;
			DrawRect(new Rect2(0f, 0f, 1920f, 1080f),
				pageA ? Palette16.SolTerre : Palette16.GazonChemin, filled: true);
			int ech = pageA ? Grand : Petit;
			float cote = IconeGeste.Cote * ech;
			float pas = cote + (pageA ? 2f : 4f);              // d'une image à la suivante
			float largeur = pageA ? 478f : 272f;               // une colonne de bandes
			float haut = cote + (pageA ? 8f : 6f);             // une bande
			int parColonne = pageA ? 12 : 7;
			for (int i = 0; i < _bandes.Count; i++)
			{
				float x = Bord + (i / parColonne) * largeur, y = Bord + (i % parColonne) * haut;
				DessinerBande(_bandes[i].Verbe, _bandes[i].Sorte, ech, x, y, pas, pageA);
			}
		}

		// L'icône immobile, puis chaque image, côte à côte, chacune sur son carreau.
		private void DessinerBande(string verbe, AnimationGeste.Sorte sorte, int ech,
			float x, float y, float pas, bool marquer)
		{
			var repos = AnimationGeste.Images(verbe, AnimationGeste.Sorte.Repos, ech);
			var images = AnimationGeste.Images(verbe, sorte, ech);
			if (repos == null || images == null) return;
			IconesPointsChauds.PointsChauds.TryGetValue(verbe, out var chaud);
			float cote = IconeGeste.Cote * ech;
			Color carreau = marquer ? Palette16.GazonChemin : Palette16.SolTerre;
			for (int k = 0; k <= images.Length; k++)
			{
				float ix = x + k * pas;
				DrawRect(new Rect2(ix, y, cote, cote), carreau, filled: true);
				DrawTexture(k == 0 ? repos[0].Tex : images[k - 1].Tex, new Vector2(ix, y));
				if (marquer) MarquerPointChaud(ix, y, chaud, k == 0);
			}
		}

		// Trait au-dessus de l'image à l'abscisse du point chaud ; à gauche, à sa
		// hauteur, pour l'icône immobile seulement (les images se touchent presque).
		private void MarquerPointChaud(float x, float y, (int X, int Y) chaud, bool gauche)
		{
			Color rouge = Palette16.Maitre[30];
			float cx = x + (chaud.X + 0.5f) * Grand, cy = y + (chaud.Y + 0.5f) * Grand;
			DrawLine(new Vector2(cx, y - 4f), new Vector2(cx, y), rouge, 2f);
			if (gauche) DrawLine(new Vector2(x - 4f, cy), new Vector2(x, cy), rouge, 2f);
		}
	}
}
