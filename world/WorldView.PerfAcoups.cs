// SYMBIOSE — WorldView.PerfAcoups.cs (partial de WorldView, sprint PERF VUE ④)
// DIAGNOSTIC DES À-COUPS pendant la fenêtre de mesure du banc E : pour chaque
// image longue (> 33 ms), QUI était en train de travailler ? On garde :
//  - les 5 pires images, chacune avec son rendu CPU, ses postes CPU (PerfPostes) et la pause
//    du ramasse-miettes .NET (GC) survenues PENDANT cet intervalle ;
//  - pour les images > 33 ms : combien coïncident avec une semaine en cours
//    d'application (étalement), un step en vol côté Python, ou un GC ;
//  - le pire passage et les octets alloués par FAMILLE d'étalement, les collectes
//    GC par génération (+ le dernier GC : pause, finaliseurs en attente), les
//    cuissons de plantes et leurs poses (D109 c).
// Les suspects du kickoff ④ (application de la semaine, parsing du snapshot,
// cuisson, GC) se départagent ainsi par mesure et non par intuition.
//
// 📖 Pédagogie (côté embarqué) : c'est un « trigger » d'oscilloscope. Au lieu de
// moyenner (qui noie l'événement rare), on capture l'état des compteurs autour
// de l'événement anormal — ici, une image trop longue.
//  - L'intervalle mesuré (horloge murale, PerfMesure.cs) va d'un appel de
//    MesurerPerfRendu au suivant ; les deltas de postes sont pris aux MÊMES
//    instants → ils décrivent exactement le travail de cet intervalle (la fin
//    du _Process précédent, son rendu, le début du _Process courant).
//  - `GC.GetTotalPauseDuration()` (.NET 7+) = temps cumulé où le GC a suspendu
//    les threads managés ; son delta par image = la pause GC de cette image.
//  - Tableaux préalloués : zéro allocation par image (sinon l'instrument
//    nourrirait lui-même le GC qu'il cherche à mesurer).

