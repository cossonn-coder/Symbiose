// SYMBIOSE — FieldOverlay.cs
// Heatmap des champs écologiques (tranche 6·C — le « mode debug champs
// écologiques » de la conception, étiqueté debug, philo #5 : autorisé hors
// HUD primaire). Touche F6 dans WorldView ; ce nœud ne fait que DESSINER la
// dernière grille reçue du serveur (commande `fields`) — zéro requête ici,
// la machine maître/esclave vit dans WorldView.
//
// 📖 Pédagogie — pourquoi des losanges en _Draw et pas une ImageTexture
// (le kickoff §9 laissait le choix) : une texture rows×cols en Nearest
// étirée sur la tuile ferait moins de primitives, MAIS il faudrait gérer
// Image/ImageTexture/Transform2D oblique (le losange iso est l'image affine
// du rectangle monde) et la re-projeter à chaque rotation D35. Le _Draw
// batch fait tout ça gratuitement : on re-projette par WorldToScreen au
// moment du dessin, et le redraw est RARE (1×/semaine quand la grille
// arrive, toggle, rotation) — 1 188 DrawColoredPolygon une fois par minute
// n'est pas un coût (BuildGround en pose autant en permanence). C'est le
// même patron qu'un seul CanvasItem que MacroLife — et l'inverse de son
// problème : lui redessine souvent peu de points, ici rarement tout le sol.

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class FieldOverlay : Node2D
	{
		// Semi-transparent : la heatmap se lit PAR-DESSUS le terrain sans
		// l'effacer (l'œil garde les plantes et la maison pour se repérer).
		private const float Alpha = 0.7f;

		// Palette PAR CHAMP (correctif t6·C2, demande Nico F5) : un dégradé
		// unique bleu→rouge mentirait — « chaud » n'a pas de sens pour de
		// l'humidité. Chaque champ porte SES deux pôles (couleur basse →
		// haute) et SES libellés, affichés en légende quand il est à l'écran.
		// Les espèces (⑥b) reprennent les teintes des points MacroLife/ForagerLayer
		// (un seul langage visuel : la heatmap d'une espèce double ses points).
		//
		// 📖 Échelle FIXE par champ (t6·C3, retour F5 « rendu binaire ») :
		// le min/max AUTO étalait le bruit d'un champ quasi uniforme sur
		// toute la palette (om_stable : span 0,001 → psychédélique). Quand le
		// champ a des bornes PHYSIQUES côté moteur, on les fige ici — la
		// couleur devient comparable d'une semaine à l'autre (une carte
		// météo, pas un contraste auto). Provenance des bornes :
		//   temperature −5..35 °C  : temp_norm = 11 ± 7 °C + dérive + gel/canicule ;
		//   humidite/fertilite/microbiome 0..3 : le moteur normalise par /3.0
		//     (effects.py, ecofields.py — min(1, x/3)) ;
		//   lumiere/disturbance/guildes 0..1 : _clamp01 et stability = 1 − d.
		// NaN = pas de bornes naturelles (om_*, soil_memory*) → repli min/max
		// AUTO de la grille, comme avant.
		private static readonly System.Collections.Generic.Dictionary<string,
			(Color Low, Color High, string LowLabel, string HighLabel,
			 float FixMin, float FixMax)> Palettes = new()
		{
			["temperature"]      = (new Color("3a6fd8"), new Color("d83a3a"), "froid", "chaud", -5f, 35f),
			["humidite"]         = (new Color("c8a96e"), new Color("2f6fd0"), "sec", "humide", 0f, 3f),
			["lumiere"]          = (new Color("2e2e38"), new Color("f5e36b"), "ombre", "plein soleil", 0f, 1f),
			["fertilite"]        = (new Color("d8cfa8"), new Color("2f8f4f"), "pauvre", "fertile", 0f, 3f),
			["microbiome"]       = (new Color("d8d2c0"), new Color("2f8f8f"), "inerte", "vivant", 0f, 3f),
			["om_fresh"]         = (new Color("e0d6a8"), new Color("8f7a3a"), "sol nu", "litière", float.NaN, float.NaN),
			["om_active"]        = (new Color("e0d6a8"), new Color("6f5a2a"), "peu", "en digestion", float.NaN, float.NaN),
			["om_stable"]        = (new Color("e0d6a8"), new Color("5a4630"), "peu", "humus", float.NaN, float.NaN),
			["soil_memory"]      = (new Color("c8c8c8"), new Color("4f4f9f"), "jeune", "ancien", float.NaN, float.NaN),
			["soil_memory_fast"] = (new Color("c8c8c8"), new Color("6f6fb8"), "jeune", "récent", float.NaN, float.NaN),
			["soil_memory_deep"] = (new Color("c8c8c8"), new Color("3a3a8f"), "jeune", "profond", float.NaN, float.NaN),
			["disturbance"]      = (new Color("d8d8d0"), new Color("a83a78"), "calme", "perturbé", 0f, 1f),
			// Heatmaps PAR ESPÈCE (catalogue enrichi ⑥b) : le registre `fields`
			// expose désormais une grille par espèce (eco.populations, 15 clés)
			// au lieu des 3 anciennes guildes. Pôle haut = la couleur du point
			// MacroLife/ForagerLayer de l'espèce (un seul langage visuel : la
			// heatmap double les points). Pôle bas = parchemin neutre « absent ».
			// Densités bornées 0..1 côté moteur → échelle FIXE comparable.
			// Ravageurs
			["puceron"]          = (new Color("e8e2d4"), new Color("6f8f3a"), "absent", "infesté", 0f, 1f),
			["limace"]           = (new Color("e8e2d4"), new Color("7a5a3a"), "absent", "présente", 0f, 1f),
			["doryphore"]        = (new Color("e8e2d4"), new Color("d8a83a"), "absent", "infesté", 0f, 1f),
			// Auxiliaires
			["coccinelle"]       = (new Color("e8e2d4"), new Color("c43a2e"), "absent", "présente", 0f, 1f),
			["chrysope"]         = (new Color("e8e2d4"), new Color("9fd86e"), "absent", "présente", 0f, 1f),
			["carabe"]           = (new Color("e8e2d4"), new Color("2e3a44"), "absent", "présent", 0f, 1f),
			["merle"]            = (new Color("e8e2d4"), new Color("1e1e22"), "absent", "présent", 0f, 1f),
			["herisson"]         = (new Color("e8e2d4"), new Color("8a6a4a"), "absent", "présent", 0f, 1f),
			// Détritivores
			["lombric"]          = (new Color("e8e2d4"), new Color("8a4a3a"), "absent", "fouisseur", 0f, 1f),
			["cloporte"]         = (new Color("e8e2d4"), new Color("8a8a8a"), "absent", "présent", 0f, 1f),
			// Pollinisateurs (butineurs ForagerLayer ; heatmap = densité d'ancrage)
			["abeille"]          = (new Color("e8e2d4"), new Color("e9c83c"), "absent", "butinant", 0f, 1f),
			["syrphe"]           = (new Color("e8e2d4"), new Color("d98f2e"), "absent", "butinant", 0f, 1f),
			["papillon"]         = (new Color("e8e2d4"), new Color("dcb4d2"), "absent", "butinant", 0f, 1f),
			["bourdon"]          = (new Color("e8e2d4"), new Color("d8a020"), "absent", "butinant", 0f, 1f),
			["osmie"]            = (new Color("e8e2d4"), new Color("b5651d"), "absent", "butinant", 0f, 1f),
		};
		// Champ inconnu de la table (futur champ moteur ramassé par
		// l'introspection) : bleu→rouge générique en échelle auto, jamais un
		// crash.
		private static readonly (Color, Color, string, string, float, float) DefaultPalette =
			(new Color("3a6fd8"), new Color("d83a3a"), "min", "max", float.NaN, float.NaN);

		/// <summary>Palette du champ (couleurs basse/haute + libellés +
		/// bornes fixes, NaN = auto) — lue par WorldView pour la légende.</summary>
		public static (Color Low, Color High, string LowLabel, string HighLabel,
					   float FixMin, float FixMax)
			PaletteOf(string field) =>
			field != null && Palettes.TryGetValue(field, out var p) ? p : DefaultPalette;

		/// <summary>Nom du champ affiché (HUD) ; null si aucune grille.</summary>
		public string FieldName { get; private set; }
		/// <summary>Bornes de la NORMALISATION (fixes si le champ en a,
		/// sinon min/max de la grille) — celles de la rampe de légende.</summary>
		public float Min { get; private set; }
		public float Max { get; private set; }
		/// <summary>Min/max RÉELS de la grille reçue (HUD : sur une échelle
		/// fixe, dit où la grille vit — « grille 14.1..14.1 » = uniforme).</summary>
		public float GridMin { get; private set; }
		public float GridMax { get; private set; }
		/// <summary>true si le champ affiché a des bornes physiques figées.</summary>
		public bool FixedScale { get; private set; }

		// Dernière réponse `fields` du serveur (grilles par tuile) + origins.
		private GDict _tiles;
		private System.Collections.Generic.Dictionary<string, Vector2> _origins;

		/// <summary>
		/// Nouvelle grille reçue : mémorise, choisit la normalisation
		/// (bornes FIXES du champ si la table en donne, sinon min/max AUTO
		/// de la grille — t6·C3), redessine. La projection se fait au
		/// _Draw : la rotation D35 n'a besoin que d'un QueueRedraw.
		/// </summary>
		public void SetGrid(string fieldName, GDict tiles,
							System.Collections.Generic.Dictionary<string, Vector2> origins)
		{
			FieldName = fieldName;
			_tiles = tiles;
			_origins = origins;
			float mn = float.MaxValue, mx = float.MinValue;
			foreach (var kv in tiles)
			{
				var vals = kv.Value.AsGodotDictionary()["values"].AsGodotArray();
				foreach (var v in vals)
				{
					float f = (float)v.AsDouble();
					if (f < mn) mn = f;
					if (f > mx) mx = f;
				}
			}
			GridMin = mn; GridMax = mx;
			var pal = PaletteOf(fieldName);
			FixedScale = !float.IsNaN(pal.FixMin);
			Min = FixedScale ? pal.FixMin : mn;
			Max = FixedScale ? pal.FixMax : mx;
			QueueRedraw();
		}

		public override void _Draw()
		{
			if (!Visible || _tiles == null) return;
			// Le losange d'un plot, en offsets écran constants (la projection
			// iso d'un carré de 50 cm — mêmes cotes que MakeLozenge du sol).
			Vector2 n = new(0f, -WorldView.TileHPx / 2f);
			Vector2 e = new(WorldView.TileWPx / 2f, 0f);
			Vector2 s = new(0f, WorldView.TileHPx / 2f);
			Vector2 o = new(-WorldView.TileWPx / 2f, 0f);
			float span = Max - Min;
			var (low, high, _, _, _, _) = PaletteOf(FieldName);
			foreach (var kv in _tiles)
			{
				if (!_origins.TryGetValue(kv.Key.AsString(), out Vector2 org))
					continue;
				var t = kv.Value.AsGodotDictionary();
				int rows = t["rows"].AsInt32(), cols = t["cols"].AsInt32();
				var vals = t["values"].AsGodotArray();
				for (int r = 0; r < rows; r++)
					for (int c = 0; c < cols; c++)
					{
						// row-major : l'index recompose (r, c) — l'ordre du
						// serveur (boucle rows puis cols), pas un 2e contrat.
						float v = (float)vals[r * cols + c].AsDouble();
						// Clamp : sur une échelle fixe, une valeur hors
						// bornes (canicule à 36 °C) sature au pôle au lieu
						// d'extrapoler la couleur.
						float tt = span > 1e-6f
							? Mathf.Clamp((v - Min) / span, 0f, 1f) : 0.5f;
						// Interpolation entre les 2 pôles du champ (la légende
						// du HUD montre exactement ces couleurs-là).
						Color col = low.Lerp(high, tt);
						col.A = Alpha;
						Vector2 ctr = WorldView.WorldToScreen(
							org.X + (c + 0.5f) * WorldView.PlotCm,
							org.Y + (r + 0.5f) * WorldView.PlotCm);
						DrawColoredPolygon(
							new[] { ctr + n, ctr + e, ctr + s, ctr + o }, col);
					}
			}
		}
	}
}
