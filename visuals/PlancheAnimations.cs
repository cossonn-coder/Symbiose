// SYMBIOSE — PlancheAnimations.cs (sprint ICÔNES & CURSEUR ④ — planche de contrôle)
// BANC D'OBSERVATION « planche des animations du curseur » : pour chaque
// mouvement (verser, couper, frapper, poser, ramasser, remuer, écraser), puis
// pour le refus et le tap, une LIGNE qui montre l'icône immobile suivie de
// toutes ses images d'animation, à ×4 sur le gazon puis à ×2 sur la terre
// (taille réelle du curseur). Deux gestes témoins par ligne (colonne de gauche,
// colonne de droite) : un mouvement partagé doit se lire sur deux outils dont le
// point chaud n'est pas au même endroit.
//
// Un petit trait rouge en haut et à gauche de chaque image ×4 marque le POINT
// CHAUD : il doit rester au même endroit d'une image à l'autre (c'est le dessin
// qui bouge, jamais le point visé). L'ordre des lignes est imprimé au journal.
// Banc VM : `tools/capture_vm.sh -W` (= --capture-icones=2). Pas un livrable joueur.

using Godot;

namespace Symbiose
{
	public partial class PlancheAnimations : Node2D
	{
		private const int Grand = 4, Petit = 2;
		private const float Marge = 24f, Ecart = 8f;
		private const float CoteGrand = IconeGeste.Cote * Grand;   // 64 px
		private const float CotePetit = IconeGeste.Cote * Petit;   // 32 px
		private const float HautLigne = CoteGrand + Ecart + CotePetit + Ecart;   // 112 px
		private const float LargeurColonne = 920f;

		// (sorte, témoin gauche, témoin droit) — une ligne par mouvement, puis refus, tap.
		private static readonly (AnimationGeste.Sorte Sorte, string Gauche, string Droite)[] Lignes =
		{
			(AnimationGeste.Sorte.Execution, "arroser", "arroser"),
			(AnimationGeste.Sorte.Execution, "couper", "pincer"),
			(AnimationGeste.Sorte.Execution, "becher", "abattre"),
			(AnimationGeste.Sorte.Execution, "poser_bac", "planter"),
			(AnimationGeste.Sorte.Execution, "recolter", "manger"),
			(AnimationGeste.Sorte.Execution, "composter", "retourner"),
			(AnimationGeste.Sorte.Execution, "ecraser", "ecraser"),
			(AnimationGeste.Sorte.Refus, "deraciner", "poser_pot"),
			(AnimationGeste.Sorte.Tap, "couper", "poser_bac"),
		};

		public override void _Ready()
		{
			var noms = new System.Collections.Generic.List<string>();
			foreach (var (sorte, g, d) in Lignes)
				noms.Add(sorte == AnimationGeste.Sorte.Execution
					? $"{AnimationGeste.NomMouvement(g)} ({g} | {d})" : $"{sorte} ({g} | {d})");
			GD.Print($"[PlancheAnimations] lignes (haut → bas) : {string.Join(" ; ", noms)}. "
				+ "Par ligne : repos puis les images, ×4 sur gazon, puis ×2 sur terre.");
		}

		public override void _Draw()
		{
			DrawRect(new Rect2(0f, 0f, 1920f, 1080f), Palette16.GazonChemin, filled: true);
			for (int i = 0; i < Lignes.Length; i++)
			{
				float y = Marge + i * HautLigne;
				DessinerLigne(Lignes[i].Gauche, Lignes[i].Sorte, Marge, y);
				DessinerLigne(Lignes[i].Droite, Lignes[i].Sorte, Marge + LargeurColonne, y);
			}
		}

		// Le repos, puis chaque image, côte à côte (×4), et la même suite à ×2 dessous.
		private void DessinerLigne(string verbe, AnimationGeste.Sorte sorte, float x, float y)
		{
			var repos = AnimationGeste.Images(verbe, AnimationGeste.Sorte.Repos, Grand);
			var grands = AnimationGeste.Images(verbe, sorte, Grand);
			var reposP = AnimationGeste.Images(verbe, AnimationGeste.Sorte.Repos, Petit);
			var petits = AnimationGeste.Images(verbe, sorte, Petit);
			if (repos == null || grands == null || reposP == null || petits == null) return;
			IconesPointsChauds.PointsChauds.TryGetValue(verbe, out var chaud);
			for (int k = 0; k <= grands.Length; k++)
			{
				var g = k == 0 ? repos[0] : grands[k - 1];
				var p = k == 0 ? reposP[0] : petits[k - 1];
				float gx = x + k * (CoteGrand + Ecart);
				DrawTexture(g.Tex, new Vector2(gx, y));
				MarquerPointChaud(gx, y, chaud);
				float py = y + CoteGrand + Ecart;
				float px = x + k * (CotePetit + Ecart);
				DrawRect(new Rect2(px, py, CotePetit, CotePetit), Palette16.SolTerre, filled: true);
				DrawTexture(p.Tex, new Vector2(px, py));
			}
		}

		// Deux traits hors de l'image, à la hauteur et à l'abscisse du point chaud.
		private void MarquerPointChaud(float x, float y, (int X, int Y) chaud)
		{
			Color rouge = Palette16.Maitre[30];
			float cx = x + (chaud.X + 0.5f) * Grand, cy = y + (chaud.Y + 0.5f) * Grand;
			DrawLine(new Vector2(cx, y - 5f), new Vector2(cx, y - 1f), rouge, 2f);
			DrawLine(new Vector2(x - 5f, cy), new Vector2(x - 1f, cy), rouge, 2f);
		}
	}
}
