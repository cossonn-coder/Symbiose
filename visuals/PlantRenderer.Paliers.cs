// SYMBIOSE — PlantRenderer.Paliers.cs (partial, sprint RENDU VISIBLE D106 T5)
// Les PALIERS BAS du dessin d'une plante : ×0,5 · ×1 · ×2. Chaque palier porte
// SON information, et l'échelle est CUMULATIVE (un palier garde ce que montrent
// les plus éloignés et ajoute UNE catégorie) — conception_rendu_visible.md §4 D4 :
//   ×0,5 PRÉSENCE + SAISON : une tache (couronne) teintée par l'espèce, rougie à
//        l'automne (`automne`), réduite au bois nu en hiver pour un caduc ;
//        mort = gris bois.
//   ×1   + PORT : la silhouette du port (arbre, buisson, touffe, dressée,
//        rosette, tapis, couchée, grimpante) à sa hauteur RELATIVE juste.
//   ×2   + SANTÉ : teinte de vigueur (vitalité + symptôme colorant dominant :
//        franc / pâle-chlorose / fané / sénescent) ; floraison en taches.
// À partir de ×4 (PaliersHautsMinZoom) on garde le dessin détaillé existant
// (segments + organes) — les paliers hauts sont le tronçon T6.
//
// Et le TAPIS PAR PLOT (D5) : une plante trop petite pour être lisible au palier
// courant (emprise projetée < TapisSeuilPx px INTERNES) n'est ni cuite ni
// dessinée individuellement : elle contribue au tapis de son plot
// (visuals/CouvertureLayer.cs, agrégé par world/WorldView.Tapis.cs).
//
// 📖 Pédagogie : rien de tout ça ne coûte à l'AFFICHAGE — la plante reste un quad
// texturé (pré-cuisson, jardin vivant T2). Le palier change ce qu'on CUIT (une
// fois, à la file), pas ce qu'on rejoue chaque frame. La vue ne recalcule aucune
// écologie : elle lit `automne`, `foliage_density`, `vitalite`, `leaf_symptoms`,
// `floraison`, `strate`, `silhouette` et la géométrie des segments (philo #5).

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer : Node2D
	{
		/// <summary>Zoom à partir duquel on dessine le détail (segments + organes) :
		/// les paliers hauts (T6). En dessous, DrawPalierBas.</summary>
		internal const float PaliersHautsMinZoom = 4f;
		// Seuils des paliers bas (CUMULATIFS) : port dès ×1, santé dès ×2.
		private const float PalierPortZoom = 1f;
		private const float PalierSanteZoom = 2f;

		/// <summary>Seuil de lisibilité du tapis (D5), en px INTERNES du SubViewport
		/// (= px canvas × zoom) : une plante dont l'emprise projetée (max de sa
		/// largeur et de sa hauteur) est plus petite part dans le tapis de son plot.
		/// Point de départ du kickoff (~3 px), réglable au F5.</summary>
		internal const float TapisSeuilPx = 3f;

		// Arbre = strate haute ET vrai bois (une partie de la plante plus épaisse que
		// le rameau feuillu, LeafMaxThickCm). Le tournesol (haute, tige ~herbacée) reste
		// « dressée » ; le jeune arbre sans tronc aussi, jusqu'à ce que son fût épaississe.
		private const string StrateHaute = "haute";
		private const string StrateGrimpante = "grimpante";
		// Taches de fleurs (×2) : une tache par ~TacheFleurPx2 px² de couronne, bornée.
		private const float TacheFleurPx2 = 40f;
		private const int TachesFleurMax = 12;
		// Feuillage partiel (débourrement, chute) : part de bois qui transparaît.
		private const float BoisTransparait = 0.6f;

		// Strate du stade courant (snapshot `strate`) : distingue arbre / grimpante.
		private string _strate;
		// Géométrie RÉELLE (sans les planchers de l'ombre) : rayon horizontal,
		// hauteur et épaisseur max DES SEGMENTS — recalculés à SetStructure
		// (MesurerPort). Pas `height_cm` : le moteur la donne parfois bien plus
		// haute que le bois dessiné (basilic : 22 cm pour un segment de ~5 cm) ;
		// la plante doit garder la même taille d'un palier à l'autre (×4 dessine
		// les segments), sinon elle « rétrécit » en zoomant.
		private float _rayonReelCm, _hauteurReelCm, _epaisseurMaxCm;
		// Décidé à chaque Invalidate (croissance, palier) : la plante est dans le tapis.
		private bool _enTapis;

		/// <summary>Plante rendue par le tapis de son plot (D5) — ni cuite ni dessinée.</summary>
		internal bool EnTapis => _enTapis;

		public void SetStrate(string strate)
		{
			if (_strate == strate) return;   // early-out : pas de recuisson inutile
			_strate = strate;
			Invalidate();
		}

		// Appelé par SetStructure : la vraie taille, que l'ombre plancher masquerait.
		private void MesurerPort()
		{
			_rayonReelCm = _hauteurReelCm = _epaisseurMaxCm = 0f;
			if (_structure == null) return;
			Vector3 c = _structure.ColletCm;
			foreach (var s in _structure.Segments)
			{
				Vector3 tip = s.Base + s.Dir * s.LengthCm;
				_rayonReelCm = Mathf.Max(_rayonReelCm, new Vector2(tip.X - c.X, tip.Y - c.Y).Length());
				_hauteurReelCm = Mathf.Max(_hauteurReelCm, tip.Z - c.Z);
				_epaisseurMaxCm = Mathf.Max(_epaisseurMaxCm, s.ThicknessCm);
			}
		}

		/// <summary>Emprise projetée en px INTERNES au zoom courant (largeur ou
		/// hauteur, la plus grande) — le critère du tapis.</summary>
		private float EmpriseInternePx() =>
			Mathf.Max(2f * _rayonReelCm * WorldView.PxPerCmX, _hauteurReelCm * WorldView.PxPerCmZ)
			* WorldView.CurrentZoom;

		// Réévalué à chaque Invalidate (Bake.cs) : SetStructure et la pompe de palier
		// (RedrawAllPlants) passent toutes deux par là.
		private void DeciderTapis() =>
			_enTapis = Bakeable && _structure != null && EmpriseInternePx() < TapisSeuilPx;

		/// <summary>Aire couverte au sol (cm²) — poids de la plante dans son tapis.</summary>
		internal float AireTapisCm2 => Mathf.Pi * Mathf.Max(_rayonReelCm, 1f) * Mathf.Max(_rayonReelCm, 1f);

		/// <summary>Teinte de la plante dans le tapis : le langage du palier ×0,5
		/// (espèce + saison, gris bois si morte).</summary>
		internal Color TeinteTapis => TeinteSaison();

		// ---------------------------------------------------------------------------
		// COULEUR — espèce + saison (×0,5), puis santé par-dessus (×2)
		// ---------------------------------------------------------------------------

		// Teinte d'ESPÈCE (limbe de sa palette, Organs.cs) tirée vers l'automne ∝
		// `automne` (une teinte chaude stable par pied, hash de position) et vers le
		// bois quand le feuillage s'éclaircit. NB : la vue ne connaît pas la FAMILLE
		// botanique (absente du snapshot) — la palette par espèce en tient lieu.
		private Color TeinteSaison()
		{
			if (!string.IsNullOrEmpty(_deadStade)) return DeadWoodColor;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			Color c = pal.Leaf;
			float automne = Mathf.Clamp(_structure.Automne, 0f, 1f);
			if (automne > 0f)
				c = c.Lerp(AutumnLeaves[(int)(_swayPhase * AutumnLeaves.Length) % AutumnLeaves.Length], automne);
			float dens = Mathf.Clamp(_structure.FoliageDensity, 0f, 1f);
			return c.Lerp(WoodColor, (1f - dens) * BoisTransparait);
		}

		// ---------------------------------------------------------------------------
		// GÉOMÉTRIE — la couronne (tache ×0,5 ou port ×1+), en px canvas locaux
		// ---------------------------------------------------------------------------

		// Port lu des descripteurs moteur : strate (arbre/grimpante) + silhouette
		// d'espèce (tapis/rosette/étalée/dressée/buisson/touffe). Mort couché → couchée.
		private string Port()
		{
			if (_deadStade == "couchee") return "couchee";
			if (_strate == StrateGrimpante) return "grimpante";
			if (_strate == StrateHaute && _epaisseurMaxCm > LeafMaxThickCm) return "arbre";
			return _silhouette switch
			{
				"tapis" => "tapis",
				"rosette" => "rosette",
				"étalée" => "couchee",
				"dressée" => "dressee",
				"buisson" => "buisson",
				_ => "touffe",
			};
		}

		/// <summary>Couronne au palier courant : (centre, demi-axes) en px canvas
		/// locaux. Tache générique sous ×1, forme du port au-delà. Sert aussi le
		/// picking (ContientCurseur) et la boîte de cuisson.</summary>
		private (Vector2 c, float rx, float ry) Couronne()
		{
			float h = _hauteurReelCm, r = Mathf.Max(_rayonReelCm, h * 0.2f);
			float px = WorldView.PxPerCmX, pz = WorldView.PxPerCmZ;
			float min = 1f / WorldView.CurrentZoom;   // ≥ 1 px interne de demi-axe
			(float zc, float rx, float ry) = WorldView.CurrentZoom < PalierPortZoom
				? (h * 0.5f, r * px, h * 0.5f * pz)                       // tache
				: Port() switch
				{
					"arbre"     => (h * 0.66f, r * px, h * 0.34f * pz),
					"buisson"   => (h * 0.5f, r * px, h * 0.5f * pz),
					"dressee"   => (h * 0.55f, r * 0.5f * px, h * 0.45f * pz),
					"grimpante" => (h * 0.5f, r * 0.35f * px, h * 0.5f * pz),
					"rosette"   => (h * 0.3f, r * px, 0f),
					"tapis"     => (h * 0.15f, r * 1.1f * px, 0f),
					"couchee"   => (h * 0.3f, r * 1.1f * px, h * 0.4f * pz),
					_           => (h * 0.5f, r * 0.9f * px, h * 0.5f * pz),   // touffe
				};
			rx = Mathf.Max(rx, min);
			ry = Mathf.Max(ry, Mathf.Max(rx * 0.45f, min));   // un disque au sol reste lisible en iso
			return (Iso(0f, 0f, zc), rx, ry);
		}

		// ---------------------------------------------------------------------------
		// DESSIN — appelé par DrawVector sous PaliersHautsMinZoom
		// ---------------------------------------------------------------------------

		private void DrawPalierBas()
		{
			// Bois nu : squelette mort, ou caduc défeuillé (l'hiver se lit au bois).
			bool mort = !string.IsNullOrEmpty(_deadStade);
			if (mort || _structure.FoliageDensity <= 0f)
			{
				DrawBoisNu(mort ? DeadWoodColor : WoodColor, _deadStade == "couchee" ? CoucheeFlatten : 1f);
				return;
			}
			bool port = WorldView.CurrentZoom >= PalierPortZoom;
			bool sante = WorldView.CurrentZoom >= PalierSanteZoom;
			Color c = TeinteSaison();
			if (sante) c = SymptomTint(c);   // ×2 : vitalité + symptôme dominant
			c = Frosted(c);                  // givre (météo T5) : lisible à tout palier
			var (centre, rx, ry) = Couronne();
			if (port) DrawTige(centre);
			DrawCouronne(centre, rx, ry, c);
			if (sante) DrawTachesFleurs(centre, rx, ry);
			DrawSnowCrown(centre, rx, ry);   // calotte de neige (météo T5)
		}

		// Couronne en volume 2 valeurs (même recette que DrawVolumeEllipse : base
		// ombrée + calotte éclairée décalée sud), mais LISSE : le nombre de sommets
		// suit la taille à l'écran (une couronne d'arbre à ×1 fait ~100 px — à 10
		// sommets elle devenait un octogone).
		private void DrawCouronne(Vector2 centre, float rx, float ry, Color col)
		{
			int n = Mathf.Clamp(Mathf.RoundToInt(rx * WorldView.CurrentZoom * 0.5f), 10, 48);
			DrawColoredPolygon(EllipsePoints(centre, rx, ry, n), HueShift(col, -OrganShade));
			DrawColoredPolygon(EllipsePoints(centre + SouthDir() * (ry * 0.5f),
				rx * LitFactorDefault, ry * LitFactorDefault, n), HueShift(col, OrganLit));
		}

		// Ce qui relie la couronne au sol au palier PORT : le fût d'un arbre, la tige
		// d'une dressée/grimpante. Largeur ∝ épaisseur réelle, ≥ 1 px interne.
		private void DrawTige(Vector2 centre)
		{
			string port = Port();
			if (port != "arbre" && port != "dressee" && port != "grimpante") return;
			float w = Mathf.Max(1f / WorldView.CurrentZoom,
				Mathf.Round(_epaisseurMaxCm * WorldView.PxPerCmX * WoodWidthFactor));
			DrawLine(Vector2.Zero, centre, port == "arbre" ? WoodColor : ApexColor, w, antialiased: false);
		}

		// Floraison (×2) : des taches de couleur de fleur dans la moitié haute de la
		// couronne, nombre ∝ floraison × taille ; positions au hash (zéro Random).
		private void DrawTachesFleurs(Vector2 centre, float rx, float ry)
		{
			if (_structure.Floraison < FloraisonSeuil) return;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			int n = Mathf.Clamp(Mathf.RoundToInt(rx * ry * WorldView.CurrentZoom * WorldView.CurrentZoom
				/ TacheFleurPx2 * _structure.Floraison), 1, TachesFleurMax);
			float rad = 1f / WorldView.CurrentZoom;   // 1 px interne de rayon
			for (int k = 0; k < n; k++)
			{
				float a = Mathf.Pi + Mathf.Pi * Hash01(83, k, 0);       // moitié haute
				float d = Mathf.Sqrt(Hash01(89, k, 0)) * 0.8f;
				DrawCircle(centre + new Vector2(rx * d * Mathf.Cos(a), ry * d * Mathf.Sin(a)),
						   rad, pal.Flower);
			}
		}

		// Bois nu : les vrais segments (même projection que DrawSegments), largeur
		// ≥ 1 px interne pour qu'un squelette ou un caduc d'hiver reste visible au
		// dézoom. `zf` aplatit un squelette couché.
		private void DrawBoisNu(Color col, float zf)
		{
			Vector3 c = _structure.ColletCm;
			float min = 1f / WorldView.CurrentZoom;
			foreach (var s in _structure.Segments)
			{
				Vector3 tip = s.Base + s.Dir * s.LengthCm;
				float w = Mathf.Max(min, Mathf.Round(s.ThicknessCm * WorldView.PxPerCmX * WoodWidthFactor));
				DrawLine(Iso(s.Base.X - c.X, s.Base.Y - c.Y, s.Base.Z * zf),
						 Iso(tip.X - c.X, tip.Y - c.Y, tip.Z * zf), col, w, antialiased: false);
			}
		}

		/// <summary>Boîte de cuisson aux paliers bas : la couronne (calotte éclairée
		/// et taches comprises) en plus des segments.</summary>
		private Rect2 EtendrePalierBas(Rect2 r)
		{
			var (c, rx, ry) = Couronne();
			// ×1,2 : la calotte éclairée déborde de ~0,16 ry vers le sud (DrawCouronne).
			var demi = new Vector2(rx, ry) * 1.2f;
			return r.Expand(c - demi).Expand(c + demi);
		}
	}
}
