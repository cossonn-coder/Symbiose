// SYMBIOSE — PlantShadow.cs
// Ombres-capsules au sol de TOUTES les plantes, en UN LOT (sprint PERF VUE ③).
// Avant ③ : un nœud PlantShadow enfant de chaque plante (t4 volet C, isolé en
// C2) — 272 polygones, chacun son ordre de dessin, intercalés dans le tri en Y
// des plantes, tous redessinés à chaque pas de soleil.
//
// Modèle INCHANGÉ (vérité Python) : disque monde de rayon spread glissé depuis
// le collet le long de la direction d'ombre solaire, sur hauteur × 1/tan(élév.)
// — les ombres-capsules du moteur (fields/light.py §3). Chaque point passe par
// WorldToScreenOffset → l'ombre suit la rotation de la vue (D35). Alpha selon
// SunStrength, comme l'ombre de la maison.
//
// 📖 Pédagogie — pourquoi un lot : pour le GPU, ce qui coûte n'est pas le
// nombre de triangles mais le nombre d'ENVOIS (draw calls) et de changements
// d'état entre eux. Toutes les capsules partent ici en UN maillage (ArrayMesh :
// un tableau de sommets + un tableau d'indices, chaque capsule convexe découpée
// en éventail), dessiné par DrawMesh. C'est le « vertex buffer unique » de
// l'embarqué : on remplit un tampon, on l'envoie une fois. ⚠️ Mesuré au banc E
// (VM, 2026-10-19) : la même géométrie passée par CanvasItemAddTriangleArray
// coûtait +55 ms de rendu par image (chemin lent du pilote) — d'où le maillage. Le nœud vit dans "Objects" avec un ZIndex relatif −2 : SOUS toutes
// les plantes et la maison (ZIndex relatif 0 / −1 derrière la maison, tri Y — D112 ②), au-dessus du sol, de la
// vie macro — hors du tri en Y des plantes, qui ne sont plus coupées en deux
// lots par leurs ombres.
//
// Recalcul (drapeau statique Sale, consommé une fois par image dans _Process) :
// pas de soleil ≥ 2° (WorldView.Soleil.cs), touche O, plante qui change
// d'emprise ou de tapis (PlantRenderer.Invalidate), entrée/sortie de la marge
// (WorldView.CullPlants), retrait d'une plante (snapshot). Seules les plantes
// DANS la marge (Visible, cf. world/MargeVue.cs) et hors tapis portent une ombre.

using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	public partial class PlantShadow : Node2D
	{
		// CASSÉ À L'ÉCRAN ③ : ombre TEINTÉE vert-noir (#071010, brief DA : jamais de
		// noir), alpha 0,2 ≈ même assombrissement qu'un noir à 0,18 sur un sol moyen.
		private static readonly Color ShadowColor = new Color(0.027f, 0.063f, 0.063f, 0.2f);
		private const int N = 8;                     // sommets par demi-cercle (+1)
		private const int SommetsParCapsule = 2 * (N + 1);

		/// <summary>Une ombre au moins a changé : le lot est à refaire.</summary>
		public static bool Sale { get; private set; } = true;
		public static void MarquerSale() => Sale = true;

		// Les plantes affichées (vue vivante sur WorldView._plantNodes).
		private readonly IEnumerable<PlantRenderer> _plantes;

		// Tampons réutilisés (pas d'allocation par recalcul hors redimension).
		private readonly List<Vector2> _pts = new();
		private readonly List<int> _idx = new();
		private readonly List<Color> _cols = new();
		private readonly ArrayMesh _mesh = new();
		private readonly Vector2[] _capsule = new Vector2[SommetsParCapsule];

		public PlantShadow(IEnumerable<PlantRenderer> plantes)
		{
			_plantes = plantes;
			Name = "Ombres";
			ZIndex = -2;          // relatif à Objects : sous toutes les plantes ET la maison (−1, D112 ②)
			MarquerSale();
		}

		// Godot exige un constructeur sans argument pour instancier un script.
		public PlantShadow() { }

		public override void _Process(double delta)
		{
			if (!Sale) return;
			Sale = false;
			QueueRedraw();
		}

		// Banc PERF VUE ① : chronométré (PerfPostes) — appels/s = recalculs du lot.
		public override void _Draw()
		{
			long t0 = PerfPostes.Debut();
			DessinerOmbres();
			PerfPostes.Fin(PerfPostes.Poste.OmbreDraw, t0);
		}

		private void DessinerOmbres()
		{
			if (!WorldView.ShadowsOn || _plantes == null) return;
			_pts.Clear(); _idx.Clear(); _cols.Clear();
			// Soleil bas → lumière faible → ombre plus pâle (et plus longue).
			var col = ShadowColor;
			col.A = ShadowColor.A * Mathf.Clamp(WorldView.SunStrength * 1.4f, 0.3f, 1f);
			foreach (var p in _plantes)
			{
				if (!IsInstanceValid(p) || !p.Visible || p.EnTapis) continue;
				Capsule(p.OmbreSpreadCm, p.OmbreHeightCm);
				int b = _pts.Count;
				foreach (var v in _capsule) { _pts.Add(p.Position + v); _cols.Add(col); }
				for (int i = 1; i < SommetsParCapsule - 1; i++)   // éventail convexe
				{
					_idx.Add(b); _idx.Add(b + i); _idx.Add(b + i + 1);
				}
			}
			if (_idx.Count == 0) return;
			var arrays = new Godot.Collections.Array();
			arrays.Resize((int)Mesh.ArrayType.Max);
			arrays[(int)Mesh.ArrayType.Vertex] = _pts.ToArray();
			arrays[(int)Mesh.ArrayType.Color] = _cols.ToArray();
			arrays[(int)Mesh.ArrayType.Index] = _idx.ToArray();
			_mesh.ClearSurfaces();
			_mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
			DrawMesh(_mesh, null);
		}

		// Contour de la capsule (offsets écran autour du collet) dans _capsule.
		private void Capsule(float spreadCm, float heightCm)
		{
			Vector2 dir = WorldView.SunShadowDir;            // unité, monde
			Vector2 end = dir * (heightCm * WorldView.SunInvTan);
			float a0 = Mathf.Atan2(dir.Y, dir.X);
			int k = 0;
			for (int i = 0; i <= N; i++)                      // arrière (collet)
			{
				float a = a0 + Mathf.Pi / 2f + Mathf.Pi * i / N;
				_capsule[k++] = WorldView.WorldToScreenOffset(
					spreadCm * Mathf.Cos(a), spreadCm * Mathf.Sin(a));
			}
			for (int i = 0; i <= N; i++)                      // avant (bout d'ombre)
			{
				float a = a0 - Mathf.Pi / 2f + Mathf.Pi * i / N;
				_capsule[k++] = WorldView.WorldToScreenOffset(
					end.X + spreadCm * Mathf.Cos(a), end.Y + spreadCm * Mathf.Sin(a));
			}
		}
	}
}
