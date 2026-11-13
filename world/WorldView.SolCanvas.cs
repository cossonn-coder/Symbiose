// SYMBIOSE — WorldView.SolCanvas.cs (partial de WorldView, sprint GESTES LISIBLES ③)
// Le câblage VUE du SOL-CANVAS (conception §3) : relaie au sol ce que le snapshot dit
// des gestes et des événements — traces de gestes (`traces_sol`), plots secs
// (`sol_sec`) et averse (`weather`, déjà publiée par MeteoPlantes). Lecture seule
// (pont 0.6.14) : Python reste la source de vérité, la vue n'invente aucune trace.
//
// 📖 Pédagogie — les deux couches naissent ICI, paresseusement, au premier snapshot
// (WorldView.cs est plein : on n'y ajoute rien). Elles sont enfants du monde (comme le
// paillis), donc survivent à RebuildWorld et se re-projettent seules au pivot. Un
// nouveau monde (autre banc) les remet à zéro : les tuiles d'avant n'existent plus.

using System.Collections.Generic;
using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		private TracesSolLayer _tracesSol;
		private EclaboussuresLayer _eclaboussures;
		private Dictionary<string, Vector2> _solCanvasOrigins;   // monde pour lequel elles sont montées

		private void ApplySolCanvas(GDict snap)
		{
			if (_origins == null) return;
			if (!ReferenceEquals(_solCanvasOrigins, _origins)) MonterSolCanvas();
			_tracesSol.Set(snap.ContainsKey("traces_sol") ? snap["traces_sol"].AsGodotDictionary() : null,
				snap.ContainsKey("sol_sec") ? snap["sol_sec"].AsGodotDictionary() : null, _origins);
		}

		// (Re)crée les deux couches pour le monde courant. ZIndex 1 = bande du sol, et
		// les traces passent SOUS le paillis (un geste sous la paille est couvert).
		private void MonterSolCanvas()
		{
			_tracesSol?.QueueFree();
			_eclaboussures?.QueueFree();
			_solCanvasOrigins = _origins;
			_tracesSol = new TracesSolLayer { Name = "TracesSol", ZIndex = 1 };
			_tracesSol.Init(ReliefRiseAtPlot);
			AddWorld(_tracesSol);
			if (_mulchLayer != null)
				_tracesSol.GetParent().MoveChild(_tracesSol, _mulchLayer.GetIndex());
			_eclaboussures = new EclaboussuresLayer { Name = "Eclaboussures", ZIndex = 2 };
			var tuiles = new List<(string, Rect2)>();
			foreach (var tv in _world["tiles"].AsGodotArray())
			{
				var t = tv.AsGodotDictionary();
				tuiles.Add((t["id"].AsString(), new Rect2(
					(float)t["origin_x_cm"].AsDouble(), (float)t["origin_y_cm"].AsDouble(),
					t["cols"].AsInt32() * PlotCm, t["rows"].AsInt32() * PlotCm)));
			}
			_eclaboussures.Init(tuiles, ReliefRiseAtPlot);
			AddWorld(_eclaboussures);
		}
	}
}
