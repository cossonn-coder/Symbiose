// SYMBIOSE — BakeQueue.cs (sprint JARDIN VIVANT T2 — file de re-cuisson étalée)
// L'ORDONNANCEUR de la pré-cuisson. Exigence Nico : JAMAIS toutes les plantes
// recuites au même moment. Une semaine simulée salit tout le jardin, un cran de
// molette aussi : la file recuit au plus PlantsPerFrame plantes par frame, et
// SEULEMENT celles que la caméra cadre (+ la marge du culling) — l'écran d'abord.
// Une plante hors marge reste « sale » sans rien coûter ; elle est recuite quand
// la caméra l'approche. Pendant l'attente elle garde son ancienne image (ou se
// dessine en direct si elle n'en a pas) : jamais de trou.
//
// 📖 Pédagogie (analogie embarqué) : c'est un ordonnanceur à budget fixe par
// tick, comme une boucle principale qui ne traite que N messages d'une FIFO par
// passage pour ne jamais rater son échéance temps réel.
//
// Marge = celle de WorldView.CullPlants (Visible=false au-delà, world/MargeVue.cs) :
// une seule définition du « près de l'écran ».
//
// D106 T4 : la file ne rebalaye plus TOUTES les plantes sales à chaque frame. Elle
// tient à part les ÉLIGIBLES (sales ET dans la marge), mis à jour aux seuls
// événements qui les changent — une plante salie (MarkDirty), une plante qui entre
// ou sort de la marge (VisibiliteChangee, appelé par CullPlants). Cas normal : les
// sales sont hors marge → zéro éligible → la frame ne coûte rien ici.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class BakeQueue : Node
	{
		// Budget par frame, DOUBLE : au plus PlantsPerFrame plantes ET au plus
		// SegmentsPerFrame segments (le coût du pinceau suit le nombre de segments :
		// ~0,06 ms/segment mesuré sur la VM, un vieil arbre de 67 segments ≈ 4 ms).
		// Toujours au moins 1 plante par frame (un arbre seul passe quand même).
		// 6 → 300 plantes cadrées en 50 frames ≈ 0,8 s à 60 FPS (cible kickoff :
		// file vidée en ~1-2 s). Valeurs à confirmer au F4 de Nico.
		private const int PlantsPerFrame = 6;
		private const int SegmentsPerFrame = 80;
		// Libération des images hors champ : balayage espacé (pas chaque frame).
		private const int ReleaseEveryFrames = 15;

		private static readonly HashSet<PlantRenderer> _all = new();
		private static readonly HashSet<PlantRenderer> _dirty = new();
		private static readonly HashSet<PlantRenderer> _eligibles = new();   // ⊂ _dirty, Visible
		private readonly List<(PlantRenderer Node, ulong Frame)> _inFlight = new();
		private readonly List<PlantRenderer> _pick = new();
		private int _pickSegs;

		// Matériau partagé : l'image cuite sur fond transparent sort PRÉMULTIPLIÉE
		// (rgb déjà × alpha, ex. feuilles à 0,92) ; on la remet en alpha DROIT pour
		// que le mélange avec le sol soit celui du dessin direct (sinon feuillage
		// assombri ~8 %). Texture blanche du dessin direct (a = 1) → sans effet.
		public static readonly ShaderMaterial Unpremultiply = new()
		{
			Shader = new Shader
			{
				Code = "shader_type canvas_item;\n"
					 + "void fragment() {\n"
					 + "\tfloat a = texture(TEXTURE, UV).a;\n"
					 + "\tif (a > 0.0) COLOR.rgb /= a;\n"
					 + "}\n",
			},
		};

		// Mesures (gravées dans 00_etat.md) : rafale = depuis la 1re cuisson jusqu'à
		// file vide. Le temps CPU du pinceau est mesuré dans son _Draw.
		private int _burstCount;
		private ulong _burstStartFrame;
		private ulong _burstStartUsec;
		private static double _drawMsSum, _drawMsMax;
		private static int _drawCount, _drawMaxSegs;

		/// <summary>Toutes les plantes cuisables (lu par l'onde de vent, T3).</summary>
		public static IReadOnlyCollection<PlantRenderer> All => _all;
		public static void Register(PlantRenderer p) => _all.Add(p);
		public static void Unregister(PlantRenderer p)
		{
			_all.Remove(p);
			_dirty.Remove(p);
			_eligibles.Remove(p);
		}

		/// <summary>La plante passe au tapis de son plot (D106 T5) : plus rien à cuire.</summary>
		public static void Retirer(PlantRenderer p)
		{
			_dirty.Remove(p);
			_eligibles.Remove(p);
		}

		public static void MarkDirty(PlantRenderer p)
		{
			_dirty.Add(p);
			if (p.Visible) _eligibles.Add(p);
		}

		/// <summary>La plante vient d'entrer dans la marge ou d'en sortir (T4).</summary>
		public static void VisibiliteChangee(PlantRenderer p)
		{
			if (p.Visible && _dirty.Contains(p)) _eligibles.Add(p);
			else _eligibles.Remove(p);
		}

		public static void RecordBrushDraw(double ms, int segs)
		{
			_drawMsSum += ms;
			_drawCount++;
			if (ms > _drawMsMax) { _drawMsMax = ms; _drawMaxSegs = segs; }
		}

		// Banc PERF VUE ① : chronométré (PerfPostes), corps inchangé.
		public override void _Process(double delta)
		{
			long t0 = PerfPostes.Debut();
			ProcessFile();
			PerfPostes.Fin(PerfPostes.Poste.CuissonFile, t0);
		}

		private void ProcessFile()
		{
			ulong frame = Engine.GetProcessFrames();
			CommitRendered(frame);
			if (frame % ReleaseEveryFrames == 0) ReleaseOffscreen();
			if (_eligibles.Count == 0) { EndBurst(frame); return; }

			// Deux passes : d'abord ce qui est À L'ÉCRAN, puis la marge.
			_pick.Clear();
			_pickSegs = 0;
			PickInto(onScreenOnly: true);
			if (_pick.Count < PlantsPerFrame && _pickSegs < SegmentsPerFrame)
				PickInto(onScreenOnly: false);
			if (_pick.Count == 0) { EndBurst(frame); return; }
			if (_burstCount == 0)
			{
				_burstStartFrame = frame;
				_burstStartUsec = Time.GetTicksUsec();
			}
			foreach (var p in _pick)
			{
				_dirty.Remove(p);
				_eligibles.Remove(p);
				if (p.Baker.Begin(WorldView.CurrentZoom))
				{
					_inFlight.Add((p, frame));
					_burstCount++;
				}
				else p.QueueRedraw();   // trop grand / vide → dessin direct
			}
		}

		private void PickInto(bool onScreenOnly)
		{
			foreach (var p in _eligibles)
			{
				if (_pick.Count >= PlantsPerFrame || _pickSegs >= SegmentsPerFrame) return;
				// IsVisibleInTree reste testé : le masque de couches (Maj+F4) cache le
				// parent « Objects » sans toucher au Visible propre de la plante.
				if (!GodotObject.IsInstanceValid(p) || !p.IsVisibleInTree() || p.EnAttente
					|| p.Baker.InFlight || _pick.Contains(p)) continue;
				if (onScreenOnly && !OnScreen(p)) continue;
				// Une plante qui ferait déborder le budget attend la frame suivante
				// (sauf si c'est la première : jamais de famine pour un gros arbre).
				if (_pick.Count > 0 && _pickSegs + p.BakeCost > SegmentsPerFrame) continue;
				_pick.Add(p);
				_pickSegs += p.BakeCost;
			}
		}

		// Le collet est-il dans le cadre du SubViewport monde ? (px internes).
		private static bool OnScreen(PlantRenderer p) =>
			p.GetViewportRect().HasPoint(p.GetGlobalTransformWithCanvas().Origin);

		// Une cuisson demandée à la frame f est rendue en fin de frame f : on ne
		// l'affiche qu'à partir de f+1 (jamais une texture pas encore peinte).
		private void CommitRendered(ulong frame)
		{
			for (int i = _inFlight.Count - 1; i >= 0; i--)
			{
				var (p, f) = _inFlight[i];
				if (f >= frame) continue;
				_inFlight.RemoveAt(i);
				if (!GodotObject.IsInstanceValid(p)) continue;
				p.Baker.Commit();
				p.QueueRedraw();
			}
		}

		// Plante sortie de la marge (culling) : on rend sa mémoire vidéo, elle
		// redevient sale (et dessinée en direct si jamais elle est vue avant cuisson).
		private static void ReleaseOffscreen()
		{
			foreach (var p in _all)
			{
				if (!p.HasBakedImage || p.IsVisibleInTree() || p.Baker.InFlight) continue;
				p.Baker.Release();
				_dirty.Add(p);
				p.QueueRedraw();
			}
		}

		private void EndBurst(ulong frame)
		{
			if (_burstCount == 0 || _inFlight.Count > 0) return;
			double ms = (Time.GetTicksUsec() - _burstStartUsec) / 1000.0;
			GD.Print($"[Cuisson] file vidée : {_burstCount} plantes en "
				+ $"{frame - _burstStartFrame} frames ({ms:F0} ms) · cache "
				+ $"{PlantBaker.TotalBytes / 1048576.0:F1} Mo / {PlantBaker.TotalImages} images · "
				+ $"pinceau {(_drawCount == 0 ? 0 : _drawMsSum / _drawCount):F2} ms/plante "
				+ $"(max {_drawMsMax:F2} ms, {_drawMaxSegs} segments) · "
				+ $"{_dirty.Count} sales hors champ.");
			_burstCount = 0;
			_drawMsSum = _drawMsMax = 0;
			_drawCount = _drawMaxSegs = 0;
		}
	}
}
