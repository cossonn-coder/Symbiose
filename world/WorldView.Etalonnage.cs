// SYMBIOSE — WorldView.Etalonnage.cs (partial de WorldView, sprint PERF VUE ①)
// BANC D'ÉTALONNAGE : touche E = le MÊME scénario sur la VM et sur le PC de Nico,
// sans ligne de commande (F5 dans l'éditeur, monde « full », puis E) :
//   1. AVANCE   — turbo jusqu'à la semaine moteur EtalonSemaine (printemps an 2) ;
//   2. CADRAGE  — zoom ×4 sur EtalonCentreCm, cadence NOMINALE (60 s/semaine :
//                 vent et animations à vitesse normale, aucun step pendant la mesure) ;
//   3. REPOS    — EtalonReposSec secondes (fin de l'étalement, file de cuisson) ;
//   4. MESURE   — EtalonMesureSec secondes : distribution des images + postes CPU ;
//   5. RAPPORT  — copié au presse-papier (comme C), mode et cadence restaurés.
// Re-E pendant le banc = abandon (mode et cadence restaurés).
//
// Déterminisme : graine (Seed) et warmup identiques au lancement normal, puis
// uniquement des semaines sans geste → le même jardin sur les deux machines. Le
// turbo s'arrête AVANT le lancement du step suivant (AvancerEtalonnage est appelé
// dans _Process entre l'étalement et le lancement), donc jamais une semaine de trop.
//
// Banc VM : `tools/perf_vm.sh -E <s>` passe `--capture-etalonnage=<s>` (même code ;
// `-z`/`-c` y remplacent zoom et centre, `-x MacroLife` / `-O` masquent vie macro et
// ombres ; `-A` la cadence pendant la mesure, PERF VUE ④). En capture, le rapport s'imprime entre `[banc] DEBUT` et `[banc] FIN`
// puis le jeu quitte.
//
// 📖 Pédagogie (côté embarqué) : une petite machine à états pilotée par la boucle
// principale (`_Process`), comme une séquence de test de production : chaque état
// attend sa condition (semaine atteinte, délai écoulé), jamais de blocage.

using Godot;
using System.Globalization;
using System.Text;

namespace Symbiose
{
	public partial class WorldView
	{
		// Scénario (VÉRIFIÉ PAR MESURE au tronçon ①, cf. 00_etat.md du sprint). Seed 42,
		// monde full : semaine moteur 45 = fin d'automne/hiver an 1, 272 plantes et 3848
		// bêtes servies [n=1 graine]. Le printemps an 2 visé par le kickoff (300-400
		// plantes) n'a AUCUNE vie macro (die-off hivernal : 0-4 bêtes, semaines 48-61) ;
		// l'été an 2 en a 5000 mais 550+ plantes → `-W 67` (perf_vm.sh) = cas de stress.
		// Centre = la cellule de 1 m la plus dense en plantes + bêtes (tuile E).
		private const int EtalonSemaineDefaut = 45;
		private static readonly Vector2 EtalonCentreCm = new(1650f, 950f);
		private const float EtalonZoom = 4f;
		private const float EtalonReposSec = 8f;
		private const float EtalonMesureSec = 20f;

		private enum EtatBanc { Inactif, Avance, Repos, Mesure }
		private EtatBanc _banc = EtatBanc.Inactif;
		private double _bancT0;                 // début de l'état courant (s, horloge murale)
		private float _bancMesureSec = EtalonMesureSec;
		private float _bancSpwAvant;            // cadence et mode restaurés à la fin
		private SimMode _bancModeAvant;
		private string _configLancee = "?";     // monde monté (posé par StartSimulation)

