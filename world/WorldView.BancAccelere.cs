// SYMBIOSE — WorldView.BancAccelere.cs (partial de WorldView, PLANTE ASSEMBLÉE ③)
// BANC ACCÉLÉRÉ : Maj+E rejoue le cas où le PC de Nico tombe à 5 FPS — jardin full,
// semaine moteur ~35, zoom ×8, mode CONTINU à 3 s/semaine — avec la même machine à
// états que le banc E (WorldView.Etalonnage.cs), et ajoute au rapport les postes
// propres au mode accéléré, que le rapport F4 n'avait pas :
//  - les STEPS de la fenêtre : durée vue par la vue, tick moteur Python, pipe
//    (calcul + transport), parse JSON (thread du pool), taille de la réponse ;
//  - le RETARD de cadence : temps où la vue voulait lancer une semaine mais ne
//    pouvait pas (step encore en vol côté Python, ou semaine précédente encore en
//    cours d'application) — dit si la cadence est tenue par le moteur ou par la vue ;
//  - la PRIORITÉ du moteur relue par l'OS (SimBridge.PrioriteEffective) : la ligne
//    dit si `BelowNormal` tient sous Windows.
// Les butineurs (ForagerLayer) ont leurs postes dans PerfPostes ; le GC et
// l'étalement par famille sont déjà au bloc « à-coups » (WorldView.PerfAcoups.cs).
// Équivalent VM : `tools/perf_vm.sh -E 20 -z 8 -A 3 -W 35`.
//
// 📖 Pédagogie (côté embarqué) : sur 2 cœurs, deux « tâches » se disputent le CPU —
// l'affichage (échéance 16 ms) et le moteur (échéance 3 s). On ne devine pas qui
// gêne qui : on mesure les deux côtés sur la même fenêtre, comme on relèverait le
// taux d'occupation de chaque tâche d'un RTOS avant de toucher aux priorités.

using Godot;
using System.Globalization;
using System.Text;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView
	{
		// Le cas de Nico (rapport F4 du 2026-10-19 : automne s35, ×8, continu 3 s/sem).
		private const int AccelSemaine = 35;
		private const float AccelZoom = 8f;
		private const float AccelCadence = 3f;

		private bool _bancAccelere;
		private string NomBanc => _bancAccelere ? "Maj+E accéléré" : "E";

		// Cumuls de la fenêtre de mesure (remis à zéro par DemarrerPostesAccelere).
		private int _baSteps;
		private double _baClient, _baClientMax, _baSrv, _baSrvMax;
		private double _baPipe, _baPipeMax, _baParse, _baParseMax, _baOctets;
		private double _baRetardStep, _baRetardEtale;   // secondes
		private double _baLecture, _baLectureMax;       // lecture des plantes (pool, FLUIDITÉ AN 2 ④)
		// Butineurs et fleurs pollinisées au DÉBUT de la fenêtre (FLUIDITÉ PC ①) : le
		// rapport ne lisait que l'état FINAL — « 0 butineur » en fin de mesure alors
		// qu'ils volaient (et se redessinaient à 24 Hz) au début (D116, faux indice).
		private int _baButineurs0 = -1, _baPollen0 = -1;

		// Fenêtre où les steps sont comptés : mesure avec images, ou phase B du banc
		// en 3 phases (rendu suspendu, aucune image — WorldView.Banc3Phases.cs).
		private bool MesureStepsActive => _distMs != null || _banc == EtatBanc.PhaseB;

		private void DemarrerPostesAccelere()
		{
			_baSteps = 0;
			_baClient = _baClientMax = _baSrv = _baSrvMax = 0;
			_baPipe = _baPipeMax = _baParse = _baParseMax = _baOctets = 0;
			_baRetardStep = _baRetardEtale = 0;
			_baLecture = _baLectureMax = 0;
			_baButineurs0 = _foragerLayer?.Count ?? -1;
			_baPollen0 = _foragerLayer?.FleursPollen ?? -1;
		}

		/// <summary>Appelé par _Process à chaque step consommé (no-op hors mesure).</summary>
		private void NoterStepBanc(SemaineRecue s)
		{
			if (!MesureStepsActive || s == null || _bridge == null) return;
			GDict snap = s.Snap;
			Cumul(ref _baLecture, ref _baLectureMax, s.LectureMs);   // plantes lues (pool, ④)
			_baSteps++;
			Cumul(ref _baClient, ref _baClientMax, _lastTickMs);
			Cumul(ref _baPipe, ref _baPipeMax, _bridge.StepPipeMs);
			Cumul(ref _baParse, ref _baParseMax, _bridge.StepParseMs);
			_baOctets += _bridge.StepOctets;
			if (snap.ContainsKey("perf"))
			{
				var mt = snap["perf"].AsGodotDictionary()["ms_tick"];
				if (mt.VariantType != Variant.Type.Nil) Cumul(ref _baSrv, ref _baSrvMax, mt.AsDouble());
			}
		}

		private static void Cumul(ref double somme, ref double max, double v)
		{
			somme += v;
			if (v > max) max = v;
		}

		/// <summary>Appelé par _Process juste avant le lancement d'un step : la semaine
		/// est due (`_timeAccum ≥ spw`) mais ne part pas → on compte ce retard.</summary>
		private void NoterRetardStep(float delta, float spw)
		{
			if (!MesureStepsActive || _timeAccum < spw) return;
			if (_pendingStep != null) _baRetardStep += delta;      // moteur pas fini
			else if (!VuePrete) _baRetardEtale += delta;          // vue pas finie (réserve pleine / bascule)
		}

		private void EcrirePostesAccelere(StringBuilder sb)
		{
			var ci = CultureInfo.InvariantCulture;
			int n = System.Math.Max(1, _baSteps);
			sb.AppendLine(string.Create(ci,
				$"  steps pendant la mesure : {_baSteps} · vu par la vue moy. {_baClient / n:F0} / max {_baClientMax:F0} ms"
				+ $" · tick moteur {_baSrv / n:F0} / {_baSrvMax:F0} ms · pipe (calcul+transport) {_baPipe / n:F0} / {_baPipeMax:F0} ms"));
			sb.AppendLine(string.Create(ci,
				$"    parse JSON (thread du pool) {_baParse / n:F1} / {_baParseMax:F1} ms · lecture plantes (pool) {_baLecture / n:F1} / {_baLectureMax:F1} ms · réponse {_baOctets / n / 1024.0:F0} Ko"
				+ $" · retard de cadence : step en vol {_baRetardStep:F1} s, semaine en application {_baRetardEtale:F1} s"));
			sb.AppendLine($"  priorité du moteur lue par l'OS : {_bridge?.PrioriteEffective() ?? "—"}"
				+ $" · butineurs début→fin {_baButineurs0}→{_foragerLayer?.Count ?? -1}"
				+ $" · fleurs pollinisées {_baPollen0}→{_foragerLayer?.FleursPollen ?? -1}");
		}
	}
}
