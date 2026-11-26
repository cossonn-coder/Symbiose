// SYMBIOSE — RubanTexture.cs (sprint BOIS & ARBRES ① — primitive « ruban texturé »)
// UNE primitive pour tout ce qui est long et courbe : le bois des plantes (tube lissé, ①), puis les
// brins et rubans des graminées (③) et le décor de lisière (S3). Indépendante de PlantRenderer :
// elle reçoit une polyligne À L'ÉCRAN, une demi-largeur par point, et pose des triangles.
//
// Coordonnées : u en TRAVERS (−1 bord droit … +1 bord gauche, côté de la normale), v le long
// (longueur d'arc en cm, fournie par l'appelant) → au ② la texture d'écorce garde son échelle à
// tous les paliers et ne se coupe jamais le long d'un axe. Au ① elle est peinte en TONS : une
// bande = une plage [u0, u1] d'une couleur choisie par l'appelant selon l'orientation du quad.
//
// 📖 Pédagogie Godot : `DrawLine` épais = un rectangle à bouts carrés — deux traits successifs
// d'angle différent laissent une encoche, et leur largeur change d'un coup (la « marche »).
// Ici les deux bords sont calculés POINT PAR POINT (normale = bissectrice des deux pas voisins,
// raccord en onglet borné) : deux quads voisins partagent leurs sommets, il n'y a plus de joint.
// Les triangles partent en UN appel `RenderingServer.CanvasItemAddTriangleArray` par bande, dans
// la liste de commandes du CanvasItem, exactement là où un `DrawLine` aurait été (même ordre).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public static class RubanTexture
	{
		// Onglet borné : au-delà, un coude très serré ferait une pointe (le bord extérieur s'envole).
		private const float OngletMax = 2f;

		/// <summary>Normales par point (unitaires × facteur d'onglet) de la polyligne `pts`.
		/// Convention : normale = (−dy, dx) de la direction, comme les flancs de l'ancien bois.</summary>
		public static Vector2[] Normales(Vector2[] pts)
		{
			int n = pts.Length;
			var nrm = new Vector2[n];
			for (int k = 0; k < n; k++)
			{
				Vector2 a = k > 0 ? Perp(pts[k] - pts[k - 1]) : Vector2.Zero;
				Vector2 b = k < n - 1 ? Perp(pts[k + 1] - pts[k]) : Vector2.Zero;
				if (a == Vector2.Zero) a = b;
				if (b == Vector2.Zero) b = a;
				Vector2 m = (a + b).Normalized();
				if (m == Vector2.Zero) m = a;   // demi-tour : on garde un côté
				float c = m.Dot(a);
				nrm[k] = c > 1e-3f ? m * Mathf.Min(1f / c, OngletMax) : m;
			}
			return nrm;
		}

		/// <summary>Perpendiculaire unitaire (−dy, dx) d'un pas ; zéro si le pas est nul.</summary>
		public static Vector2 Perp(Vector2 d)
		{
			float l = d.Length();
			return l < 1e-5f ? Vector2.Zero : new Vector2(-d.Y, d.X) / l;
		}

		// Tampons réutilisés (le dessin se fait sur le fil principal, un ruban à la fois).
		private static readonly List<Vector2> _pts = new();
		private static readonly List<Color> _cols = new();
		private static readonly List<Vector2> _uvs = new();
		private static readonly List<int> _idx = new();

		/// <summary>Ajoute la bande [u0, u1] du ruban (`pts` écran, `demi` demi-largeurs, `nrm` de
		/// `Normales`, `v` longueur d'arc) au lot en cours. `couleur(perp)` donne la couleur d'un quad
		/// selon la perpendiculaire de son pas (l'appelant en tire l'orientation du flanc). Les bandes
		/// s'empilent dans l'ordre d'ajout ; `Envoyer` les pose en UN appel.</summary>
		public static void PoserBande(Vector2[] pts, float[] demi, Vector2[] nrm, float[] v,
			float u0, float u1, System.Func<Vector2, Color> couleur)
		{
			for (int k = 0; k + 1 < pts.Length; k++)
			{
				Vector2 perp = Perp(pts[k + 1] - pts[k]);
				if (perp == Vector2.Zero) continue;   // pas nul (segment naissant) : rien à poser
				Color c = couleur(perp);
				int b = _pts.Count;
				_pts.Add(pts[k] + nrm[k] * (demi[k] * u0));
				_pts.Add(pts[k] + nrm[k] * (demi[k] * u1));
				_pts.Add(pts[k + 1] + nrm[k + 1] * (demi[k + 1] * u1));
				_pts.Add(pts[k + 1] + nrm[k + 1] * (demi[k + 1] * u0));
				for (int q = 0; q < 4; q++) _cols.Add(c);
				_uvs.Add(new Vector2(u0, v[k])); _uvs.Add(new Vector2(u1, v[k]));
				_uvs.Add(new Vector2(u1, v[k + 1])); _uvs.Add(new Vector2(u0, v[k + 1]));
				_idx.Add(b); _idx.Add(b + 1); _idx.Add(b + 2);
				_idx.Add(b); _idx.Add(b + 2); _idx.Add(b + 3);
			}
		}

		/// <summary>② : bande [u0, u1] TEXTURÉE par une bande PÉRIODIQUE de la texture `tex` (rectangle
		/// `rect` en texels) : u en travers → largeur du rectangle, v (cm) + `decalage` → hauteur, une
		/// période `periode` (cm) = toute la hauteur. Un quad qui franchit une période est COUPÉ à la
		/// frontière (sans quoi l'interpolation des UV remonterait toute la bande à l'envers dans le
		/// quad) : chaque morceau lit sa portion, la coupure du haut rejoint celle du bas. Une seule
		/// couleur `mod` (palette de la pièce, modulate). `garder(k)` : le quad k est-il posé.</summary>
		public static void PoserBandePeriodique(Vector2[] pts, float[] demi, Vector2[] nrm, float[] v,
			float u0, float u1, Texture2D tex, Rect2 rect, float periode, float decalage, Color mod,
			System.Func<int, bool> garder)
		{
			Vector2 taille = tex.GetSize();
			float x0 = rect.Position.X / taille.X, x1 = rect.End.X / taille.X;
			for (int k = 0; k + 1 < pts.Length; k++)
			{
				if (!garder(k) || pts[k].IsEqualApprox(pts[k + 1])) continue;
				Vector2 a = pts[k] + nrm[k] * (demi[k] * u0), b = pts[k] + nrm[k] * (demi[k] * u1);
				Vector2 c = pts[k + 1] + nrm[k + 1] * (demi[k + 1] * u1), d = pts[k + 1] + nrm[k + 1] * (demi[k + 1] * u0);
				float f0 = (v[k] + decalage) / periode, f1 = (v[k + 1] + decalage) / periode;
				float ta = 0f;
				while (ta < 1f)
				{
					// Fin du morceau : la prochaine frontière de période, ou le bout du quad.
					float fa = f0 + (f1 - f0) * ta, n = Mathf.Floor(fa + 1e-5f);
					float tb = f1 - f0 > 1e-6f ? Mathf.Min(1f, (n + 1f - f0) / (f1 - f0)) : 1f;
					float fb = f0 + (f1 - f0) * tb;
					// Rangée : le haut de la bande (rangée 0) est le bout de la période (f → 1).
					float ya = (rect.Position.Y + (1f - (fa - n)) * rect.Size.Y) / taille.Y;
					float yb = (rect.Position.Y + (1f - (fb - n)) * rect.Size.Y) / taille.Y;
					int i0 = _pts.Count;
					_pts.Add(a.Lerp(d, ta)); _pts.Add(b.Lerp(c, ta)); _pts.Add(b.Lerp(c, tb)); _pts.Add(a.Lerp(d, tb));
					_uvs.Add(new Vector2(x0, ya)); _uvs.Add(new Vector2(x1, ya)); _uvs.Add(new Vector2(x1, yb)); _uvs.Add(new Vector2(x0, yb));
					for (int q = 0; q < 4; q++) _cols.Add(mod);
					_idx.Add(i0); _idx.Add(i0 + 1); _idx.Add(i0 + 2);
					_idx.Add(i0); _idx.Add(i0 + 2); _idx.Add(i0 + 3);
					ta = tb > ta ? tb : 1f;
				}
			}
		}

		/// <summary>Pose le lot en cours sur le CanvasItem `ci` (un seul appel) puis le vide. `tex` :
		/// texture du ② lue en (u, v) ; null = tons seuls (aucune coordonnée envoyée).</summary>
		public static void Envoyer(CanvasItem ci, Texture2D tex = null)
		{
			if (_idx.Count > 0)
				RenderingServer.CanvasItemAddTriangleArray(ci.GetCanvasItem(), _idx.ToArray(), _pts.ToArray(),
					_cols.ToArray(), tex != null ? _uvs.ToArray() : null, texture: tex?.GetRid() ?? default);
			_pts.Clear(); _cols.Clear(); _uvs.Clear(); _idx.Clear();
		}
	}
}