		// Arguments du banc VM (cf. WorldView.Capture.cs pour les autres).
		private static readonly float CaptureEtalonnage = ParseFloat(ArgCapture("etalonnage"));
		private static readonly string CaptureOmbres = ArgCapture("ombres");
		private static readonly float CaptureBancSemaine = ParseFloat(ArgCapture("banc-semaine"));
		// Zoom / centre du CADRAGE (étape 2) : l'avance turbo, elle, se fait au cadrage
		// de départ (×0,5, monde entier) comme au F5 — c'est là que la vie macro fuit.
		private static readonly float CaptureBancZoom = ParseFloat(ArgCapture("banc-zoom"));
		private static readonly string CaptureBancCentre = ArgCapture("banc-centre");
		private string _bancCadrage = "";       // état de la vie macro au cadrage (fuite)
		// Cadence PENDANT la mesure (PERF VUE ④) : absente = nominale (60 s/semaine,
		// aucun step) ; 0 = turbo (« au plus vite ») ; s > 0 = s secondes par semaine
		// (1 = le défaut de test de Nico). Le rapport donne la cadence obtenue.
		private static readonly float CaptureBancCadence = ParseFloat(ArgCapture("banc-cadence"));
		private int _bancSemaineMesure;         // semaine moteur au début de la mesure
		private static int EtalonSemaine =>
			float.IsNaN(CaptureBancSemaine) ? EtalonSemaineDefaut : (int)CaptureBancSemaine;

		private int SemaineMoteur => _lastSnap == null ? -1 : _lastSnap["week"].AsInt32();
		private static double Maintenant => Time.GetTicksUsec() / 1e6;

		/// <summary>Touche E (ou `--capture-etalonnage`) : lance ou abandonne le banc.</summary>
		private void ToggleEtalonnage()
		{
			if (_banc != EtatBanc.Inactif) { FinBanc(null); GD.Print("[banc] abandon."); return; }
			if (SemaineMoteur > EtalonSemaine)
			{
				GD.Print($"[banc] semaine moteur {SemaineMoteur} > {EtalonSemaine} : relancer le jeu (F5) puis E.");
				_lastActionMsg = "banc E : jardin trop avancé — relancer le jeu puis E";
				UpdateActionHud();
				return;
			}
			if (!float.IsNaN(CaptureEtalonnage) && CaptureEtalonnage > 0f) _bancMesureSec = CaptureEtalonnage;
			_bancSpwAvant = DebugSecondsPerWeek;
			_bancModeAvant = _simMode;
			_simMode = SimMode.Turbo;
			SetPhase(Phase.Saison);
			_banc = EtatBanc.Avance;
			GD.Print($"[banc] avance turbo jusqu'à la semaine moteur {EtalonSemaine} "
				+ $"(actuelle {SemaineMoteur}).");
		}

		/// <summary>Appelé à chaque frame par _Process (no-op hors banc).</summary>
		private void AvancerEtalonnage()
		{
			switch (_banc)
			{
				case EtatBanc.Avance:
					if (SemaineMoteur < EtalonSemaine) return;
					// Cadence nominale : DebugSecondsPerWeek = 0 → SecondsPerWeek (60 s).
					_simMode = SimMode.Saison;
					DebugSecondsPerWeek = 0f;
					_timeAccum = 0f;
					CadrerBanc();
					_banc = EtatBanc.Repos;
					_bancT0 = Maintenant;
					GD.Print($"[banc] semaine {SemaineMoteur} atteinte → cadrage, repos {EtalonReposSec} s.");
					return;
				case EtatBanc.Repos:
					if (_etale != null || _pendingStep != null || Maintenant - _bancT0 < EtalonReposSec) return;
					DemarrerDistribution();
					PoserCadenceMesure();
					_banc = EtatBanc.Mesure;
					_bancT0 = Maintenant;
					GD.Print($"[banc] mesure {_bancMesureSec} s.");
					return;
				case EtatBanc.Mesure:
					if (Maintenant - _bancT0 < _bancMesureSec) return;
					var sb = new StringBuilder();
					sb.AppendLine(string.Create(CultureInfo.InvariantCulture,
						$"[banc E] semaine moteur {SemaineMoteur} · zoom ×{ZoomSteps[_zoomIndex]} · "
						+ $"centre {EtalonCentre().X:F0},{EtalonCentre().Y:F0} cm · mesure {_bancMesureSec:F0} s · monde {_worldVp.Size.X}×{_worldVp.Size.Y}"));
					sb.AppendLine($"  vie macro au cadrage (avant purge) : {_bancCadrage}");
					EcrireCadenceMesure(sb);
					EcrireDistribution(sb);
					FinBanc(ConstruireRapportPerf(sb.ToString()));
					return;
			}
		}

