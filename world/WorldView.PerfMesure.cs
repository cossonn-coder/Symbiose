// SYMBIOSE — WorldView.PerfMesure.cs (partial de WorldView, sprint RENDU VISIBLE T1)
// Mesure COMPARABLE du coût d'une frame de rendu : envois GPU (draw calls),
// objets et primitives dessinés, temps de frame. Les FPS de la VM (llvmpipe,
// rendu logiciel) ne disent rien du PC de Nico (iGPU HD 4600) ; le nombre
// d'envois GPU par frame, lui, est le même sur les deux machines → c'est LA
// métrique de vérification des tronçons suivants (conception §2).
//
// 📖 Pédagogie Godot/C# :
//  - `Performance.GetMonitor(...)` lit les compteurs internes du moteur (comme
//    les registres de statistiques d'un périphérique en embarqué). Les moniteurs
//    `Render*InFrame` décrivent la DERNIÈRE frame dessinée.
//  - Un « draw call » = un envoi de commande de dessin au GPU. Godot regroupe
//    (batch) les items voisins de même texture/matériau en un seul envoi ;
//    alterner deux types de nœuds casse ce regroupement → le compteur grimpe.
//  - On moyenne sur une fenêtre d'~1 s (accumulateur + remise à zéro) : la
//    valeur d'une seule frame est trop bruitée pour comparer deux réglages.
//  - Le temps vient de l'HORLOGE MURALE (`Time.GetTicksUsec`), pas du `delta`
//    de _Process : mesuré sur la VM, le delta sous-estimait la frame (~7,5 FPS
//    affichés contre 5-6 par `--print-fps`) — Godot lisse/borne ce delta.
//  - Ligne `[perf]` en culture INVARIANTE (point décimal) : la culture FR du
//    poste écrirait « 133,5 » et casserait le parseur du script.
//
// Échantillonné à CHAQUE frame (quelques lectures de compteurs, coût nul),
// indépendamment de F4 : le mode capture (tools/perf_vm.sh) imprime une ligne
// `[perf]` par fenêtre sans afficher le HUD.
//
// PERF VUE ① — DISTRIBUTION : pendant la fenêtre de mesure du banc (touche E),
// chaque temps d'image (horloge murale) est GARDÉ dans une liste, pour en
// sortir médiane / p95 / p99 / max et le nombre d'images > 33 ms et > 100 ms.
// 📖 Une moyenne cache les à-coups : 59 images à 10 ms + 1 à 400 ms font une
// moyenne de 16 ms (« 60 FPS ») alors que l'œil voit un saut. Les percentiles
// (la valeur sous laquelle tombent 95 % / 99 % des images) le révèlent.
// On y ajoute le temps de rendu mesuré par le serveur de rendu Godot
// (`ViewportSetMeasureRenderTime`) : CPU de rendu et, si le pilote le permet,
// GPU — 0 = non disponible sur ce pilote.

