// SYMBIOSE — TracesSolLayer.cs (sprint GESTES LISIBLES ③, conception §3)
// La couche des TRACES AU SOL : ce que les gestes y ont laissé (bloc `traces_sol`,
// pont 0.6.14) et le sol CRAQUELÉ des plots secs (bloc `sol_sec`). Règle cardinale
// (D3, Nico : « on invente pas ») : une trace n'est dessinée QUE si le snapshot la
// porte ; elle disparaît quand le moteur la purge. La vue ne fait que l'estomper
// avec son âge (une trace ancienne est plus pâle).
//
// 📖 Pédagogie — rendu EN LOT PAR TUILE (patron du sol D106, SolMaillage) : chaque
// tuile a son propre petit nœud enfant qui accumule ses triangles dans UN
// LotTriangles → un envoi GPU par tuile marquée. Le nœud d'une tuile ne se
// redessine QUE si sa liste a changé (signature texte du bloc) ou si la vue a
// pivoté / franchi le palier de détail — jamais à chaque image. Godot écarte seul
// un nœud hors écran (son rectangle de dessin ne touche pas la caméra).
//
// 📖 Hystérésis du craquelé (§3.2) : le pont envoie les plots sous 0,5 (seuil où les
// plantes sentent la sécheresse) avec leur humidité brute. La vue fait APPARAÎTRE le
// craquelé sous `SeuilApparition` et ne l'EFFACE qu'au-dessus du seuil du pont (le
// plot quitte la liste) : entre les deux, un plot déjà craquelé le reste. Sans cette
// marge, un plot qui oscille autour d'un seuil unique clignoterait chaque semaine.

