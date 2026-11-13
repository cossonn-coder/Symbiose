// SYMBIOSE — PlancheIcones.cs (sprint ICÔNES & CURSEUR ① — planche de contrôle)
// BANC D'OBSERVATION « planche des icônes de gestes » : toutes les icônes du
// registre `IconeGeste.Familles`, un BLOC par famille (une colonne par geste) :
//
//   ligne 1 : l'icône à ×4, sur le gazon des chemins   (lecture du dessin)
//   ligne 2 : sa silhouette à ×4, sur plaque sombre    (geste pressenti)
//   ligne 3 : l'icône à ×2 sur la terre, puis sa silhouette à ×2 sur plaque
//             sombre (la taille réelle d'une case de la palette et du curseur)
//
// Les fonds sont ceux sur lesquels l'icône vivra : gazon et terre (curseur posé
// sur le jardin), plaque sombre (case de la palette et du tiroir). Aucun nom
// affiché : l'ordre des blocs et des colonnes est imprimé au journal.
// Banc VM : `tools/capture_vm.sh -I` (= --capture-icones=1). Pas un livrable
// joueur. C'est l'outil de contrôle des tronçons ② à ④ du sprint.
//
// 📖 Pédagogie Godot/C# : un Node2D ne dessine rien tout seul ; Godot appelle
// son `_Draw` une fois, garde le résultat, et ne le rappelle que sur
// `QueueRedraw()`. La planche est fixe : elle n'est donc peinte qu'une fois.

using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	public partial class PlancheIcones : Node2D
	{
		private const int Grand = 4, Petit = 2;            // échelles entières
		private const float Marge = 24f, Ecart = 8f;
		private const float CoteGrand = IconeGeste.Cote * Grand;   // 64 px
		private const float CotePetit = IconeGeste.Cote * Petit;   // 32 px
		private const float PasColonne = CoteGrand + Ecart;        // un geste = 72 px
		private const float HautBloc = 2f * (CoteGrand + Ecart) + CotePetit + 3f * Ecart;
		private const int BlocsParColonne = 4;             // 8 familles = 2 colonnes d'écran
		private const float LargeurColonne = 960f;

		public override void _Ready()
		{
			var blocs = new List<string>();
			foreach (var (nom, grilles) in IconeGeste.Familles)
				blocs.Add($"{nom} [{string.Join(", ", grilles.Keys)}]");
			GD.Print($"[PlancheIcones] blocs (haut → bas, puis colonne de droite) : {string.Join(" ; ", blocs)}. "
				+ "Par bloc : ×4, silhouette ×4, puis ×2 et silhouette ×2.");
		}

		public override void _Draw()
		{
			DrawRect(new Rect2(0f, 0f, 1920f, 1080f), Palette16.GazonChemin, filled: true);
			for (int b = 0; b < IconeGeste.Familles.Length; b++)
			{
				float x0 = Marge + (b / BlocsParColonne) * LargeurColonne;
				float y0 = Marge + (b % BlocsParColonne) * HautBloc;
				int i = 0;
				foreach (string verbe in IconeGeste.Familles[b].Grilles.Keys)
					DessinerGeste(verbe, x0 + i++ * PasColonne, y0);
			}
		}

		// Une colonne : le geste sous ses quatre formes (cf. en-tête).
		private void DessinerGeste(string verbe, float x, float y)
		{
			DrawTexture(IconeGeste.Texture(verbe, Grand), new Vector2(x, y));
			y += CoteGrand + Ecart;
			Plaque(x, y, CoteGrand, Palette16.MaitreSombre);
			DrawTexture(IconeGeste.Texture(verbe, Grand, silhouette: true), new Vector2(x, y));
			y += CoteGrand + Ecart;
			Plaque(x, y, CotePetit, Palette16.SolTerre);
			DrawTexture(IconeGeste.Texture(verbe, Petit), new Vector2(x, y));
			Plaque(x + CotePetit, y, CotePetit, Palette16.MaitreSombre);
			DrawTexture(IconeGeste.Texture(verbe, Petit, silhouette: true), new Vector2(x + CotePetit, y));
		}

		private void Plaque(float x, float y, float cote, Color fond) =>
			DrawRect(new Rect2(x, y, cote, cote), fond, filled: true);
	}
}
