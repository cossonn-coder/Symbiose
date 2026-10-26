// SYMBIOSE — WorldView.ZoomJournal.cs (partial de WorldView, FLUIDITÉ PC LEVIERS ①)
// OUTIL « À-COUP DE ZOOM » : Nico sent un à-coup à chaque cran de molette. Ce
// journal l'EXTRAIT pendant qu'il zoome / dézoome, sans banc à lancer :
//  - à chaque palier changé (molette StepZoom, planche L, balayage scripté), on
//    ouvre une FENÊTRE d'observation (~1 s, au moins 3 images) et on y relève :
//    pire image, somme des images, images > 33 / > 100 ms, coût du redessin du
//    décor (capté sur DecorLayer, pas recalculé), plantes invalidées, longueur de
//    la file de cuisson au départ et le temps qu'elle met à se vider, postes CPU
//    (PerfPostes) de la pire image ;
//  - on garde les ZoomJournalMax derniers changements (borné) ;
//  - touche Z = rapport copié au presse-papier (une ligne par changement + une
//    synthèse par paire de paliers : pire, médiane des pires) ;
//  - `--capture-zoom-balayage=<s>` (tools/perf_vm.sh -Z) : balayage scripté
//    ×0,5 → ×32 → ×0,5, s secondes par palier, rapport imprimé puis sortie.
// C'est la MESURE « avant » des tronçons ② ③ : il ne corrige rien.
//
// 📖 Pédagogie (côté embarqué) : même idée que PerfAcoups.cs — un « trigger »
// d'oscilloscope, mais déclenché par un ÉVÉNEMENT (le changement de palier) et non
// par un seuil : on capture la fenêtre qui SUIT l'événement, là où l'à-coup vit.
// La file de cuisson se vide souvent après la fenêtre : on la suit à part (≤ 10 s).

