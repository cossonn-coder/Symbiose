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

		// Crée les deux couches (appelé en _Ready, avant BuildHud pour l'ordre Z
		// du CanvasLayer ambiance, et après _origins pour le manteau).
		private void BuildMeteoLayers()
		{
			_weatherLayer = new WeatherLayer { Name = "Weather" };
			AddChild(_weatherLayer);

			_snowLayer = new SnowLayer { Name = "Snow", ZIndex = 2 };
			AddChild(_snowLayer);
		}

		// Bloc `weather` (lecture tolérante : pré-0.5.0 sans le bloc → ciel neutre).
		private void ApplyWeather(GDict weather) => _weatherLayer?.SetWeather(weather);

		// Bloc `temperature` (lecture tolérante : pré-0.5.0 → pas de manteau).
		private void ApplySnow(GDict temperature) =>
			_snowLayer?.SetSnow(temperature, _origins);
	}
}
