// SYMBIOSE — WorldView.Capture.cs (sprint JARDIN VIVANT, T0 — banc de capture VM)
// Mode CAPTURE : lancé par `tools/capture_vm.sh` (Godot sous Xvfb + Movie Maker),
// il saute l'écran de sélection, monte directement un monde/banc et cadre la
// caméra à un palier de zoom donné. Les PNG eux-mêmes sont écrits par le Movie
// Maker de Godot (`--write-movie`), pas par ce code. Sert d'« yeux » à l'agent
// sur la VM sans écran — ce n'est PAS un livrable joueur.
//
// 📖 Pédagogie Godot/C# :
//  - OS.GetCmdlineUserArgs() rend les arguments placés APRÈS `--` sur la ligne
//    de commande Godot (ceux que le moteur ne consomme pas). Comme argv en C,
//    mais déjà filtré des options moteur.
//  - INACTIF PAR DÉFAUT : sans `--capture-banc=…`, `CaptureBanc` reste null et
//    rien ne change (le F5 de Nico, lancé sans argument, est intact).
//
// Arguments reconnus (après `--`) :
//   --capture-banc=<nom>     monde/banc à monter (full, smoke, propre, ou un banc
//                            du registre Python `BANCS`) — active le mode
//   --capture-zoom=<z>       palier de zoom (0.5 1 2 4 8 16 32) ; défaut = cadrage
//   --capture-centre=<x>,<y> point visé en cm monde (défaut = centre 1000,1000)
//   --capture-souris=<x>,<y> souris posée en px ÉCRAN (survol : losange, étiquette)
//   --capture-geste=<n>      slot de geste armé (0..9) — losange qui « respire »
//   --capture-vent=<f>[,<d>] force de vent imposée (0 = calme) et direction
//                            D'OÙ il vient en rad (défaut = celle du snapshot) — T3
//   --capture-meteo=<kind>[,<intensité>[,<durée_s>]]  météo imposée (ex. Canicule,
//                            « Pluie prolongée », Orage) ; après <durée_s> secondes de
//                            jeu, retour à celle du snapshot (observe l'« après ») — T4
//   --capture-semaines=<n>   semaines de warmup (défaut WarmupWeeks = 12) — T4
//   --capture-defile=1       lance le défilé « jardin vivant » (touche F12) — T5
//   --capture-seed=<n>       seed du monde (défaut Seed = 42 ; ex. 12345 pour le
//                            collapse du banc `effondrement`, cf. BANC_SEED) — T5
//   --capture-orient=<n>     orientation D35 imposée (0..3 quarts de tour) — D106 T2
//   --capture-cacher=<N1>,<N2>  couches masquées par NOM de nœud (Ground, Decor,
//                            Objects…) — banc temps réel tools/perf_vm.sh, même
//                            mécanique que Shift+F4 (WorldView.Couches.cs) — D106 T1

