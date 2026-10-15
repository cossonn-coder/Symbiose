// SYMBIOSE — WorldView.Meteo.cs (partial de WorldView, tronçon ⑨)
// Le câblage VUE de la météo : instancie les deux couches du rendu météo et leur
// relaie les blocs `weather` (ambiance écran) et `temperature` (manteau par
// tuile) du snapshot 0.5.0 (lecture seule). Comme la décompo (WorldView.Compost.cs),
// la logique reste à Python : ici on ne fait que PEINTRE. Golden NEUTRE.

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Ambiance globale (CanvasLayer écran) : nébulosité + précipitations +
		// flashs d'orage. AU-DESSUS du monde, SOUS le HUD (ajouté avant BuildHud).
		private WeatherLayer _weatherLayer;
		// Manteau neigeux (Node2D monde) : voile blanc par tuile, ZIndex 2 =
		// au-dessus de la litière (1) et du sol (0), SOUS la vie macro (5) et les
		// plantes (10) — la neige est au sol, les plantes en dépassent.
		private SnowLayer _snowLayer;
		// Heatmap T sol spatialisée (⑩, Node2D monde) : ZIndex 3 comme FieldOverlay
		// — par-dessus sol/ombre/manteau, sous vie macro (5) et plantes (10). Cachée
		// par défaut, allumée à F7. Lit `temperature[tile].t_sol` du snapshot.
		private SoilTempOverlay _soilTempOverlay;

		// Crée les couches météo (appelé en _Ready, avant BuildHud pour l'ordre Z
		// du CanvasLayer ambiance, et après _origins pour le manteau / la heatmap).
		private void BuildMeteoLayers()
		{
			// Ambiance = CanvasLayer plein écran → reste dans le viewport PRINCIPAL
			// (AddChild, pas AddWorld) : un voile de pluie/nuages full-résolution
			// sur tout l'écran, au-dessus du monde pixellisé et sous le HUD.
			_weatherLayer = new WeatherLayer { Name = "Weather" };
			AddChild(_weatherLayer);

			_snowLayer = new SnowLayer { Name = "Snow", ZIndex = 2 };
			AddWorld(_snowLayer);

			_soilTempOverlay = new SoilTempOverlay
			{
				Name = "SoilTempOverlay", ZIndex = 3, Visible = false,
			};
			AddWorld(_soilTempOverlay);
		}

		// Bloc `weather` (lecture tolérante : pré-0.5.0 sans le bloc → ciel neutre).
		// T3 (0.5.44) : sous-bloc `wind` → onde de vent des plantes (WindWave).
		// Absent (binaire pré-0.5.44) → vent nul → jardin immobile.
		private void ApplyWeather(GDict weather)
		{
			_weatherLayer?.SetWeather(weather);
			var w = weather.ContainsKey("wind") ? weather["wind"].AsGodotDictionary() : null;
			WindWave.SetWind(w != null ? (float)w["force"].AsDouble() : 0f,
							 w != null ? (float)w["direction"].AsDouble() : 0f,
							 w != null && w.ContainsKey("gusts") ? w["gusts"].AsGodotArray() : null);
		}

		// Bloc `temperature` (lecture tolérante : pré-0.5.0 → pas de manteau).
		private void ApplySnow(GDict temperature) =>
			_snowLayer?.SetSnow(temperature, _origins);

		// Bloc `temperature.t_sol` → heatmap T sol (⑩). Même GDict que ApplySnow ;
		// l'overlay ne redessine que s'il est visible (coût nul quand caché).
		private void ApplySoilTemp(GDict temperature) =>
			_soilTempOverlay?.SetTemperature(temperature, _origins);

		// Touche F7 : carte thermique du SOL ON/OFF. Visible=false court-circuite
		// _Draw (coût nul) ; les données continuent de suivre les snapshots —
		// rallumer est gratuit (même esprit que ToggleMacroLife/ToggleFieldOverlay).
		private void ToggleSoilTemp()
		{
			if (_soilTempOverlay == null) return;
			_soilTempOverlay.Visible = !_soilTempOverlay.Visible;
			GD.Print($"[WorldView] F7 → carte T sol {(_soilTempOverlay.Visible ? "ON" : "OFF")}.");
		}
	}
}