using Godot;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Symbiose
{
	public partial class WorldView
	{
		private const double PerfFenetreSec = 1.0;

		// Accumulateurs de la fenêtre en cours.
		private double _pmDraw, _pmObj, _pmPrim;
		private ulong _pmDebutUs;
		private int _pmFrames;
		// Gel (D106 T4, méthode 73a3f24) : frame la plus longue de la fenêtre et
		// nombre de frames > 250 ms — la moyenne seule masque l'à-coup hebdomadaire.
		private ulong _pmPrecUs;
		private double _pmMaxMs;
		private int _pmGels;
		// Moyennes de la dernière fenêtre close (−1 = pas encore mesuré).
		private double _pmFrameMs = -1, _pmDrawMoy = -1, _pmObjMoy = -1, _pmPrimMoy = -1;

		// Fenêtre de DISTRIBUTION (banc PERF VUE ①) : null = pas de mesure en cours.
		private List<double> _distMs;
		private ulong _distDebutUs;
		private double _distDraw, _distPrim, _distProcMs, _distRenduCpu, _distRenduGpu;

		// Appelé chaque frame depuis _Process (toutes phases).
		private void MesurerPerfRendu()
		{
			ulong now = Time.GetTicksUsec();
			if (_pmDebutUs == 0) { _pmDebutUs = _pmPrecUs = now; return; }   // 1re frame : ouvre la fenêtre
			_pmFrames++;
			double frameMs = (now - _pmPrecUs) / 1000.0;
			_pmPrecUs = now;
			if (frameMs > _pmMaxMs) _pmMaxMs = frameMs;
			if (frameMs > 250.0) _pmGels++;
			_pmDraw += Performance.GetMonitor(Performance.Monitor.RenderTotalDrawCallsInFrame);
			_pmObj += Performance.GetMonitor(Performance.Monitor.RenderTotalObjectsInFrame);
			_pmPrim += Performance.GetMonitor(Performance.Monitor.RenderTotalPrimitivesInFrame);
			if (_distMs != null) EchantillonDistribution(frameMs);
			double temps = (now - _pmDebutUs) / 1e6;
			if (temps < PerfFenetreSec) return;

			_pmFrameMs = 1000.0 * temps / _pmFrames;
			_pmDrawMoy = _pmDraw / _pmFrames;
			_pmObjMoy = _pmObj / _pmFrames;
			_pmPrimMoy = _pmPrim / _pmFrames;
			// Banc temps réel (perf_vm.sh) : une ligne machine-lisible par fenêtre.
			if (CaptureActive)
				GD.Print(string.Create(CultureInfo.InvariantCulture,
					$"[perf] fps={1000.0 / _pmFrameMs:F1} ms={_pmFrameMs:F1} "
					+ $"draw={_pmDrawMoy:F0} obj={_pmObjMoy:F0} prim={_pmPrimMoy:F0} "
					+ $"max={_pmMaxMs:F0} gels={_pmGels} couches={NomCasCouches()}"));
			_pmDraw = _pmObj = _pmPrim = 0;
			_pmMaxMs = 0;
			_pmGels = 0;
			_pmDebutUs = now;
			_pmFrames = 0;
		}

		/// <summary>Ouvre la fenêtre de distribution (et les chronos par poste).</summary>
		private void DemarrerDistribution()
		{
			_distMs = new List<double>(4096);
			_distDebutUs = Time.GetTicksUsec();
			_distDraw = _distPrim = _distProcMs = _distRenduCpu = _distRenduGpu = 0;
			RenderingServer.ViewportSetMeasureRenderTime(GetViewport().GetViewportRid(), true);
			RenderingServer.ViewportSetMeasureRenderTime(_worldVp.GetViewportRid(), true);
			PerfPostes.Reset();
			DemarrerAcoups();   // pires images + GC (WorldView.PerfAcoups.cs, ④)
		}

		private void EchantillonDistribution(double frameMs)
		{
			_distMs.Add(frameMs);
			EchantillonAcoups(frameMs);
			_distDraw += Performance.GetMonitor(Performance.Monitor.RenderTotalDrawCallsInFrame);
			_distPrim += Performance.GetMonitor(Performance.Monitor.RenderTotalPrimitivesInFrame);
			_distProcMs += 1000.0 * Performance.GetMonitor(Performance.Monitor.TimeProcess);
			AjouterRendu(GetViewport().GetViewportRid());   // fenêtre (HUD + composition)
			AjouterRendu(_worldVp.GetViewportRid());         // SubViewport monde
		}

		private void AjouterRendu(Rid vp)
		{
			_distRenduCpu += RenderingServer.ViewportGetMeasuredRenderTimeCpu(vp);
			_distRenduGpu += RenderingServer.ViewportGetMeasuredRenderTimeGpu(vp);
		}

		/// <summary>Ferme la fenêtre et écrit le bloc « distribution + postes ».</summary>
		private void EcrireDistribution(StringBuilder sb)
		{
			if (_distMs == null || _distMs.Count == 0) { sb.AppendLine("  (aucune image mesurée)"); return; }
			var t = new List<double>(_distMs);
			t.Sort();
			int n = t.Count;
			double sec = (Time.GetTicksUsec() - _distDebutUs) / 1e6;
			double moy = 1000.0 * sec / n;
			double P(double q) => t[System.Math.Min(n - 1, (int)System.Math.Floor(q * n))];
			int sup33 = 0, sup100 = 0;
			foreach (double v in t) { if (v > 33.0) sup33++; if (v > 100.0) sup100++; }
			var ci = CultureInfo.InvariantCulture;
			sb.AppendLine(string.Create(ci,
				$"  images {n} en {sec:F1} s · FPS {n / sec:F1} · moyenne {moy:F1} ms · "
				+ $"médiane {P(0.5):F1} · p95 {P(0.95):F1} · p99 {P(0.99):F1} · max {t[n - 1]:F1} ms"));
			sb.AppendLine(string.Create(ci,
				$"  images > 33 ms : {sup33} · > 100 ms : {sup100} · draw calls {_distDraw / n:F0} · "
				+ $"primitives {_distPrim / n:F0}"));
			sb.AppendLine(string.Create(ci,
				$"  moniteur TimeProcess {_distProcMs / n:F2} ms/image · rendu CPU {_distRenduCpu / n:F2} · "
				+ $"rendu GPU {_distRenduGpu / n:F2} ms/image (0 = non mesuré par ce pilote)"));
			double postes = PerfPostes.TotalMs() / n;
			sb.AppendLine(string.Create(ci,
				$"  postes CPU (somme {postes:F2} ms/image, non attribué {moy - postes:F2}) :"));
			PerfPostes.Ecrire(sb, n, sec, moy);
			EcrireAcoups(sb, n);
			_distMs = null;
			RenderingServer.ViewportSetMeasureRenderTime(GetViewport().GetViewportRid(), false);
			RenderingServer.ViewportSetMeasureRenderTime(_worldVp.GetViewportRid(), false);
		}

		// Ligne « rendu » ajoutée à l'overlay F4 et au rapport presse-papier (C).
		private string LignePerfRendu()
		{
			if (_pmFrameMs < 0) return "rendu — mesure en cours… · couches : " + NomCasCouches();
			return $"rendu — frame {_pmFrameMs:F1} ms (moy. ~1 s) · draw calls "
				+ $"{_pmDrawMoy:F0} · objets {_pmObjMoy:F0} · primitives {_pmPrimMoy:F0} · "
				+ $"couches : {NomCasCouches()}";
		}
	}
}
