// SYMBIOSE — LotTriangles.cs (sprint PLANTE ASSEMBLÉE ①, « Decor + couvre-sol en lot »)
// Accumulateur de TRIANGLES COLORÉS → UN ArrayMesh → UN DrawMesh (un envoi GPU).
// Remplace, dans les couches statiques (DecorLayer, couvre-sol), les centaines de
// DrawColoredPolygon / DrawCircle / DrawEllipse / DrawLine qui coûtaient CHACUN
// un draw call (banc E s45 ×4 [VM, n=1] : Decor 1 099 + couvre-sol 449 sur 2 013).
//
// 📖 Pédagogie — même recette que PlantShadow (ombres) et SolMaillage (sol) :
// pour le GPU, ce qui coûte, c'est le nombre d'ENVOIS, pas de triangles. On
// remplit un tampon de sommets (position + couleur par sommet), on l'envoie une
// fois. L'ORDRE DES TRIANGLES EST L'ORDRE DE PEINTURE : on les émet dans l'ordre
// des anciens appels → même recouvrement, mêmes mélanges alpha, même image.
//
// 📖 Pour que l'image reste IDENTIQUE AU PIXEL, chaque méthode rejoue la
// géométrie exacte que Godot 4.6 produisait pour l'appel remplacé
// (servers/rendering/renderer_canvas_cull.cpp) :
//   - Polygone ← draw_colored_polygon : triangulé par Geometry2D.TriangulatePolygon
//     (la même fonction) ; triangulation impossible → rien, comme Godot ;
//   - Ellipse/Cercle ← draw_ellipse/draw_circle pleins : 64 points sur le bord +
//     le centre, éventail centre→(i, i+1) ;
//   - Ligne ← draw_line à largeur ≥ 0 : quad (from±t, to±t), t = normale × w/2.
// Tous les anciens appels étaient sans antialiasing (défaut Godot) : rien à rejouer.
// ⚠️ Seul écart mesuré (captures VM avant/après) : ±1/255 sur un canal, JAMAIS plus
// — un maillage stocke ses couleurs de sommet sur 8 bits, l'ancien draw_* en float.
// La géométrie, elle, est identique (aucun bord déplacé). Une recentration de la
// couleur sur son niveau 8 bits a été essayée : elle déplace l'écart sans
// l'annuler → abandonnée (invisible à l'œil, pas de code pour rien).
//
// Vue pure, aucun état moteur ; réutilisable (Vider garde la capacité des listes).

