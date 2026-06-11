// SYMBIOSE — PlantRenderer.cs
// Premier RENDU VISIBLE des branches (tronçon 4 du sprint Croissance).
// Un Node2D qui projette en isométrie la structure de segments (exportée par
// Python, source de vérité) et la rastérise en pixels. Consommateur passif :
// aucune logique écologique, aucun RNG — juste géométrie → pixels.
//
// Idiomes Godot expliqués (Nico débute le frontend) :
//  · Node2D = nœud d'arbre de scène avec une transform 2D (position/rotation/
//    échelle). Son `Position` place son ORIGINE locale à l'écran. Ici on pose
//    l'origine sur le COLLET de la plante (sa position au sol dans la grille).
//  · _Draw() = rappel de DESSIN IMMÉDIAT. Godot l'appelle quand le nœud doit se
//    redessiner ; on y émet des primitives (DrawLine, DrawColoredPolygon) en
//    coordonnées LOCALES (relatives à Position). Pour forcer un redraw après un
//    changement de données, on appelle QueueRedraw().
//  · antialiased:false sur DrawLine = pas de lissage → cohérent avec le pixel art
//    (filtre Nearest partout, cf. CLAUDE.md). Sans ça, les branches « bavent ».

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer : Node2D
	{
		// --- Projection iso : DÉLÉGUÉE à WorldView.WorldToScreen (tranche 2) ---
		// UNE seule projection pour tout le monde (tuiles, maison, plantes),
		// calibrée sur le losange réel du sprite tuile (78×39 px pour 50 cm →
		// 0.78 px/cm) — c'est la levée de D2 : l'ancien couple cos30/sin30 ×
		// PxPerCm=0.42 (maquette SVG, allure « panneau ») dupliquait un 2ᵉ modèle
		// iso qui ne coïncidait pas avec la grille. dz (hauteur) tire vers le
		// HAUT : en 2D Godot +Y est vers le BAS, donc on SOUSTRAIT dz·PxPerCmZ.
		// NB : l'échelle est désormais celle du MONDE — un pommier de 350 cm fait
		// ~273 px de haut (~7 plots), c'est voulu (cohérence spatiale empreintes ↔
		// couronnes). L'ancienne démo TileGrid affichera donc ses spécimens plus
		// grands qu'avant — elle n'est plus la scène principale, assumé.

		// Palier de zoom STUBÉ (la caméra/zoom n'est pas encore câblée — beaucoup de
		// C# est stub). Pilote le LOD (§H.3) : ≤4 → silhouette de couronne ; ≥8 →
		// détail segment. TODO: brancher sur le vrai zoom caméra quand il existera.
		[Export] public int ZoomPalier = 16;

		// Couleurs (identiques à la maquette) : apex vert vif, bois brun.
		private static readonly Color ApexColor = new Color("5ec46a");
		private static readonly Color WoodColor = new Color("7a5230");
		private static readonly Color CrownColor = new Color("3f7a4e"); // silhouette LOD

		// La structure à dessiner (assignée par le spawner, cf. TileGrid). Null tant
		// que rien n'est chargé → _Draw ne fait rien.
		private PlantStructure _structure;
		// Étendue horizontale max des segments autour du collet (cm) — rayon de
		// l'ombre au sol, recalculé à chaque SetStructure (t4 A2).
		private float _spreadCm;
		// Hauteur de cime (cm) — porte la LONGUEUR de l'ombre-capsule (t4 volet
		// C) : longueur = hauteur × 1/tan(élévation), exactement le modèle
		// ombres-capsules du moteur (fields/light.py §3).
		private float _heightCm;
		// L'ombre vit dans un nœud ENFANT séparé (volet C2, retour perf Nico) :
		// quand le soleil balaye, SEULE l'ombre se redessine (un polygone),
		// jamais les segments — le coût du balayage ne grandit plus avec l'âge
		// des plantes. ShowBehindParent la dessine SOUS le bois, même YSort.
		private PlantShadow _shadow;

		public override void _Ready()
		{
			_shadow = new PlantShadow { Name = "Shadow", ShowBehindParent = true };
			AddChild(_shadow);
			_shadow.SetExtent(_spreadCm, _heightCm);   // si SetStructure a précédé
		}

		public void SetStructure(PlantStructure s)
		{
			_structure = s;
			_spreadCm = 8f;   // minimum visible, même pour une pousse droite
			_heightCm = 10f;  // plancher : même une pousse projette un soupçon
			if (s != null)
			{
				Vector3 collet = s.ColletCm;
				foreach (var seg in s.Segments)
				{
					Vector3 tip = seg.Base + seg.Dir * seg.LengthCm;
					float d = new Vector2(tip.X - collet.X, tip.Y - collet.Y).Length();
					if (d > _spreadCm) _spreadCm = d;
					float z = tip.Z - collet.Z;
					if (z > _heightCm) _heightCm = z;
				}
			}
			_shadow?.SetExtent(_spreadCm, _heightCm);
			QueueRedraw(); // redemande un _Draw au prochain frame
		}

		// ---------------------------------------------------------------------------
		// PROJECTION
		// ---------------------------------------------------------------------------

		// dx/dy sont des OFFSETS au collet (vecteurs) → variante Offset de la
		// projection : seule la partie linéaire de l'orientation de vue (D35,
		// tranche 4) s'applique. WorldToScreen (points absolus) ajouterait la
		// translation du quart de tour et téléporterait chaque branche. Effet
		// gagné : la plante « tourne » avec le monde — son phototropisme penche
		// vers le même point monde (la maison) quelle que soit la vue.
		private static Vector2 Iso(float dx, float dy, float dz) =>
			WorldView.WorldToScreenOffset(dx, dy) - new Vector2(0f, dz * WorldView.PxPerCmZ);

		// ---------------------------------------------------------------------------
		// DESSIN
		// ---------------------------------------------------------------------------

		public override void _Draw()
		{
			if (_structure == null || _structure.Segments.Count == 0)
				return;

			// L'ombre au sol n'est PLUS dessinée ici (volet C2) : elle vit dans
			// le nœud enfant PlantShadow (ShowBehindParent) — le balayage du
			// soleil ne redessine qu'elle, jamais ces segments-ci.

			// LOD §H.3 : zoom faible → on ne rastérise pas chaque brindille, on
			// dessine la silhouette de couronne dérivée de l'empreinte (§G).
			if (ZoomPalier <= 4)
			{
				DrawCanopySilhouette();
				return;
			}

			DrawSegments();
		}

		private void DrawSegments()
		{
			Vector3 collet = _structure.ColletCm;

			// Tri par épaisseur DÉCROISSANTE : le bois épais (tronc) se dessine
			// d'abord (dessous), les fines brindilles par-dessus — comme _panel.
			var segs = new List<Segment>(_structure.Segments);
			segs.Sort((a, b) => b.ThicknessCm.CompareTo(a.ThicknessCm));

			foreach (var s in segs)
			{
				Vector3 tip = s.Base + s.Dir * s.LengthCm;
				// On soustrait x,y du collet (recadrage horizontal) et on garde z
				// absolu (le collet est au sol, z=0) — exactement comme _iso(bx-cx,…).
				Vector2 p1 = Iso(s.Base.X - collet.X, s.Base.Y - collet.Y, s.Base.Z);
				Vector2 p2 = Iso(tip.X - collet.X, tip.Y - collet.Y, tip.Z);

				// Largeur ∝ épaisseur, ARRONDIE au pixel (pixel art). NB : à un vrai
				// zoom ×N, 1 px logique = N px écran ; l'arrondi entier ici donne un
				// trait net au palier. min 1 px pour rester visible.
				float w = Mathf.Max(1f, Mathf.Round(s.ThicknessCm * WorldView.PxPerCmX * 2.2f));
				Color color = s.IsApex ? ApexColor : WoodColor;

				DrawLine(p1, p2, color, w, antialiased: false);
			}
		}

		// Silhouette grossière de couronne pour le LOD faible : une ellipse pleine
		// centrée à mi-hauteur de la plante, dimensionnée par le rayon de couronne
		// (empreinte §G). Volontairement simple — placeholder LOD, pas un rendu fin.
		private void DrawCanopySilhouette()
		{
			float cr = _structure.CanopyRadiusCm;
			Vector2 center = Iso(0f, 0f, _structure.HeightCm * 0.55f);
			float rx = cr * WorldView.PxPerCmX;        // largeur ~ rayon couronne projeté
			float ry = cr * WorldView.PxPerCmX * 0.8f; // couronne légèrement aplatie

			const int n = 24;
			var pts = new Vector2[n];
			for (int i = 0; i < n; i++)
			{
				float a = Mathf.Tau * i / n;
				pts[i] = center + new Vector2(rx * Mathf.Cos(a), ry * Mathf.Sin(a));
			}
			DrawColoredPolygon(pts, CrownColor);
		}
	}

	// =======================================================================
	// OMBRE-CAPSULE AU SOL (t4 volet C, isolée en C2 — retour perf Nico) :
	// disque monde de rayon spread glissé depuis le collet le long de la
	// direction d'ombre solaire, sur hauteur × 1/tan(élévation) — le modèle
	// EXACT des ombres-capsules du moteur (fields/light.py §3). Nœud séparé :
	// quand UpdateSun balaye (≥ 2°), il ne fait QueueRedraw QUE sur ces nœuds
	// — un petit polygone chacun — jamais sur les segments des plantes. Chaque
	// point passe par WorldToScreenOffset → l'ombre suit AUSSI la rotation de
	// la vue (D35). Touche O (WorldView.ShadowsOn) : _Draw vide = coût nul.
	// =======================================================================
	public partial class PlantShadow : Node2D
	{
		private static readonly Color ShadowColor = new Color(0f, 0f, 0f, 0.18f);
		private float _spreadCm = 8f;    // rayon de la capsule (étalement)
		private float _heightCm = 10f;   // hauteur de cime → longueur d'ombre

		public void SetExtent(float spreadCm, float heightCm)
		{
			_spreadCm = spreadCm;
			_heightCm = heightCm;
			QueueRedraw();
		}

		public override void _Draw()
		{
			if (!WorldView.ShadowsOn) return;
			Vector2 dir = WorldView.SunShadowDir;            // unité, monde
			Vector2 end = dir * (_heightCm * WorldView.SunInvTan);
			float a0 = Mathf.Atan2(dir.Y, dir.X);
			const int n = 8;                                  // par demi-cercle
			var pts = new Vector2[2 * (n + 1)];
			int k = 0;
			for (int i = 0; i <= n; i++)                      // arrière (collet)
			{
				float a = a0 + Mathf.Pi / 2f + Mathf.Pi * i / n;
				pts[k++] = WorldView.WorldToScreenOffset(
					_spreadCm * Mathf.Cos(a), _spreadCm * Mathf.Sin(a));
			}
			for (int i = 0; i <= n; i++)                      // avant (bout d'ombre)
			{
				float a = a0 - Mathf.Pi / 2f + Mathf.Pi * i / n;
				pts[k++] = WorldView.WorldToScreenOffset(
					end.X + _spreadCm * Mathf.Cos(a), end.Y + _spreadCm * Mathf.Sin(a));
			}
			// Soleil bas → lumière faible → ombre plus pâle (et plus longue).
			var col = ShadowColor;
			col.A = ShadowColor.A * Mathf.Clamp(WorldView.SunStrength * 1.4f, 0.3f, 1f);
			DrawColoredPolygon(pts, col);
		}
	}
}
