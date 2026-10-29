// SYMBIOSE — PlantRenderer.Froid.cs (partial, sprint JARDIN VIVANT T5 — froid)
// Côté PLANTE des épisodes froids et violents : neige, givre, grêle. Comme la
// canicule et la pluie (PlantRenderer.Meteo.cs), c'est une VARIANTE DE DESSIN
// cuite dans l'image (PlantBaker, × ses poses de flexion T3).
//
//  · NEIGE (pendant « Neige », état global MeteoPlantes) : une calotte blanche
//    sur le dessus des feuilles, des branches peu inclinées et de la couronne
//    au LOD, ∝ la charge. Plus chargée en haut de la plante (la neige se pose
//    sur la canopée). La charge RAIDIT la plante (flexion du vent réduite,
//    SnowStiffness) ; sous un vent qui forcit elle tombe PAR PLAQUES : chaque
//    feuille/branche porte un seuil au hash → quand la charge baisse, ce sont
//    toujours les mêmes plaques qui tombent, à des instants propres à la plante.
//  · GIVRE (pendant « Gelée tardive ») : limbe désaturé bleuté + liseré clair
//    sur une part des feuilles, puis il se dissipe (MeteoPlantes, ThawSec).
//  · GRÊLE : feuilles DÉCHIQUETÉES (encoches au bord) ∝ le symptôme `grele`,
//    en plus du criblage existant (DrawLeafDamage). C'est une TRACE : elle reste
//    tant que le snapshot porte la marque (plant.symptom_marks côté moteur) —
//    la vue n'invente aucune durée. Idem pour les bords noircis du `gel`.
//  · ABRI : une plante sous voile/cloche (`couvert_pose` du snapshot, marqué
//    par WorldView.Ciel.cs) ne porte ni neige ni givre ; pour la grêle et le gel
//    c'est le MOTEUR qui l'épargne déjà (pas de symptôme → pas de trace).
//
// 📖 Pédagogie : un état par plante (_snow, _frost, _covered). Il ne change qu'au
// passage d'un palier → la plante devient « sale » et la file la recuit ; aucune
// déformation n'est recalculée par frame (animation = signal d'état).

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer : Node2D
	{
		// Raideur sous charge : flexion × (1 − SnowStiffen × neige).
		private const float SnowStiffen = 0.6f;
		// Givre : part de teinte bleutée du limbe à givre 1.
		private const float FrostTintMax = 0.45f;
		private static readonly Color SnowColor = Palette16.MaitreBlanc;
		private static readonly Color SnowShade = new Color("a8cfe6");   // ombre bleutée de la neige
		private static readonly Color FrostTint = new Color("a8c4d0");   // limbe givré (désaturé froid)
		private static readonly Color FrostEdge = Palette16.MaitreBlanc; // liseré de givre

		private float _snow;     // charge de neige (palier propre de la plante)
		private float _frost;    // givre ∈ {0, 1/3, 2/3, 1}
		private bool _covered;   // sous voile/cloche posé (snapshot `couvert_pose`)

		/// <summary>Facteur de flexion sous la neige (1 = libre).</summary>
		internal float SnowStiffness => 1f - SnowStiffen * _snow;

		/// <summary>Plante abritée par une couverture posée (voile/cloche) ?</summary>
		public void SetCovered(bool covered)
		{
			if (covered == _covered) return;
			_covered = covered;
			RefreshMeteo();
		}

		/// <summary>Variante froide de la plante ; vrai si elle a changé
		/// (l'appelant, RefreshMeteo, salit alors la plante).</summary>
		private bool RefreshCold(bool vivante)
		{
			bool exposee = vivante && !_covered;
			float snow = exposee ? MeteoPlantes.SnowLevelFor(_swayPhase) : 0f;
			float frost = exposee && _structure.FoliageDensity > 0f ? MeteoPlantes.Frost : 0f;
			if (snow == _snow && frost == _frost) return false;
			_snow = snow;
			_frost = frost;
			return true;
		}

		/// <summary>Tissu vert givré : tiré vers le bleu pâle ∝ givre.</summary>
		private Color Frosted(Color c) =>
			_frost > 0f ? c.Lerp(FrostTint, FrostTintMax * _frost) : c;

		// Épaisseur d'1 pixel de la grille pixel-art (canvas × zoom), en canvas.
		private static float Px(float canvas)
		{
			float z = WorldView.CurrentZoom;
			return Mathf.Max(1f, Mathf.Round(canvas * z)) / z;
		}

		/// <summary>Marques froides d'une feuille de centre `c`, rayon `r`, à la
		/// hauteur `z` : encoches de grêle (trace), liseré de givre, calotte de neige.</summary>
		private void DrawColdLeaf(Vector2 c, float r, int i, int j, float z)
		{
			float rx = r * 1.15f, ry = r * 0.65f * LeafOpen;
			// Encoches de grêle et liseré de givre = SYMPTÔMES FINS (×16, D106 T6) ;
			// la teinte givrée (Frosted) et la neige se lisent dès ×4.
			bool fin = AuPalier(PalierSymptomesZoom);
			// Grêle : 1 à 3 encoches triangulaires mordant le bord du limbe.
			if (fin && _grele > 0f)
			{
				int notches = Mathf.CeilToInt(_grele * 3f);
				for (int k = 0; k < notches; k++)
				{
					float a = Hash01(61 + k, i, j) * Mathf.Tau;
					var pts = new Vector2[3];
					for (int e = 0; e < 2; e++)
					{
						float ae = a + (e == 0 ? -0.35f : 0.35f);
						pts[e] = c + new Vector2(Mathf.Cos(ae) * rx * 1.05f, Mathf.Sin(ae) * ry * 1.05f);
					}
					float depth = 0.45f + 0.25f * Hash01(67 + k, i, j);
					pts[2] = c + new Vector2(Mathf.Cos(a) * rx, Mathf.Sin(a) * ry) * (1f - depth);
					DrawColoredPolygon(pts, Trou(LeafHoleColor));
				}
			}
			// Givre : liseré clair sur une part des feuilles (les mêmes, au hash).
			if (fin && _frost > 0f && Hash01(59, i, j) < 0.4f + 0.6f * _frost)
				DrawEllipseOutline(c, rx, ry, Lit(FrostEdge), Px(r * 0.08f));
			// Neige : calotte sur le dessus, plus probable en haut de la plante.
			float top = Mathf.Clamp(z / Mathf.Max(_heightCm, 1f), 0f, 1f);
			if (_snow > 0f && Hash01(47, i, j) < _snow * (0.55f + 0.45f * top))
			{
				Vector2 cap = c - new Vector2(0f, ry * 0.55f);
				DrawEllipse(cap, rx * 0.95f, ry * 0.55f, Lit(SnowShade));
				DrawEllipse(cap - new Vector2(0f, ry * 0.12f), rx * 0.8f, ry * 0.4f, Lit(SnowColor));
			}
		}

		/// <summary>Neige posée sur une branche (segment k du tri tronc-dessous) :
		/// un trait blanc sur le dessus, plutôt sur les branches peu inclinées.</summary>
		private void DrawSnowOnBranch(Vector2 p1, Vector2 p2, float w, Segment s, int k)
		{
			if (_snow <= 0f) return;
			float horiz = new Vector2(s.Dir.X, s.Dir.Y).Length();   // 0 = vertical, 1 = à plat
			if (Hash01(53, k, 0) >= _snow * (0.25f + 0.75f * horiz)) return;
			float sw = Px(Mathf.Max(w * 0.5f, 0.5f));
			Vector2 up = new Vector2(0f, -(w + sw) * 0.5f);
			DrawLine(p1 + up, p2 + up, Lit(SnowColor), sw, antialiased: false);
		}

		/// <summary>Calotte de neige sur la couronne des paliers bas (×0,5-×2, D106 T5) :
		/// `center`/`rx`/`ry` = la couronne dessinée (PlantRenderer.Paliers.cs).</summary>
		private void DrawSnowCrown(Vector2 center, float rx, float ry)
		{
			if (_snow <= 0f) return;
			Vector2 cap = center - new Vector2(0f, ry * 0.5f);
			// Lit() : code de palette quand le pinceau cuit indexé (③), sinon littéral.
			DrawEllipse(cap, rx * (0.5f + 0.4f * _snow), ry * 0.45f, Lit(SnowShade));
			DrawEllipse(cap - new Vector2(0f, ry * 0.08f), rx * (0.4f + 0.35f * _snow), ry * 0.32f, Lit(SnowColor));
		}
	}
}
