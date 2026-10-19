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

		/// <summary>Repart à vide en gardant la capacité des listes.</summary>
		public void Vider()
		{
			_sommets.Clear();
			_couleurs.Clear();
		}

		/// <summary>≡ DrawColoredPolygon(pts, col).</summary>
		public void Polygone(Vector2[] pts, Color col)
		{
			foreach (int i in Geometry2D.TriangulatePolygon(pts))
				Ajouter(pts[i], col);
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

		private void Ajouter(Vector2 p, Color c)
		{
			_sommets.Add(p);
			_couleurs.Add(c);
		}


		/// <summary>Envoie le lot accumulé : UN DrawMesh sur `ci` (à appeler
		/// depuis son _Draw). Rien à peindre → aucun envoi.</summary>
		public void Dessiner(CanvasItem ci)
		{
			if (_sommets.Count == 0) return;
			var arrays = new Godot.Collections.Array();
			arrays.Resize((int)Mesh.ArrayType.Max);
			arrays[(int)Mesh.ArrayType.Vertex] = _sommets.ToArray();
			arrays[(int)Mesh.ArrayType.Color] = _couleurs.ToArray();
			_mesh.ClearSurfaces();
			_mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
			ci.DrawMesh(_mesh, null);
		}
	}
}
