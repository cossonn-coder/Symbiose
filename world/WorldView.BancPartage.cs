// SYMBIOSE — WorldView.BancPartage.cs (partial de WorldView, FLUIDITÉ PC PARTAGE ②)
// BANC DE PARTAGE : la phase A du banc 3 phases (WorldView.Banc3Phases.cs) se
// découpe en 4 SOUS-PHASES de SEC secondes, enchaînées dans le même run :
//   A1 régulateur OFF + moteur BelowNormal  (= la phase A d'avant ce sprint)
//   A2 régulateur OFF + moteur Normal
//   A3 régulateur 15  + moteur BelowNormal  (= le jeu tel qu'il est livré)
//   A4 régulateur 15  + moteur Normal
// Ordre conservé : C → A1..A4 → B. Le rapport finit par un tableau côte à côte
// (s/sem, tick, step vu, images moy., p99, > 100 ms, FPS, % du temps régulé) + le
// rappel de C et B. C'est la courbe « cadence ↔ images » qui tranche l'hypothèse
// TDP/L3 partagés de la conception (§2) et le réglage final de la priorité.
//
// Lancement : `--capture-banc-partage=SEC` EN PLUS des arguments du banc 3 phases
// (`--capture-banc-3phases=…`, `--capture-banc-cadence=…`…). VM :
// `tools/perf_vm.sh -3 25,25,20 -P 20 -A 1 -W 90 -S 1521550718`.
// Linux : remonter la priorité (nice) exige des droits → les sous-phases « Normal »
// y restent en BelowNormal, le rapport l'écrit (« non applicable »).
//
// Biais assumé : chaque sous-phase joue des semaines DIFFÉRENTES (le jardin avance
// d'environ SEC / s-par-semaine semaines à chaque fois), et un step lancé en fin de
// sous-phase est compté dans la suivante.
//
// 📖 Pédagogie (côté embarqué) : un plan d'expérience 2×2 (deux facteurs, deux
// niveaux) dans un seul banc — on ne change qu'un réglage à la fois entre deux
// lignes voisines, comme on balayerait fréquence × priorité d'une tâche RTOS.

using Godot;
using System.Globalization;
using System.Text;

namespace Symbiose
{
	public partial class WorldView
	{
		private static readonly float CapturePartage = ParseFloat(ArgCapture("banc-partage"));
		private static readonly string[] PartageNoms =
		{
			"A1 régulateur OFF · BelowNormal", "A2 régulateur OFF · Normal",
			"A3 régulateur 15  · BelowNormal", "A4 régulateur 15  · Normal",
		};

		private bool PartageActif => Banc3Actif && !float.IsNaN(CapturePartage) && CapturePartage > 0f;
		private int _bpIndex;
		private bool _bpTouche;                 // réglages modifiés → à rétablir
		private readonly Bilan3[] _bp = new Bilan3[4];
		private readonly string[] _bpPrio = new string[4];

		// Appelé par PreparerBanc3 : SEC remplace la durée de la phase A.
		private void PreparerPartage()
		{
			if (PartageActif) _bancMesureSec = CapturePartage;
		}

		// Début d'une sous-phase : régulateur et priorité posés (la fenêtre de mesure
		// est déjà ouverte par l'appelant).
		private void EntrerSousPhase(int i)
		{
			_bpIndex = i;
			_bpTouche = true;
			_regActif = i >= 2;
			_bpPrio[i] = _bridge?.PoserPriorite(normale: i % 2 == 1) ?? "moteur absent";
			GD.Print($"[banc] phase {PartageNoms[i]} {_bancMesureSec} s ({_bpPrio[i]}).");
		}

		/// <summary>Fin d'une sous-phase (TerminerPhaseA). Vrai quand A4 est close :
		/// l'appelant passe alors à la phase B.</summary>
		private bool TerminerSousPhase()
		{
			int i = _bpIndex;
			_b3Sb.AppendLine($"── phase {PartageNoms[i]} (priorité : {_bpPrio[i]})");
			EcrireCadenceMesure(_b3Sb);
			var d = EcrireDistribution(_b3Sb);
			EcrirePostesAccelere(_b3Sb);
			_bp[i] = Bilan(d);
			if (i < 3)
			{
				DemarrerDistribution();
				DemarrerPostesAccelere();
				_bancSemaineMesure = SemaineMoteur;
				_bancT0 = Maintenant;
				EntrerSousPhase(i + 1);
				return false;
			}
			_b3A = _bp[0];          // synthèse 3 phases : A1 = la phase A d'avant
			RetablirPartage();      // B se mesure avec les réglages du jeu
			return true;
		}

		// Fin de banc, abandon ou entrée en B : réglages du jeu (régulateur = choix
		// du joueur dans Paramètres, moteur BelowNormal). Idempotent.
		private void RetablirPartage()
		{
			if (!_bpTouche) return;
			_regActif = _regChoix;
			_bridge?.PoserPriorite(normale: false);
			_bpTouche = false;
		}

		private void EcrireSynthesePartage(StringBuilder sb)
		{
			var ci = CultureInfo.InvariantCulture;
			sb.AppendLine("── synthèse partage (régulateur × priorité moteur) — biais : chaque sous-phase "
				+ "joue des semaines différentes, comparer les tendances plutôt que les petits écarts");
			sb.AppendLine("  sous-phase                        s/sem   tick  step vu  img moy    p99  >100ms   FPS  régulé");
			for (int i = 0; i < 4; i++)
			{
				var b = _bp[i];
				sb.AppendLine(string.Create(ci,
					$"  {PartageNoms[i],-32} {b.SecSem,6:F2} {b.TickSrv,6:F0} {b.StepVu,8:F0} {b.Moy,8:F1} {b.P99,6:F1} {b.Sup100,7} {b.Fps,5:F1} {b.Regule,6:F0} %"));
			}
			sb.AppendLine(string.Create(ci,
				$"  rappel C (moteur en pause) : images moy. {_b3C.Moy:F1} ms · p99 {_b3C.P99:F1} · > 100 ms {_b3C.Sup100} · FPS {_b3C.Fps:F1}"));
			sb.AppendLine(string.Create(ci,
				$"  rappel B (rendu suspendu) : {_b3B.SecSem:F2} s/sem · tick {_b3B.TickSrv:F0} ms · step vu {_b3B.StepVu:F0} ms · steps {_b3B.Steps}"));
		}
	}
}
