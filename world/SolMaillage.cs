// SYMBIOSE — SolMaillage.cs (sprint RENDU VISIBLE D106, tronçon T2 « sol en un lot »)
// Construit le MAILLAGE d'une tuile de sol : tous ses plots (flanc du relief +
// dessus texturé) dans UN SEUL ArrayMesh, donc UN SEUL envoi au GPU par tuile.
//
// 📖 POURQUOI (diagnostic docs/perf/lod/conception_rendu_visible.md §2). Avant T2,
// chaque plot était DEUX nœuds : un Polygon2D (flanc, sans texture) puis un
// Sprite2D (dessus, texture du sol). Godot regroupe en lot (« batch ») des
// nœuds consécutifs qui partagent texture et matériau ; l'alternance
// polygone-sans-texture / sprite-texturé cassait le lot à CHAQUE nœud →
// ~2400 envois GPU par frame rien que pour le sol (≈ 105 ms sur la VM à ×0,5).
//
// 📖 L'ORDRE DES TRIANGLES EST L'ORDRE DE PEINTURE. Dans un maillage, le GPU
// dessine les triangles dans l'ordre où on les émet : on les émet donc dans
// l'ordre des anciens nœuds (flanc PUIS dessus, plot par plot) → même
// recouvrement, même image. Le damier (Modulate 1 / 0,95 du Sprite2D) devient
// un DRAPEAU de couleur de sommet ; le flanc uni porte un UV hors texture
// (UvFlanc). Le shader de SolMateriau lit l'un et l'autre.
//
// 📖 GÉOMÉTRIE DU DESSUS : le rectangle W×H de l'ancien Sprite2D centré, mêmes
// triangles, mêmes UV, et l'arrondi au pixel que Godot faisait sur CHAQUE
// sprite rejoué ici (AjouterDessus). Builder sans état moteur (vue pure).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	internal sealed class SolMaillage
	{
		// Les 6 sommets (2 triangles) du rectangle d'un Sprite2D, dans l'ORDRE
		// où le moteur de rendu 2D de Godot les émet (diagonale (0,0)-(1,1)), en
		// fraction du rectangle = UV exacts 0/1. 📖 Pourquoi tant de soin : à ×0,5
		// chaque centre de pixel tombe PILE sur une frontière de texel ; le texel
		// choisi dépend alors des arrondis d'interpolation → mêmes triangles,
		// mêmes UV, même choix qu'avant.
		private static readonly Vector2[] Quad =
		{
			new(0f, 0f), new(0f, 1f), new(1f, 1f),
			new(1f, 0f), new(0f, 0f), new(1f, 1f),
		};

		// UV hors [0,1] : marque un sommet de FLANC (couleur unie, le shader de
		// SolMateriau n'y lit pas la texture).
		public static readonly Vector2 UvFlanc = new(-1f, -1f);

		private readonly List<Vector2> _sommets = new();
		private readonly List<Vector2> _uvs = new();
		private readonly List<Color> _couleurs = new();

		/// <summary>Flanc du relief : polygone écran (le même que l'ancien
		/// Polygon2D), triangulé par la MÊME fonction que Polygon2D
		/// (Geometry2D.TriangulatePolygon) → même couverture ; dégénéré (relief
		/// nul) → aucun triangle, comme avant.</summary>
		public void AjouterFlanc(Vector2[] poly, Color couleur)
		{
			foreach (int i in Geometry2D.TriangulatePolygon(poly))
				Ajouter(poly[i], UvFlanc, couleur);
		}

		/// <summary>Dessus texturé centré sur `centre` (px écran) ; `damier` =
		/// drapeau de SolMateriau.DrapeauDamier (ex-Modulate du Sprite2D).</summary>
		public void AjouterDessus(Vector2 centre, Color damier)
		{
			var taille = new Vector2(SolTexture.W, SolTexture.H);
			// 📖 L'ARRONDI DU SPRITE2D, rejoué ici. Le SubViewport du monde snappe
			// au pixel (WorldView.tscn : snap_2d_transforms_to_pixel). Godot
			// arrondissait donc l'ORIGINE de chaque sprite, floor(pos + 0,5), dans
			// l'espace LOCAL du sol (la caméra s'applique après, dans le shader de
			// rendu), puis posait le rectangle à un décalage ENTIER,
			// floor(−taille/2 + 0,5) = (−19, −10). Sans ce double arrondi, un
			// plot sur deux glissait d'un pixel (relief visiblement différent,
			// constaté aux captures). Calcul CPU en float, comme Godot.
			var demi = new Vector2(0.5f, 0.5f);
			Vector2 coin = (centre + demi).Floor() + (-taille / 2f + demi).Floor();
			foreach (Vector2 q in Quad)
				Ajouter(coin + q * taille, q, damier);
		}

		private void Ajouter(Vector2 p, Vector2 uv, Color c)
		{
			_sommets.Add(p);
			_uvs.Add(uv);
			_couleurs.Add(c);
		}

		/// <summary>Le maillage d'une surface (triangles non indexés, sommets 2D),
		/// ou null si rien à peindre.</summary>
		public ArrayMesh Construire()
		{
			if (_sommets.Count == 0) return null;
			var arrays = new Godot.Collections.Array();
			arrays.Resize((int)Mesh.ArrayType.Max);
			arrays[(int)Mesh.ArrayType.Vertex] = _sommets.ToArray();
			arrays[(int)Mesh.ArrayType.TexUV] = _uvs.ToArray();
			arrays[(int)Mesh.ArrayType.Color] = _couleurs.ToArray();
			var mesh = new ArrayMesh();
			mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
			return mesh;
		}
	}
}