using System;
using System.Collections.Generic;
using System.Text;
using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class TracesSolLayer : Node2D
	{
		// Palier de détail : sous ×1 les traces (un détail de sol) se taisent.
		private const float MinZoom = 1f;
		// Le craquelé naît sous ce seuil (le pont exporte sous 0,5 : marge d'hystérésis).
		private const float SeuilApparition = 0.35f;
		// Estompage par l'âge (semaines) : la vue ne connaît pas la durée de vie d'une
		// sorte (table moteur) — elle pâlit chaque semaine, le moteur décide la fin.
		private const float PerteParSemaine = 0.16f, OpaciteMin = 0.25f;

		private readonly struct Trace
		{
			public readonly int R, C;
			public readonly float X, Y;
			public readonly string Sorte;
			public readonly int Age;
			public Trace(int r, int c, float x, float y, string sorte, int age)
			{ R = r; C = c; X = x; Y = y; Sorte = sorte; Age = age; }
		}

		// Un nœud de dessin par tuile : ses traces, ses plots craquelés, sa signature.
		private sealed partial class Tuile : Node2D
		{
			public string Id;
			public Vector2 Origine;
			public readonly List<Trace> Traces = new();
			public readonly Dictionary<(int, int), float> Secs = new();   // plot → sécheresse ∈ [0,1]
			public string SigTraces = "", SigSecs = "";
			public Func<string, int, int, float> Relief;
			private readonly LotTriangles _lot = new();

			public override void _Draw()
			{
				_lot.Vider();
				if (WorldView.CurrentZoom >= MinZoom) Peindre();
				_lot.Dessiner(this);
			}

			private Vector2 Point(int r, int c, float xCm, float yCm) =>
				WorldView.WorldToScreen(Origine.X + xCm, Origine.Y + yCm)
				- new Vector2(0f, Relief?.Invoke(Id, r, c) ?? 0f);

			private void Peindre()
			{
				// Le craquelé d'abord (c'est l'état du sol), les gestes par-dessus.
				foreach (var kv in Secs)
				{
					var (r, c) = kv.Key;
					Vector2 p = Point(r, c, (c + 0.5f) * WorldView.PlotCm, (r + 0.5f) * WorldView.PlotCm);
					TracesSolMotifs.Craquele(_lot, p, kv.Value,
						TracesSolMotifs.Hash($"{Id}|{r}|{c}|sec"));
				}
				foreach (var t in Traces)
				{
					// Les traces au PLOT (bêche, grelinette…) se centrent sur le plot ; le
					// pas reste au point cliqué (le moteur fournit les deux).
					bool auPoint = t.Sorte == "pas";
					float x = auPoint ? t.X : (t.C + 0.5f) * WorldView.PlotCm;
					float y = auPoint ? t.Y : (t.R + 0.5f) * WorldView.PlotCm;
					float a = Mathf.Max(OpaciteMin, 1f - PerteParSemaine * t.Age);
					TracesSolMotifs.Trace(_lot, t.Sorte, Point(t.R, t.C, x, y), a,
						TracesSolMotifs.Hash($"{Id}|{t.R}|{t.C}|{t.X}|{t.Y}|{t.Sorte}"));
				}
			}
		}

		private readonly Dictionary<string, Tuile> _tuiles = new();
		private Func<string, int, int, float> _relief;
		private Vector2 _cleVue = new(float.NaN, 0f);   // orientation (projection de l'origine)
		private bool _zoomOk;

		/// <summary>Recalage relief (px vers le haut) d'un plot — WorldView.ReliefRiseAtPlot.</summary>
		public void Init(Func<string, int, int, float> relief) => _relief = relief;

		/// <summary>Applique `traces_sol` et `sol_sec` (null = clé absente : la tuile garde
		/// ce qu'elle avait de cette source). Ne redessine que les tuiles qui changent.</summary>
		public void Set(GDict traces, GDict secs, Dictionary<string, Vector2> origins)
		{
			// Tuile neuve (première trace ou premier plot sec) : son nœud naît ici.
			foreach (GDict bloc in new[] { traces, secs })
				if (bloc != null)
					foreach (var kv in bloc) Creer(kv.Key.AsString(), origins);
			foreach (var (id, t) in _tuiles)
			{
				string sigT = traces != null ? LireTraces(t, Bloc(traces, id)) : t.SigTraces;
				string sigS = secs != null ? LireSecs(t, Bloc(secs, id)) : t.SigSecs;
				if (sigT == t.SigTraces && sigS == t.SigSecs) continue;   // rien n'a bougé
				t.SigTraces = sigT;
				t.SigSecs = sigS;
				t.QueueRedraw();
			}
		}

		private static Godot.Collections.Array Bloc(GDict d, string id) =>
			d.ContainsKey(id) ? d[id].AsGodotArray() : null;

		private void Creer(string id, Dictionary<string, Vector2> origins)
		{
			if (_tuiles.ContainsKey(id) || !origins.TryGetValue(id, out Vector2 o)) return;
			var t = new Tuile { Id = id, Origine = o, Relief = _relief, Name = "Traces_" + id };
			_tuiles[id] = t;
			AddChild(t);
		}

		// Signature = le contenu lu + le relief (px arrondi) de chaque plot marqué : un
		// plot creusé descend, sa trace doit descendre avec lui.
		private static string LireTraces(Tuile t, Godot.Collections.Array arr)
		{
			t.Traces.Clear();
			if (arr == null) return "";
			var sig = new StringBuilder();
			foreach (var v in arr)
			{
				// Format 0.6.14 : [r, c, x_cm, y_cm, sorte, age] (x/y tuile-locaux).
				var e = v.AsGodotArray();
				var tr = new Trace(e[0].AsInt32(), e[1].AsInt32(), (float)e[2].AsDouble(),
					(float)e[3].AsDouble(), e[4].AsString(), e[5].AsInt32());
				t.Traces.Add(tr);
				sig.Append(tr.R).Append(',').Append(tr.C).Append(',').Append(tr.X).Append(',')
					.Append(tr.Y).Append(',').Append(tr.Sorte).Append(',').Append(tr.Age).Append(',')
					.Append(Mathf.RoundToInt(t.Relief?.Invoke(t.Id, tr.R, tr.C) ?? 0f)).Append(';');
			}
			return sig.ToString();
		}

		private static string LireSecs(Tuile t, Godot.Collections.Array arr)
		{
			var avant = new HashSet<(int, int)>(t.Secs.Keys);
			t.Secs.Clear();
			if (arr == null) return "";
			var sig = new StringBuilder();
			foreach (var v in arr)
			{
				// Format 0.6.14 : [r, c, humidite] des plots sous le seuil du pont.
				var e = v.AsGodotArray();
				var rc = (e[0].AsInt32(), e[1].AsInt32());
				float h = (float)e[2].AsDouble();
				if (h >= SeuilApparition && !avant.Contains(rc)) continue;   // hystérésis
				float sec = Mathf.Clamp(1f - h / SeuilApparition, 0f, 1f);
				t.Secs[rc] = sec;
				sig.Append(rc.Item1).Append(',').Append(rc.Item2).Append(',')
					.Append(Mathf.RoundToInt(sec * 4f)).Append(',')
					.Append(Mathf.RoundToInt(t.Relief?.Invoke(t.Id, rc.Item1, rc.Item2) ?? 0f)).Append(';');
			}
			return sig.ToString();
		}

		public override void _Process(double delta)
		{
			// Pivot de vue (D35) ou palier franchi : toutes les tuiles se redessinent.
			Vector2 cle = WorldView.WorldToScreen(0f, 0f);
			bool zoomOk = WorldView.CurrentZoom >= MinZoom;
			if (cle == _cleVue && zoomOk == _zoomOk) return;
			_cleVue = cle;
			_zoomOk = zoomOk;
			foreach (var t in _tuiles.Values) t.QueueRedraw();
		}
	}
}
