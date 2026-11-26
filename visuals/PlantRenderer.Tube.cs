// SYMBIOSE — PlantRenderer.Tube.cs (partial, sprint BOIS & ARBRES ① — tube lissé)
// LE BOIS EN TUBE : chaque segment du moteur était un `DrawLine` à bouts carrés, à largeur
// arrondie au pixel → tronc en pile de rectangles (marches), branches en bâtons, coudes cassés.
// Ici le bois suit la courbe de BoisAxes.cs (passe par tous les nœuds du moteur), avec une
// largeur continue, un pied évasé et des cols de branche, et il se peint par la primitive
// RubanTexture.cs. Les tons restent ceux de l'ancien `DrawEcorce` (âme plate + 2 flancs orientés
// + stries au hash) ; ② y pose l'écorce cuite de l'essence (PlantRenderer.Ecorce.cs).
//
// Tri par PROFONDEUR iso (et non plus par épaisseur) : une branche partie derrière le tronc passe
// derrière lui. L'unité triée est le morceau (un segment) ; deux morceaux voisins d'un même axe
// partagent leurs sommets, leur ordre de pose ne laisse donc aucun joint.
//
// Géométrie unique : `PointDuBois` est LE point du bois pour tous les lecteurs (rameaux, feuilles,
// bout tendre, clic, surbrillance). INTERRUPTEUR : le même que les splats (Maj+F11,
// SYMBIOSE_SPLATS=0) → l'ancien bois droit ET les anciens lecteurs droits, intacts.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		/// <summary>Bois en tube lissé (sinon : l'ancien bois, segment par segment).</summary>
		private static bool TubeActif => SplatsActifs;

		// Demi-largeur interne (px) au-dessus de laquelle le départ d'une branche reçoit un bout rond.
		private const float CapMinPx = 1.5f;

		/// <summary>LE point du bois : segment `s`, `t` ∈ [0,1] de sa base à son bout. Sur la courbe
		/// quand le tube est actif, sur le segment droit sinon (ce qui est dessiné, dans les deux cas).</summary>
		private Vector3 PointDuBois(in Segment s, float t) =>
			TubeActif && _structure != null ? BoisAxes.De(_structure).PointDe(s, t)
			: s.Base + s.Dir * (s.LengthCm * t);

		// Le morceau du segment `i` à l'écran (repère local, origine = collet). `zf` écrase la hauteur
		// (squelette « couché » historique, facteur aujourd'hui neutre).
		private Vector2[] ProjeterMorceau(BoisAxes.Morceau m, Vector3 collet, float zf = 1f)
		{
			var pts = new Vector2[m.Points.Length];
			for (int k = 0; k < pts.Length; k++)
			{
				Vector3 p = m.Points[k];
				pts[k] = Iso(p.X - collet.X, p.Y - collet.Y, p.Z * zf);
			}
			return pts;
		}

		// Largeur du bois en px (repère local) pour une épaisseur en cm : CONTINUE (plus d'arrondi au
		// pixel par segment, cause des marches) ; mêmes planchers que l'ancien bois.
		private float LargeurBoisPx(float cm, bool houppier)
		{
			float w = cm * WorldView.PxPerCmX * WoodWidthFactor;
			return houppier ? Mathf.Max(BoisArbreMinPx / WorldView.CurrentZoom, w) : Mathf.Max(1f, w);
		}

		private float[] DemiLargeurs(BoisAxes.Morceau m, bool houppier, out float moy)
		{
			var demi = new float[m.LargeurCm.Length];
			moy = 0f;
			for (int k = 0; k < demi.Length; k++)
			{
				demi[k] = LargeurBoisPx(m.LargeurCm[k], houppier) * 0.5f;
				moy += demi[k] * 2f / demi.Length;
			}
			return demi;
		}

		// Ordre de pose : du fond vers l'avant (profondeur iso du milieu du morceau), à égalité le
		// plus bas d'abord puis l'index — ordre total, déterministe.
		private List<BoisAxes.Morceau> MorceauxParProfondeur(BoisAxes axes, Vector3 c)
		{
			var liste = new List<(float Prof, int I)>(axes.Morceaux.Length);
			foreach (var m in axes.Morceaux)
			{
				Vector3 p = m.Points[m.Points.Length / 2];
				liste.Add((WorldView.WorldToScreenOffset(p.X - c.X, p.Y - c.Y).Y + p.Z * 1e-3f, m.Index));
			}
			liste.Sort(static (a, b) => a.Prof != b.Prof ? a.Prof.CompareTo(b.Prof) : a.I.CompareTo(b.I));
			var ordre = new List<BoisAxes.Morceau>(liste.Count);
			foreach (var (_, i) in liste) ordre.Add(axes.Morceaux[i]);
			return ordre;
		}

		/// <summary>Le bois vivant en tube (remplace la boucle de segments de DrawSegments). Un tronc
		/// posé au sol reçoit d'abord sa section au sol (ellipse iso) : le pied s'arrondit au lieu de
		/// finir sur un bord horizontal.</summary>
		private void DrawTube(Vector3 collet, bool houppier)
		{
			var axes = BoisAxes.De(_structure);
			foreach (var m in MorceauxParProfondeur(axes, collet))
			{
				var s = _structure.Segments[m.Index];
				Vector2[] pts = ProjeterMorceau(m, collet);
				float[] demi = DemiLargeurs(m, houppier, out float w);
				Vector2[] nrm = RubanTexture.Normales(pts);
				// Même couleur que l'ancien bois : rampe de lignification, écorce de la fiche, symptômes.
				float lig = LigVue(s, houppier);
				Color baseCol = AvecEcorce(WoodRamp(lig), s);
				Color col = baseCol.Lerp(SymptomTint(baseCol), 1f - lig);
				if (m.RangAxe == 0 && s.Parent < 0 && m.Points[0].Z <= 1f)
					DrawColoredPolygon(EllipsePoints(pts[0], demi[0], demi[0] * 0.5f, 16), Ton(col, PaletteIndexee.TonBase));
				// ⑥ : départ d'une branche ARRONDI. Le col naît dans le porteur ; une branche posée
				// DEVANT lui montrait son bout carré par-dessus (vu au noisetier ×16-×32). Le rond est
				// au ton d'OMBRE : au ton de base il se lisait comme une bûche sciée (capture ⑥).
				else if (m.RangAxe == 0 && s.Parent >= 0 && demi[0] * WorldView.CurrentZoom >= CapMinPx)
					DrawColoredPolygon(EllipsePoints(pts[0], demi[0], demi[0], 12), Ton(col, PaletteIndexee.TonBase - 1));
				PeindreEcorceTube(m, pts, demi, nrm, col, w, lig, CleSegment(s));
				if (houppier) DrawBoutTendre(s, collet);
				DrawNeigeTube(pts, demi, w, s, m.Index);
			}
		}

		/// <summary>Squelette (bois mort uniforme) en tube : même courbe, une seule bande.</summary>
		private void DrawSqueletteTube(Vector3 collet, float zf)
		{
			var axes = BoisAxes.De(_structure);
			Color mort = Lit(DeadWoodColor);
			foreach (var m in MorceauxParProfondeur(axes, collet))
			{
				Vector2[] pts = ProjeterMorceau(m, collet, zf);
				float[] demi = DemiLargeurs(m, false, out _);
				RubanTexture.PoserBande(pts, demi, RubanTexture.Normales(pts), m.V, -1f, 1f, _ => mort);
				RubanTexture.Envoyer(this);
			}
		}

		// Tons de l'ancien DrawEcorce, le long de la courbe : âme plate, flancs orientés selon la
		// normale LOCALE (le côté soleil s'éclaire tout au long du coude), stries au hash. Les 8
		// tons orientés sont calculés une fois par morceau (pas un Ton par quad).
		private readonly Color[] _tonsFlanc = new Color[8];

		private void PeindreEcorceTube(BoisAxes.Morceau m, Vector2[] pts, float[] demi, Vector2[] nrm, Color col, float w,
			float lig, int graine)
		{
			float[] v = m.V;
			float z = WorldView.CurrentZoom, wi = w * z;
			Color ame = Ton(col, PaletteIndexee.TonBase);
			RubanTexture.PoserBande(pts, demi, nrm, v, -1f, 1f, _ => ame);
			if (wi >= 3f)
			{
				for (int o = 0; o < 8; o++) _tonsFlanc[o] = Ton(col, PaletteIndexee.TonBase, o);
				RubanTexture.PoserBande(pts, demi, nrm, v, 1f / 3f, 1f, p => _tonsFlanc[Orientation(p)]);
				RubanTexture.PoserBande(pts, demi, nrm, v, -1f, -1f / 3f, p => _tonsFlanc[Orientation(-p)]);
			}
			RubanTexture.Envoyer(this);   // âme + flancs en un appel, avant l'écorce
			// ② : l'écorce cuite de l'essence par-dessus ; à défaut (bois fin, tige tendre), les stries.
			if (!PeindreEcorceCuite(m, pts, demi, nrm, col, wi, lig) && wi >= StrieMinPx)
				StriesTube(pts, demi, nrm, col, wi, graine);
		}

		// Stries : traits fins le long du tube, à u fixe, par tronçons au hash (même tirage que
		// l'ancien bois, graine = clé stable du segment : une coupe ailleurs ne les déplace pas).
		// Un tronçon couvre une plage de longueur d'arc ; il se trace pas à pas (DrawLine par pas
		// d'échantillonnage couvert), sans liste intermédiaire.
		private void StriesTube(Vector2[] pts, float[] demi, Vector2[] nrm, Color col, float wi, int g)
		{
			int nb = Mathf.Min(StriesMax, (int)(wi / 3f));
			var cumul = new float[pts.Length];
			for (int k = 1; k < pts.Length; k++) cumul[k] = cumul[k - 1] + pts[k].DistanceTo(pts[k - 1]);
			float len = cumul[^1];
			if (len < 1e-4f) return;
			int runs = Mathf.Clamp((int)(len * WorldView.CurrentZoom / 4f), 1, StrieRunsMax);
			float pix = PixelInterne;
			for (int s = 0; s < nb; s++)
			{
				float u = ((s + 0.5f) / nb - 0.5f) * 1.7f;   // = l'ancien décalage 0,85 × w, en demi-largeurs
				for (int r = 0; r < runs; r++)
				{
					if (Hash01(141, g + s, r) >= 0.55f) continue;
					float a = len * (r + 0.2f * Hash01(143, g + s, r)) / runs;
					float b = len * Mathf.Min(1f, (r + 0.6f + 0.4f * Hash01(147, g + s, r)) / runs);
					int ton = Hash01(149, g + s, r) < 0.6f ? 1 : 3;
					for (int k = 0; k + 1 < pts.Length; k++)
					{
						float c0 = cumul[k], c1 = cumul[k + 1];
						if (c1 <= a || c0 >= b || c1 - c0 < 1e-6f) continue;
						Vector2 p0 = pts[k] + nrm[k] * (demi[k] * u), p1 = pts[k + 1] + nrm[k + 1] * (demi[k + 1] * u);
						Vector2 perp = RubanTexture.Perp(pts[k + 1] - pts[k]);
						int o = u > 0.3f ? Orientation(perp) : u < -0.3f ? Orientation(-perp) : PaletteIndexee.OrientPlat;
						DrawLine(p0.Lerp(p1, Mathf.Max(0f, (a - c0) / (c1 - c0))), p0.Lerp(p1, Mathf.Min(1f, (b - c0) / (c1 - c0))),
							Ton(col, ton, o), pix, antialiased: false);
					}
				}
			}
		}

		// Neige posée sur le dessus du tube (règle de DrawSnowOnBranch : plus probable sur le bois
		// peu incliné), le long de la courbe.
		private void DrawNeigeTube(Vector2[] pts, float[] demi, float w, in Segment s, int k)
		{
			if (_snow <= 0f) return;
			float horiz = new Vector2(s.Dir.X, s.Dir.Y).Length();
			if (Hash01(53, k, 0) >= _snow * (0.25f + 0.75f * horiz)) return;
			float sw = Px(Mathf.Max(w * 0.5f, 0.5f));
			var dessus = new Vector2[pts.Length];
			for (int j = 0; j < pts.Length; j++) dessus[j] = pts[j] - new Vector2(0f, demi[j] + sw * 0.5f);
			DrawPolyline(dessus, Lit(SnowColor), sw, antialiased: false);
		}

		/// <summary>Distance (px, repère local) du point `local` au bois DESSINÉ du segment `i`
		/// (sa courbe projetée) — clic, sécateur, priorité plante > maison.</summary>
		private float DistanceAuBois(int i, Vector2 local, Vector3 collet)
		{
			if (!TubeActif)
			{
				var s = _structure.Segments[i];
				Vector3 tip = s.Base + s.Dir * s.LengthCm;
				return local.DistanceTo(Geometry2D.GetClosestPointToSegment(local,
					Iso(s.Base.X - collet.X, s.Base.Y - collet.Y, s.Base.Z), Iso(tip.X - collet.X, tip.Y - collet.Y, tip.Z)));
			}
			Vector2[] pts = ProjeterMorceau(BoisAxes.De(_structure).Morceaux[i], collet);
			float d = float.MaxValue;
			for (int k = 0; k + 1 < pts.Length; k++)
				d = Mathf.Min(d, local.DistanceTo(Geometry2D.GetClosestPointToSegment(local, pts[k], pts[k + 1])));
			return pts.Length == 1 ? local.DistanceTo(pts[0]) : d;
		}

		/// <summary>Surbrillance du segment `i` le long de sa courbe (tube actif).</summary>
		private void DrawHighlightTube(int i, Vector3 collet, float w)
		{
			Vector2[] pts = ProjeterMorceau(BoisAxes.De(_structure).Morceaux[i], collet);
			if (pts.Length >= 2) DrawPolyline(pts, HighlightColor, w, antialiased: false);
		}
	}
}
