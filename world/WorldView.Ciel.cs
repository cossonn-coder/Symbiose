// SYMBIOSE — WorldView.Ciel.cs (partial de WorldView, sprint effondrement météo ④)
// Le câblage VUE du « ciel de la semaine » : instancie l'ENCART diégétique
// (SkyPanel, un CanvasLayer écran) et la couche des PLACEHOLDERS de couvertures
// posées (CoverLayer, dans le monde), puis leur relaie les blocs `ciel`,
// `couvert_pose` et `ombre_pose` du snapshot (protocole 0.5.43, lecture seule).
// Comme la météo (WorldView.Meteo.cs), toute la logique reste à Python : ici on ne
// fait que PEINTRE ce que le pont expose. Golden NEUTRE (pur rendu + pont read-only).

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Encart « état du ciel » (CanvasLayer écran, coin haut-droit) : condense la
		// convergence + les signes du bloc `ciel`, s'assombrit à l'approche du composé.
		private SkyPanel _skyPanel;
		// Placeholders des couvertures posées (voile/cloche/ombrière) — ZIndex 12 :
		// AU-DESSUS des plantes (10) et des butineurs (11), car une couverture est
		// tendue PAR-DESSUS le jardin. Enfant direct de WorldView (survit à
		// RebuildWorld, se re-projette seul). Lit `couvert_pose`/`ombre_pose` (0.5.43).
		private CoverLayer _coverLayer;

		// Couche monde des couvertures — appelée en _Ready avec les autres AddWorld.
		private void BuildCielView()
		{
			_coverLayer = new CoverLayer { Name = "Covers", ZIndex = 12 };
			AddWorld(_coverLayer);
		}

		// Encart écran — appelé APRÈS BuildHud pour rester au-dessus dans l'ordre Z.
		private void BuildSkyPanel()
		{
			_skyPanel = new SkyPanel { Name = "SkyPanel" };
			AddChild(_skyPanel);
		}

		// Bloc `ciel` du snapshot (lecture tolérante : pré-0.5.43 sans le bloc → encart
		// neutre, jamais appelé).
		// Le dernier bloc réel est gardé : le défilé F12 (T5) le restaure en sortant.
		private void ApplyCiel(GDict ciel)
		{
			_lastCiel = ciel;
			if (!DefileActif) _skyPanel?.SetSky(ciel);
			if (!DefileActif) _decorLayer?.SetSignes(ciel);   // AUTOMNE ⑥
		}
		private GDict _lastCiel;

		// Blocs `couvert_pose` / `ombre_pose` (lecture tolérante : un bloc absent →
		// null → CoverLayer le saute, pas de placeholder dessiné).
		private void ApplyCovers(GDict couvert, GDict ombre)
		{
			_coverLayer?.SetCovers(couvert, ombre, _origins);
			MarkCoveredPlants(couvert);
		}

		// Jardin vivant T5 : une plante dont le PLOT-foyer porte un voile/cloche
		// (`couvert_pose` > 0) ne montre ni neige ni givre. Appelé APRÈS la mise à
		// jour des plantes du même snapshot (ApplySnapshot) ; la position monde
		// (méta tile/lx/ly) est l'identité de la plante, plot = floor(pos / 50 cm).
		private void MarkCoveredPlants(GDict couvert)
		{
			var abrites = new System.Collections.Generic.HashSet<(string, int, int)>();
			if (couvert != null)
				foreach (var kv in couvert)
				{
					using var plots = kv.Value.AsGodotArray();
					for (int i = 0; i < plots.Count; i++)
					{
						using var a = LectureSnap.Tab(plots, i);   // PERF VUE ④ : sans finaliseur
						abrites.Add((kv.Key.AsString(), (int)LectureSnap.D(a, 0), (int)LectureSnap.D(a, 1)));
					}
				}
			foreach (var p in _plantNodes.Values)
			{
				int r = Mathf.FloorToInt((float)p.GetMeta(LectureSnap.Meta("ly")).AsDouble() / PlotCm);
				int c = Mathf.FloorToInt((float)p.GetMeta(LectureSnap.Meta("lx")).AsDouble() / PlotCm);
				p.SetCovered(abrites.Contains((p.GetMeta(LectureSnap.Meta("tile")).AsString(), r, c)));
			}
		}
	}
}