		private void PoserCadenceMesure()
		{
			_bancSemaineMesure = SemaineMoteur;
			if (float.IsNaN(CaptureBancCadence)) return;   // nominale : déjà posée
			if (CaptureBancCadence <= 0f) _simMode = SimMode.Turbo;
			else DebugSecondsPerWeek = CaptureBancCadence;
			_timeAccum = 0f;
		}

		private void EcrireCadenceMesure(StringBuilder sb)
		{
			int n = SemaineMoteur - _bancSemaineMesure;
			string consigne = float.IsNaN(CaptureBancCadence) ? "nominale 60 s/semaine"
				: CaptureBancCadence <= 0f ? "turbo (au plus vite)" : $"{CaptureBancCadence:F1} s/semaine";
			string obtenue = n > 0
				? string.Create(CultureInfo.InvariantCulture, $" → {_bancMesureSec / n:F2} s/semaine obtenues") : "";
			sb.AppendLine($"  cadence {consigne} : {n} semaines appliquées{obtenue}"
				+ $" · dernier tick vu par la vue {_lastTickMs:F0} ms");
		}

		// Zoom et centre du banc ; en capture VM, `-z` / `-c` les remplacent.
		private float EtalonZoomEffectif() => float.IsNaN(CaptureBancZoom) ? EtalonZoom : CaptureBancZoom;

		private Vector2 EtalonCentre()
		{
			string[] xy = CaptureBancCentre?.Split(',');
			return xy != null && xy.Length == 2
				? new Vector2(ParseFloat(xy[0]), ParseFloat(xy[1])) : EtalonCentreCm;
		}

		private void CadrerBanc()
		{
			if (_camera == null) return;
			// Fuite MacroLife (corrigée en ②) : les bêtes disparues ne sont purgées que
			// dans _Draw, absent sous MinZoom → on les compte AVANT le premier dessin à ×4.
			_bancCadrage = _macroLife == null ? "—"
				: $"{_macroLife.Count} entrées dont {_macroLife.CountMourantes} mourantes";
			int idx = System.Array.IndexOf(ZoomSteps, EtalonZoomEffectif());
			if (idx < 0) idx = System.Array.IndexOf(ZoomSteps, EtalonZoom);
			Vector2 c = EtalonCentre();
			PoserCamera(idx, WorldToScreen(c.X, c.Y));   // WorldView.Planche.cs
		}

		// Fin (rapport non nul) ou abandon (null) : cadence/mode restaurés, planification.
		private void FinBanc(string rapport)
		{
			_banc = EtatBanc.Inactif;
			_distMs = null;
			DebugSecondsPerWeek = _bancSpwAvant;
			_simMode = _bancModeAvant;
			SetPhase(Phase.Planification);
			if (rapport == null) return;
			CopierRapport(rapport);
			_lastActionMsg = "banc E terminé — rapport copié (presse-papier)";
			UpdateActionHud();
			if (!CaptureActive) return;
			GD.Print("[banc] DEBUT\n" + rapport + "[banc] FIN");
			GetTree().Quit();
		}

		// Appelé en fin d'AppliquerCapture : options du banc VM.
		private void AppliquerCaptureBanc()
		{
			if (CaptureOmbres == "0" && ShadowsOn) ToggleShadows();
			if (!float.IsNaN(CaptureEtalonnage)) ToggleEtalonnage();
		}
	}
}
