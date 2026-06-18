// SYMBIOSE — SoilTempOverlay.cs (tronçon ⑩, vue pure)
// LA HEATMAP DE LA TEMPÉRATURE DU SOL, SPATIALISÉE (touche F7). Lit la grille
// `temperature[tile].t_sol` du snapshot (0.5.0) — la T de SURFACE plot par plot
// calculée au tronçon ⑤ (surchauffe solaire − évaporation − isolation litière −
// nébulosité, inertie lerp). LECTURE SEULE — golden NEUTRE : Godot ne fait que
// teinter le sol, aucune règle écologique ici.
//
// 📖 Pourquoi un overlay SÉPARÉ de FieldOverlay (F6) et pas un champ de plus :
// F6 est alimenté par la commande serveur `fields` (une seule grille « courante »
// venue d'une requête maître/esclave) et n'affiche, pour `temperature`, que la T
// de l'AIR hebdo UNIFORME. Le t_sol, lui, arrive DANS le snapshot à chaque
// semaine, sans requête — même source que SnowLayer/LitterLayer. Mélanger les
// deux dans FieldOverlay casserait son contrat. Les deux heatmaps coexistent et
// disent deux choses : F6 = air uniforme (introspection champs), F7 = sol
// spatialisé (coin chaud/sec vs frais/ombragé/humide).
//
// 📖 MÊME patron de dessin que FieldOverlay : un Node2D qui REPROJETTE tous les
// losanges au _Draw via WorldToScreen → la rotation de vue (D35) est gratuite
// (un simple QueueRedraw). Redraw RARE (1×/semaine quand le snapshot arrive,
// toggle, rotation) ; ~1 188 DrawColoredPolygon une fois par minute n'est pas un
// coût (BuildGround en pose autant en permanence). Palette et bornes RÉUTILISÉES
// telles quelles de FieldOverlay.PaletteOf("temperature") : un seul langage de
// couleur (froid #3a6fd8 → chaud #d83a3a), échelle FIXE −5..35 °C — une carte
// comparable d'une semaine à l'autre (leçon t6·C3 : l'auto-échelle étale le bruit
// d'un champ quasi uniforme sur toute la palette).

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class SoilTempOverlay : Node2D
	{
		// Semi-transparent : la heatmap se lit PAR-DESSUS le sol sans l'effacer
		// (même valeur qu'à F6 — un seul langage visuel pour les deux cartes).
		private const float Alpha = 0.7f;

		// Dernier bloc `temperature` du snapshot (grilles t_sol par tuile) + origins.
		private GDict _temperature;
		private Dictionary<string, Vector2> _origins;

		/// <summary>Min/max RÉELS des grilles t_sol reçues (où la carte VIT, pour
		/// une éventuelle légende — la palette/échelle, elle, est FIXE).</summary>
		public float GridMin { get; private set; }
		public float GridMax { get; private set; }

		/// <summary>
		/// Applique le bloc `temperature` du snapshot (0.5.0) : mémorise les grilles
		/// t_sol + origins, relève le min/max réel, redessine. La projection se fait
		/// au _Draw : la rotation D35 n'a besoin que d'un QueueRedraw. `origins` =
		/// origin_cm par tuile (le même cache que plantes/litière/neige). Lecture
		/// tolérante : une tuile sans `t_sol` est ignorée, jamais de crash.
		/// </summary>
		public void SetTemperature(GDict temperature, Dictionary<string, Vector2> origins)
		{
			_temperature = temperature;
			_origins = origins;
			float mn = float.MaxValue, mx = float.MinValue;
			foreach (var kv in temperature)
			{
				var td = kv.Value.AsGodotDictionary();
				if (!td.ContainsKey("t_sol")) continue;
				foreach (var rowV in td["t_sol"].AsGodotArray())
					foreach (var cv in rowV.AsGodotArray())
					{
						float f = (float)cv.AsDouble();
						if (f < mn) mn = f;
						if (f > mx) mx = f;
					}
			}
			GridMin = mn; GridMax = mx;
			QueueRedraw();
		}

		public override void _Draw()
		{
			if (!Visible || _temperature == null || _origins == null) return;
			// Le losange d'un plot, en offsets écran constants (la projection iso
			// d'un carré de 50 cm — mêmes cotes que MakeLozenge du sol / FieldOverlay).
			Vector2 n = new(0f, -WorldView.TileHPx / 2f);
			Vector2 e = new(WorldView.TileWPx / 2f, 0f);
			Vector2 s = new(0f, WorldView.TileHPx / 2f);
			Vector2 o = new(-WorldView.TileWPx / 2f, 0f);
			// Palette + bornes FIXES du champ temperature, partagées avec F6.
			var (low, high, _, _, fixMin, fixMax) = FieldOverlay.PaletteOf("temperature");
			float span = fixMax - fixMin;
			foreach (var kv in _temperature)
			{
				if (!_origins.TryGetValue(kv.Key.AsString(), out Vector2 org))
					continue;
				var td = kv.Value.AsGodotDictionary();
				if (!td.ContainsKey("t_sol")) continue;
				// t_sol est une LISTE DE LIGNES (row-major) : t_sol[r][c] = °C du
				// plot (r,c). On lit la 2D directement (≠ index plat de FieldOverlay,
				// dont la commande `fields` aplatit la grille en values[r*cols+c]).
				var tsol = td["t_sol"].AsGodotArray();
				int rows = tsol.Count;
				for (int r = 0; r < rows; r++)
				{
					var row = tsol[r].AsGodotArray();
					int cols = row.Count;
					for (int c = 0; c < cols; c++)
					{
						float v = (float)row[c].AsDouble();
						// Clamp : sur l'échelle fixe, une canicule à 36 °C sature au
						// pôle chaud au lieu d'extrapoler la couleur.
						float tt = span > 1e-6f
							? Mathf.Clamp((v - fixMin) / span, 0f, 1f) : 0.5f;
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
}
