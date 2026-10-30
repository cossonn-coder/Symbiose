// SYMBIOSE — PuddleLayer.Mare.cs (sprint SOL NOURRICIER ⑤)
// La MARE lisible en grammaire SNES. Avant ⑤, la mare peuplée du ④ se dessinait
// comme une grosse flaque : losanges translucides bleu-gris, sol visible dessous.
// Ici on ne crée AUCUNE couche ni aucun champ : on CROISE deux blocs déjà lus
// par PuddleLayer (`marais` avec son booléen d'hystérèse `etat`, et `eau_surface`).
//
//   · MARE  = plot marais INSTALLÉ ET en eau → eau permanente : aplat OPAQUE
//     sombre (plus sombre au cœur, là où les 4 voisins sont aussi de l'eau),
//     reflets clairs courts posés en lignes horizontales (le ciel dans l'eau),
//     RIVE de vase sur les arêtes qui ne touchent pas l'eau.
//   · BERGE = plot marécageux (voile de tourbe) SANS mare, voisin (8-connexité)
//     d'un plot de mare → terre humide foncée, piquée de mousse (sphaigne).
//
// 📖 Pédagogie — l'œil reconnaît une mare à trois indices, pas à sa couleur seule :
// (1) l'eau est OPAQUE et plus sombre que le sol (une flaque laisse voir le fond) ;
// (2) des reflets en traits horizontaux (convention 16 bits de l'eau calme) ;
// (3) un BORD net (rive) qui ferme la forme. Les trois sont dessinés ici.
// Couleurs vérifiées hors quasi-noir (`tools/da_image.py`, L OKLab ≥ 0,36).
//
// Déterminisme : les reflets et la mousse sont placés par un hash ENTIER du plot
// (jamais d'aléa) ; tout part dans le MÊME lot que la couche (0 draw call de plus).
// Les arêtes se calculent en projetant les coins MONDE du plot → la rive suit la
// rotation D35 (une arête « nord » reste celle qui touche le voisin r−1).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PuddleLayer
	{
		// Eau permanente : bleu-vert profond (rive) → plus sombre au cœur.
		private static readonly Color MareColor = new Color("24566b");
		private static readonly Color MareCoeurColor = new Color("1f4a5c");
		// Reflets : ciel clair + un ton intermédiaire (2 crans, pas de dégradé).
		private static readonly Color RefletClair = new Color("a8d4e0");
		private static readonly Color RefletMoyen = new Color("5f9aae");
		// Rive : vase humide brun-olive ; berge : terre mouillée + mousse.
		private static readonly Color RiveColor = new Color("5a4a2c");
		private static readonly Color BergeColor = new Color("4b3a28");
		private static readonly Color MousseColor = new Color("5f7a3a");
		private const float BergeAlpha = 0.75f;

		private readonly List<Wet> _mare = new();
		private readonly List<Wet> _berge = new();
		private readonly HashSet<(string, int, int)> _installes = new();

		// Après lecture des deux blocs : un plot en eau ET marais installé passe de
		// _flaques à _mare ; un plot marais voisin d'une mare passe de _marais à _berge.
		private void ClasserMare()
		{
			var mare = new HashSet<(string, int, int)>();
			for (int i = _flaques.Count - 1; i >= 0; i--)
			{
				var w = _flaques[i];
				if (!_installes.Contains((w.TileId, w.R, w.C))) continue;
				mare.Add((w.TileId, w.R, w.C));
				_mare.Add(w);
				_flaques.RemoveAt(i);
			}
			if (mare.Count == 0) return;
			for (int i = 0; i < _mare.Count; i++)
			{
				var w = _mare[i];
				w.Voisins = (mare.Contains((w.TileId, w.R - 1, w.C)) ? 1 : 0)
						  | (mare.Contains((w.TileId, w.R, w.C + 1)) ? 2 : 0)
						  | (mare.Contains((w.TileId, w.R + 1, w.C)) ? 4 : 0)
						  | (mare.Contains((w.TileId, w.R, w.C - 1)) ? 8 : 0);
				_mare[i] = w;
			}
			for (int i = _marais.Count - 1; i >= 0; i--)
			{
				var w = _marais[i];
				if (mare.Contains((w.TileId, w.R, w.C)) || !ToucheMare(mare, w)) continue;
				_berge.Add(w);
				_marais.RemoveAt(i);
			}
		}

		private static bool ToucheMare(HashSet<(string, int, int)> mare, Wet w)
		{
			for (int dr = -1; dr <= 1; dr++)
				for (int dc = -1; dc <= 1; dc++)
					if (mare.Contains((w.TileId, w.R + dr, w.C + dc))) return true;
			return false;
		}

		// Coins écran du plot, ordre NO, NE, SE, SO en MONDE (x = colonnes, y = lignes),
		// recalés au relief. Arête k = (coin k, coin k+1) touche le voisin de bit 1<<k.
		private static Vector2[] Coins(Wet w)
		{
			float h = WorldView.PlotCm / 2f;
			Vector2 up = new(0f, w.RisePx);
			return new[]
			{
				WorldView.WorldToScreen(w.Cx - h, w.Cy - h) - up,
				WorldView.WorldToScreen(w.Cx + h, w.Cy - h) - up,
				WorldView.WorldToScreen(w.Cx + h, w.Cy + h) - up,
				WorldView.WorldToScreen(w.Cx - h, w.Cy + h) - up,
			};
		}

		// Hash entier du plot (déterministe, stable d'un snapshot à l'autre). PAS
		// string.GetHashCode : en .NET il est randomisé à chaque lancement.
		private static int HashPlot(Wet w)
		{
			int t = 0;
			foreach (char ch in w.TileId) t = t * 31 + ch;
			return (w.R * 73856093) ^ (w.C * 19349663) ^ (t * 83492791);
		}

		private void DrawMare(Wet w, Rect2 vis)
		{
			var k = Coins(w);
			Vector2 ctr = (k[0] + k[2]) / 2f;
			if (!vis.HasPoint(ctr)) return;
			// (1) Eau opaque, plus sombre au cœur (4 voisins d'eau).
			_lot.Polygone(k, w.Voisins == 15 ? MareCoeurColor : MareColor);
			// (2) Reflets : 2 traits horizontaux courts, placés par hash dans le
			// losange intérieur (|dx|/demiL + |dy|/demiH ≤ 0,5 → jamais sur la rive).
			int hsh = HashPlot(w) & 0x7fffffff;
			float dl = WorldView.TileWPx / 2f, dh = WorldView.TileHPx / 2f;
			for (int i = 0; i < 2; i++)
			{
				float u = ((hsh >> (i * 8)) & 0xff) / 255f - 0.5f;          // −0,5..0,5
				float v = ((hsh >> (i * 8 + 4)) & 0xf) / 15f - 0.5f;
				float dx = u * dl * 0.5f, dy = v * dh * 0.4f;
				float len = dl * (i == 0 ? 0.22f : 0.14f);
				Vector2 a = ctr + new Vector2(dx - len / 2f, dy);
				_lot.Ligne(a, a + new Vector2(len, 0f), i == 0 ? RefletClair : RefletMoyen, 1f);
			}
			// (3) Rive : arêtes sans voisin d'eau.
			for (int e = 0; e < 4; e++)
				if ((w.Voisins & (1 << e)) == 0)
					_lot.Ligne(k[e], k[(e + 1) % 4], RiveColor, 2f);
		}

		private void DrawBerge(Wet w, Rect2 vis)
		{
			var k = Coins(w);
			Vector2 ctr = (k[0] + k[2]) / 2f;
			if (!vis.HasPoint(ctr)) return;
			Color sol = BergeColor;
			sol.A = BergeAlpha;
			_lot.Polygone(k, sol);
			// Mousse : 3 touffes de 2×1 px internes, placées par hash.
			int hsh = HashPlot(w) & 0x7fffffff;
			float dl = WorldView.TileWPx / 2f, dh = WorldView.TileHPx / 2f;
			for (int i = 0; i < 3; i++)
			{
				float u = ((hsh >> (i * 7)) & 0x7f) / 127f - 0.5f;
				float v = ((hsh >> (i * 7 + 3)) & 0xf) / 15f - 0.5f;
				Vector2 p = ctr + new Vector2(u * dl * 0.8f, v * dh * 0.5f);
				_lot.Ligne(p, p + new Vector2(2f, 0f), MousseColor, 1f);
			}
		}
	}
}
