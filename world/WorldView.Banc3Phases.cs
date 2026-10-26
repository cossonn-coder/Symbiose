// SYMBIOSE — WorldView.Banc3Phases.cs (partial de WorldView, sprint FLUIDITÉ PC ①)
// BANC E EN 3 PHASES : un seul lancement qui dit OÙ part le CPU au PC de Nico
// (2 cœurs / 4 threads). Au même point de banc (graine, semaine, cadrage), trois
// fenêtres s'enchaînent, dans l'ordre C → A → B :
//   C — MOTEUR EN PAUSE : rendu actif, AUCUN step (la journée rejoue en boucle, le
//                         soleil et le vent bougent comme en A) → la vue seule ;
//   A — NORMAL          : cadence demandée (`-A`), rendu actif — le jeu tel quel ;
//   B — RENDU SUSPENDU  : les steps continuent à la même cadence, Godot ne dessine
//                         plus (`RenderingServer.RenderLoopEnabled = false`) → le
//                         moteur tourne SANS le rendu à côté. Pas d'images : seule la
//                         chaîne du step est rapportée.
// A↔B dit ce que le dessin coûte au moteur (contention ?) ; A↔C ce que le moteur
// coûte aux images (les 40-50 ms/image « inexpliqués » de D116).
// Pourquoi C d'abord (mesuré au banc VM, 1er essai A → B → C) : chaque phase à
// steps avance le jardin (~10-14 semaines en 25 s) ; C en dernier mesurait un autre
// jardin (24 semaines plus tard, une autre saison) ET la file de cuisson qui
// rattrapait la phase B. En tête, C voit le jardin exact du banc ; A le suit
// immédiatement, B (sans images) vient en dernier.
//
// Lancement : `--capture-banc-3phases=A,B,C` (secondes ; une valeur manquante prend
// le défaut 25,25,20), avec les arguments du banc E (`--capture-banc-cadence`,
// `--capture-banc-semaine`…). VM : `tools/perf_vm.sh -3 25,25,20 -A 1 -W 90`.
// La touche E sans ces arguments garde son comportement (une seule fenêtre).
//
// Précautions de la phase B :
//  - sans rendu il n'y a plus d'attente de synchro verticale : la boucle principale
//    tournerait à vide et volerait un cœur au moteur → `Engine.MaxFps` = 60 pendant B ;
//  - une page d'atlas lancée pendant B ne serait jamais rendue (rectangle vide une
//    fois « cuite ») → la file de cuisson est FIGÉE (BakeQueue.Suspendue), une image
//    AVANT de couper le rendu (les pages déjà lancées ont le temps d'être rendues) et
//    jusqu'au rétablissement (même image : Godot relit l'interrupteur après _Process) ;
//  - les `_Draw` des couches continuent d'enregistrer leurs commandes (Godot les
//    appelle hors rendu) : B retire le RENDU, pas tout le travail de la vue.
//
// 📖 Pédagogie (côté embarqué) : c'est la mesure « une tâche à la fois » d'un RTOS —
// on suspend la tâche d'affichage pour chronométrer la tâche de calcul seule, puis
// l'inverse, au lieu de deviner qui retarde qui en les regardant ensemble.

using Godot;
using System.Globalization;
using System.Text;

namespace Symbiose
{
	public partial class WorldView
	{
		private static readonly string CaptureBanc3 = ArgCapture("banc-3phases");
		private static readonly float[] Banc3Defaut = { 25f, 25f, 20f };
		private const int Banc3MinStepsB = 6;      // B s'allonge jusqu'à 6 steps…
		private const float Banc3PlafondB = 4f;    // … au plus 4× sa durée
		private const int Banc3MaxFpsB = 60;       // boucle bridée sans rendu (vsync absente)

		private float[] _b3Durees;                 // null = banc E ordinaire
		private bool Banc3Actif => _b3Durees != null;
		private StringBuilder _b3Sb;
		private ulong _b3Image;                    // image du gel de la cuisson
		private bool _b3RenduCoupe;
		private int _b3MaxFpsAvant;
		private Bilan3 _b3A, _b3B, _b3C;

		// Résumé d'une phase pour la synthèse finale.
		private struct Bilan3
		{
			public double Moy, Inexpl, Fps, TickSrv, StepVu, SecSem;
			public int Sup100, Steps;
		}

		/// <summary>Phase C : aucun step ne part, la journée rejoue.</summary>
		private bool BancMoteurEnPause => _banc == EtatBanc.PhaseC;

		// Appelé par ToggleEtalonnage : durées A/B/C (A remplace la durée de mesure).
		private void PreparerBanc3()
		{
			_b3Durees = null;
			if (CaptureBanc3 == null) return;
			_b3Durees = (float[])Banc3Defaut.Clone();
			string[] v = CaptureBanc3.Split(',');
			for (int i = 0; i < 3 && i < v.Length; i++)
			{
				float d = ParseFloat(v[i]);
				if (!float.IsNaN(d) && d > 0f) _b3Durees[i] = d;
			}
			_bancMesureSec = _b3Durees[0];
		}

		// Fin du repos (Etalonnage.cs) : distribution ouverte, cadence posée → phase C.
		private void EntrerPhaseC()
		{
			_b3Sb = new StringBuilder();
			_b3Sb.AppendLine(string.Create(CultureInfo.InvariantCulture,
				$"[banc E 3 phases] semaine moteur {_bancSemaineMesure} · zoom ×{ZoomSteps[_zoomIndex]} · "
				+ $"centre {EtalonCentre().X:F0},{EtalonCentre().Y:F0} cm · durées C/A/B {_b3Durees[2]:F0}/{_b3Durees[0]:F0}/{_b3Durees[1]:F0} s"
				+ $" · monde {_worldVp.Size.X}×{_worldVp.Size.Y}"));
			_b3Sb.AppendLine($"  vie macro au cadrage (avant purge) : {_bancCadrage}");
			_banc = EtatBanc.PhaseC;
			GD.Print($"[banc] phase C (moteur en pause) {_b3Durees[2]} s.");
		}

