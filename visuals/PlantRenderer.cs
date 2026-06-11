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
		// Surbrillance du segment sous la souris en mode tailler (tranche 5) :
		// même jaune clair que le flash de geste réussi — un seul langage visuel.
		private static readonly Color HighlightColor = new Color("ffe66b");

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

		// Segment à surligner (index dans Segments = l'ordre du SNAPSHOT, le
		// même que structure_to_dict() Python — c'est CET index qui part dans
		// target.segment). −1 = aucun. 📖 Propriété avec setter early-out : on
		// peut l'écrire chaque frame depuis WorldView, le QueueRedraw (coûteux
		// sur un vieil arbre) ne part qu'au CHANGEMENT de segment survolé.
		private int _highlightSegment = -1;
		public int HighlightSegment
		{
			get => _highlightSegment;
			set
			{
				if (value == _highlightSegment) return;
				_highlightSegment = value;
				QueueRedraw();
			}
		}

		public override void _Ready()
		{
			_shadow = new PlantShadow { Name = "Shadow", ShowBehindParent = true };
			AddChild(_shadow);
			_shadow.SetExtent(_spreadCm, _heightCm);   // si SetStructure a précédé
		}

		public void SetStructure(PlantStructure s)
		{
			_structure = s;
			// Les index de segments changent à chaque snapshot (une coupe
			// réindexe la structure côté moteur) : une surbrillance gardée
			// pointerait la mauvaise branche — le survol la re-résout au
			// prochain frame, on repart de « rien ».
			_highlightSegment = -1;
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
		// HIT-TEST DE SEGMENT (tranche 5 — taille au clic)
		// ---------------------------------------------------------------------------

		/// <summary>
		/// Le segment le plus proche de `canvasPos` (souris en coordonnées
		/// canvas, cf. GetGlobalMousePosition) à moins de `maxDistPx` px CANVAS,
		/// ou −1. L'index renvoyé est celui du SNAPSHOT (ordre préservé par
		/// StructureLoader.FromSnapshot) : il part tel quel dans target.segment.
		/// 📖 La géométrie est EXACTEMENT celle de DrawSegments (même Iso, mêmes
		/// extrémités — leçon D2 : pas de 2ᵉ projection « presque pareille ») :
		/// on surligne précisément ce qu'on dessine. Distance point-segment via
		/// Geometry2D.GetClosestPointToSegment (clamp aux extrémités compris).
		/// ~50 segments max par plante (MAX_SEGMENTS) : linéaire, trivial.
		/// Le segment 0 (collet, protégé moteur) est EXCLU : un clic au pied ne
		/// doit pas désigner l'incoupable — il retombe sur le repli t4
		/// (params.cible), comportement inchangé, critère 2 du kickoff.
		/// </summary>
		public int FindSegmentNear(Vector2 canvasPos, float maxDistPx)
		{
			if (_structure == null || _structure.Segments.Count < 2)
				return -1;
			// ToLocal : canvas → repère local du nœud (sa Position est le
			// collet à l'écran) — le même espace que les primitives de _Draw.
			Vector2 local = ToLocal(canvasPos);
			Vector3 collet = _structure.ColletCm;
			int best = -1;
			float bestD = maxDistPx;
			for (int i = 1; i < _structure.Segments.Count; i++)   // 0 = collet, exclu
			{
				var s = _structure.Segments[i];
				Vector3 tip = s.Base + s.Dir * s.LengthCm;
				Vector2 p1 = Iso(s.Base.X - collet.X, s.Base.Y - collet.Y, s.Base.Z);
				Vector2 p2 = Iso(tip.X - collet.X, tip.Y - collet.Y, tip.Z);
				float d = local.DistanceTo(
					Geometry2D.GetClosestPointToSegment(local, p1, p2));
				if (d < bestD) { bestD = d; best = i; }
			}
			return best;
		}

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

			// Surbrillance (tranche 5) : le segment sous la souris en mode
			// tailler se redessine PAR-DESSUS, après tout le bois.
			DrawHighlight(collet);
		}

		// Le segment surligné, en clair et un peu plus large — « c'est CETTE
		// branche que le sécateur va prendre ». Index lu dans la liste
		// ORIGINALE du snapshot (le tri par épaisseur de DrawSegments est une
		// copie locale) : ce qu'on surligne = ce qu'on enverra en target.segment.
		private void DrawHighlight(Vector3 collet)
		{
			int hi = HighlightSegment;
			if (hi < 0 || hi >= _structure.Segments.Count)
				return;
			var s = _structure.Segments[hi];
			Vector3 tip = s.Base + s.Dir * s.LengthCm;
			Vector2 p1 = Iso(s.Base.X - collet.X, s.Base.Y - collet.Y, s.Base.Z);
			Vector2 p2 = Iso(tip.X - collet.X, tip.Y - collet.Y, tip.Z);
			float w = Mathf.Max(2f,
				Mathf.Round(s.ThicknessCm * WorldView.PxPerCmX * 2.2f) + 2f);
			DrawLine(p1, p2, HighlightColor, w, antialiased: false);
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