using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Symbiose
{
	public partial class WorldView
	{
		private const int AcoupsPires = 5;

		private readonly long[] _acPrec = new long[PerfPostes.Nombre];
		private readonly long[] _acCour = new long[PerfPostes.Nombre];
		private double _acGcPrecMs;
		private int _acGcNbPrec;

		// Images > 33 ms et leurs coïncidences.
		private int _acLongues, _acEtale, _acStep, _acGc;
		private double _acGcTotalMs;

		private sealed class PireImage
		{
			public double Ms, GcMs, RenduMs;
			public bool Etale, Step;
			public readonly long[] Postes = new long[PerfPostes.Nombre];
		}
		private readonly List<PireImage> _acPires = new();

		// Pire passage d'UNE famille d'étalement dans une image (µs), par famille.
		private static readonly string[] NomsFamilles =
			{ "sol", "plantes", "vie macro", "couches sol", "structures", "météo", "ménage" };
		private readonly long[] _acFamilleMaxUs = new long[NomsFamilles.Length];
		private readonly int[] _acGcGen = new int[3];
		private long _acOctets0;
		private long _acCuissons0, _acPoses0;   // cuissons de plantes (PlantBaker)   // octets alloués, tous threads, au début de la fenêtre

		private readonly long[] _acFamilleOctets = new long[NomsFamilles.Length];

		private void NoterFamille(int famille, long us, long octets)
		{
			if (_distMs == null) return;
			if (us > _acFamilleMaxUs[famille]) _acFamilleMaxUs[famille] = us;
			_acFamilleOctets[famille] += octets;
		}

		private static double GcPauseMs() => System.GC.GetTotalPauseDuration().TotalMilliseconds;
		private static int GcNombre() => System.GC.CollectionCount(0);   // gen 0 compte toutes les collectes

		/// <summary>Ouvre la fenêtre (appelé par DemarrerDistribution).</summary>
		private void DemarrerAcoups()
		{
			PerfPostes.Copier(_acPrec);
			_acGcPrecMs = GcPauseMs();
			_acGcNbPrec = GcNombre();
			_acLongues = _acEtale = _acStep = _acGc = 0;
			_acGcTotalMs = 0;
			_acPires.Clear();
			System.Array.Clear(_acFamilleMaxUs);
			System.Array.Clear(_acFamilleOctets);
			for (int g = 0; g < 3; g++) _acGcGen[g] = System.GC.CollectionCount(g);
			_acOctets0 = System.GC.GetTotalAllocatedBytes(false);
			_acCuissons0 = PlantBaker.Cuissons;
			_acPoses0 = PlantBaker.PosesCuites;
		}

		/// <summary>Une image mesurée : deltas de postes et de GC sur son intervalle.</summary>
		private void EchantillonAcoups(double frameMs)
		{
			PerfPostes.Copier(_acCour);
			double gc = GcPauseMs();
			int gcNb = GcNombre();
			double gcMs = gc - _acGcPrecMs;
			bool gcIci = gcNb != _acGcNbPrec;
			_acGcTotalMs += gcMs;
			bool etale = _etale != null, step = _pendingStep != null;
			if (frameMs > 33.0)
			{
				_acLongues++;
				if (etale) _acEtale++;
				if (step) _acStep++;
				if (gcIci) _acGc++;
			}
			// Garde les AcoupsPires pires (liste triée décroissante, très courte).
			if (_acPires.Count < AcoupsPires || frameMs > _acPires[^1].Ms)
			{
				var p = _acPires.Count < AcoupsPires ? new PireImage() : _acPires[^1];
				_acPires.Remove(p);
				p.Ms = frameMs; p.GcMs = gcMs; p.RenduMs = RenduCpuDerniere(); p.Etale = etale; p.Step = step;
				for (int i = 0; i < PerfPostes.Nombre; i++) p.Postes[i] = _acCour[i] - _acPrec[i];
				int k = _acPires.FindIndex(q => q.Ms < frameMs);
				_acPires.Insert(k < 0 ? _acPires.Count : k, p);
			}
			System.Array.Copy(_acCour, _acPrec, PerfPostes.Nombre);
			_acGcPrecMs = gc;
			_acGcNbPrec = gcNb;
		}

		// Rendu CPU de la dernière image dessinée (fenêtre + SubViewport monde), ms.
		private double RenduCpuDerniere() =>
			Godot.RenderingServer.ViewportGetMeasuredRenderTimeCpu(GetViewport().GetViewportRid())
			+ Godot.RenderingServer.ViewportGetMeasuredRenderTimeCpu(_worldVp.GetViewportRid());

		/// <summary>Bloc « à-coups » du rapport du banc.</summary>
		private void EcrireAcoups(StringBuilder sb, int n)
		{
			var ci = CultureInfo.InvariantCulture;
			sb.AppendLine(string.Create(ci,
				$"  à-coups : {_acLongues} images > 33 ms, dont {_acEtale} pendant l'application d'une "
				+ $"semaine, {_acStep} avec un step en vol, {_acGc} avec un GC · pause GC totale "
				+ $"{_acGcTotalMs:F1} ms ({_acGcTotalMs / System.Math.Max(1, n):F2} ms/image)"));
			var fam = new StringBuilder("    étalement, pire passage par famille :");
			for (int i = 0; i < NomsFamilles.Length; i++)
				fam.Append(string.Create(ci, $" {NomsFamilles[i]} {_acFamilleMaxUs[i] / 1000.0:F1}"));
			sb.AppendLine(fam.Append(" ms").ToString());
			var oct = new StringBuilder("    étalement, alloué par famille :");
			for (int i = 0; i < NomsFamilles.Length; i++)
				oct.Append(string.Create(ci, $" {NomsFamilles[i]} {_acFamilleOctets[i] / 1048576.0:F1}"));
			sb.AppendLine(oct.Append(" Mo").ToString());
			sb.AppendLine($"    collectes GC gen0/1/2 : {System.GC.CollectionCount(0) - _acGcGen[0]}"
				+ $" / {System.GC.CollectionCount(1) - _acGcGen[1]} / {System.GC.CollectionCount(2) - _acGcGen[2]}"
				+ $" · mode {System.Runtime.GCSettings.LatencyMode}"
				+ $" · serveur GC {System.Runtime.GCSettings.IsServerGC}"
				+ $" · alloué {(System.GC.GetTotalAllocatedBytes(false) - _acOctets0) / 1048576.0:F0} Mo (tous threads)");
			long cu = PlantBaker.Cuissons - _acCuissons0, po = PlantBaker.PosesCuites - _acPoses0;
			sb.AppendLine(string.Create(ci,
				$"    cuissons {cu} · poses cuites {po} ({(cu > 0 ? (double)po / cu : 0):F1} par cuisson) · "
				+ $"vent force {WindWave.Force:F2} ({(WindWave.Active ? "actif" : "calme")})"));
			var gi = System.GC.GetGCMemoryInfo(System.GCKind.Any);
			if (gi.Index > 0)
				sb.AppendLine(string.Create(ci,
					$"    dernier GC : gen{gi.Generation} · pause {gi.PauseDurations[0].TotalMilliseconds:F1} ms · "
					+ $"tas {gi.HeapSizeBytes / 1048576.0:F0} Mo · promus {gi.PromotedBytes / 1048576.0:F1} Mo · "
					+ $"épinglés {gi.PinnedObjectsCount} · finaliseurs en attente {gi.FinalizationPendingCount} · "
					+ $"compacté {gi.Compacted} · concurrent {gi.Concurrent}"));
			foreach (var p in _acPires)
				sb.AppendLine(string.Create(ci,
					$"    pire {p.Ms:F1} ms : rendu CPU {p.RenduMs:F1} ms · {PerfPostes.Detail(p.Postes, 0.5)} · GC {p.GcMs:F1} ms"
					+ $"{(p.Etale ? " · étalement" : "")}{(p.Step ? " · step en vol" : "")}"));
		}
	}
}