using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	internal sealed class LotTriangles
	{
		// Godot : `static const int circle_segments = 64` (canvas_item_add_ellipse).
		private const int SegmentsCercle = 64;
		private const float PasCercle = Mathf.Tau / SegmentsCercle;

		private readonly List<Vector2> _sommets = new();
		private readonly List<Color> _couleurs = new();
		private readonly ArrayMesh _mesh = new();
		// UV par sommet (FLUIDITÉ PC ③, kit du décor) : n'est ENVOYÉ que si
		// Dessiner reçoit une texture. Les triangles « unis » prennent `UvUni`,
		// qui doit viser un texel BLANC de l'atlas : couleur de sommet × blanc =
		// la couleur, donc pièces texturées et aplats restent dans UN SEUL envoi.
		private readonly List<Vector2> _uvs = new();
		public Vector2 UvUni = Vector2.Zero;

		/// <summary>Nombre de sommets accumulés (trace de coût, DecorLayer).</summary>
		public int Sommets => _sommets.Count;

		/// <summary>Repart à vide en gardant la capacité des listes.</summary>
		public void Vider()
		{
			_sommets.Clear();
			_couleurs.Clear();
			_uvs.Clear();
		}

		/// <summary>≡ DrawColoredPolygon(pts, col).</summary>
		public void Polygone(Vector2[] pts, Color col)
		{
			foreach (int i in Geometry2D.TriangulatePolygon(pts))
				Ajouter(pts[i], col);
		}

		/// <summary>Polygone CONVEXE en éventail depuis pts[0] (FLUIDITÉ PC ③) : même
		/// couverture que Polygone pour un convexe, sans l'appel natif
		/// Geometry2D.TriangulatePolygon (marshalling coûteux quand on en fait des
		/// milliers par redessin — mesuré sur l'assise et les arbres du décor).</summary>
		public void PolygoneConvexe(Vector2[] pts, Color col)
		{
			for (int i = 1; i + 1 < pts.Length; i++)
			{
				Ajouter(pts[0], col); Ajouter(pts[i], col); Ajouter(pts[i + 1], col);
			}
		}

		/// <summary>≡ DrawCircle(centre, r, col) (plein, sans antialiasing).</summary>
		public void Cercle(Vector2 centre, float r, Color col) => Ellipse(centre, r, r, col);

		/// <summary>≡ DrawEllipse(centre, rx, ry, col) (plein, sans antialiasing).</summary>
		public void Ellipse(Vector2 centre, float rx, float ry, Color col)
		{
			// Éventail : (centre, bord i, bord i+1), le dernier se referme sur 0.
			Vector2 prec = Bord(centre, rx, ry, 0);
			Vector2 premier = prec;
			for (int i = 1; i <= SegmentsCercle; i++)
			{
				Vector2 cour = i < SegmentsCercle ? Bord(centre, rx, ry, i) : premier;
				Ajouter(centre, col); Ajouter(prec, col); Ajouter(cour, col);
				prec = cour;
			}
		}

		// Point i du bord, calculé dans l'ordre d'opérations de Godot (float) :
		// (cos(angle) × rx, sin(angle) × ry) + centre.
		private static Vector2 Bord(Vector2 c, float rx, float ry, int i)
		{
			float a = i * PasCercle;
			return new Vector2(Mathf.Cos(a) * rx, Mathf.Sin(a) * ry) + c;
		}

		/// <summary>≡ DrawLine(a, b, col, largeur) avec largeur ≥ 0 (quad).</summary>
		public void Ligne(Vector2 a, Vector2 b, Color col, float largeur)
		{
			Vector2 t = (a - b).Orthogonal().Normalized() * largeur * 0.5f;
			Vector2 gA = a + t, dA = a - t, gB = b + t, dB = b - t;
			// Quad (gA, dA, dB, gB) en deux triangles — même couverture.
			Ajouter(gA, col); Ajouter(dA, col); Ajouter(dB, col);
			Ajouter(gA, col); Ajouter(dB, col); Ajouter(gB, col);
		}

		/// <summary>Un triangle plein (sol qui respire ⑧ : silhouettes basse
		/// définition des carpophores et du bois mort — quelques triangles au lieu
		/// des 64 d'un Cercle, l'œil n'en voit pas plus à 3-10 px).</summary>
		public void Triangle(Vector2 a, Vector2 b, Vector2 c, Color col)
		{
			Ajouter(a, col); Ajouter(b, col); Ajouter(c, col);
		}

		/// <summary>Un GRAIN pixel-art (FLUIDITÉ PC LEVIERS ②, pollen + butineurs) à
		/// la place d'un DrawCircle de rayon r ≤ ~3 px : au pixel près, un cercle
		/// aussi petit ne montre pas ses 64 côtés. r &lt; 2 → losange (2 triangles :
		/// mêmes pixels « en croix » que le cercle de r 1,3) ; sinon octogone
		/// (6 triangles, sommets à 22,5° → silhouette ronde à 2-3 px). Pas
		/// d'écart à l'image hors bord du disque d'un pixel au plus.</summary>
		public void Grain(Vector2 c, float r, Color col)
		{
			if (r < 2f)
			{
				Vector2 h = new(0f, -r), b = new(0f, r), g = new(-r, 0f), d = new(r, 0f);
				Triangle(c + h, c + d, c + b, col);
				Triangle(c + h, c + b, c + g, col);
				return;
			}
			// Octogone en éventail depuis le sommet 0 (convexe).
			Vector2 p0 = c + Octo(r, 0);
			for (int i = 1; i < 7; i++)
				Triangle(p0, c + Octo(r, i), c + Octo(r, i + 1), col);
		}

		private static Vector2 Octo(float r, int i)
		{
			float a = (i + 0.5f) * (Mathf.Tau / 8f);
			return new Vector2(Mathf.Cos(a) * r, Mathf.Sin(a) * r);
		}

		/// <summary>Un rectangle TEXTURÉ (pièce d'atlas) : `dst` en coordonnées
		/// du canvas, `uv` en fraction de la texture, `mod` multiplie la pièce
		/// (blanc = telle quelle). Même diagonale que SolMaillage.Quad.</summary>
		public void Quad(Rect2 dst, Rect2 uv, Color mod)
		{
			Vector2 a = dst.Position, c = dst.End;
			Vector2 ua = uv.Position, uc = uv.End;
			Vector2 b = new(a.X, c.Y), d = new(c.X, a.Y);
			Vector2 ub = new(ua.X, uc.Y), ud = new(uc.X, ua.Y);
			Ajouter(a, ua, mod); Ajouter(b, ub, mod); Ajouter(c, uc, mod);
			Ajouter(d, ud, mod); Ajouter(a, ua, mod); Ajouter(c, uc, mod);
		}

		private void Ajouter(Vector2 p, Color c) => Ajouter(p, UvUni, c);

		private void Ajouter(Vector2 p, Vector2 uv, Color c)
		{
			_sommets.Add(p);
			_uvs.Add(uv);
			_couleurs.Add(c);
		}


		/// <summary>FIGE le lot accumulé dans un ArrayMesh NEUF, à garder et à
		/// redessiner tel quel (FLUIDITÉ PC LEVIERS ③ : une maille de décor par
		/// palier). null si le lot est vide.</summary>
		public ArrayMesh Figer(bool avecUv)
		{
			if (_sommets.Count == 0) return null;
			var arrays = new Godot.Collections.Array();
			arrays.Resize((int)Mesh.ArrayType.Max);
			arrays[(int)Mesh.ArrayType.Vertex] = _sommets.ToArray();
			arrays[(int)Mesh.ArrayType.Color] = _couleurs.ToArray();
			if (avecUv) arrays[(int)Mesh.ArrayType.TexUV] = _uvs.ToArray();
			var m = new ArrayMesh();
			m.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
			return m;
		}

		/// <summary>Envoie le lot accumulé : UN DrawMesh sur `ci` (à appeler
		/// depuis son _Draw). Rien à peindre → aucun envoi. `texture` (optionnelle)
		/// = l'atlas des pièces posées par Quad ; sans elle, les UV ne partent pas.</summary>
		public void Dessiner(CanvasItem ci, Texture2D texture = null)
		{
			if (_sommets.Count == 0) return;
			var arrays = new Godot.Collections.Array();
			arrays.Resize((int)Mesh.ArrayType.Max);
			arrays[(int)Mesh.ArrayType.Vertex] = _sommets.ToArray();
			arrays[(int)Mesh.ArrayType.Color] = _couleurs.ToArray();
			if (texture != null) arrays[(int)Mesh.ArrayType.TexUV] = _uvs.ToArray();
			_mesh.ClearSurfaces();
			_mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
			ci.DrawMesh(_mesh, texture);
		}
	}
}