using Godot;
using System.Globalization;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView
	{
		// Parsés UNE fois au chargement de la classe (les arguments ne changent pas
		// pendant l'exécution). null / NaN = option absente.
		private static readonly string CaptureBanc = ArgCapture("banc");
		private static readonly float CaptureZoom = ParseFloat(ArgCapture("zoom"));
		private static readonly string CaptureCentre = ArgCapture("centre");
		private static readonly string CaptureSouris = ArgCapture("souris");
		private static readonly float CaptureGeste = ParseFloat(ArgCapture("geste"));
		private static readonly string CaptureVent = ArgCapture("vent");
		private static readonly string CaptureMeteo = ArgCapture("meteo");
		private static readonly float CaptureSemaines = ParseFloat(ArgCapture("semaines"));
		private static readonly bool CaptureDefile = ArgCapture("defile") != null;
		private static readonly float CaptureSeed = ParseFloat(ArgCapture("seed"));
		private static readonly string CaptureCacher = ArgCapture("cacher");
		// Orientation D35 imposée (0..3 quarts de tour, D106 T2 : vérifier le sol
		// en un lot sous les 4 orientations). Appliquée AVANT le centrage caméra.
		private static readonly float CaptureOrient = ParseFloat(ArgCapture("orient"));

		// Météo imposée par le banc (T4) : active jusqu'à l'échéance de sa durée.
		private bool _captureMeteoActive = CaptureMeteo != null;
		private GDict _lastWeather;

		// Vrai quand le jeu est lancé par le banc de capture (WorldView._Ready
		// saute alors le sélecteur de monde).
		private static bool CaptureActive => CaptureBanc != null;

		private static string ArgCapture(string cle)
		{
			string prefixe = $"--capture-{cle}=";
			foreach (string a in OS.GetCmdlineUserArgs())
				if (a.StartsWith(prefixe)) return a.Substring(prefixe.Length);
			return null;
		}

		private static float ParseFloat(string s) =>
			s != null && float.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out float v)
				? v : float.NaN;

		// Appelé AVANT StartSimulation : warmup imposé et fin programmée de la
		// météo imposée (minuterie de l'arbre = temps de jeu, fixe en Movie Maker).
		private void PreparerCapture()
		{
			if (!float.IsNaN(CaptureSemaines)) WarmupWeeks = Mathf.Max(0, (int)CaptureSemaines);
			if (!float.IsNaN(CaptureSeed)) Seed = (int)CaptureSeed;
			string[] m = CaptureMeteo?.Split(',');
			if (m == null || m.Length < 3) return;
			GetTree().CreateTimer(ParseFloat(m[2])).Timeout += () =>
			{
				_captureMeteoActive = false;
				GD.Print("[Capture] fin de la météo imposée → météo du snapshot.");
				if (_lastWeather != null) ApplyWeather(_lastWeather);
			};
		}

		// Bloc `weather` éventuellement remplacé par la météo imposée du banc.
		private GDict CaptureMeteoOverride(GDict weather)
		{
			if (!_captureMeteoActive) return weather;
			string[] m = CaptureMeteo.Split(',');
			var w = weather.Duplicate();
			w["kind"] = m[0];
			if (m.Length > 1) w["intensity"] = ParseFloat(m[1]);
			return w;
		}

		// Appelé APRÈS FrameCamera (monde construit) : impose le palier de zoom et
		// le point visé. On n'utilise pas StepZoom (zoom centré SOURIS — sous Xvfb
		// la souris n'a pas de position utile) : on pose directement l'état caméra,
		// puis on refait ce que StepZoom fait après coup (redraw LOD + culling).
		private void AppliquerCapture()
		{
			if (!CaptureActive || _camera == null) return;
			GD.Print($"[Capture] banc « {CaptureBanc} », zoom {CaptureZoom}, centre {CaptureCentre ?? "monde"}.");
			if (!float.IsNaN(CaptureOrient) && (int)CaptureOrient % 4 != 0)
				RotateView((int)CaptureOrient % 4);

			if (CaptureCentre != null)
			{
				string[] xy = CaptureCentre.Split(',');
				if (xy.Length == 2)
					_camera.Position = ClampToWorld(WorldToScreen(ParseFloat(xy[0]), ParseFloat(xy[1])));
			}
			if (!float.IsNaN(CaptureZoom))
			{
				int idx = System.Array.IndexOf(ZoomSteps, CaptureZoom);
				if (idx < 0)
					GD.PushWarning($"[Capture] zoom {CaptureZoom} hors paliers {string.Join(" ", ZoomSteps)} — ignoré.");
				else
				{
					_zoomIndex = idx;
					_camera.Zoom = Vector2.One * CaptureZoom;
					CurrentZoom = CaptureZoom;
				}
			}
			// Xvfb a un vrai pointeur X : WarpMouse le déplace, GetMousePosition le relit.
			if (CaptureSouris != null)
			{
				string[] s = CaptureSouris.Split(',');
				if (s.Length == 2)
				{
					Input.WarpMouse(new Vector2(ParseFloat(s[0]), ParseFloat(s[1])));
					ResemerSouris();   // T3 : la frame suivante relit le pointeur
				}
			}
			if (!float.IsNaN(CaptureGeste)) SelectSlot((int)CaptureGeste);
			// Vent imposé (T3) : rend l'onde observable quelle que soit la semaine.
			if (CaptureVent != null)
			{
				string[] v = CaptureVent.Split(',');
				WindWave.SetCaptureOverride(ParseFloat(v[0]),
											v.Length > 1 ? ParseFloat(v[1]) : float.NaN);
			}
			if (CaptureDefile) ToggleDefile();   // défilé jardin vivant (T5)
			if (CaptureCacher != null) AppliquerMasqueCouches();   // D106 T1
			RedrawAllPlants();
			CullPlants();
		}
	}
}