		// Fin de la fenêtre A (état Mesure) : bloc A écrit, cuisson figée, → VersB.
		private void TerminerPhaseA()
		{
			_b3Sb.AppendLine("── phase A — normal (rendu actif, steps à la cadence demandée)");
			EcrireCadenceMesure(_b3Sb);
			var d = EcrireDistribution(_b3Sb);
			EcrirePostesAccelere(_b3Sb);
			_b3A = Bilan(d);
			BakeQueue.Suspendue = true;
			_b3Image = Engine.GetProcessFrames();
			_banc = EtatBanc.VersB;
		}

		/// <summary>États PhaseC, VersB, PhaseB (appelé par AvancerEtalonnage).</summary>
		private void AvancerBanc3()
		{
			switch (_banc)
			{
				case EtatBanc.PhaseC:
					if (Maintenant - _bancT0 < _b3Durees[2]) return;
					_b3Sb.AppendLine("── phase C — moteur en pause (rendu actif, aucun step, la journée rejoue)");
					EcrireCadenceMesure(_b3Sb);
					var d = EcrireDistribution(_b3Sb);
					EcrirePostesAccelere(_b3Sb);
					_b3C = Bilan(d);
					// → A : même cadrage, les steps repartent à la cadence posée.
					DemarrerDistribution();
					DemarrerPostesAccelere();
					_bancSemaineMesure = SemaineMoteur;
					_bancT0 = Maintenant;
					_banc = EtatBanc.Mesure;
					GD.Print($"[banc] phase A (normal) {_bancMesureSec} s.");
					return;
				case EtatBanc.VersB:
					if (Engine.GetProcessFrames() < _b3Image + 2) return;   // pages lancées avant le gel : rendues
					_b3MaxFpsAvant = Engine.MaxFps;
					Engine.MaxFps = Banc3MaxFpsB;
					RenderingServer.RenderLoopEnabled = false;
					_b3RenduCoupe = true;
					DemarrerPostesAccelere();
					_bancSemaineMesure = SemaineMoteur;
					_bancT0 = Maintenant;
					_banc = EtatBanc.PhaseB;
					GD.Print($"[banc] phase B (rendu suspendu) {_b3Durees[1]} s, ≥ {Banc3MinStepsB} steps.");
					return;
				case EtatBanc.PhaseB:
					double t = Maintenant - _bancT0;
					if (t < _b3Durees[1]) return;
					if (_baSteps < Banc3MinStepsB && t < Banc3PlafondB * _b3Durees[1]) return;
					_b3Sb.AppendLine("── phase B — rendu suspendu (steps à la même cadence, aucune image dessinée)");
					EcrireCadenceMesure(_b3Sb);
					EcrirePostesAccelere(_b3Sb);
					_b3B = Bilan((0, 0, 0, 0));
					EcrireSynthese3(_b3Sb);
					FinBanc(ConstruireRapportPerf(_b3Sb.ToString()));   // rétablit le rendu
					return;
			}
		}

		private Bilan3 Bilan((double Moy, double Inexpl, int Sup100, double Fps) d)
		{
			int n = System.Math.Max(1, _baSteps);
			int sem = SemaineMoteur - _bancSemaineMesure;
			return new Bilan3
			{
				Moy = d.Moy, Inexpl = d.Inexpl, Sup100 = d.Sup100, Fps = d.Fps,
				Steps = _baSteps, TickSrv = _baSrv / n, StepVu = _baClient / n,
				SecSem = sem > 0 ? (Maintenant - _bancT0) / sem : double.NaN,
			};
		}

		// Les deux comparaisons qui tranchent D116, sur une ligne chacune.
		private void EcrireSynthese3(StringBuilder sb)
		{
			var ci = CultureInfo.InvariantCulture;
			sb.AppendLine("── synthèse 3 phases");
			sb.AppendLine(string.Create(ci,
				$"  A↔B (ce que le rendu coûte au moteur) : tick moteur {_b3A.TickSrv:F0} / {_b3B.TickSrv:F0} ms"
				+ $" · step vu par la vue {_b3A.StepVu:F0} / {_b3B.StepVu:F0} ms"
				+ $" · {_b3A.SecSem:F2} / {_b3B.SecSem:F2} s/semaine · steps {_b3A.Steps} / {_b3B.Steps}"));
			sb.AppendLine(string.Create(ci,
				$"  A↔C (ce que le moteur coûte aux images) : moyenne {_b3A.Moy:F1} / {_b3C.Moy:F1} ms"
				+ $" · inexpliqué {_b3A.Inexpl:F1} / {_b3C.Inexpl:F1} ms · images > 100 ms {_b3A.Sup100} / {_b3C.Sup100}"
				+ $" · FPS {_b3A.Fps:F1} / {_b3C.Fps:F1}"));
		}

		// Fin de banc ou abandon (FinBanc) : rendu rétabli, boucle débridée, cuisson
		// relancée. Idempotent (appelé aussi hors banc 3 phases).
		private void RetablirRenduBanc3()
		{
			if (_b3RenduCoupe)
			{
				RenderingServer.RenderLoopEnabled = true;
				Engine.MaxFps = _b3MaxFpsAvant;
				_b3RenduCoupe = false;
			}
			BakeQueue.Suspendue = false;
		}
	}
}