using Godot;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Symbiose
{
	public partial class WorldView
	{
		private const int ZoomJournalMax = 40;
		private const double ZoomFenetreSec = 1.0;
		private const int ZoomFenetreImagesMin = 3;
		private const double ZoomFileSuiviMaxSec = 10.0;

		private sealed class ChangementPalier
		{
			public float Avant, Apres;
			public ulong T0Us;
			public int Images, Sup33, Sup100, Invalidees, FileDepart, FileMax;
			public double PireMs, SommeMs, DecorMs = -1, FileVideeMs = -1;
			public int DecorSommets;
			public long DecorDessins0;
			public bool Fenetre = true, SuiviFile = true;
			public readonly long[] PostesPire = new long[PerfPostes.Nombre];
		}

		private readonly List<ChangementPalier> _zj = new();
		private ChangementPalier _zjCour;
		private readonly long[] _zjPrec = new long[PerfPostes.Nombre];
		private readonly long[] _zjTmp = new long[PerfPostes.Nombre];

		/// <summary>Un palier vient de changer (appelé APRÈS redraw + culling, pour que
		/// la file de cuisson de départ soit déjà remplie).</summary>
		private void NoterChangementPalier(float avant, float apres)
		{
			if (_zjCour != null) _zjCour.Fenetre = _zjCour.SuiviFile = false;   // interrompu par ce cran
			var c = new ChangementPalier
			{
				Avant = avant, Apres = apres, T0Us = Time.GetTicksUsec(),
				Invalidees = _plantNodes.Count,   // RedrawAllPlants invalide chaque nœud
				FileDepart = BakeQueue.FileEligibles,
				DecorDessins0 = DecorLayer.Dessins,
			};
			c.FileMax = c.FileDepart;
			_zj.Add(c);
			if (_zj.Count > ZoomJournalMax) _zj.RemoveAt(0);
			_zjCour = c;
			PerfPostes.Copier(_zjPrec);
		}

		/// <summary>Une image mesurée (PerfMesure.cs) : alimente la fenêtre ouverte et
		/// le suivi de la file de cuisson. Zéro allocation.</summary>
		private void EchantillonZoom(double frameMs)
		{
			var c = _zjCour;
			if (c == null) return;
			double ecoule = (Time.GetTicksUsec() - c.T0Us) / 1e6;
			if (c.Fenetre)
			{
				PerfPostes.Copier(_zjTmp);
				c.Images++;
				c.SommeMs += frameMs;
				if (frameMs > 33.0) c.Sup33++;
				if (frameMs > 100.0) c.Sup100++;
				if (frameMs > c.PireMs)
				{
					c.PireMs = frameMs;
					for (int i = 0; i < PerfPostes.Nombre; i++) c.PostesPire[i] = _zjTmp[i] - _zjPrec[i];
				}
				System.Array.Copy(_zjTmp, _zjPrec, PerfPostes.Nombre);
				if (DecorLayer.Dessins != c.DecorDessins0)
				{
					c.DecorMs = DecorLayer.DernierDessinMs;
					c.DecorSommets = DecorLayer.DernierDessinSommets;
				}
				if (ecoule >= ZoomFenetreSec && c.Images >= ZoomFenetreImagesMin) c.Fenetre = false;
			}
			if (!c.SuiviFile) { if (!c.Fenetre) _zjCour = null; return; }
			int file = BakeQueue.FileEligibles;
			if (file > c.FileMax) c.FileMax = file;
			if (file == 0)
			{
				c.FileVideeMs = ecoule * 1000.0;
				c.SuiviFile = false;
			}
			else if (ecoule > ZoomFileSuiviMaxSec) c.SuiviFile = false;
		}

		// Touche Z : rapport des à-coups de zoom au presse-papier.
		private void CopierRapportZoom() => CopierRapport(ConstruireRapportZoom());

		private string ConstruireRapportZoom()
		{
			var ci = CultureInfo.InvariantCulture;
			var sb = new StringBuilder();
			sb.AppendLine($"=== À-coups de zoom Symbiose — {_zj.Count} changement(s) de palier "
				+ $"(les {ZoomJournalMax} derniers au plus) — {_season} an {_year} semaine {_weekInSeason}/13 ===");
			sb.AppendLine($"[machine] {OS.GetName()} · {OS.GetProcessorName()} · GPU "
				+ $"{RenderingServer.GetVideoAdapterName()} · {(CaptureActive ? "banc (capture)" : "F5")} "
				+ $"· plantes {_plantNodes.Count} · monde « {_configLancee} » seed {Seed}");
			sb.AppendLine("  fenêtre = ~1 s après le changement (≥ 3 images) ; décor = dernier _Draw du "
				+ "décor dans la fenêtre (— = pas de redessin) ; file = plantes à cuire à l'écran/marge");
			foreach (var c in _zj)
			{
				string decor = c.DecorMs < 0 ? "—" : string.Create(ci, $"{c.DecorMs:F1} ms ({c.DecorSommets} sommets)");
				string vide = c.FileVideeMs >= 0
					? string.Create(ci, $"vidée en {c.FileVideeMs:F0} ms")
					: c.SuiviFile ? "en cours" : "non vidée (suivi clos)";
				sb.AppendLine(string.Create(ci,
					$"  ×{c.Avant}→×{c.Apres} : pire {c.PireMs:F1} ms · somme {c.SommeMs:F0} ms / {c.Images} images · "
					+ $">33 : {c.Sup33} · >100 : {c.Sup100} · décor {decor} · invalidées {c.Invalidees} · "
					+ $"file {c.FileDepart} (max {c.FileMax}) {vide} · pire image : {PerfPostes.Detail(c.PostesPire, 0.5)}"));
			}
			EcrireSyntheseZoom(sb);
			return sb.ToString();
		}

		// Synthèse par paire « avant→après » : n, pire des pires, médiane des pires.
		private void EcrireSyntheseZoom(StringBuilder sb)
		{
			var paires = new SortedDictionary<(float, float), List<double>>();
			foreach (var c in _zj)
			{
				if (!paires.TryGetValue((c.Avant, c.Apres), out var l)) paires[(c.Avant, c.Apres)] = l = new();
				l.Add(c.PireMs);
			}
			sb.AppendLine("--- synthèse par paire de paliers (pire image de chaque changement) ---");
			foreach (var kv in paires)
			{
				var l = kv.Value;
				l.Sort();
				double med = l.Count % 2 == 1 ? l[l.Count / 2] : (l[l.Count / 2 - 1] + l[l.Count / 2]) / 2;
				sb.AppendLine(string.Create(CultureInfo.InvariantCulture,
					$"  ×{kv.Key.Item1}→×{kv.Key.Item2} : n={l.Count} · pire {l[^1]:F1} ms · médiane {med:F1} ms"));
			}
		}

		// --- Balayage scripté (banc VM) -------------------------------------
		// --capture-zoom-balayage=<s> : après un repos initial (2 s : cuisson du
		// montage), ×0,5 → ×32 → ×0,5 sur la position caméra courante, s secondes
		// par palier ; rapport imprimé entre « [zoom] DEBUT » et « [zoom] FIN », sortie.
		private static readonly float CaptureZoomBalayage = ParseFloat(ArgCapture("zoom-balayage"));
		private const float BalayageReposSec = 2f;

		private void LancerBalayageZoom()
		{
			if (float.IsNaN(CaptureZoomBalayage) || CaptureZoomBalayage <= 0f || _camera == null) return;
			var suite = new List<int>();
			for (int i = 0; i < ZoomSteps.Length; i++) suite.Add(i);
			for (int i = ZoomSteps.Length - 2; i >= 0; i--) suite.Add(i);
			if (_zoomIndex == 0) suite.RemoveAt(0);   // déjà à ×0,5 : pas de faux changement
			GD.Print($"[zoom] balayage {suite.Count} paliers, {CaptureZoomBalayage} s chacun.");
			GetTree().CreateTimer(BalayageReposSec).Timeout += () => EtapeBalayage(suite, 0);
		}

		private void EtapeBalayage(List<int> suite, int k)
		{
			if (k >= suite.Count)
			{
				GD.Print("[zoom] DEBUT\n" + ConstruireRapportZoom() + "[zoom] FIN");
				GetTree().Quit();
				return;
			}
			PoserCamera(suite[k], _camera.Position);
			GetTree().CreateTimer(CaptureZoomBalayage).Timeout += () => EtapeBalayage(suite, k + 1);
		}
	}
}
