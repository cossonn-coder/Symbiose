// SYMBIOSE — WorldView.PerfReport.cs (partial de WorldView, résorption D68)
// Le RAPPORT PERF ENRICHI copié au presse-papier (touche C). Extrait de
// WorldView.Hud.cs le 2026-07-09 (garde-fou taille : le Hud dépassait la
// bande) — un fichier = un concept. Ici : sérialiser en texte collable les
// métriques live du client PUIS le rapport serveur (pires ticks + état
// courant, répartition par tuile/espèce/segments). Aucun changement de
// comportement : simple déplacement (C# résout par type, partial même classe).

using Godot;
using System.Text;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Touche C (demande Nico) : copie un RAPPORT PERF ENRICHI dans le presse-
		// papier système — les métriques live du client, PUIS le rapport serveur
		// (top-K pires ticks + état courant, répartition par tuile/espèce/segments).
		// L'appel `PerfReport()` est SYNCHRONE : sûr même si une Task step/fields est
		// en vol grâce au verrou d'I/O de SimBridge (le bug de pont qu'on vient de
		// corriger). But : coller les chiffres ici, sans les retaper à la main.
		private void CopyPerfReport() => CopierRapport(ConstruireRapportPerf(null));

		// Le texte du rapport. `blocBanc` (banc d'étalonnage, touche E — PERF VUE ①)
		// s'insère juste sous l'en-tête : distribution des images + postes CPU.
		private string ConstruireRapportPerf(string blocBanc)
		{
			var sb = new StringBuilder();
			sb.AppendLine($"=== Rapport perf Symbiose — {_season} an {_year} "
				+ $"semaine {_weekInSeason}/13 ===");
			// Machine (VM ou PC de Nico ?) — les FPS ne se comparent qu'à machine égale.
			sb.AppendLine($"[machine] {OS.GetName()} · {OS.GetProcessorName()} "
				+ $"({OS.GetProcessorCount()} threads) · GPU {RenderingServer.GetVideoAdapterName()} "
				+ $"· pilote {RenderingServer.GetCurrentRenderingDriverName()} "
				+ $"· {(CaptureActive ? "banc VM (capture)" : "F5")}");
			if (blocBanc != null) sb.Append(blocBanc);
			// Ligne CLIENT (ce que la vue mesure : pipe+parse inclus).
			string tick = _lastTickMs < 0 ? "—" : $"{_lastTickMs:F0} ms";
			string cad = _lastWeekGapSec <= 0 ? "—"
				: $"{_lastWeekGapSec:F1} s/sem ({7.0 / _lastWeekGapSec:F1} j/s)";
			sb.AppendLine($"[client] FPS {Engine.GetFramesPerSecond():F0} · tick {tick} "
				+ $"· cadence {cad}");
			sb.AppendLine($"  plantes {_plantNodes.Count} (+{_nPousses} pousses) · "
				+ $"segments {_nSegments} · "
				+ $"vie macro {(_macroLife == null ? "—" : $"{_macroLife.Count} entrées dont {_macroLife.CountMourantes} mourantes, {(_macroLife.IsVisibleInTree() ? "AFFICHÉE" : "MASQUÉE")}")} · "
				+ $"butineurs {(_foragerLayer == null ? "—" : _foragerLayer.Count.ToString())} · "
				+ $"ombres {(ShadowsOn ? "ON" : "OFF")} · zoom ×{ZoomSteps[_zoomIndex]}");
			// Bascules de cadence : la même scène coûte autre chose en turbo qu'à 60 s/sem.
			float spw = DebugSecondsPerWeek > 0f ? DebugSecondsPerWeek : SecondsPerWeek;
			sb.AppendLine($"  cadence : phase {_phase} · mode {_simMode} · "
				+ $"{(_simMode == SimMode.Turbo ? "turbo" : $"{spw:F0} s/semaine")} · "
				+ $"monde « {_configLancee} » seed {Seed} · semaine moteur {SemaineMoteur}");
			// Ligne SERVEUR (tick moteur pur, cf. banc perf).
			string srvTick = _srvMsTick < 0 ? "—" : $"{_srvMsTick:F1} ms";
			sb.AppendLine($"[serveur] tick moteur {srvTick} · N plantes "
				+ $"{(_srvNPlants < 0 ? "—" : _srvNPlants.ToString())} · "
				+ $"RSS {(_srvRssMo < 0 ? "—" : $"{_srvRssMo:F0} Mo")}");
			sb.AppendLine($"[{LignePerfRendu()}]");   // envois GPU (PerfMesure.cs)

			// Rapport serveur enrichi (pires ticks + état courant).
			var rep = _bridge?.PerfReport();
			if (rep == null)
				sb.AppendLine("\n(rapport serveur indisponible — moteur muet)");
			else
			{
				sb.AppendLine("\n--- pires ticks (serveur) ---");
				var worst = rep["worst"].AsGodotArray();
				if (worst.Count == 0) sb.AppendLine("  (aucun tick enregistré)");
				foreach (var wv in worst)
					AppendDump(sb, wv.AsGodotDictionary());
				sb.AppendLine("--- état courant ---");
				AppendDump(sb, rep["current"].AsGodotDictionary());
			}
			return sb.ToString();
		}

		private void CopierRapport(string texte)
		{
			DisplayServer.ClipboardSet(texte);
			GD.Print("[WorldView] C → rapport perf copié dans le presse-papier "
				+ $"({texte.Length} caractères).");
			// Flash de la 2e ligne HUD comme accusé visuel (réutilise le tween).
			if (_actionLabel != null)
			{
				_lastActionMsg = "rapport perf copié (presse-papier)";
				UpdateActionHud();
			}
		}

		// Met en forme UN dump diagnostique (pire tick ou état courant) : ligne de
		// compteurs + répartition par tuile + par espèce. Format lisible, pensé pour
		// être collé tel quel dans un rapport ou un message.
		private static void AppendDump(StringBuilder sb, GDict d)
		{
			string rss = d["rss_mo"].VariantType == Variant.Type.Nil
				? "—" : $"{d["rss_mo"].AsDouble():F0} Mo";
			sb.AppendLine($"  s{d["week"].AsInt32()} (an {d["year"].AsInt32()}) : "
				+ $"{d["ms_tick"].AsDouble():F1} ms · {d["n_plants"].AsInt32()} pl · "
				+ $"{d["n_segments"].AsInt32()} seg · RSS {rss}");
			// Par tuile : id plants/segments.
			var pt = d["par_tuile"].AsGodotDictionary();
			var tuiles = new StringBuilder();
			foreach (var kv in pt)
			{
				var v = kv.Value.AsGodotDictionary();
				tuiles.Append($"{kv.Key.AsString()} {v["plants"].AsInt32()}/"
					+ $"{v["segments"].AsInt32()}  ");
			}
			sb.AppendLine($"    tuiles (pl/seg) : {tuiles.ToString().TrimEnd()}");
			// Par espèce : nom×n (déjà trié par abondance côté serveur).
			var pe = d["par_espece"].AsGodotDictionary();
			var especes = new StringBuilder();
			foreach (var kv in pe)
				especes.Append($"{kv.Key.AsString()}×{kv.Value.AsInt32()}  ");
			sb.AppendLine($"    espèces : {especes.ToString().TrimEnd()}");
		}
	}
}
